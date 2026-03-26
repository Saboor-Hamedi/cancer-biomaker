import numpy as np
import pandas as pd
from datetime import datetime

class VelocityManager:
    """Handles longitudinal patient data and biomarker trajectory calculations."""
    
    def __init__(self, db_manager=None):
        # Professional Persistence: DB stores history across app sessions
        self.db_manager = db_manager
        self.patient_histories = {} # Local cache for performance

    def load_historical_data(self, df):
        """Mock method to generate synthetic historical context from a single snapshot."""
        if df is None or len(df) == 0: return
        
        # In a real deployed environment, this would pull from EHR/EMR Autobridge
        for idx in df.index:
            row = df.loc[idx]
            patient_id = str(row.get('sample_id', f"PAT-{idx}"))
            
            # 1. CHECK PERSISTENT DATABASE FIRST
            if self.db_manager:
                db_history = self.db_manager.get_patient_history(patient_id)
                if db_history and len(db_history) >= 2:
                    self.patient_histories[patient_id] = db_history
                    continue

            # 2. GENERATE AND PERSIST SIMULATED HISTORY IF NONE EXISTS
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
            
            # Persist to database for forensic durability
            if self.db_manager:
                for snapshot in history:
                    self.db_manager.save_patient_snapshot(patient_id, snapshot, is_simulated=1)
            
            self.patient_histories[patient_id] = history

    def get_patient_velocity(self, patient_id, current_metrics=None):
        """Returns the time-series trajectory and calculated velocity for a patient."""
        # 1. Fetch from Cache
        history = self.patient_histories.get(patient_id)
        
        # 2. Fetch from DB if cache miss
        if not history and self.db_manager:
            history = self.db_manager.get_patient_history(patient_id)
            if history: self.patient_histories[patient_id] = history
        
        # 3. Handle live single predictions (Sync to DB)
        if not history and current_metrics:
            df_mock = pd.DataFrame([current_metrics])
            df_mock['sample_id'] = patient_id
            self.load_historical_data(df_mock)
            history = self.patient_histories.get(patient_id)
        elif history and current_metrics:
            # Update history with NEW measurement if it's recent
            # This turns the "simulated" history into a "real" longitudinal record
            last_in_db = str(history[-1]['month'])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Only record if it's a new day/session (basic deduplication)
            if last_in_db[:10] != now[:10]:
                if self.db_manager:
                    self.db_manager.save_patient_snapshot(patient_id, current_metrics, is_simulated=0)
                history.append({
                    "month": now, "psa": current_metrics.get('psa', 0), 
                    "afp": current_metrics.get('afp', 0), "ca125": current_metrics.get('ca125', 0), 
                    "risk": current_metrics.get('risk', 0)
                })

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
            
        # 5. Predictive Trajectories (Time-to-Threshold)
        # Estimates months until the patient crosses the Level 1 Triage threshold (0.85 risk)
        def calc_time_to_threshold(current_risk, prev_risk, threshold=0.85, months_gap=3):
            if current_risk >= threshold: return "AT THRESHOLD"
            if current_risk <= prev_risk: return "> 12 Mo (N/A)"
            
            slope = (current_risk - prev_risk) / months_gap
            if slope <= 0: return "> 12 Mo (Stable)"
            
            months_to_go = (threshold - current_risk) / slope
            if months_to_go > 12: return "> 12 Mo"
            return f"~{months_to_go:.1f} Mo"

        time_to_risk = calc_time_to_threshold(last['risk'], prev['risk'])

        velocity_metrics = {
            "psa_velocity": psa_v,
            "psa_doubling": psa_double,
            "afp_velocity": afp_v,
            "risk_delta": risk_v,
            "time_to_threshold": time_to_risk,
            "verdict": verdict,
            "verdict_level": level
        }
        
        return {
            "history": history,
            "forecast": forecast,
            "metrics": velocity_metrics
        }

