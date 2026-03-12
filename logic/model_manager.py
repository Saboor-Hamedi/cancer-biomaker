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

# ── Logging setup ─────────────────────────────────────────────────────────────
log = logging.getLogger(__name__)

# Max rows for heavy unsupervised ops (t-SNE / SHAP) to avoid memory freeze
_TSNE_MAX_ROWS  = 2_000
_SHAP_MAX_ROWS  = 100


class ModelManager:
    def __init__(self, script_dir):
        # Models are now saved in src/models folder (sibling to tkinter_ui)
        self.script_dir = os.path.join(os.path.dirname(script_dir), 'src', 'models')
        os.makedirs(self.script_dir, exist_ok=True)

        self.rf_model  = None
        self.lr_model  = None
        self.svm_model = None
        self.mlp_model = None
        self.xgb_model = None

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
        self.rf_model = self.lr_model = self.svm_model = self.xgb_model = None

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

        missing = [m for m in models_data
                   if not os.path.exists(os.path.join(self.script_dir, m[0]))]
        if not missing and not force and os.path.exists(os.path.join(self.script_dir, 'feature_names.pkl')):
            return True, "Models present"

        if not os.path.exists(data_path):
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
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset missing at {data_path}")
        self.cached_train_df = self._read_excel_safe(data_path)
        return self._prepare_df(self.cached_train_df)

    # ── Analytics Methods ──────────────────────────────────────────────────────

    def get_detailed_metrics(self, model_name, data_path):
        """Calculate clinical metrics: Sensitivity, Specificity, PPV, NPV (cached)."""
        if model_name in self.analytics_cache['metrics']:
            return self.analytics_cache['metrics'][model_name]

        model = self.load_model(model_name)
        if model is None:
            return None

        _, X_test, _, y_test, _ = self._load_training_data(data_path)
        y_pred = model.predict(X_test)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

        metrics = {
            "Accuracy":                      (tp + tn) / (tp + tn + fp + fn),
            "Sensitivity (Recall)":          recall_score(y_test, y_pred),
            "Specificity":                   tn / (tn + fp) if (tn + fp) > 0 else 0.0,
            "PPV (Precision)":               precision_score(y_test, y_pred, zero_division=0),
            "NPV (Negative Predictive Val)": tn / (tn + fn) if (tn + fn) > 0 else 0.0,
            "F1-Score":                      f1_score(y_test, y_pred),
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

    # ── Model Loading ──────────────────────────────────────────────────────────

    def load_model(self, model_name):
        """Load a model by name, using in-memory cache to avoid repeated disk reads."""
        _map = {
            "Random Forest":       ('rf_model',  'random_forest_model.pkl'),
            "Logistic Regression": ('lr_model',  'logistic_regression_model.pkl'),
            "SVM":                 ('svm_model', 'svm_model.pkl'),
            "XGBoost":             ('xgb_model', 'xgboost_model.pkl'),
            "MLP":                 ('mlp_model', 'mlp_model.pkl'),
        }
        if model_name not in _map:
            return None
        attr, fname = _map[model_name]
        try:
            if getattr(self, attr) is None:
                path = os.path.join(self.script_dir, fname)
                if os.path.exists(path):
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
        confs = [prob[pred] for pred, prob in zip(predictions, probabilities)]
        risks = [prob[1]    for prob      in probabilities]
        return predictions, confs, risks

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
