import pandas as pd
import numpy as np
import joblib
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

# Load data
df = pd.read_excel("../data/cancer_biomarkers.xlsx", sheet_name='Training_Data')

# Create target
if "cancer_risk_class" not in df.columns:
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    df["cancer_risk_class"] = kmeans.fit_predict(df.select_dtypes(include=[np.number]))

X = df.drop(["sample_id", "cancer_risk_class"], axis=1)
y = df["cancer_risk_class"]

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 1. Random Forest
print("Training Random Forest...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
joblib.dump(rf_model, 'rf_model.pkl')

# 2. Logistic Regression
print("Training Logistic Regression...")
lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train, y_train)
joblib.dump(lr_model, 'lr_model.pkl')

# 3. SVM
print("Training SVM...")
svm_model = SVC(probability=True, random_state=42)
svm_model.fit(X_train, y_train)
joblib.dump(svm_model, 'svm_model.pkl')

# 4. XGBoost (if available)
if HAS_XGB:
    print("Training XGBoost...")
    xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_model.fit(X_train, y_train)
    joblib.dump(xgb_model, 'xgboost_model.pkl')
    print("XGBoost model saved.")

joblib.dump(X.columns.tolist(), 'feature_names.pkl')
print("All models trained and saved successfully.")