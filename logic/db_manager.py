import sqlite3
import os
import json
import pandas as pd
from datetime import datetime

class DBManager:
    """Handles unified clinical data persistence using SQLite."""
    
    def __init__(self, db_path):
        self.db_path = os.path.join(db_path, "clinical_vault.db")
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Build the clinical schema for audit logs and longitudinal tracking."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Audit Table: Stores all live predictions for forensic review
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    patient_id TEXT,
                    model TEXT,
                    prediction INTEGER,
                    risk REAL,
                    confidence REAL,
                    consensus TEXT,
                    biomarkers_json TEXT
                )
            ''')
            
            # 2. Longitudinal Table: Stores periodic measurements for Velocity analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patient_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    timestamp TEXT,
                    psa REAL,
                    afp REAL,
                    ca125 REAL,
                    risk REAL,
                    is_simulated INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()

    def log_prediction(self, data):
        """Save a forensic record of a single patient prediction."""
        try:
            inputs = data.get('inputs', {})
            p_id = inputs.get('sample_id', "ActivePatient-01")
            
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO audit_log 
                    (timestamp, patient_id, model, prediction, risk, confidence, consensus, biomarkers_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    p_id,
                    data.get('model', 'Unknown'),
                    data.get('prediction', -1),
                    data.get('risk', 0.0),
                    data.get('confidence', 0.0),
                    str(data.get('consensus', 'N/A')),
                    json.dumps(inputs)
                ))
        except Exception as e:
            print(f"Database Error (Audit): {e}")

    def save_patient_snapshot(self, patient_id, metrics, is_simulated=0):
        """Store a biomarker snapshot for trajectory calculations."""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO patient_history 
                    (patient_id, timestamp, psa, afp, ca125, risk, is_simulated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    metrics.get('psa', 0.0),
                    metrics.get('afp', 0.0),
                    metrics.get('ca125', 0.0),
                    metrics.get('risk', 0.0),
                    is_simulated
                ))
        except Exception as e:
            print(f"Database Error (History): {e}")

    def get_patient_history(self, patient_id):
        """Retrieve all recorded snapshots for a patient ordered by time."""
        try:
            with self._get_connection() as conn:
                query = "SELECT timestamp, psa, afp, ca125, risk FROM patient_history WHERE patient_id = ? ORDER BY timestamp ASC"
                df = pd.read_sql_query(query, conn, params=(patient_id,))
                
                # Convert back to list of dicts for VelocityManager compatibility
                history = []
                for _, row in df.iterrows():
                    history.append({
                        "month": row['timestamp'],
                        "psa": row['psa'],
                        "afp": row['afp'],
                        "ca125": row['ca125'],
                        "risk": row['risk']
                    })
                return history
        except Exception as e:
            print(f"Database Error (Query): {e}")
            return []

    def clear_vault(self):
        """Wipe all clinical records (System Reset)."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM audit_log")
                conn.execute("DELETE FROM patient_history")
                conn.commit()
        except Exception as e:
            print(f"Database Error (Purge): {e}")
