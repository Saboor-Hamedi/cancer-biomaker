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
            row = df.loc[idx]
            patient_id = row.get('sample_id', f"PAT-{idx}")
            
            # Robust extraction: find columns that look like PSA, AFP, CA125
            def find_val(row, terms):
                for col in row.index:
                    if any(t.lower() in str(col).lower() for t in terms):
                        try:
                            val = float(row[col])
                            return val if not np.isnan(val) else 0
                        except (ValueError, TypeError):
                            continue
                return 0

            psa = find_val(row, ['psa', 'prostate_specific'])
            afp = find_val(row, ['afp', 'alpha_fetoprotein'])
            ca125 = find_val(row, ['ca125', 'cancer_antigen'])
            
            # Use provided risk if exists, else estimate
            risk = row.get('risk', row.get('prediction', 0.8 if psa > 28000 else 0.2))
            
            # Map values to a standardized history (Simulate Month -9, -6, -3, Today)
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
            # Normalize keys to match what load_historical_data expects if needed
            df_mock = pd.DataFrame([current_metrics])
            df_mock['sample_id'] = patient_id
            self.load_historical_data(df_mock)
            history = self.patient_histories.get(patient_id)

        if not history or len(history) < 2:
            return None
            
        # 1. Standard Velocity Calculations (Last 3 Months)
        last = history[-1]
        prev = history[-2]
        
        def calc_velocity(l, p):
            if p == 0: return 0.0 if l == 0 else 100.0
            return ((l - p) / p) * 100
        
        psa_v = calc_velocity(last['psa'], prev['psa'])
        afp_v = calc_velocity(last['afp'], prev['afp'])
        risk_v = (last['risk'] - prev['risk']) * 100
        
        # 2. Doubling Time Calculation (Standard Oncology Metric)
        def calc_doubling_time(v2, v1, months=3):
            # T_d = (ln(2) * dt) / (ln(V2/V1))
            try:
                if v1 <= 0 or v2 <= v1: return "Stable"
                dt = (np.log(2) * months) / np.log(v2 / v1)
                return f"{dt:.1f} Mo"
            except (ZeroDivisionError, ValueError):
                return "N/A"
            
        psa_double = calc_doubling_time(last['psa'], prev['psa'])
        
        # 3. 3-Month Forecast Projection (Linear)
        forecast_month = 3
        def project(v_now, v_prev, months_gap=3):
            if months_gap <= 0: return v_now
            slope = (v_now - v_prev) / months_gap
            proj = v_now + (slope * forecast_month)
            return max(0, proj)
            
        forecast = {
            "month": forecast_month,
            "psa": project(last['psa'], prev['psa']),
            "afp": project(last['afp'], prev['afp']),
            "ca125": project(last['ca125'], prev['ca125']),
            "risk": min(1.0, project(last['risk'], prev['risk']))
        }
        
        # 4. Clinical Trend Verdict (Human-Friendly Output)
        if risk_v > 15:
            verdict = "⚠️ CRITICAL: Rapidly escalating risk profile detected. Immediate intervention recommended."
            level = "DANGER"
        elif risk_v > 5 or psa_v > 20:
            verdict = "⚠️ WARNING: Significant metabolic momentum observed. Prioritize for clinical re-verification."
            level = "WARNING"
        elif risk_v < -5:
            verdict = "✅ POSITIVE: Diagnostic risk is receding. Treatment response appears favorable."
            level = "SUCCESS"
        else:
            verdict = "ℹ️ STABLE: Biomarker levels are consistent with baseline. Maintain routine surveillance."
            level = "INFO"
            
        velocity_metrics = {
            "psa_velocity": psa_v,
            "psa_doubling": psa_double,
            "afp_velocity": afp_v,
            "risk_delta": risk_v,
            "verdict": verdict,
            "verdict_level": level
        }
        
        return {
            "history": history,
            "forecast": forecast,
            "metrics": velocity_metrics
        }

