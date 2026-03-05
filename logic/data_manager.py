import os
import pandas as pd
import numpy as np

class DataManager:
    def __init__(self, data_path=None):
        self.data_path = data_path
        self.uploaded_df = None
        self.prediction_results = None

    def load_excel(self, file_path, sheet_name=None):
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            self.uploaded_df = df
            return df, None
        except Exception as e:
            return None, str(e)

    def validate_data(self, df):
        issues = []
        if df is None:
            return issues

        # Check for NaN values
        nan_count = df.isnull().sum().sum()
        if nan_count > 0:
            nan_cols = df.columns[df.isnull().any()].tolist()
            issues.append(f"Found {nan_count} NaN values in: {', '.join(nan_cols)}")

        # Check for non-numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric_cols = [col for col in df.columns if col not in numeric_cols and col not in ['sample_id', 'cancer_risk_class']]
        if non_numeric_cols:
            issues.append(f"Non-numeric columns detected: {', '.join(non_numeric_cols)}")

        return issues

    def apply_imputation(self, df, method='mean'):
        if df is None: return None
        new_df = df.copy()
        numeric_cols = new_df.select_dtypes(include=[np.number]).columns
        
        if method == 'mean':
            for col in numeric_cols:
                new_df[col].fillna(new_df[col].mean(), inplace=True)
        elif method == 'drop':
            new_df.dropna(inplace=True)
            
        return new_df

    def apply_scaling(self, df, method='normalize'):
        if df is None: return None
        new_df = df.copy()
        numeric_cols = new_df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if method == 'normalize':
                min_v, max_v = new_df[col].min(), new_df[col].max()
                if max_v != min_v:
                    new_df[col] = (new_df[col] - min_v) / (max_v - min_v)
            elif method == 'standard':
                mean_v, std_v = new_df[col].mean(), new_df[col].std()
                if std_v != 0:
                    new_df[col] = (new_df[col] - mean_v) / std_v
        return new_df

    def remove_outliers(self, df):
        if df is None: return None
        new_df = df.copy()
        numeric_cols = new_df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            Q1 = new_df[col].quantile(0.25)
            Q3 = new_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            new_df = new_df[(new_df[col] >= lower) & (new_df[col] <= upper)]
        return new_df
