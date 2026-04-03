import os
import json
import pandas as pd
import numpy as np

class DataManager:
    def __init__(self, data_path=None, user_data_path=None, db_manager=None):
        self.data_path = data_path
        self.uploaded_df = None
        self.raw_subset = None # Stores the raw data BEFORE preprocessing for non-destructive toggling
        self.master_df = None # Persistent in-memory cache for fast forensic searching
        self.prediction_results = None
        self.mean_values = None
        self.selected_indices = set()
        self.db_manager = db_manager
        
        # Use provided user_data_path or fallback to script location
        self.user_data_dir = user_data_path or os.path.dirname(os.path.abspath(__file__))
        self._config_path = os.path.join(self.user_data_dir, 'session_config.json')

    def save_session(self):
        """Persist session state (last data path)."""
        try:
            cfg = {'last_data_path': self.data_path or ''}
            with open(self._config_path, 'w') as f:
                json.dump(cfg, f)
        except Exception:
            pass

    def restore_session(self):
        """Restore last session's data path so Analytics work on relaunch."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path) as f:
                    cfg = json.load(f)
                path = cfg.get('last_data_path', '')
                if path and os.path.exists(path):
                    self.data_path = path
                    df, _ = self.load_data(path)
                    if df is not None:
                        self.uploaded_df = df
                        self.master_df = df.copy() # Cache master data
                        return True
        except Exception:
            pass
        return self.ensure_default_dataset()

    def ensure_default_dataset(self):
        """Fallback to the clinical gold-standard dataset if no user data is loaded."""
        # Try a few common relative locations for the clinical set
        possible_paths = [
            os.path.join(self.user_data_dir, 'cancer_biomarkers.xlsx'),
            os.path.join(self.user_data_dir, '..', 'src', 'data', 'cancer_biomarkers.xlsx'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'data', 'cancer_biomarkers.xlsx')
        ]
        
        for path in possible_paths:
            path = os.path.abspath(path)
            if os.path.exists(path):
                self.data_path = path
                df, _ = self.load_data(path)
                if df is not None:
                    self.uploaded_df = df
                    return True
        return False

    def save_prospective_audit(self, prediction_data):
        """Save a newly run live prediction to the real-world prospective audit log (DB + CSV fallback)."""
        # 1. PERSIST TO SQLITE (Primary Vault)
        if self.db_manager:
            self.db_manager.log_prediction(prediction_data)
            
        # 2. LEGACY CSV FALLBACK (For manual researcher review)
        try:
            audit_path = os.path.join(self.user_data_dir, 'prospective_audit_log.csv')
            
            record = {
                'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                'model': prediction_data.get('model', 'Unknown'),
                'prediction': prediction_data.get('prediction', -1),
                'risk': prediction_data.get('risk', 0.0),
                'confidence': prediction_data.get('confidence', 0.0),
                'consensus': str(prediction_data.get('consensus', 'N/A'))
            }
            
            inputs = prediction_data.get('inputs', {})
            for k, v in inputs.items():
                record[f"feature_{k}"] = v
                
            df = pd.DataFrame([record])
            if os.path.exists(audit_path):
                df.to_csv(audit_path, mode='a', header=False, index=False)
            else:
                df.to_csv(audit_path, mode='w', header=True, index=False)
        except Exception as e:
            print(f"Failed to write prospective CSV audit: {e}")

    def save_prospective_audit_batch(self, df, model_name):
        """Save batch evaluation to prospective audit log (DB + CSV fallback)."""
        # 1. PERSIST TO SQLITE
        if self.db_manager:
            for idx in df.index:
                row = df.loc[idx]
                row_data = {
                    'model': model_name,
                    'prediction': 1 if str(row.get('Prediction')).upper() == 'POSITIVE' else 0,
                    'risk': float(row.get('Risk_Score', 0)),
                    'confidence': float(row.get('Confidence', 0)),
                    'consensus': str(row.get('Consensus_Count', 'N/A')),
                    'inputs': row.to_dict()
                }
                self.db_manager.log_prediction(row_data)

        # 2. LEGACY CSV
        try:
            audit_path = os.path.join(self.user_data_dir, 'prospective_audit_log.csv')
            log_df = df.copy()
            log_df['timestamp'] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            log_df['model_run'] = model_name
            
            if os.path.exists(audit_path):
                log_df.to_csv(audit_path, mode='a', header=False, index=False)
            else:
                log_df.to_csv(audit_path, mode='w', header=True, index=False)
        except Exception as e:
            print(f"Failed to save prospective batch CSV audit: {e}")

    def load_data(self, file_path, sheet_name=None):
        """Unified data loader for Excel and CSV."""
        ext = str(file_path).lower().split('.')[-1]
        if ext in ['xlsx', 'xls']:
            return self.load_excel(file_path, sheet_name)
        elif ext == 'csv':
            return self.load_csv(file_path)
        else:
            return None, f"Unsupported file format: .{ext}"

    def load_csv(self, file_path):
        """Load and wash CSV dataset."""
        try:
            df = pd.read_csv(file_path)
            # Wash columns
            df.columns = [str(c).strip() for c in df.columns]
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            self.uploaded_df = df
            self.master_df = df.copy() # Cache master
            return df, None
        except Exception as e:
            return None, str(e)

    def load_excel(self, file_path, sheet_name=None):
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Try standard clinical sheet first, fallback to index 0
                try:
                    df = pd.read_excel(file_path, sheet_name='Training_Data')
                except ValueError:
                    xl = pd.ExcelFile(file_path)
                    if not xl.sheet_names:
                        return None, "Excel file is empty."
                    df = pd.read_excel(file_path, sheet_name=xl.sheet_names[0])
            
            # --- Robustness Improvements ---
            # 1. Clean Column Names (Strip whitespace)
            df.columns = [str(c).strip() for c in df.columns]

            # 2. Drop completely empty rows (Stop dropping empty cols so placeholders remain)
            df.dropna(how='all', inplace=True)

            # 3. Clinical Placeholder Injection (Ensure results columns always exist)
            placeholders = ['Prediction', 'Risk_Score', 'Cancer Risk Class']
            for p in placeholders:
                # Fuzzy check to avoid duplicates if columns exist with slightly different names
                if not any(str(p).lower() in str(c).lower() for c in df.columns):
                    df[p] = "" 
            
            self.uploaded_df = df
            self.master_df = df.copy() # Cache master
            return df, None
        except Exception as e:
            return None, str(e)

    def validate_data(self, df):
        """Standard validation check."""
        issues = []
        if df is None: return issues

        # Check for NaN values
        nan_count = df.isnull().sum().sum()
        if nan_count > 0:
            nan_cols = df.columns[df.isnull().any()].tolist()
            issues.append(f"Found {nan_count} NaN values in: {', '.join(nan_cols)}")

        # Check for non-numeric columns (Exclude patient metadata and diagnostic placeholders)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        ignore_keywords = ['id', 'sample', 'rish', 'class', 'prediction', 'risk', 'score', 'verdict']
        
        non_numeric_cols = [
            col for col in df.columns 
            if col not in numeric_cols and not any(k in str(col).lower() for k in ignore_keywords)
        ]
        
        if non_numeric_cols:
            issues.append(f"Non-numeric columns detected: {', '.join(non_numeric_cols)}")

        return issues

    def strict_validate(self, df, required_features):
        """Strict validation for model compatibility."""
        if df is None: return False, "No data loaded."
        
        missing = [f for f in required_features if f not in df.columns]
        if missing:
            return False, f"Missing required biomarkers: {', '.join(missing[:5])}..."
            
        # Check for sufficient data
        if len(df) < 5:
            return False, "Insufficient data samples (min 5 required for analysis)."
            
        return True, "Data validated for clinical analysis."

    def apply_imputation(self, df, method='mean'):
        if df is None: return None
        new_df = df.copy()
        numeric_cols = new_df.select_dtypes(include=[np.number]).columns

        if method == 'mean':
            for col in numeric_cols:
                new_df[col] = new_df[col].fillna(new_df[col].mean())
        elif method == 'drop':
            new_df = new_df.dropna()

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

    def remove_outliers(self, df, factor=3.0, preserve_positives=True):
        """
        Refined outlier handling for clinical data. 
        Instead of dropping rows (which removes patients), we use Winsorization (clipping)
        to preserve the records while suppressing extreme measurement noise.
        """
        if df is None: return None
        new_df = df.copy()
        numeric_cols = new_df.select_dtypes(include=[np.number]).columns
        
        # Clinical biomarkers often have 'peaks' that are the signal, not noise.
        # We use a higher factor (3.0 vs standard 1.5) to avoid cutting these.
        for col in numeric_cols:
            # Skip ID columns if they were detected as numeric
            if any(term in str(col).lower() for term in ['id', 'sample', 'class']):
                continue
                
            Q1 = new_df[col].quantile(0.25)
            Q3 = new_df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # ROBUSTNESS FIX: Only apply clipping if there's enough variance to calculate a meaningful IQR
            if IQR > 0:
                lower = Q1 - factor * IQR
                upper = Q3 + factor * IQR
                
                # Winsorization: Clip extreme values instead of dropping rows.
                # This ensures positive cases (who HAVE high biomarker values) stay in the dataset.
                new_df[col] = new_df[col].clip(lower=lower, upper=upper)
            
        return new_df

    def get_processed_data(self, df, settings):
        """Standardized processing pipeline that respects user settings."""
        if df is None: return None
        new_df = df.copy()
        
        # 1. Imputation (Default for NaN to prevent model crashes)
        new_df = self.apply_imputation(new_df, 'mean')
        
        # 2. Outlier Removal (Respect user setting)
        if settings.get('outlier_removal', True):
            new_df = self.remove_outliers(new_df)
            
        # 3. Scaling (Respect user setting)
        if settings.get('scaling_enabled', True):
            new_df = self.apply_scaling(new_df, 'standard')
            
        return new_df
