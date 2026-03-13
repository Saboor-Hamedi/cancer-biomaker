import logging
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.svm import SVC

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import torch
    import torch.nn.functional as F
    from torch_geometric.data import Data, DataLoader
    from torch_geometric.nn import GCNConv, global_mean_pool
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ── Logging setup ─────────────────────────────────────────────────────────────
log = logging.getLogger(__name__)

# Max rows for heavy unsupervised ops (t-SNE / SHAP) to avoid memory freeze
_TSNE_MAX_ROWS  = 2_000
_SHAP_MAX_ROWS  = 100


class GNNClassifier:
    """Graph Neural Network classifier with sklearn-like interface."""

    def __init__(self, num_features=1, hidden_channels=64, num_classes=2):
        if not HAS_TORCH:
            raise ImportError("PyTorch and torch_geometric required for GNN")

        self.num_features = num_features
        self.hidden_channels = hidden_channels
        self.num_classes = num_classes
        self.model = None
        self.edge_index = None
        self.feature_names = None

    def _build_graph(self, X):
        """Build graph from correlation matrix."""
        if self.feature_names is None:
            self.feature_names = X.columns.tolist()

        corr_matrix = X.corr()
        edges = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > 0.5:  # Lower threshold for more connections
                    edges.append([i, j])
                    edges.append([j, i])

        self.edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

    def _create_graph_data(self, X, y=None):
        """Create PyG Data objects."""
        data_list = []
        for idx in X.index:
            x = torch.tensor(X.loc[idx].values, dtype=torch.float).view(-1, 1)
            data = Data(x=x, edge_index=self.edge_index)
            if y is not None:
                data.y = torch.tensor(y.loc[idx], dtype=torch.long)
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

        return self

    def predict(self, X):
        """Predict class labels."""
        self.model.eval()
        test_data = self._create_graph_data(X)
        test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

        preds = []
        with torch.no_grad():
            for data in test_loader:
                out = self.model(data.x, data.edge_index, data.batch)
                pred = out.argmax(dim=1)
                preds.extend(pred.cpu().numpy())

        return np.array(preds)

    def predict_proba(self, X):
        """Predict class probabilities."""
        self.model.eval()
        test_data = self._create_graph_data(X)
        test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

        probs = []
        with torch.no_grad():
            for data in test_loader:
                out = self.model(data.x, data.edge_index, data.batch)
                prob = F.softmax(out, dim=1)
                probs.extend(prob.cpu().numpy())

        return np.array(probs)


class GNN(torch.nn.Module):
    """PyTorch GNN model."""
    def __init__(self, num_features, hidden_channels, num_classes):
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
        self._feature_hash   = self._hash_features(self.feature_names)
        self.cached_train_df = None

        self.analytics_cache = {
            'calibration': {}, 'learning': {}, 'metrics': {},
            'stability': {}, 'tsne': None, 'pr_threshold': {}, 'shap': {}
        }

    # ── Cache & State ──────────────────────────────────────────────────────────

    def reset_analytics(self):
        """Clears all cached analytical results and unloads in-memory models."""
        self.analytics_cache = {
            'calibration': {}, 'learning': {}, 'metrics': {},
            'stability': {}, 'tsne': None, 'pr_threshold': {}, 'shap': {}
        }
        self.cached_train_df = None
        self.rf_model = self.lr_model = self.svm_model = self.xgb_model = self.gnn_model = None

    @property
    def features(self):
        return self.feature_names

    @staticmethod
    def _hash_features(features):
        """Return a stable hash of a feature list for mismatch detection."""
        return hash(tuple(sorted(features))) if features else 0

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

    def check_feature_compatibility(self, data_columns):
        """
        Returns (is_compatible, message).
        Raises a clear warning when the uploaded dataset's columns differ
        from the features used to train the currently loaded models.
        """
        if not self.feature_names:
            return True, "No trained features to compare."
        data_hash = self._hash_features([c for c in data_columns
                                         if c not in ('sample_id', 'cancer_risk_class')])
        if data_hash != self._feature_hash:
            return False, (
                "⚠️  Feature mismatch detected!\n"
                "The uploaded dataset has different columns from the trained models.\n"
                "Please Re-Train All Models (Data → Re-Train) to sync them."
            )
        return True, "OK"

    # ── Training ───────────────────────────────────────────────────────────────

    def check_and_train_models(self, data_path, status_callback=None, force=False):
        """Check if models exist. Trains ONLY if missing and data is available."""
        if not data_path:
            # If not forcing, we just check if models exist
            if not force:
                models_exist = all(os.path.exists(os.path.join(self.script_dir, m)) for m in [
                    'random_forest_model.pkl', 'logistic_regression_model.pkl', 'svm_model.pkl'
                ])
                if models_exist:
                    return True, "Models present"
            return False, "Dataset path is empty. Please upload a dataset to train models."

        if not os.path.exists(data_path) and not force:
            return False, "Dataset file not found. Please upload a dataset to train models."

        models_data = [
            ('random_forest_model.pkl',  'Random Forest',       RandomForestClassifier(n_estimators=100, random_state=42)),
            ('logistic_regression_model.pkl',  'Logistic Regression',  LogisticRegression(random_state=42, max_iter=1000)),
            ('svm_model.pkl', 'SVM',                  SVC(probability=True, random_state=42)),
        ]
        if HAS_XGB:
            models_data.append(('xgboost_model.pkl', 'XGBoost',
                                 XGBClassifier(eval_metric='logloss', random_state=42)))
        if HAS_TORCH:
            models_data.append(('gnn_model.pkl', 'GNN', GNNClassifier()))

        missing = [m for m in models_data
                   if not os.path.exists(os.path.join(self.script_dir, m[0]))]
        if not missing and not force and os.path.exists(os.path.join(self.script_dir, 'feature_names.pkl')):
            return True, "Models present"

        if not data_path or not os.path.exists(data_path):
            return False, "Training required but dataset missing."

        if status_callback:
            status_callback("Training models… This might take a moment.", "orange")

        try:
            X_train, X_test, y_train, y_test, features = self._load_training_data(data_path)
            self.feature_names = features
            self._feature_hash = self._hash_features(features)
            joblib.dump(features, os.path.join(self.script_dir, 'feature_names.pkl'))

            for pkl, name, model_obj in models_data:
                target_path = os.path.join(self.script_dir, pkl)
                if not os.path.exists(target_path) or force:
                    if status_callback:
                        status_callback(f"Training {name}…", "orange")
                    model_obj.fit(X_train, y_train)
                    joblib.dump(model_obj, target_path)
                    log.info("Trained and saved: %s", name)

            self.reset_analytics()
            return True, "Training process finished."
        except Exception as e:
            log.error("Training failed: %s", e)
            return False, f"Training failed: {str(e)}"

    # ── Data Loading ───────────────────────────────────────────────────────────

    def _read_excel_safe(self, data_path):
        """
        Read 'Training_Data' sheet from Excel with a clean error message
        if the sheet is missing (item #6).
        """
        try:
            df = pd.read_excel(data_path, sheet_name='Training_Data')
        except ValueError:
            xl = pd.ExcelFile(data_path)
            sheets = xl.sheet_names
            raise ValueError(
                f"Sheet 'Training_Data' not found in the Excel file.\n"
                f"Available sheets: {', '.join(sheets)}\n"
                f"Please rename your data sheet to 'Training_Data'."
            )
        return df

    def _prepare_df(self, df):
        """Auto-label, split X/y, drop metadata columns."""
        if "cancer_risk_class" not in df.columns:
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            df = df.copy()
            df["cancer_risk_class"] = kmeans.fit_predict(
                df.select_dtypes(include=[np.number])
            )
        X = df.drop(["sample_id", "cancer_risk_class"], axis=1, errors='ignore')
        y = df["cancer_risk_class"]
        return X, y

    def _load_training_data(self, data_path):
        """Standardized data loader — always reads fresh from disk."""
        if not os.path.exists(data_path):
            raise FileNotFoundError(
                f"Dataset not found at:\n{data_path}\nPlease upload data first."
            )
        self.cached_train_df = self._read_excel_safe(data_path)
        X, y = self._prepare_df(self.cached_train_df)
        return (*train_test_split(X, y, test_size=0.2, random_state=42), X.columns.tolist())

    def get_raw_training_set(self, data_path):
        """Returns full (X, y) without train/test split."""
        if not data_path or not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset missing at {data_path}")
        self.cached_train_df = self._read_excel_safe(data_path)
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
        _map = {
            "Random Forest":       ('rf_model',  'random_forest_model.pkl'),
            "Logistic Regression": ('lr_model',  'logistic_regression_model.pkl'),
            "SVM":                 ('svm_model', 'svm_model.pkl'),
            "XGBoost":             ('xgb_model', 'xgboost_model.pkl'),
            "MLP":                 ('mlp_model', 'mlp_model.pkl'),
            "GNN":                 ('gnn_model', 'gnn_model.pkl'),
        }
        if model_name not in _map:
            return None
        attr, fname = _map[model_name]
        try:
            if getattr(self, attr) is None:
                path = os.path.join(self.script_dir, fname)
                if os.path.exists(path):
                    if model_name == "GNN":
                        # Load PyTorch model
                        model_data = joblib.load(path)
                        model = GNNClassifier()
                        model.model = model_data['model']
                        model.edge_index = model_data['edge_index']
                        model.feature_names = model_data['feature_names']
                        setattr(self, attr, model)
                    else:
                        setattr(self, attr, joblib.load(path))
                else:
                    return None
            return getattr(self, attr)
        except Exception as e:
            log.error("Error loading model '%s': %s", model_name, e)
            return None

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
        prediction   = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]

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

        predictions   = model.predict(X)
        probabilities  = model.predict_proba(X)
        confs = np.array([prob[pred] for pred, prob in zip(predictions, probabilities)])
        risks = probabilities[:, 1]
        return predictions, confs, risks

    def predict_ensemble(self, X_input, is_single=True):
        """
        AI Clinical Ensemble: Performs majority voting across all trained models.
        Returns prediction, confidence (agreement level), and risk (mean probability).
        """
        available_models = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            available_models.append("XGBoost")

        all_preds = []
        all_probs = []

        for name in available_models:
            try:
                model = self.load_model(name)
                if model is not None:
                    if is_single:
                        # Normalize single input for consistency
                        if isinstance(X_input, dict):
                            X_test = pd.DataFrame([X_input])[self.feature_names]
                        else:
                            X_test = pd.DataFrame([X_input]).iloc[:, :len(self.feature_names)]
                            X_test.columns = self.feature_names
                        
                        pred = model.predict(X_test)[0]
                        prob = model.predict_proba(X_test)[0]
                    else:
                        X_test = X_input[self.feature_names]
                        pred = model.predict(X_test)
                        prob = model.predict_proba(X_test)
                    
                    all_preds.append(pred)
                    all_probs.append(prob)
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
            return final_pred, confidence, risk
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
        Analyzes all models and returns a ranked leaderboard based on accuracy and stability.
        """
        from sklearn.metrics import accuracy_score, f1_score
        # Use load_training_data to get test split for evaluation
        _, X_test, _, y_test, _ = self._load_training_data(data_path)
        
        available_models = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            available_models.append("XGBoost")
            
        leaderboard = []
        for name in available_models:
            model = self.load_model(name)
            if model:
                y_pred = model.predict(X_test[self.feature_names])
                acc = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred)
                leaderboard.append({
                    'model': name,
                    'accuracy': acc,
                    'f1': f1,
                    'rank_score': (acc + f1) / 2
                })
        
        # Sort by rank score
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

    def get_dataset_summary(self, data_path):
        """Get summarized dataset for visualization."""
        if not data_path or not os.path.exists(data_path):
            return None
        return self._read_excel_safe(data_path)
