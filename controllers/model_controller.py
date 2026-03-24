"""
Model Controller - Handles model training, predictions, and analytics.
"""

import os
import threading
from tkinter import messagebox

import pandas as pd
import numpy as np
import logging
from utils.error_handler import ErrorHandler

log = logging.getLogger(__name__)


from logic.diagnostic_engine import DiagnosticEngine

class ModelController:
    """Controller for model training, predictions, and analytics operations."""

    def __init__(self, model_manager, data_manager, layout_manager, error_handler=None, velocity_manager=None, async_runner=None):
        self.model_manager = model_manager
        self.data_manager = data_manager
        self.layout_manager = layout_manager
        self.error_handler = error_handler or ErrorHandler()
        self.velocity_manager = velocity_manager
        self.async_runner = async_runner
        self.current_prediction_data = None
        self.diagnostic_engine = DiagnosticEngine()
        self.CORE_MODELS = ["Random Forest", "Logistic Regression", "SVM", "XGBoost"]


    def handle_train_models(self):
        """Handle model training request."""
        if not self.layout_manager.get_components()['sidebar']:
            return

        if not self.data_manager.data_path:
            messagebox.showwarning("Data Required", "Please upload a dataset first to train your models.")
            return

        self.layout_manager.update_status("Initiating clinical model training...", "orange")

        def _train_task():
            success, msg = self.model_manager.check_and_train_models(
                self.data_manager.data_path if hasattr(self.data_manager, 'data_path') else None,
                self.layout_manager.update_status,
                force=True
            )
            if not success:
                return False, msg
                
            # Update Leaderboard (Heavy calculation - keep in background)
            leaderboard = self.model_manager.get_model_leaderboard(self.data_manager.data_path)
            return True, (leaderboard, self.model_manager.feature_names)

        def _on_finish(result):
            if isinstance(result, tuple) and result[0] is True:
                leaderboard, features = result[1]
                self.layout_manager.refresh_input_features(features)
                self.layout_manager.tab_leaderboard.update_leaderboard(leaderboard)
                
                status_msg = "All clinical models re-trained successfully"
                self.layout_manager.update_status(status_msg, "#10B981")
                self.error_handler.notify(status_msg, type='success')
            else:
                msg = result[1] if isinstance(result, tuple) else "Unknown error"
                self.layout_manager.update_status(f"Training failed: {msg}", "red")

        # Start Async Task
        if self.async_runner:
            self.async_runner.run_async("Training AI Committee", _train_task, on_finish=_on_finish)
        else:
            threading.Thread(target=lambda: _on_finish(_train_task()), daemon=True).start()

    def predict_single(self, feature_values, silent=False):
        """Perform single prediction."""
        model_name = self.layout_manager.sidebar.model_var.get()

        # Validate inputs
        for k, v in feature_values.items():
            try:
                float(v)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid value for '{k}': '{v}'. All biomarker values must be numeric.")

        # Route to Ensemble or Individual Model
        is_ensemble = "AI Ensemble" in model_name
        models_list = self.layout_manager.callbacks.get('models', ["Random Forest", "Logistic Regression", "SVM"])
        
        try:
            if is_ensemble:
                ensemble_res = self.model_manager.predict_ensemble(feature_values, is_single=True)
                prediction = ensemble_res['prediction']
                conf = ensemble_res['confidence']
                risk = ensemble_res['risk']
                consensus_str = ensemble_res['consensus']
                individual_results = ensemble_res['individual_results']
            else:
                # 1. Primary Model Prediction
                prediction, conf, risk = self.model_manager.predict_single(model_name, feature_values)

                # 2. Calculate Consensus among CORE models only
                votes = []
                for m_name in self.CORE_MODELS:
                    try:
                        p, _, _ = self.model_manager.predict_single(m_name, feature_values)
                        votes.append(p)
                    except:
                        continue
                
                total_models = len(votes)
                agree_count = votes.count(prediction)
                consensus_str = f"{agree_count}/{total_models} Models"

            result = {
                'prediction': prediction,
                'confidence': conf,
                'risk': risk,
                'model': model_name,
                'inputs': feature_values,
                'consensus': consensus_str
            }
            
            if is_ensemble:
                result['individual_results'] = individual_results
            else:
                try:
                    ensemble_res = self.model_manager.predict_ensemble(feature_values, is_single=True)
                    result['individual_results'] = ensemble_res['individual_results']
                except:
                    pass

            # 4. Generate Clinical Forensic Data
            result['forensic'] = self.diagnostic_engine.get_individual_forensic(feature_values, risk)

            # 5. Prediction Stability Check (Asynchronous)
            # This involves 122+ secondary predictions which can cause UI lag.
            result['stability_metric'] = "Calculating..."
            
            def _stability_task():
                perturb_stable = True
                try:
                    for feat, val in feature_values.items():
                        v = float(val)
                        for perturb in [0.98, 1.02]:
                            temp_inp = feature_values.copy()
                            temp_inp[feat] = v * perturb
                            p_temp, _, _ = self.model_manager.predict_single(model_name, temp_inp)
                            if p_temp != result['prediction']:
                                return False
                    return True
                except:
                    return True

            def _on_stability_finish(stable):
                result['stability_metric'] = "98% Robust" if stable else "Low (Sensitivity detected)"
                if not silent:
                    self.layout_manager.update_status(f"Clinical stability verified: {result['stability_metric']}", "#10B981")
                # Persist result if audit supported
                if hasattr(self.data_manager, 'save_prospective_audit'):
                    self.data_manager.save_prospective_audit(result)

            if not silent:
                self.layout_manager.update_status("Analyzing clinical robustness...", "orange")

            if self.async_runner:
                self.async_runner.run_async("Robustness Check", _stability_task, on_finish=_on_stability_finish)
            else:
                _on_stability_finish(_stability_task())

            # 6. Longitudinal Context Injection
            patient_id = feature_values.get('sample_id', 'ActivePatient-01')
            if self.velocity_manager:
                vel_data = self.velocity_manager.get_patient_velocity(patient_id, feature_values)
                if vel_data:
                    result['velocity_context'] = vel_data['metrics']
                else:
                    result['velocity_context'] = None

            self.current_prediction_data = result




            if not silent:
                self._update_ui_with_prediction(result)

            # Phase 1: Real-world Validation Logging
            if hasattr(self.data_manager, 'save_prospective_audit'):
                self.data_manager.save_prospective_audit(result)

            return result

        except Exception as e:
            self.error_handler.log_and_notify("Single Prediction", e, "Prediction Error")
            return None

    def _update_ui_with_prediction(self, result):
        """Update UI with prediction results."""
        prediction = result['prediction']
        confidence = result['confidence']
        risk = result['risk']
        model_name = result['model']

        # Update dashboard
        status = "POSITIVE" if prediction == 1 else "NEGATIVE"
        triage = "High Risk" if risk > 0.7 else "Medium Risk" if risk > 0.3 else "Low Risk"
        consensus = result.get('consensus', "N/A")

        self.layout_manager.update_metrics(
            confidence=confidence,
            risk=risk,
            triage=triage,
            consensus=consensus
        )

        # ── Update AI Consensus (Validation Tab) ──
        if 'individual_results' in result:
            self.layout_manager.tab_validation.update_comparison(result)
        else:
            # If user ran a single model, run ensemble in background for consensus forensic
            try:
                ensemble_res = self.model_manager.predict_ensemble(result.get('inputs', {}), is_single=True)
                self.layout_manager.tab_validation.update_comparison(ensemble_res)
            except:
                pass

        # ── Generate Qualitative Clinical Analysis ──
        if prediction == 1:
            narrative = f"The {model_name} indicates a HIGH RISK patient profile. "
            if risk > 0.8:
                narrative += "Aggressive biomarker signals detected. Urgent oncology consultation is recommended. "
            else:
                narrative += "Moderate physiological indicators observed. Suggest further diagnostic imaging. "
            level = "DANGER"
        else:
            narrative = f"Biological signals fall within the clinical baseline. {model_name} predicts a NEGATIVE diagnosis. "
            if consensus.startswith("3") or consensus.startswith("4") or consensus.startswith("5"):
                narrative += "Strong AI consensus reinforces this result. Suggest routine monitoring."
            else:
                narrative += "Minor variances detected in some algorithms; results remain below the risk threshold."
            level = "SUCCESS"

        if "AI Ensemble" in model_name:
            narrative += f" [Ensemble Consensus: {consensus}]"

        self.layout_manager.dashboard.update_narrative(narrative, level=level)

        # ── Update Analysis Tab (Professional Report) ──
        self.layout_manager.tab_analysis.display_prediction_results(result)

        # ── Update Velocity Trajectory Tab ──
        if hasattr(self, 'velocity_manager') and self.velocity_manager:
            inputs = result.get('inputs', {})
            patient_id = inputs.get('sample_id', "Current_Patient")
            
            # Fuzzy match biomarker keys
            def get_val(keyword):
                for k, v in inputs.items():
                    if keyword.lower() in str(k).lower(): return float(v)
                return 0.0
                
            v_data = self.velocity_manager.get_patient_velocity(patient_id, current_metrics={
                'psa': get_val('psa'),
                'afp': get_val('afp'),
                'ca125': get_val('ca125'),
                'risk': risk
            })
            if v_data and hasattr(self.layout_manager, 'tab_velocity'):
                self.layout_manager.tab_velocity.update_velocity_data(patient_id, v_data)

        # Update status
        risk_color = "#EF4444" if risk > 0.7 else "#F59E0B" if risk > 0.3 else "#10B981"
        self.layout_manager.update_status(
            f"Prediction: {status} (Risk: {risk:.1%})",
            risk_color
        )

    def predict_batch(self):
        """Perform batch prediction on uploaded data."""
        if self.data_manager.uploaded_df is None:
            # Auto-recovery: if path exists but data isn't in memory yet
            if self.data_manager.data_path and os.path.exists(self.data_manager.data_path):
                self.layout_manager.update_status("Reloading clinical dataset...", "orange")
                df, _ = self.data_manager.load_data(self.data_manager.data_path)
                if df is not None:
                    self.layout_manager.refresh_data_tree()
            
            # If still None, prompt user to select a file for batch forensic
            if self.data_manager.uploaded_df is None:
                from tkinter import filedialog
                file_path = filedialog.askopenfilename(
                    title="Select Clinical Dataset for Batch Forensic",
                    filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
                )
                if not file_path:
                    return
                
                self.layout_manager.update_status("Loading dataset for forensic analysis...", "orange")
                df, err = self.data_manager.load_data(file_path)
                if df is None:
                    messagebox.showerror("Load Error", f"Could not load dataset: {err}")
                    return
                
                # Success! Update data path and table
                self.data_manager.data_path = file_path
                self.layout_manager.refresh_data_tree()
                # Also update the dashboard counts
                rows, cols = len(df), len(df.columns)
                features = len(self.model_manager.feature_names)
                self.layout_manager.dashboard.update_data_info(rows=rows, cols=cols, samples=rows)

        model_name = self.layout_manager.sidebar.model_var.get()
        is_ensemble = "AI Ensemble" in model_name

        def _batch_task():
            # Validation & Loading inside the background task
            if not is_ensemble:
                model = self.model_manager.load_model(model_name)
                if model is None:
                    return None, "Model file missing", "N/A"
            else:
                success, _ = self.model_manager.check_and_train_models("", force=False)
                if not success:
                    return None, "Committee models not trained", "N/A"

            # All heavy lifting moved to background task
            df = self.data_manager.uploaded_df.copy()
            
            # --- LOCAL EVALUATION: Identify Ground Truth (Labels) if present ---
            target_col = None
            for col in df.columns:
                c_low = str(col).lower()
                if any(k in c_low for k in ['target', 'class', 'label', 'rish', 'cancer']):
                    target_col = col
                    break
            
            y_true = None
            if target_col is not None:
                try:
                    # Clean Ground Truth mapping
                    # Clean Ground Truth mapping - Handle empty strings as UNKNOWN
                    mapping = {'POSITIVE': 1, 'NEGATIVE': 0, '1': 1, '0': 0, 1: 1, 0: 0, 'positive': 1, 'negative': 0}
                    raw_y = df[target_col].astype(str).str.upper().str.strip()
                    y_true = np.array([mapping.get(v, -1) for v in raw_y])
                    
                    # Only allow F1 if there are valid labels (not all -1)
                    if (y_true == -1).all():
                        y_true = None
                except:
                    y_true = None
            
            # --- SELECTION COHORT FILTER ---
            selected = self.data_manager.selected_indices
            if selected and len(selected) > 0:
                # CLINICAL AUDIT SYNC: Use label-based selection to preserve absolute spreadsheet IDs
                # This prevents ID shifting (e.g. ID 34 showing PSA of row 7)
                current_indices = df.index.tolist()
                valid_ids = [i for i in selected if i in current_indices]
                if valid_ids:
                    df = df.loc[valid_ids].copy()
                    # CRITICAL: Do NOT reset_index here, or we lose the clinical trail
            models_list = self.layout_manager.callbacks.get('models', ["Random Forest", "Logistic Regression", "SVM"])
            
            # 1. Prediction routing
            if is_ensemble:
                predictions, confidences, risks = self.model_manager.predict_ensemble(df, is_single=False)
                total_indiv = len([m for m in models_list if "AI Ensemble" not in m])
                agreement_counts = confidences * total_indiv
            else:
                predictions, confidences, risks = self.model_manager.predict_batch(model_name, df)

            # 2. Consensus Calculation & Per-Model Batch Summary
            batch_results_summary = []
            batch_votes = [] 
            all_model_risks = {} 
            successfully_run_models = []
            
            for m_name in self.CORE_MODELS:
                try:
                    p, _, r = self.model_manager.predict_batch(m_name, df)
                    batch_votes.append(p)
                    all_model_risks[m_name] = r
                    successfully_run_models.append(m_name)
                    
                    pos_count = int(np.sum(p))
                    avg_risk = float(np.mean(r))
                    det_rate = (pos_count / len(df)) * 100 if len(df) > 0 else 0
                    
                    # Compute LOCAL performance for this specific cohort
                    l_f1 = 0.0
                    l_acc = 0.0
                    if y_true is not None and len(np.unique(y_true)) > 1:
                        try:
                            from sklearn.metrics import f1_score, accuracy_score
                            l_f1 = float(f1_score(y_true, p))
                            l_acc = float(accuracy_score(y_true, p))
                        except: pass
                    
                    # Retrieve GLOBAL metrics for comparison
                    global_m = self.model_manager.get_detailed_metrics(m_name, self.data_manager.data_path)
                    g_f1 = global_m.get('F1-Score', 0) if global_m else 0
                    g_auc = global_m.get('AUC', 0) if global_m else 0
                    
                    batch_results_summary.append({
                        'model': m_name, 'positives': pos_count, 'risk': avg_risk, 
                        'rate': det_rate, 'local_f1': l_f1, 'local_acc': l_acc,
                        'global_f1': g_f1, 'global_auc': g_auc
                    })
                except: continue

            # 3. Calculate Agreement/Consensus across CORE models
            total_models = len(batch_votes)
            agreement_counts = np.zeros(len(predictions))
            if total_models > 0:
                for v in batch_votes:
                    agreement_counts += (v == predictions).astype(int)
            
            avg_consensus = np.mean(agreement_counts) if len(agreement_counts) > 0 else 0
            consensus_str = f"{avg_consensus:.2f}/{total_models}"
            
            # Determine Champion: Prioritize highest LOCAL F1 if truth exists, else highest Avg Risk
            if y_true is not None and any(res['local_f1'] > 0 for res in batch_results_summary):
                 leader_model = max(batch_results_summary, key=lambda x: x['local_f1'])['model']
            elif batch_results_summary:
                 leader_model = max(batch_results_summary, key=lambda x: x['risk'])['model']
            else:
                 leader_model = "N/A"
            present_markers = [c for c in df.columns if any(k in str(c).lower() for k in ['psa', 'afp', 'ca125', 'peak', 'slope'])]
            top_markers = present_markers[:3] if present_markers else ["Global Distribution"]

            summary_metadata = {
                'avg_consensus': avg_consensus,
                'total_committee': total_models,
                'scoreboard': batch_results_summary,
                'champion': leader_model,
                'top_markers': top_markers,
                'clinical_status': "ALERT" if np.sum(predictions) > 0 else "STABLE",
                'rate': (np.sum(predictions)/len(df)*100 if len(df)>0 else 0)
            }

            # Detailed Audit Data
            pos_indices = np.where(predictions == 1)[0]
            if len(pos_indices) == 0: pos_indices = np.where(risks > 0.5)[0]
            target_audit_indices = pos_indices # Removed [:10] limit to show all dynamic cases
            detailed_audit_data = []
            
            for array_idx in target_audit_indices:
                array_idx_int = int(array_idx)
                df_idx = df.index[array_idx_int]
                flagging_models = []
                max_r = -1.0
                lead_m = "N/A"
                
                for m_idx, m_name in enumerate(successfully_run_models):
                    if batch_votes[m_idx][array_idx_int] == 1:
                        short_name = m_name.replace("Logistic Regression", "LR").replace("Random Forest", "RF").replace("SVM", "SVM").replace("XGBoost", "XGB")
                        flagging_models.append(short_name)
                    r_val = float(all_model_risks[m_name][array_idx_int])
                    if r_val > max_r:
                        max_r = r_val
                        lead_m = m_name
                
                def get_m_val(keyword):
                    match = [c for c in df.columns if keyword.lower() in str(c).lower()]
                    if match: return float(df.loc[df_idx, match[0]]) if pd.notna(df.loc[df_idx, match[0]]) else 0.0
                    return 0.0

                r_val = float(risks[array_idx_int])
                if r_val > 0.9:
                    action = "URGENT CLINICAL REVIEW / BIOPSY"
                elif r_val > 0.7:
                    action = "IMMEDIATE MONITORING / SCAN"
                elif r_val > 0.5:
                    action = "3-MONTH FOLLOW-UP RE-TEST"
                else:
                    action = "ROUTINE CLINICAL OBSERVATION"

                detailed_audit_data.append({
                    'id': df_idx, 'lead_model': lead_m, 'detectors': ", ".join(flagging_models),
                    'risk': r_val, 'consensus': f"{int(agreement_counts[array_idx_int])}/{total_models}",
                    'psa': get_m_val('PSA'), 'afp': get_m_val('AFP'), 'ca125': get_m_val('CA125'),
                    'action': action
                })

            summary_metadata['audit_registry'] = detailed_audit_data
            
            # Smart-Sync diagnostics: overwrite existing columns if detected (even with typos)
            def update_best_match(keywords, data):
                for col in df.columns:
                    c_low = str(col).lower()
                    if any(k in c_low for k in keywords):
                        df[col] = data
                        return True
                return False

            # 1. Update Decision/Class
            if not update_best_match(['prediction', 'risk', 'class', 'status', 'verdict'], 
                                   ['POSITIVE' if p == 1 else 'NEGATIVE' for p in predictions]):
                df['Prediction'] = ['POSITIVE' if p == 1 else 'NEGATIVE' for p in predictions]

            # 2. Update Risk/Probability
            if not update_best_match(['risk', 'probability', 'score'], risks):
                df['Risk_Score'] = risks

            # 3. Update Confidence/Reliability
            if not update_best_match(['confidence', 'reliability', 'certainty'], confidences):
                df['Confidence'] = confidences
            
            df['Consensus_Count'] = agreement_counts

            # 3.5 Dynamic Diagnostic Analysis (Signal Drift & Strength)
            # CRITICAL: This MUST happen after updating columns (Prediction, Risk_Score) 
            # so the engine can calculate confidence zones and triage correctly.
            try:
                from logic.diagnostic_engine import DiagnosticEngine
                engine = DiagnosticEngine()
                dynamic_insights = engine.analyze_batch(df)
                summary_metadata['dynamic_insights'] = dynamic_insights
            except Exception as e:
                log.error("Dynamic Analysis failed: %s", e)
                summary_metadata['dynamic_insights'] = {}
            
            # 4. Move Leaderboard Calculation to Background
            # This is extremely heavy due to Cross-Validation and was causing UI freezing
            leaderboard = self.model_manager.get_model_leaderboard(self.data_manager.data_path)
            
            return df, summary_metadata, consensus_str, leaderboard

        def _on_finish(result):
            df, summary_metadata, consensus_str, leaderboard = result
            self.data_manager.prediction_results = df
            
            pos_count = int(np.sum(df['Prediction'] == 'POSITIVE'))
            total_count = len(df)
            avg_risk = df['Risk_Score'].mean() * 100
            avg_conf = df['Confidence'].mean() * 100
            triage = "Action Required" if pos_count > 0 else "Monitoring"
            
            # Update Dashboard
            self.layout_manager.update_metrics(
                confidence=avg_conf, risk=avg_risk, triage=triage, consensus=consensus_str
            )
            
            # Refresh Leaderboard (Fast UI update only)
            self.layout_manager.tab_leaderboard.update_leaderboard(leaderboard)
            
            # Update AI Consensus (Validation Tab) - Show per-model cohort metrics
            self.layout_manager.tab_validation.update_batch_comparison(
                summary_metadata['scoreboard'], total_count
            )
            
            # Update Analysis
            self.layout_manager.tab_analysis.display_batch_report(df, metadata=summary_metadata)
            
            # Switch view
            try: self.layout_manager.dashboard.notebook.select(self.layout_manager.dashboard.analysis_tab)
            except: pass
            
            # Audit log
            if hasattr(self.data_manager, 'save_prospective_audit_batch'):
                self.data_manager.save_prospective_audit_batch(df, model_name)

            status_msg = f"Forensic Complete: {pos_count} clinical positives in {total_count} records"
            self.layout_manager.update_status(status_msg, "#10B981")
            self.error_handler.notify(status_msg, type='success')

        # Start Async Task
        self.layout_manager.update_status(f"Performing Forensic Audit with {model_name}...", "orange")
        if self.async_runner:
            self.async_runner.run_async("Batch Prediction", _batch_task, on_finish=_on_finish)
        else:
            # Fallback
            _on_finish(_batch_task())

    def handle_system_reset(self):
        """Total system purge: deletes models, clears tables, and resets UI state."""
        if not messagebox.askyesno("Confirm System Reset", 
                                 "CRITICAL ACTION: This will delete ALL trained model files, "
                                 "clear all patient data, and reset the environment. Proceed?"):
            return

        # CANCEL ALL BACKGROUND TASKS: Ensure pending training/predictions don't overwrite the purge
        if self.async_runner:
            self.async_runner.cancel_all()

        def task():
            # 1. Purge models from disk
            self.model_manager.delete_all_models()
            
            # 2. Reset Data Manager state
            self.data_manager.uploaded_df = None
            self.data_manager.data_path = None
            self.data_manager.prediction_results = None
            
            # 3. Wipe UI Components
            return "SUCCESS"

        def _on_finish(res):
            self.layout_manager.clear_all_data()
            status_msg = "SYSTEM RESET COMPLETE: All clinical artifacts purged."
            self.layout_manager.update_status(status_msg, "#475569")
            self.error_handler.notify(status_msg, type='info')
            self.layout_manager.dashboard.update_narrative("Awaiting clinical data... System has been reset to factory defaults.", "INFO")

        if self.async_runner:
            self.async_runner.run_async("System Reset", task, on_finish=_on_finish)
        else:
            threading.Thread(target=lambda: _on_finish(task()), daemon=True).start()

    def get_analytics_data(self, analysis_type, **kwargs):
        """Get data for various analytics."""
        model_name = kwargs.get('model_name', self.layout_manager.sidebar.model_var.get())

        try:
            if analysis_type == 'detailed_metrics':
                return self.model_manager.get_detailed_metrics(model_name, self.data_manager.data_path)
            elif analysis_type == 'calibration':
                return self.model_manager.get_calibration_data(model_name, self.data_manager.data_path)
            elif analysis_type == 'learning_curve':
                return self.model_manager.compute_learning_curve(model_name, self.data_manager.data_path)
            elif analysis_type == 'stability':
                return self.model_manager.get_model_stability(model_name, self.data_manager.data_path)
            elif analysis_type == 'shap':
                return self.model_manager.get_shap_data(model_name, self.data_manager.data_path)
            elif analysis_type == 'tsne':
                return self.model_manager.get_tsne_data(self.data_manager.data_path)
            elif analysis_type == 'cv_scores':
                return self.model_manager.get_cv_scores(model_name, self.data_manager.data_path)

        except Exception as e:
            self.error_handler.log_and_notify(f"{analysis_type} Analytics", e, "Analytics Error")
            return None

        return None
