import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.cluster import KMeans

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

class ModelManager:
    def __init__(self, script_dir):
        # Set directory to 'views/modal' within the script folder as requested
        self.script_dir = os.path.join(script_dir, 'views', 'modal')
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
            
        self.rf_model = None
        self.lr_model = None
        self.svm_model = None
        self.xgb_model = None
        self.feature_names = self._load_feature_names()

    @property
    def features(self):
        return self.feature_names

    def _load_feature_names(self):
        try:
            path = os.path.join(self.script_dir, 'feature_names.pkl')
            if os.path.exists(path):
                return joblib.load(path)
            # Default fallback common biomarkers if pkl is missing
            return ["CA-125", "CEA", "AFP", "PSA", "CA-15-3", "CA-19-9", "NSE", "HE4", "CYFRA 21-1", "B2M"]
        except Exception as e:
            print(f"Error loading feature names: {e}")
            return []

    def check_and_train_models(self, data_path, status_callback=None, force=False):
        """Check if models exist, otherwise train them. Skips existing unless force=True"""
        models_data = [
            ('rf_model.pkl', 'Random Forest', RandomForestClassifier(n_estimators=100, random_state=42)),
            ('lr_model.pkl', 'Logistic Regression', LogisticRegression(random_state=42, max_iter=1000)),
            ('svm_model.pkl', 'SVM', SVC(probability=True, random_state=42))
        ]
        if HAS_XGB:
            models_data.append(('xgboost_model.pkl', 'XGBoost', XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)))
        
        missing = [m for m in models_data if not os.path.exists(os.path.join(self.script_dir, m[0]))]
        
        if not missing and not force and os.path.exists(os.path.join(self.script_dir, 'feature_names.pkl')):
            return True, "Models present"

        if status_callback: 
            status_callback("Training models... This might take a moment.", "orange")
        
        try:
            # Load training data
            df = pd.read_excel(data_path, sheet_name='Training_Data')
            
            # Create target if missing
            if "cancer_risk_class" not in df.columns:
                kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
                df["cancer_risk_class"] = kmeans.fit_predict(df.select_dtypes(include=[np.number]))
            
            X = df.drop(["sample_id", "cancer_risk_class"], axis=1, errors='ignore')
            y = df["cancer_risk_class"]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Save feature names
            joblib.dump(X.columns.tolist(), os.path.join(self.script_dir, 'feature_names.pkl'))
            self.feature_names = X.columns.tolist()

            # Train each model if missing or if forcing
            for pkl, name, model_obj in models_data:
                target_path = os.path.join(self.script_dir, pkl)
                if not os.path.exists(target_path) or force:
                    if status_callback: status_callback(f"Training {name}...", "orange")
                    model_obj.fit(X_train, y_train)
                    joblib.dump(model_obj, target_path)
                    
            return True, "Training process finished."
        except Exception as e:
            return False, f"Training failed: {str(e)}"

    def load_model(self, model_name):
        """Load a model dynamically with robust error handling from 'models/' folder"""
        try:
            if model_name == "Random Forest":
                if self.rf_model is None:
                    path = os.path.join(self.script_dir, 'rf_model.pkl')
                    if os.path.exists(path): self.rf_model = joblib.load(path)
                    else: return None
                return self.rf_model
            elif model_name == "Logistic Regression":
                if self.lr_model is None:
                    path = os.path.join(self.script_dir, 'lr_model.pkl')
                    if os.path.exists(path): self.lr_model = joblib.load(path)
                    else: return None
                return self.lr_model
            elif model_name == "SVM":
                if self.svm_model is None:
                    path = os.path.join(self.script_dir, 'svm_model.pkl')
                    if os.path.exists(path): self.svm_model = joblib.load(path)
                    else: return None
                return self.svm_model
            elif model_name == "XGBoost":
                if self.xgb_model is None:
                    path = os.path.join(self.script_dir, 'xgboost_model.pkl')
                    if os.path.exists(path): self.xgb_model = joblib.load(path)
                    else: return None # Model logic will handle this being None
                return self.xgb_model
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None
        return None

    def predict_single(self, model_name, feature_values):
        model = self.load_model(model_name)
        if model is None:
            raise ValueError(f"Model '{model_name}' could not be loaded. Please ensure it is trained and the file exists.")
            
        # Create a dictionary with all features initialized to 0.0
        full_input = {feat: 0.0 for feat in self.feature_names}
        
        # Update with provided values (ensure conversion to float)
        for k, v in feature_values.items():
            if k in full_input:
                full_input[k] = float(v)
        
        # Create DataFrame with correct feature names and order
        input_df = pd.DataFrame([full_input])[self.feature_names]
            
        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0]
        return prediction, max(probability)

    def predict_batch(self, model_name, df):
        model = self.load_model(model_name)
        if model is None:
            raise ValueError(f"Model '{model_name}' could not be loaded. Please ensure it is trained and the file exists.")
            
        # Create a copy to avoid modifying original
        X = df.copy()
        
        # Ensure all required features exist, fill missing with 0.0
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0.0
        
        # Select and reorder to match training
        X = X[self.feature_names]
                
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        return predictions, [max(prob) for prob in probabilities]

    def get_local_explanation(self, model_name, inputs):
        """Simple contribution analysis for a single prediction"""
        model = self.load_model(model_name)
        
        # Contribution proxy logic
        if hasattr(model, 'feature_importances_'):
            # Works for RF and XGBoost
            contrib = model.feature_importances_
        elif hasattr(model, 'coef_'):
            # Works for Logistic Regression
            contrib = np.abs(model.coef_[0])
        else:
            # Fallback for SVM: Use RF importance as a proxy for feature significance
            try:
                rf_ref = self.load_model("Random Forest")
                contrib = rf_ref.feature_importances_
            except:
                contrib = np.ones(len(self.feature_names)) # Equal weight if all else fails
            
        # Create a sorted list of (feature, contribution)
        explanation = []
        for i, feat in enumerate(self.feature_names):
            # Scale by input value - heuristic for local impact
            val = float(inputs.get(feat, 0.0))
            score = contrib[i] * (val / 10.0) # Heuristic scaling
            explanation.append((feat, score))
            
        # Sort by absolute score
        explanation.sort(key=lambda x: abs(x[1]), reverse=True)
        return explanation[:10] # Top 10 factors
