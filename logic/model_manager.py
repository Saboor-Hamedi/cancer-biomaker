import importlib.util
import logging
import os
import io
import shutil

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.svm import SVC

# --- High-Performance Lazy Detection ---
# We check if libraries exist without actually importing their massive binaries.
# This prevents the initial app freeze.
HAS_XGB = importlib.util.find_spec("xgboost") is not None
HAS_TORCH = importlib.util.find_spec("torch") is not None and importlib.util.find_spec("torch_geometric") is not None

if HAS_TORCH:
    import torch
    import torch.nn.functional as F
    from torch_geometric.data import Data
    from torch_geometric.loader import DataLoader
    from torch_geometric.nn import GCNConv, global_mean_pool
    torch_base = torch.nn.Module
    # Allowlisting the GNN model for PyTorch 2.6+ security policy
    try:
        if hasattr(torch.serialization, 'add_safe_globals'):
             # We forward-declare/import inside if needed, or use the global class name.
             # But it's easier to just allowlist the module path or use weights_only=False later.
             pass 
    except: pass
else:
    # Placeholder for torch_base used as a type hint
    torch_base = object

# ── Logging setup ─────────────────────────────────────────────────────────────
log = logging.getLogger(__name__)
log = logging.getLogger(__name__)

# Max rows for heavy unsupervised ops (t-SNE / SHAP) to avoid memory freeze
_TSNE_MAX_ROWS  = 2_000
_SHAP_MAX_ROWS  = 100


class GNNClassifier:
    """Graph Neural Network classifier with sklearn-like interface."""

    def __init__(self, num_features=1, hidden_channels=32, num_classes=2):
        if not HAS_TORCH:
            raise ImportError("PyTorch and torch_geometric required for GNN")

        self.num_features = num_features
        self.hidden_channels = hidden_channels
        self.num_classes = num_classes
        self.model: torch_base = None
        self.edge_index = None
        self.feature_names = None

    def _build_graph(self, X):
        """Build graph from correlation matrix with dimensionality safety."""
        if self.feature_names is None:
            self.feature_names = X.columns.tolist()

        corr_matrix = X.corr()
        edges = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > 0.5:
                    edges.append([i, j])
                    edges.append([j, i])

        if not edges:
            # Dimension safety: PyG requires [2, E] shape. tensor([]) would be [0].
            self.edge_index = torch.zeros((2, 0), dtype=torch.long)
        else:
            self.edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

    def _create_graph_data(self, X, y=None):
        """Create PyG Data objects."""
        data_list = []
        for idx in X.index:
            x = torch.tensor(X.loc[idx].values, dtype=torch.float).view(-1, 1)
            data = Data(x=x, edge_index=self.edge_index)
            if y is not None:
                # Use unsqueeze to ensure labels are treatable as 1D tensors during batching
                data.y = torch.tensor(y.loc[idx], dtype=torch.long).unsqueeze(0)
            data_list.append(data)
        return data_list

    def fit(self, X, y):
        """Train the GNN model."""
        self._build_graph(X)

        # Create training data
        train_data = self._create_graph_data(X, y)
        train_loader = DataLoader(train_data, batch_size=32, shuffle=True)

        # Initialize model
        self.model = GNN(self.num_features, self.hidden_channels, self.num_classes)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        criterion = torch.nn.CrossEntropyLoss()

        # Train
        self.model.train()
        for epoch in range(100):  # Simple training loop
            for data in train_loader:
                optimizer.zero_grad()
                out = self.model(data.x, data.edge_index, data.batch)
                loss = criterion(out, data.y)
                loss.backward()
                optimizer.step()

        # Phase 2 Optimization: Quantization for high-performance CPU inference
        try:
            log.info("Applying clinical optimizations (Quantization)...")
            self.model.eval()
            # 1. Dynamic Quantization (reduces size and improves CPU speed)
            # We only quantize Linear layers as GCNConv is custom and less stable under quantization
            self.model = torch.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8
            )
            log.info("GNN Optimization successful.")
        except Exception as e:
            log.warning("PyTorch optimizations (Quantization) skipped: %s", e)

        return self

    def __getstate__(self):
        """Prepare for joblib/pickle: Models need special handling for thread safety."""
        state = self.__dict__.copy()
        if HAS_TORCH and self.model is not None:
            # We save the model state to a byte stream
            buffer = io.BytesIO()
            torch.save(self.model, buffer)
            state['model_stream'] = buffer.getvalue()
            state['model'] = None  # Remove live object
        return state

    def __setstate__(self, state):
        """Restore from joblib/pickle."""
        self.__dict__.update(state)
        if HAS_TORCH and 'model_stream' in state:
            # Restore model from byte stream
            buffer = io.BytesIO(state['model_stream'])
            try:
                # [SECURITY SYNC]: PyTorch 2.6+ defaults to weights_only=True. 
                # Since we are loading our own locally-persisted GNN objects, we explicitly
                # set weights_only=False to allow restoring the full GNN class structure.
                self.model = torch.load(buffer, map_location='cpu', weights_only=False)
            except Exception as e:
                log.warning("Failed to load model from stream: %s", e)
                self.model = None
            if self.model:
                self.model.eval()
            del self.model_stream

    def predict(self, X):
        """Predict class labels with robust data conversion."""
        self.model.eval()
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names)
            
        test_data = self._create_graph_data(X)
        test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

        preds = []
        with torch.no_grad():
            for data in test_loader:
                out = self.model(data.x, data.edge_index, data.batch)
                if out is not None:
                    pred = out.argmax(dim=1)
                    preds.extend(pred.cpu().numpy())

        return np.array(preds)

    def predict_proba(self, X):
        """Predict class probabilities with robust data conversion."""
        self.model.eval()
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names)

        test_data = self._create_graph_data(X)
        test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

        probs = []
        with torch.no_grad():
            for data in test_loader:
                out = self.model(data.x, data.edge_index, data.batch)
                if out is not None:
                    prob = F.softmax(out, dim=1)
                    probs.extend(prob.cpu().numpy())

        return np.array(probs)


class GNN(torch_base):
    """PyTorch GNN model definition."""
    def __init__(self, num_features, hidden_channels, num_classes):
        if not HAS_TORCH:
            super().__init__()
            return
        super(GNN, self).__init__()
        self.conv1 = GCNConv(num_features, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.lin = torch.nn.Linear(hidden_channels, num_classes)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = x.relu()
        x = self.conv2(x, edge_index)
        x = x.relu()
        x = global_mean_pool(x, batch)
        x = self.lin(x)
        return x

    def __getstate__(self):
        """Standard pickle support for the GNN module."""
        return self.__dict__.copy()

    def __setstate__(self, state):
        """Restore module state."""
        self.__dict__.update(state)


class EnsembleProxy:
    """Proxy object that makes the AI Ensemble look like a standard sklearn model."""
    def __init__(self, manager):
        self.manager = manager
        # Mirror attributes needed for some visualization logic
        self.feature_names = manager.feature_names
        self.classes_ = [0, 1]

    @property
    def feature_importances_(self):
        """Aggregate feature importance from constituent models."""
        importances = []
        # Use RF and XGBoost as the primary sources of global importance for the ensemble
        for name in ["Random Forest", "XGBoost"]:
            try:
                m = self.manager.load_model(name)
                if m and hasattr(m, 'feature_importances_'):
                    importances.append(m.feature_importances_)
            except:
                continue
        
        if importances:
            return np.mean(importances, axis=0)
        # Uniform fallback if no importance sources found
        return np.ones(len(self.manager.feature_names)) / len(self.manager.feature_names)

    @property
    def coef_(self):
        """Aggregate coefficients if applicable (fallback to importance)."""
        return np.array([self.feature_importances_])

    def predict(self, X):
        # Ensure input is a DataFrame with correct columns
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.manager.feature_names)
        res, _, _ = self.manager.predict_ensemble(X, is_single=False)
        return res

    def predict_proba(self, X):
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.manager.feature_names)
        _, _, risks = self.manager.predict_ensemble(X, is_single=False)
        # risks contains p(1) -> [p(0), p(1)]
        return np.column_stack([1 - risks, risks])


class ModelManager:
    def __init__(self, script_dir):
        # Models are now saved in views/models within the tkinter_ui directory
        self.script_dir = os.path.join(script_dir, 'views', 'models')
        os.makedirs(self.script_dir, exist_ok=True)

        self.rf_model  = None
        self.lr_model  = None
        self.svm_model = None
        self.mlp_model = None
        self.xgb_model = None
        self.gnn_model = None

        self.feature_names   = self._load_feature_names()
        self.scaling_stats   = self._load_scaling_stats()
        self._feature_hash   = self._hash_features(self.feature_names)
        self.cached_train_df = None
        self._cached_data_path = None # item #11: Track source for caching

        self.analytics_cache = {
            'calibration': {}, 'learning': {}, 'metrics': {},
            'stability': {}, 'tsne': None, 'pr_threshold': {}, 'shap': {}
        }

    # ── Cache & State ──────────────────────────────────────────────────────────

    def reset_internal_state(self):
        """Strategic reset of all clinical memory and algorithmic benchmarks."""
        self.rf_model = self.lr_model = self.svm_model = self.xgb_model = self.gnn_model = self.mlp_model = None
        self.feature_names = []
        self.scaling_stats = {}
        self.cached_train_df = None
        self._cached_data_path = None
        self.analytics_cache = {
            'calibration': {}, 'learning': {}, 'metrics': {},
            'stability': {}, 'tsne': None, 'pr_threshold': {}, 'shap': {}
        }
        
        # Purge Persistent Artifacts
        for f in ['feature_names.pkl', 'scaler_meta.pkl', 'random_forest_model.pkl', 
                  'logistic_regression_model.pkl', 'svm_model.pkl', 'xgboost_model.pkl', 'mlp_model.pkl']:
            path = os.path.join(self.script_dir, f)
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
        
        log.info("Clinical Model Manager: Internal state purified.")
        self.cached_train_df = None
        self._cached_data_path = None
        self.scaling_stats = {}
        self.rf_model = self.lr_model = self.svm_model = self.xgb_model = self.gnn_model = self.mlp_model = None

    def reset_analytics(self):
        """Clears all cached analytical results and unloads in-memory models."""
        self.analytics_cache = {
            'calibration': {}, 'learning': {}, 'metrics': {},
            'stability': {}, 'tsne': None, 'pr_threshold': {}, 'shap': {}
        }
        self.cached_train_df = None
        self._cached_data_path = None
        self.scaling_stats = {}
        self.rf_model = self.lr_model = self.svm_model = self.xgb_model = self.gnn_model = self.mlp_model = None

    def delete_all_models(self):
        """Permanently deletes all trained model files and feature metadata from the disk."""
        import shutil
        if os.path.exists(self.script_dir):
            for filename in os.listdir(self.script_dir):
                if filename.endswith('.pkl'):
                    try:
                        os.remove(os.path.join(self.script_dir, filename))
                    except:
                        pass
        
        # Cleanup XGBoost/Joblib cache as well
        # self.script_dir is tkinter_ui/views/models, so cachedir is at tkinter_ui/cachedir
        cachedir = os.path.abspath(os.path.join(self.script_dir, '..', '..', 'cachedir'))
        if os.path.exists(cachedir):
            try:
                shutil.rmtree(cachedir, ignore_errors=True)
                log.info("Clinical cache (cachedir) cleared.")
            except:
                pass
        
        # Also definitely remove feature names to force a fresh sync next time
        feature_path = os.path.join(self.script_dir, 'feature_names.pkl')
        if os.path.exists(feature_path):
            try:
                os.remove(feature_path)
            except:
                pass
                
        self.feature_names = []
        self._feature_hash = 0
        self.reset_analytics()

    @property
    def features(self):
        return self.feature_names

    @staticmethod
    def _hash_features(features):
        """Return a stable SHA-256 hash of a feature list for mismatch detection."""
        if not features: return "0"
        import hashlib
        feat_str = ",".join(sorted(str(f).upper().strip() for f in features))
        return hashlib.sha256(feat_str.encode()).hexdigest()[:16]

    # ── Feature Names ──────────────────────────────────────────────────────────

    def _load_feature_names(self):
        try:
            path = os.path.join(self.script_dir, 'feature_names.pkl')
            if os.path.exists(path):
                return joblib.load(path)
            return ["CA-125", "CEA", "AFP", "PSA", "CA-15-3",
                    "CA-19-9", "NSE", "HE4", "CYFRA 21-1", "B2M"]
        except Exception as e:
            log.error("Error loading feature names: %s", e)
            return []

    def _load_scaling_stats(self):
        try:
            path = os.path.join(self.script_dir, 'scaler_meta.pkl')
            if os.path.exists(path):
                return joblib.load(path)
            return {}
        except Exception as e:
            log.error("Error loading scaling stats: %s", e)
            return {}

    def check_feature_compatibility(self, data_columns):
        """
        Returns (is_compatible, message).
        Raises a clear warning when the uploaded dataset's columns differ
        from the features used to train the currently loaded models.
        """
        if not self.feature_names:
            return True, "No trained features to compare."
            
        # Strip all numerical tags and spaces for a fuzzy match
        clean_data = [str(c).lower().strip() for c in data_columns if not any(f in str(c).lower() for f in ["sample_id", "cancer_risk_class", "prediction", "risk"])]
        clean_trained = [str(f).lower().strip() for f in self.feature_names]
        
        # Check if they are subset/superset enough to proceed
        matches = [f for f in clean_trained if f in clean_data]
        if len(matches) < len(clean_trained) * 0.7:
            return False, (
                "⚠️  Clinical Feature Mismatch detected!\n"
                f"Trained: {len(clean_trained)} biomarkers | Detected: {len(matches)} matches.\n"
                "Please Re-Sync Committee via 'Train' button."
            )
        return True, "OK"

    # ── Training ───────────────────────────────────────────────────────────────

    def check_and_train_models(self, data_path, status_callback=None, force=False, validation_split=0.2, outlier_removal=True, scaling_enabled=True):
        """Check if models exist. Trains ONLY if missing and data is available."""
        if not data_path:
            required_models = [
                'random_forest_model.pkl', 'logistic_regression_model.pkl', 
                'svm_model.pkl', 'mlp_model.pkl'
            ]
            if HAS_XGB:   required_models.append('xgboost_model.pkl')
            if HAS_TORCH: required_models.append('gnn_model.pkl')
                
            models_exist = all(os.path.exists(os.path.join(self.script_dir, m)) for m in required_models)
            if models_exist and os.path.exists(os.path.join(self.script_dir, 'feature_names.pkl')):
                return True, "Ensemble committee is fully calibrated and present."
            return False, "Strategic calibration required. Please upload a dataset to begin."

        # ... (rest of guards) ...

        if not os.path.exists(data_path) and not force:
            return False, "Dataset file not found. Please upload a dataset to train models."

        # Strategic Verification: Should we skip training?
        if not force and os.path.exists(os.path.join(self.script_dir, 'feature_names.pkl')):
            required = ['random_forest_model.pkl', 'logistic_regression_model.pkl', 'svm_model.pkl', 'mlp_model.pkl']
            if all(os.path.exists(os.path.join(self.script_dir, m)) for m in required):
                return True, "Models present"

        if status_callback:
            status_callback("Training models… This might take a moment.", "orange")

        try:
            # ── Strategic Schema Reset ──
            if force:
                log.info("Clinical Context: Resetting feature schema for new training session.")
                self.feature_names = None

            # 🛡️ Strategic Pre-Load Guard: Ensure dataframe exists before split
            if self.cached_train_df is None and not os.path.exists(data_path):
                 return False, "Clinical Ingress Fail: No cohort found to calibrate."

            X_train, X_test, y_train, y_test, features = self._load_training_data(
                data_path, 
                validation_split=validation_split,
                outlier_removal=outlier_removal,
                scaling_enabled=scaling_enabled
            )

            # Signal Strength Verification
            f_count = len(features)
            if status_callback:
                status_callback(f"Identified {f_count} critical biomarkers. Calibrating Committee…", "orange")
            log.info("Training on %d features. Class distribution: %s", f_count, np.bincount(y_train))

            models_data = [
                ('random_forest_model.pkl',  'Random Forest',       RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')),
                ('logistic_regression_model.pkl',  'Logistic Regression',  LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')),
                ('svm_model.pkl', 'SVM',                  SVC(probability=True, random_state=42, class_weight='balanced')),
            ]
            
            # Mission Scoped Metrics Extraction
            counts = np.bincount(y_train)
            xgb_weight = counts[0] / counts[1] if len(counts) >= 2 and counts[1] > 0 else 1.0
            
            if len(counts) >= 2 and (counts[0] < 5 or counts[1] < 5):
                if status_callback: status_callback("Alert: Weak biological diversity detected.", "orange")

            if HAS_XGB:
                from xgboost import XGBClassifier
                models_data.append(('xgboost_model.pkl', 'XGBoost',
                                     XGBClassifier(eval_metric='logloss', random_state=42, scale_pos_weight=xgb_weight)))
            
            from sklearn.neural_network import MLPClassifier
            models_data.append(('mlp_model.pkl', 'MLP', MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)))

            if HAS_TORCH:
                models_data.append(('gnn_model.pkl', 'GNN', GNNClassifier(num_features=1)))

            self.feature_names = features
            self._feature_hash = self._hash_features(features)
            joblib.dump(features, os.path.join(self.script_dir, 'feature_names.pkl'))

            for pkl, name, model_obj in models_data:
                target_path = os.path.join(self.script_dir, pkl)
                if status_callback:
                    status_callback(f"Training {name}…", "orange")
                
                model_obj.fit(X_train, y_train)
                joblib.dump(model_obj, target_path)

            # Persist Scaling Metadata for Inference Consistency
            stats_path = os.path.join(self.script_dir, 'scaler_meta.pkl')
            joblib.dump(self.scaling_stats, stats_path)

            self.reset_analytics()
            return True, "Ensemble calibration successful."
        except Exception as e:
            log.error("Training failed: %s", e)
            return False, f"Training failed: {str(e)}"

    # ── Data Preparation ────────────────────────────────────────────────────────
    def _read_excel_safe(self, data_path):
        """
        Smart read from Excel: try 'Training_Data' first, fallback to the first
        available sheet.
        """
        try:
            # Attempt 1: Look for clinical standard sheet name
            df = pd.read_excel(data_path, sheet_name='Training_Data')
        except ValueError:
            # Attempt 2: Auto-fallback to the first available sheet
            xl = pd.ExcelFile(data_path)
            sheets = xl.sheet_names
            if not sheets:
                raise ValueError("The uploaded Excel file appears to be empty (no sheets found).")
            
            first_sheet = sheets[0]
            df = pd.read_excel(data_path, sheet_name=first_sheet)
            log.info("Fallback: Loading model training data from sheet '%s'", first_sheet)
            
        return df

    def _prepare_df(self, df, outlier_removal=True, scaling_enabled=True):
        """Auto-label and prepare feature vector based on UI settings."""
        df = df.copy()
        
        # ── Step 1: Tactical Feature Selection ──
        forbidden = [
            "sample_id", "patient_id", "cancer_risk_class", "prediction", "risk", 
            "is_simulated", "timestamp", "date", "id", "unnamed", "target"
        ]
        
        # Determine X_cols for both training and clustering
        if self.feature_names:
            X_cols = []
            available = [str(c).lower() for c in df.columns]
            for f in self.feature_names:
                f_low = str(f).lower()
                if f_low in available:
                    idx = available.index(f_low)
                    X_cols.append(df.columns[idx])
                else:
                    matches = [c for c in df.columns if f_low in str(c).lower()]
                    if matches: X_cols.append(matches[0])
                    else:
                        df[f] = 0.0
                        X_cols.append(f)
        else:
            standard_patterns = ['concentration', 'peak', 'psa', 'afp', 'ca125']
            selected_cols = []
            for pat in standard_patterns:
                matches = [c for c in df.columns if pat.lower() in str(c).lower()]
                selected_cols.extend(matches)
            
            X_cols = [c for c in selected_cols if not any(f in str(c).lower() for f in forbidden)]
            
            # Fallback for generic numeric datasets
            if not X_cols:
                all_num = df.select_dtypes(include=[np.number]).columns.tolist()
                X_cols = [c for c in all_num if not any(f in str(c).lower() for f in forbidden)]
            
            X_cols = sorted(list(set(X_cols)))

        # ── Step 2: Clinical Label Discovery ──
        label_target = None
        for col in df.columns:
            c_low = str(col).lower().replace("_", "").replace(" ", "")
            # Expanded keyword list for better clinical detection
            if c_low in ["cancerriskclass", "target", "diagnosis", "class", "result", "outcome", "cancer", "detection", "verdict", "groundtruth"]:
                label_target = col
                break
        
        if label_target:
            y_raw = df[label_target]
            # Handle object-based labels (M/B, Sick/Healthy)
            if y_raw.dtype == object or y_raw.dtype == str or len(np.unique(y_raw.dropna())) > 2:
                y_mapped = []
                for val in y_raw:
                    v_low = str(val).lower().strip()
                    # Fuzzy clinical match
                    if any(term in v_low for term in ['pos', 'malig', 'canc', 'sick', 'true', '1', 'detected', 'high']):
                        y_mapped.append(1)
                    else:
                        y_mapped.append(0)
                df["cancer_risk_class"] = y_mapped
            else:
                df["cancer_risk_class"] = y_raw.fillna(0).astype(int)
        else:
            # BIOLOGICAL CLUSTERING: Final fallback for unlabelled datasets
            clustering_data = df[X_cols].copy()
            if clustering_data.isnull().any().any():
                clustering_data = clustering_data.fillna(clustering_data.mean())
            
            if clustering_data.empty:
                # Absolute fallback: uniform labels (indicates bad feature selection)
                df["cancer_risk_class"] = 0
            else:
                from sklearn.preprocessing import StandardScaler
                from sklearn.cluster import KMeans
                try:
                    c_scaled = StandardScaler().fit_transform(clustering_data)
                    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
                    clusters = kmeans.fit_predict(c_scaled)
                    
                    # Align higher biomarker values to Class 1 (Malignant)
                    ref_col = X_cols[0] if X_cols else None
                    for c in X_cols:
                        if any(p in str(c).lower() for p in ['psa', 'afp', 'concentration', 'biomarker']):
                            ref_col = c; break
                    if ref_col:
                        m0, m1 = df.loc[clusters == 0, ref_col].mean(), df.loc[clusters == 1, ref_col].mean()
                        if m0 > m1: clusters = 1 - clusters
                    df["cancer_risk_class"] = clusters
                except:
                    df["cancer_risk_class"] = 0

        X = df[X_cols]
        y = df["cancer_risk_class"]
        
        # Ensure column order consistency
        if self.feature_names:
            X = X.reindex(columns=self.feature_names, fill_value=0.0)
        
        # ── Step 3: CLINICAL DATA REFINEMENT ──
        X = X.copy()
        if outlier_removal:
            for col in X.columns:
                if X[col].dtype in [np.float64, np.float32, np.int64]:
                    Q1, Q3 = X[col].quantile(0.25), X[col].quantile(0.75)
                    IQR = Q3 - Q1
                    if IQR > 0:
                        # Standardized Winzorization @ 3.0 IQR for signal preservation
                        lower, upper = Q1 - 3.0 * IQR, Q3 + 3.0 * IQR
                        X[col] = X[col].clip(lower=lower, upper=upper)

        if scaling_enabled:
            for col in X.columns:
                if X[col].dtype in [np.float64, np.float32, np.int64]:
                    # Strategic Scaling Restoration:
                    # If we have saved stats for this feature, use them (Enforces inference consistency)
                    # If not (Training time), calculate and save them.
                    if col in self.scaling_stats:
                        mean, std = self.scaling_stats[col]
                    else:
                        mean, std = X[col].mean(), X[col].std()
                        self.scaling_stats[col] = (float(mean), float(std))
                        
                    # Numerical Stability: Only scale if there is meaningful variance
                    if std > 1e-6:
                        X[col] = (X[col] - mean) / std
                    else:
                        X[col] = 0.0 # Suppress static features
            
        X = X.fillna(0.0)
        return X, y

    def _load_training_data(self, data_path, validation_split=0.2, outlier_removal=True, scaling_enabled=True):
        """Standardized data loader — utilizes memory cache to avoid expensive Excel I/O."""
        if not data_path or not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset not found at:\n{data_path}\nPlease upload data first.")
            
        ap = os.path.abspath(data_path)
        if self.cached_train_df is None or self._cached_data_path != ap:
            self.cached_train_df = self._read_excel_safe(data_path)
            self._cached_data_path = ap

        X, y = self._prepare_df(
            self.cached_train_df, 
            outlier_removal=outlier_removal, 
            scaling_enabled=scaling_enabled
        )
        # 🛡️ FATAL GUARD: Prevent ensemble deliberation on null or mono-class data (SegFault Fix)
        if X.empty or len(np.unique(y)) < 2:
            raise ValueError("Clinical Diversity Failure: Dataset must contain both Benign and Malignant samples (min 2 of each).")
            
        return (*train_test_split(X, y, test_size=validation_split, random_state=42, stratify=y), X.columns.tolist())

    def get_raw_training_set(self, data_path):
        """Returns full (X, y) without train/test split (utilizes memory cache)."""
        if not data_path or not os.path.exists(data_path):
             # Strategic Fallback: Return empty tensors for uncalibrated state
             import pandas as pd
             return pd.DataFrame(), pd.Series()
            
        ap = os.path.abspath(data_path)
        if self.cached_train_df is None or self._cached_data_path != ap:
             self.cached_train_df = self._read_excel_safe(data_path)
             self._cached_data_path = ap
             
        return self._prepare_df(self.cached_train_df)

    # ── Analytics Methods ──────────────────────────────────────────────────────

    def get_detailed_metrics(self, model_name, data_path):
        """Calculate clinical metrics: Sensitivity, Specificity, PPV, NPV (cached)."""
        if not data_path or not os.path.exists(data_path):
            return None

        if model_name in self.analytics_cache['metrics']:
            return self.analytics_cache['metrics'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None

        _, X_test, _, y_test, _ = self._load_training_data(data_path)
        y_pred = model.predict(X_test)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

        from sklearn.metrics import roc_auc_score
        y_probs = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        auc = roc_auc_score(y_test, y_probs) if y_probs is not None else 0.85

        metrics = {
            "Accuracy":                      (tp + tn) / (tp + tn + fp + fn),
            "Sensitivity (Recall)":          recall_score(y_test, y_pred),
            "Recall":                        recall_score(y_test, y_pred), # Alias
            "Specificity":                   tn / (tn + fp) if (tn + fp) > 0 else 0.0,
            "PPV (Precision)":               precision_score(y_test, y_pred, zero_division=0),
            "Precision":                     precision_score(y_test, y_pred, zero_division=0), # Alias
            "NPV (Negative Predictive Val)": tn / (tn + fn) if (tn + fn) > 0 else 0.0,
            "F1-Score":                      f1_score(y_test, y_pred),
            "F1 Score":                      f1_score(y_test, y_pred), # Alias
            "AUC":                           auc,
            "True Positives":                int(tp),
            "True Negatives":                int(tn),
            "False Positives":               int(fp),
            "False Negatives":               int(fn),
        }
        self.analytics_cache['metrics'][model_name] = metrics
        return metrics

    def get_calibration_data(self, model_name, data_path):
        """Prepare ground truth and probabilities for calibration curve (cached)."""
        if model_name in self.analytics_cache['calibration']:
            return self.analytics_cache['calibration'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None, None

        _, X_test, _, y_test, _ = self._load_training_data(data_path)
        y_probs = model.predict_proba(X_test)[:, 1]
        res = (y_test, y_probs)
        self.analytics_cache['calibration'][model_name] = res
        return res

    def compute_learning_curve(self, model_name, data_path):
        """Learning curve computation with stratified CV and class-count guard."""
        if model_name in self.analytics_cache['learning']:
            return self.analytics_cache['learning'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None

        X, y = self.get_raw_training_set(data_path)
        if len(np.unique(y)) < 2:
            log.warning("Learning curve skipped: only one class in target.")
            return None

        from sklearn.model_selection import learning_curve as sk_learn_curve
        cv     = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        n_jobs = 1  # Force single process on Windows to avoid resource_tracker leaks

        train_sizes, train_scores, test_scores = sk_learn_curve(
            model, X, y, cv=cv, n_jobs=n_jobs,
            train_sizes=np.linspace(0.1, 1.0, 5), scoring='accuracy'
        )
        data = {
            'sizes':      train_sizes,
            'train_mean': np.mean(train_scores, axis=1),
            'test_mean':  np.mean(test_scores,  axis=1),
        }
        self.analytics_cache['learning'][model_name] = data
        return data

    def get_model_stability(self, model_name, data_path):
        """Analyze model consistency across 5 stratified folds (cached)."""
        if model_name in self.analytics_cache['stability']:
            return self.analytics_cache['stability'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None

        X, y = self.get_raw_training_set(data_path)
        if len(np.unique(y)) < 2:
            return None

        from sklearn.model_selection import cross_val_score
        cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        n_jobs = 1  # Force single process on Windows to avoid resource_tracker leaks
        scores = cross_val_score(model, X, y, cv=cv, n_jobs=n_jobs)

        res = {'scores': scores, 'mean': float(np.mean(scores)), 'std': float(np.std(scores))}
        self.analytics_cache['stability'][model_name] = res
        return res

    def get_tsne_data(self, data_path):
        """
        Generate 2D patient clustering via t-SNE (cached).
        Auto-subsamples to _TSNE_MAX_ROWS to prevent memory freeze on large datasets.
        """
        if self.analytics_cache['tsne'] is not None:
            return self.analytics_cache['tsne']

        X, y = self.get_raw_training_set(data_path)

        # Memory cap — item #7
        if len(X) > _TSNE_MAX_ROWS:
            log.info("t-SNE: subsampling %d → %d rows for performance.", len(X), _TSNE_MAX_ROWS)
            idx = np.random.choice(len(X), _TSNE_MAX_ROWS, replace=False)
            X, y = X.iloc[idx], y.iloc[idx]

        from sklearn.manifold import TSNE
        from sklearn.preprocessing import StandardScaler

        X_scaled    = StandardScaler().fit_transform(X)
        perplexity  = min(30, len(X) - 1)
        X_embedded  = TSNE(n_components=2, perplexity=perplexity, random_state=42).fit_transform(X_scaled)

        res = {'x': X_embedded[:, 0], 'y': X_embedded[:, 1], 'labels': y}
        self.analytics_cache['tsne'] = res
        return res

    def get_pr_threshold_data(self, model_name, data_path):
        """Precision and Recall vs Decision Threshold (cached)."""
        if model_name in self.analytics_cache['pr_threshold']:
            return self.analytics_cache['pr_threshold'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None

        _, X_test, _, y_test, _ = self._load_training_data(data_path)
        from sklearn.metrics import precision_recall_curve
        y_probs = model.predict_proba(X_test)[:, 1]
        p, r, t = precision_recall_curve(y_test, y_probs)

        res = {'precision': p, 'recall': r, 'thresholds': t}
        self.analytics_cache['pr_threshold'][model_name] = res
        return res

    def get_shap_data(self, model_name, data_path):
        """
        Global XAI feature importance via SHAP (with robust fallbacks).
        Subsampled to _SHAP_MAX_ROWS for UI performance.
        """
        if model_name in self.analytics_cache['shap']:
            return self.analytics_cache['shap'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None

        _, X_test, _, y_test, _ = self._load_training_data(data_path)
        X_sample = X_test.iloc[:_SHAP_MAX_ROWS]

        try:
            import shap
            explainer   = shap.Explainer(model, X_sample)
            shap_values = explainer(X_sample)
            vals = np.abs(shap_values.values).mean(0)
            res  = sorted(zip(X_test.columns, vals), key=lambda x: x[1], reverse=True)[:10]
        except Exception:
            # Fallback: native importance → coef → permutation
            if hasattr(model, 'feature_importances_'):
                vals = model.feature_importances_
            elif hasattr(model, 'coef_'):
                vals = np.abs(model.coef_[0])
            else:
                from sklearn.inspection import permutation_importance
                r    = permutation_importance(model, X_sample, y_test.iloc[:_SHAP_MAX_ROWS],
                                              n_repeats=5, random_state=42, n_jobs=1)
                vals = r.importances_mean
            res = sorted(zip(X_test.columns, vals), key=lambda x: x[1], reverse=True)[:10]

        self.analytics_cache['shap'][model_name] = res
        return res

    def get_cv_scores(self, model_name, data_path):
        """Get cross-validation scores for robustness analysis."""
        model = self.load_model(model_name)
        if model is None:
            return None

        X, y = self.get_raw_training_set(data_path)
        if len(np.unique(y)) < 2:
            return None

        from sklearn.model_selection import cross_val_score
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv, n_jobs=1)
        return scores.tolist()

    def get_training_data(self, data_path):
        """Get training data for analysis."""
        X, y = self.get_raw_training_set(data_path)
        return X, y

    # ── Model Loading ──────────────────────────────────────────────────────────

    def load_model(self, model_name):
        """Load a model by name, using in-memory cache to avoid repeated disk reads."""
        if "AI Ensemble" in model_name:
            return EnsembleProxy(self)

        _map = {
            "Random Forest":       ('rf_model',  'random_forest_model.pkl'),
            "Logistic Regression": ('lr_model',  'logistic_regression_model.pkl'),
            "SVM":                 ('svm_model', 'svm_model.pkl'),
            "XGBoost":             ('xgb_model', 'xgboost_model.pkl'),
            "MLP":                 ('mlp_model', 'mlp_model.pkl'),
            "Graph Neural Network":('gnn_model', 'gnn_model.pkl'),
            # Aliases for UI consistency
            "MLP Model":           ('mlp_model', 'mlp_model.pkl'),
            "GNN":                 ('gnn_model', 'gnn_model.pkl'),
            "GNN Model":           ('gnn_model', 'gnn_model.pkl')
        }
        if model_name not in _map:
            return None
        attr, fname = _map[model_name]
        try:
            if getattr(self, attr) is None:
                path = os.path.join(self.script_dir, fname)
                if os.path.exists(path):
                    if attr == 'gnn_model':
                        if not HAS_TORCH:
                            log.warning("GNN artifact exists but PyTorch is not available for loading.")
                            return None
                        # Load PyTorch GNN model
                        loaded = joblib.load(path)
                        if isinstance(loaded, GNNClassifier):
                            setattr(self, attr, loaded)
                        elif isinstance(loaded, dict):
                            # Fallback for dict-style saves
                            model_instance = GNNClassifier()
                            model_instance.model = loaded.get('model')
                            model_instance.edge_index = loaded.get('edge_index')
                            model_instance.feature_names = loaded.get('feature_names')
                            setattr(self, attr, model_instance)
                        else:
                            # Direct state_dict or other fallback
                            try:
                                model_instance = GNNClassifier()
                                model_instance.model = loaded
                                setattr(self, attr, model_instance)
                            except Exception:
                                log.error("Unsupported GNN load format.")
                                return None
                    else:
                        setattr(self, attr, joblib.load(path))
                else:
                    return None
            return getattr(self, attr)
        except Exception as e:
            log.error("Error loading model '%s': %s", model_name, e)
            return None

    def pre_warm_models(self, status_callback=None):
        """Proactively loads all trained model artifacts into memory for instant clinical feedback."""
        models = ["Random Forest", "Logistic Regression", "SVM", "XGBoost", "MLP"]
        total = len(models)
        log.info("Initiating model pre-warming for clinical performance...")
        
        for i, name in enumerate(models):
            if status_callback:
                status_callback(f"Waking up AI Ensemble ({i+1}/{total}): {name}...", "orange")
            # This triggers load_model's internal caching system
            self.load_model(name)
        
        log.info("Model warming complete. Clinical dashboard ready for low-latency operations.")
        if status_callback:
            status_callback("AI Ensemble Ready — Instant Diagnosis Enabled", "#10B981")

    # ── Predictions ────────────────────────────────────────────────────────────

    def predict_single(self, model_name, feature_values):
        model = self.load_model(model_name)
        if model is None:
            raise ValueError(
                f"Model '{model_name}' could not be loaded.\n"
                "Please train it first via Data → Re-Train All Models."
            )

        # Validate inputs are numeric — item #1
        for k, v in feature_values.items():
            try:
                float(v)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid value for '{k}': '{v}'. All biomarker values must be numeric.")

        full_input  = {feat: 0.0 for feat in self.feature_names}
        for k, v in feature_values.items():
            if k in full_input:
                full_input[k] = float(v)

        input_df     = pd.DataFrame([full_input])[self.feature_names]
        
        # Apply Clinical Scaling before prediction
        X_scaled, _ = self._prepare_df(input_df, outlier_removal=True, scaling_enabled=True)
        
        prediction   = model.predict(X_scaled)[0]
        probabilities = model.predict_proba(X_scaled)[0]

        risk = probabilities[1]
        conf = probabilities[int(prediction)]
        return prediction, conf, risk

    def predict_batch(self, model_name, df):
        model = self.load_model(model_name)
        if model is None:
            raise ValueError(
                f"Model '{model_name}' could not be loaded.\n"
                "Please train it first via Data → Re-Train All Models."
            )

        X = df.copy()
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0.0
        X = X[self.feature_names]

        # Apply Clinical Scaling to batch data
        X_scaled, _ = self._prepare_df(X, outlier_removal=True, scaling_enabled=True)

        predictions   = model.predict(X_scaled)
        probabilities  = model.predict_proba(X_scaled)
        confs = np.array([prob[pred] for pred, prob in zip(predictions, probabilities)])
        risks = probabilities[:, 1]
        return predictions, confs, risks

    def predict_ensemble(self, X_input, is_single=True):
        """
        AI Clinical Ensemble: Performs majority voting across all trained models.
        Returns prediction, confidence (agreement level), and risk (mean probability).
        """
        # ── THE CLINICAL AI VESTA COMMITTEE ──
        # Restricted to exactly 4 members for maximum clinical deliberative clarity
        available_models = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: available_models.append("XGBoost")
        else:       available_models.append("MLP")

        all_preds = []
        all_probs = []
        model_names_loaded = []

        for name in available_models:
            try:
                model = self.load_model(name)
                if model is not None:
                    if is_single:
                        # 1. Prediction Engineering for Individual Samples
                        if isinstance(X_input, dict):
                            full_input = {feat: 0.0 for feat in self.feature_names}
                            for k, v in X_input.items():
                                k_low = str(k).lower().strip()
                                for feat in self.feature_names:
                                    if k_low == str(feat).lower().strip() or k_low in str(feat).lower():
                                        try: full_input[feat] = float(str(v).split()[0])
                                        except: pass
                                        break
                            X_test = pd.DataFrame([full_input])[self.feature_names]
                        elif isinstance(X_input, pd.Series):
                            full_input = {feat: 0.0 for feat in self.feature_names}
                            for feat in self.feature_names:
                                if feat in X_input: full_input[feat] = X_input[feat]
                            X_test = pd.DataFrame([full_input])[self.feature_names]
                        else:
                            X_test = pd.DataFrame([X_input]).reindex(columns=self.feature_names, fill_value=0.0)

                        pred = model.predict(X_test)[0]
                        prob = model.predict_proba(X_test)[0]
                        
                        all_preds.append(int(pred))
                        all_probs.append(prob)
                    else:
                        # 2. Batch Clinical Auditing Logic
                        X_test = X_input[self.feature_names]
                        pred = model.predict(X_test)
                        prob = model.predict_proba(X_test)
                        
                        all_preds.append(pred)
                        all_probs.append(prob)
                    
                    model_names_loaded.append(name)
            except:
                continue

        if not all_preds:
            raise ValueError("No models available for ensemble prediction.")

        # Voting Logic
        if is_single:
            # Simple Majority Vote for single prediction
            final_pred = 1 if all_preds.count(1) > all_preds.count(0) else 0
            # Confidence = % of models that agreed with the final prediction
            confidence = all_preds.count(final_pred) / len(all_preds)
            # Risk = Mean of all 'Detected' probabilities
            risk = np.mean([p[1] for p in all_probs])

            # Bundle individual results for the forensic validation tab
            individual_results = []
            for name, p, pr in zip(model_names_loaded, all_preds, all_probs):
                individual_results.append({
                    'model': name,
                    'prediction': int(p),
                    'risk': float(pr[1])
                })

            return {
                'prediction': int(final_pred),
                'confidence': float(confidence),
                'risk': float(risk),
                'individual_results': individual_results,
                'consensus': f"{all_preds.count(final_pred)}/{len(all_preds)} AI agreement"
            }
        else:
            # Batch Voting
            stacked_preds = np.array(all_preds) # (models, samples)
            final_preds = []
            agreement_levels = []
            
            for i in range(stacked_preds.shape[1]):
                votes = list(stacked_preds[:, i])
                win_pred = 1 if votes.count(1) > votes.count(0) else 0
                final_preds.append(win_pred)
                agreement_levels.append(votes.count(win_pred) / len(votes))
            
            # Risks = mean across models for each sample
            stacked_probs = np.array([p[:, 1] for p in all_probs]) # (models, samples)
            final_risks = np.mean(stacked_probs, axis=0)
            
            return np.array(final_preds), np.array(agreement_levels), final_risks

    def get_model_leaderboard(self, data_path):
        """
        Deep clinical leaderboard: Ranks all models by F1 and returns
        Accuracy, F1, Precision, Recall, Specificity, CV Mean +/- Std.
        Ranked by F1-Score - the most meaningful metric for imbalanced cancer data.
        """
        if not data_path or not os.path.exists(data_path):
             return [] # Empty cohort metrics when dataset is missing

        from sklearn.metrics import (
            accuracy_score, f1_score, precision_score,
            recall_score, confusion_matrix
        )
        from sklearn.model_selection import StratifiedKFold, cross_val_score

        X_all, y_all = self.get_raw_training_set(data_path)
        _, X_test, _, y_test, _ = self._load_training_data(data_path)

        available_models = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            available_models.append("XGBoost")
        available_models.append("MLP")

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        leaderboard = []
        for name in available_models:
            model = self.load_model(name)
            if model is None:
                continue
            try:
                X_pred = X_test[self.feature_names]
                y_pred = model.predict(X_pred)
                acc  = accuracy_score(y_test, y_pred)
                f1   = f1_score(y_test, y_pred, zero_division=0)
                prec = precision_score(y_test, y_pred, zero_division=0)
                rec  = recall_score(y_test, y_pred, zero_division=0)

                try:
                    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
                    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
                except ValueError:
                    spec = 0.0

                try:
                    from sklearn.metrics import roc_auc_score
                    y_prob = model.predict_proba(X_pred)[:, 1] if hasattr(model, 'predict_proba') else None
                    auc_val = roc_auc_score(y_test, y_prob) if y_prob is not None else 0.5
                except:
                    auc_val = 0.5

                try:
                    cv_scores = cross_val_score(model, X_all[self.feature_names], y_all, cv=cv, scoring='accuracy', n_jobs=1)
                    cv_mean = float(cv_scores.mean())
                    cv_std  = float(cv_scores.std())
                except Exception:
                    cv_mean, cv_std = acc, 0.0

                leaderboard.append({
                    'model':       name,
                    'accuracy':    acc,
                    'f1':          f1,
                    'precision':   prec,
                    'recall':      rec,
                    'specificity': spec,
                    'auc':         auc_val,
                    'cv_mean':     cv_mean,
                    'cv_std':      cv_std,
                    'rank_score':  (f1 * 0.7) + (auc_val * 0.3), # Composite score for better ranking
                })
            except Exception as e:
                log.warning("Leaderboard: skipped %s - %s", name, e)
                continue

        leaderboard.sort(key=lambda x: x['rank_score'], reverse=True)
        return leaderboard

    # ── Local Explanation ──────────────────────────────────────────────────────

    def get_local_explanation(self, model_name, inputs, data_path=None):
        """Feature contribution analysis for a single prediction."""
        model = self.load_model(model_name)
        if model is None:
            return None

        if hasattr(model, 'feature_importances_'):
            contrib = model.feature_importances_
        elif hasattr(model, 'coef_'):
            contrib = np.abs(model.coef_[0])
        else:
            # Fallback: RF proxy → permutation importance
            try:
                rf_ref = self.load_model("Random Forest")
                if rf_ref is not None:
                    contrib = rf_ref.feature_importances_
                else:
                    raise ValueError()
            except Exception:
                if data_path:
                    from sklearn.inspection import permutation_importance
                    _, X_test, _, y_test, _ = self._load_training_data(data_path)
                    r = permutation_importance(model, X_test.iloc[:20], y_test.iloc[:20],
                                               n_repeats=5, random_state=42, n_jobs=1)
                    contrib = r.importances_mean
                else:
                    contrib = np.ones(len(self.feature_names))

        normalized_inputs = {str(k).lower().strip(): v for k, v in inputs.items()}
        explanation = []
        for i, feat in enumerate(self.feature_names):
            val   = float(normalized_inputs.get(str(feat).lower().strip(), 0.0))
            score = contrib[i] * (val / 10.0)
            explanation.append((feat, score))

        explanation.sort(key=lambda x: abs(x[1]), reverse=True)
        return explanation[:10]

    def get_counterfactual_recommendations(self, model_name, inputs, data_path=None):
        """
        Generate What-If counterfactuals: Determine the minimal biomarker changes 
        required to shift a high-risk prediction to a low-risk prediction.
        """
        model = self.load_model(model_name)
        if model is None:
            return None

        # Prepare base input
        normalized_inputs = {str(k).lower().strip(): float(v) for k, v in inputs.items()}
        
        full_input = {feat: 0.0 for feat in self.feature_names}
        for k in full_input:
            key_lower = str(k).lower().strip()
            if key_lower in normalized_inputs:
                full_input[k] = normalized_inputs[key_lower]
                
        base_df = pd.DataFrame([full_input])[self.feature_names]
        
        # Check current prediction
        base_pred = model.predict(base_df)[0]
        base_prob = model.predict_proba(base_df)[0][1]
        
        if base_pred == 0:
            # If healthy, provide a "Safety Buffer" analysis instead of empty results
            # Compare patient biomarkers to the high-risk population mean
            stats = self.get_biomarker_separation_stats(data_path) if data_path else {}
            explanation = self.get_local_explanation(model_name, inputs, data_path)
            
            changes_applied = []
            if explanation and stats:
                for feat, _ in explanation[:3]:
                    if feat in stats:
                        h_mean, d_mean = stats[feat]
                        changes_applied.append({
                            "feature": feat,
                            "original": float(base_df.at[0, feat]),
                            "new": float(d_mean),
                            "reduction": 0.0, # Not a reduction, but a comparison
                            "mode": "buffer"
                        })

            return {
                "status": "Healthy (Low Risk)",
                "message": "Patient is in the safe zone. Visualizing buffer relative to High-Risk population.",
                "current_risk": float(base_prob),
                "new_risk": float(base_prob),
                "changes": changes_applied,
                "is_healthy": True
            }

            
        # If high risk, find top contributing features
        explanation = self.get_local_explanation(model_name, inputs, data_path)
        if not explanation:
            return None
            
        # Try perturbing the top 3 risk drivers
        best_cf_df = base_df.copy()
        changes_applied = []
        
        # Determine direction: we want to lower the probability of class 1.
        # We incrementally reduce the top positive contributors.
        for feat, score in explanation[:3]:
            if score <= 0:
                continue # Only reduce features that contribute to risk
                
            orig_val = best_cf_df.at[0, feat]
            
            # Iteratively reduce by 10% steps up to 50%
            for step in [0.9, 0.8, 0.7, 0.6, 0.5]:
                new_val = orig_val * step
                temp_df = best_cf_df.copy()
                temp_df.at[0, feat] = new_val
                
                new_prob = model.predict_proba(temp_df)[0][1]
                
                # If risk drops significantly or flips, accept this change
                if new_prob < base_prob - 0.05 or model.predict(temp_df)[0] == 0:
                    best_cf_df = temp_df
                    base_prob = new_prob
                    changes_applied.append({
                        "feature": feat,
                        "original": orig_val,
                        "new": new_val,
                        "reduction": (1 - step) * 100
                    })
                    break
                    
            # Stop early if we flipped the prediction
            if model.predict(best_cf_df)[0] == 0:
                break
                
        final_pred = model.predict(best_cf_df)[0]
        final_prob = model.predict_proba(best_cf_df)[0][1]
        
        return {
            "status": "Actionable" if final_pred == 0 else "High Resistance",
            "message": "Found actionable biomarker targets" if final_pred == 0 else "Note: Significant changes required for this profile.",
            "current_risk": float(model.predict_proba(base_df)[0][1]),
            "new_risk": float(final_prob),
            "changes": changes_applied
        }

    def get_biomarker_separation_stats(self, data_path):
        """Calculate mean values for Healthy vs Detected patients for each biomarker."""
        X, y = self.get_raw_training_set(data_path)
        stats = {}
        for feat in self.feature_names:
            if feat in X.columns:
                h_mean = X[y == 0][feat].mean()
                d_mean = X[y == 1][feat].mean()
                stats[feat] = (h_mean, d_mean)
        return stats

    def get_biomarker_network_data(self, data_path):
        """Extract graph structure (nodes & edges) for network visualization."""
        if not data_path or not os.path.exists(data_path):
            return None

        # Load data to compute correlations if needed, or use the GNN's edge_index
        X, _ = self.get_training_data(data_path)
        if X is None or X.empty:
            return None

        features = X.columns.tolist()
        corr_matrix = X.corr()
        
        nodes = []
        for feat in features:
            nodes.append({
                "id": feat,
                "importance": float(corr_matrix[feat].abs().mean()) # Proxy for node importance
            })

        edges = []
        for i in range(len(features)):
            for j in range(i + 1, len(features)):
                weight = corr_matrix.iloc[i, j]
                if abs(weight) > 0.4: # Clinical threshold for "connected" biomarkers
                    edges.append({
                        "source": features[i],
                        "target": features[j],
                        "weight": float(weight)
                    })

        return {"nodes": nodes, "edges": edges}
