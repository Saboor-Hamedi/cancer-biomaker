import numpy as np
import pandas as pd

class VelocityManager:
    """Handles longitudinal patient data and biomarker trajectory calculations."""
    
    def __init__(self):
        # We will hold simulated historical data in-memory or load from a db
        self.patient_histories = {}

    def load_historical_data(self, df):
        """Mock method to generate synthetic historical context from a single snapshot."""
        if df is None or len(df) == 0: return
        
        # In a real deployed environment, this would pull from EHR/EMR Autobridge
        for idx in df.index:
            patient_id = df.loc[idx].get('sample_id', f"PAT-{idx}")
            
            # Extract key baseline features
            psa = df.loc[idx].get('PSA_concentration', 0)
            afp = df.loc[idx].get('AFP_level', 0)
            ca125 = df.loc[idx].get('CA125_level', 0)
            
            risk = 0.8 if psa > 28000 else 0.2
            
            # Simulate historical timeline (Month -9, Month -6, Month -3, Today)
            history = [
                {"month": -9, "psa": max(0, psa * 0.4), "afp": max(0, afp * 0.6), "ca125": max(0, ca125 * 0.7), "risk": max(0.05, risk - 0.4)},
                {"month": -6, "psa": max(0, psa * 0.6), "afp": max(0, afp * 0.8), "ca125": max(0, ca125 * 0.9), "risk": max(0.05, risk - 0.2)},
                {"month": -3, "psa": max(0, psa * 0.85), "afp": max(0, afp * 0.95), "ca125": max(0, ca125 * 0.95), "risk": max(0.05, risk - 0.1)},
                {"month": 0, "psa": psa, "afp": afp, "ca125": ca125, "risk": risk}
            ]
            
            self.patient_histories[patient_id] = history

    def get_patient_velocity(self, patient_id, current_metrics=None):
        """Returns the time-series trajectory and calculated velocity for a patient."""
        history = self.patient_histories.get(patient_id)
        
        # If not pre-loaded but we have current metrics (e.g., from a live single prediction)
        if not history and current_metrics:
            df_mock = pd.DataFrame([current_metrics])
            df_mock['sample_id'] = patient_id
            self.load_historical_data(df_mock)
            history = self.patient_histories.get(patient_id)

        if not history or len(history) < 2:
            return None
            
        # Calculate doubling time roughly based on last 2 readings (Month -3 to Today)
        last = history[-1]
        prev = history[-2]
        
        def calc_velocity(l, p):
            if p == 0: return 0.0
            return ((l - p) / p) * 100
        
        velocity_metrics = {
            "psa_velocity": calc_velocity(last['psa'], prev['psa']),
            "afp_velocity": calc_velocity(last['afp'], prev['afp']),
            "risk_delta": (last['risk'] - prev['risk']) * 100  # Percentage point shift
        }
        
        return {
            "history": history,
            "metrics": velocity_metrics
        }
