"""
Model Controller - Handles model training, predictions, and analytics.
"""

import threading
from tkinter import messagebox

import pandas as pd
import numpy as np
from utils.error_handler import ErrorHandler


class ModelController:
    """Controller for model training, predictions, and analytics operations."""

    def __init__(self, model_manager, data_manager, layout_manager, error_handler=None):
        self.model_manager = model_manager
        self.data_manager = data_manager
        self.layout_manager = layout_manager
        self.error_handler = error_handler or ErrorHandler()
        self.current_prediction_data = None

    def handle_train_models(self):
        """Handle model training request."""
        if not self.layout_manager.get_components()['sidebar']:
            return

        if not self.data_manager.data_path:
            messagebox.showwarning("Data Required", "Please upload a dataset first to train your models.")
            return

        if not messagebox.askyesno("Confirm Training",
                                 "This will retrain all models (RF, LR, SVM, XGBoost) using the current dataset. Proceed?"):
            return

        def task():
            success, msg = self.model_manager.check_and_train_models(
                self.data_manager.data_path if hasattr(self.data_manager, 'data_path') else None,
                self.layout_manager.update_status,
                force=True
            )
            if success:
                self.layout_manager.root.after(0, lambda: self.layout_manager.refresh_input_features(self.model_manager.feature_names))
                status_msg = "All clinical models re-trained successfully"
                self.layout_manager.root.after(0, lambda: self.layout_manager.update_status(status_msg, "#10B981"))
                self.layout_manager.root.after(0, lambda: self.error_handler.notify(status_msg, type='success'))
            else:
                self.layout_manager.root.after(0, lambda: self.layout_manager.update_status(f"Training failed: {msg}", "red"))

        threading.Thread(target=task, daemon=True).start()

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
                prediction, conf, risk = self.model_manager.predict_ensemble(feature_values, is_single=True)
                # For Ensemble, consensus is baked into 'conf' (agreement %)
                total_models = len([m for m in models_list if "AI Ensemble" not in m])
                agree_count = int(round(conf * total_models))
                consensus_str = f"{agree_count}/{total_models} Models"
            else:
                # 1. Primary Model Prediction
                prediction, conf, risk = self.model_manager.predict_single(model_name, feature_values)

                # 2. Calculate Consensus among individual models
                votes = []
                for m_name in models_list:
                    if "AI Ensemble" in m_name: continue
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

            self.current_prediction_data = result

            if not silent:
                self._update_ui_with_prediction(result)

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
            accuracy=confidence,
            precision=risk,
            status=status,
            triage=triage,
            consensus=consensus
        )

        # Update status
        risk_color = "#EF4444" if risk > 0.7 else "#F59E0B" if risk > 0.3 else "#10B981"
        self.layout_manager.update_status(
            f"Prediction: {status} (Risk: {risk:.1%})",
            risk_color
        )

    def predict_batch(self):
        """Perform batch prediction on uploaded data."""
        if self.data_manager.uploaded_df is None:
            messagebox.showwarning("Warning", "Please upload data first")
            return

        model_name = self.layout_manager.sidebar.model_var.get()
        model = self.model_manager.load_model(model_name)
        if not self.error_handler.require_model(model, model_name):
            return

        try:
            self.layout_manager.update_status(f"Predicting with {model_name}...", "orange")

            df = self.data_manager.uploaded_df.copy()
            models_list = self.layout_manager.callbacks.get('models', ["Random Forest", "Logistic Regression", "SVM"])
            is_ensemble = "AI Ensemble" in model_name
            
            # 1. Prediction routing
            if is_ensemble:
                predictions, confidences, risks = self.model_manager.predict_ensemble(df, is_single=False)
                # total individual models (excluding ensemble entry)
                total_indiv = len([m for m in models_list if "AI Ensemble" not in m])
                agreement_counts = confidences * total_indiv
            else:
                predictions, confidences, risks = self.model_manager.predict_batch(model_name, df)

            # 2. Consensus Calculation
            if is_ensemble:
                avg_consensus = np.mean(agreement_counts)
                total_models = len(models_list) - 1
                consensus_str = f"{avg_consensus:g}/{total_models} Models"
            else:
                batch_votes = [] # List of prediction arrays
                for m_name in models_list:
                    if "AI Ensemble" in m_name: continue
                    try:
                        p, _, _ = self.model_manager.predict_batch(m_name, df)
                        batch_votes.append(p)
                    except:
                        continue
                
                # Calculate per-sample agreement with primary prediction
                agreement_counts = np.zeros(len(predictions))
                for v in batch_votes:
                    agreement_counts += (v == predictions).astype(int)
                
                avg_consensus = np.mean(agreement_counts)
                total_models = len(batch_votes)
                consensus_str = f"{avg_consensus:g}/{total_models} Models"

            # Add results to dataframe
            df['Prediction'] = ['POSITIVE' if p == 1 else 'NEGATIVE' for p in predictions]
            df['Confidence'] = confidences
            df['Risk_Score'] = risks
            df['Consensus_Count'] = agreement_counts

            self.data_manager.prediction_results = df

            # Update UI
            pos_count = sum(predictions)
            total_count = len(predictions)
            
            # Update Dashboard Metrics
            avg_risk = np.mean(risks) * 100
            avg_conf = np.mean(confidences) * 100
            triage = "Review Required" if avg_risk > 50 else "Stable"
            
            self.layout_manager.update_metrics(
                accuracy=avg_conf, 
                precision=avg_risk, 
                status=f"Batch: {pos_count} Positives",
                triage=triage,
                consensus=consensus_str
            )

            status_msg = f"Batch prediction: {pos_count}/{total_count} positive cases"
            self.layout_manager.update_status(status_msg, "#10B981")
            self.error_handler.notify(status_msg, type='success')

        except Exception as e:
            self.error_handler.log_and_notify("Batch Prediction", e, "Batch Prediction Error")

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
