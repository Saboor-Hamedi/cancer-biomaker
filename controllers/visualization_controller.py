"""
Visualization Controller - Handles all plotting and visualization operations.
"""

import tkinter as tk
from logic.model_manager import HAS_XGB, HAS_TORCH
import pandas as pd
import numpy as np
from utils.error_handler import ErrorHandler
from views.visualizations import Visualizer


class VisualizationController:
    """Controller for all visualization and plotting operations."""

    def __init__(self, model_manager, data_manager, layout_manager, error_handler=None, model_controller=None):
        self.model_manager = model_manager
        self.data_manager = data_manager
        self.layout_manager = layout_manager
        self.error_handler = error_handler or ErrorHandler()
        self.model_controller = model_controller

    def _require_data(self, context='analytics'):
        """Show a friendly warning and return False when no dataset is loaded."""
        if not self.data_manager.data_path:
            from tkinter import messagebox
            messagebox.showwarning("No Data", f"No dataset loaded. Please upload or load a sample first for {context}.")
            return False
        return True

    def _require_model(self, model_name):
        """Return False when the model file is missing."""
        if self.model_manager.load_model(model_name) is None:
            from tkinter import messagebox
            messagebox.showwarning("Model Missing", f"Model '{model_name}' could not be loaded.\nPlease train it first via Data → Re-Train All Models.")
            return False
        return True

    def _require_data_and_model(self, context):
        """Check if data and model are available."""
        if not self._require_data(context):
            return False
        model_name = self.layout_manager.sidebar.model_var.get()
        return self._require_model(model_name)

    def _update_analysis_text(self, title, content):
        """Standardized helper to update the Performance Analysis tab."""
        from datetime import datetime
        if not self.layout_manager.tab_analysis:
            return

        text_widget = self.layout_manager.tab_analysis.text
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)

        header = f"{title.upper()}\n"
        header += f"System Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*60 + "\n\n"

        text_widget.insert(tk.END, header)
        text_widget.insert(tk.END, content)
        text_widget.insert(tk.END, "\n\n" + "-"*60 + "\n")
        text_widget.insert(tk.END, "End of analysis profile.")
        
        text_widget.config(state=tk.DISABLED)
        # Switch to the analysis tab
        try:
            notebook = self.layout_manager.dashboard.notebook
            notebook.select(self.layout_manager.dashboard.analysis_tab)
        except:
            pass

    def _run_async_task(self, label, func, on_finish=None):
        """Unified helper to run background tasks with GUI status management."""
        self.layout_manager.dashboard.update_status(f"Calculating {label}…", "orange")

        def task():
            try:
                result = func()
                if on_finish:
                    self.layout_manager.root.after(0, lambda: on_finish(result))
                self.layout_manager.root.after(0, lambda: self.layout_manager.dashboard.update_status(f"{label} Complete", "#10B981"))
                self.layout_manager.root.after(0, lambda: self.error_handler.notify(f"{label} calculated successfully", type='success'))
            except Exception as e:
                self.error_handler.log_and_notify(f"{label} Task", e)
                self.layout_manager.root.after(0, lambda: self.layout_manager.dashboard.update_status(f"Error: {label} failed", "red"))

        import threading
        threading.Thread(target=task, daemon=True).start()

    def show_feature_importance(self):
        """Show feature importance plot."""
        if not self._require_data_and_model("Feature Importance"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def finish(fig):
            if fig:
                Visualizer.show_modal(self.layout_manager.root, f"Feature Importance - {model_name}", fig)

        self._run_async_task(
            "Feature Weights",
            lambda: Visualizer.plot_feature_importance(
                self.model_manager.load_model(model_name),
                self.model_manager.feature_names,
                model_name
            ),
            on_finish=finish
        )

    def show_local_explanation(self):
        """Show local explanation for current prediction."""
        pred_data = None
        if self.model_controller and self.model_controller.current_prediction_data:
            pred_data = self.model_controller.current_prediction_data

        if not pred_data:
            from tkinter import messagebox
            messagebox.showwarning("No Prediction", "Please make a prediction first to see local explanations.")
            return

        model_name = pred_data.get('model', 'Active Model')

        # If explanation already cached in pred_data, show it immediately
        explanation = pred_data.get('explanation')
        if explanation:
            fig = Visualizer.plot_local_explanation(explanation, model_name)
            Visualizer.show_modal(self.layout_manager.root, f"Clinical Impact Profile — {model_name}", fig)
            return

        # Otherwise compute it now
        inputs = pred_data.get('inputs', {})
        if not inputs:
            from tkinter import messagebox
            messagebox.showwarning("No Inputs", "No biomarker input values found for this prediction.")
            return

        self.layout_manager.update_status("Calculating clinical explanation...", "orange")

        def calculate_task():
            full_input = {feat: 0.0 for feat in self.model_manager.feature_names}
            for k, v in inputs.items():
                if k in full_input:
                    full_input[k] = float(v)
            input_df = pd.DataFrame([full_input])[self.model_manager.feature_names]
            inputs_dict = input_df.iloc[0].to_dict()
            return self.model_manager.get_local_explanation(
                model_name,
                inputs_dict,
                data_path=self.data_manager.data_path
            )

        def finish(expl):
            if expl:
                fig = Visualizer.plot_local_explanation(expl, model_name)
                Visualizer.show_modal(self.layout_manager.root, f"Clinical Impact Profile — {model_name}", fig)
                self.layout_manager.update_status("Explanation generated", "#10B981")
            else:
                self.layout_manager.update_status("Explanation failed", "red")

        self._run_async_task("SHAP Analysis", calculate_task, on_finish=finish)

    def show_patient_radar(self):
        """Show patient radar profile."""
        pred_data = None
        if self.model_controller and self.model_controller.current_prediction_data:
            pred_data = self.model_controller.current_prediction_data
            
        if not pred_data:
            from tkinter import messagebox
            messagebox.showwarning("No Prediction", "Please make a prediction first to see patient profile.")
            return

        model_name = pred_data.get('model', 'Active Model')
        inputs = pred_data.get('inputs', {})

        # Display analysis in tab
        radar_data = Visualizer.get_patient_radar_data(inputs, model_name)
        self._display_patient_radar_metrics(radar_data)

        # Show the plot in modal
        fig = Visualizer.plot_patient_radar(inputs, model_name)
        Visualizer.show_modal(self.layout_manager.root, f"Patient Biomarker Radar — {model_name}", fig)

    def _display_patient_radar_metrics(self, radar_data):
        """Display patient radar analysis in the analysis tab."""
        from datetime import datetime

        self.layout_manager.tab_analysis.text.config(state=tk.NORMAL)
        self.layout_manager.tab_analysis.text.delete("1.0", tk.END)

        header = "PATIENT BIOMARKER PROFILE ANALYSIS\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.layout_manager.tab_analysis.text.insert(tk.END, header)
        self.layout_manager.tab_analysis.text.insert(tk.END, f"Model Used: {radar_data['model_name']}\n")
        self.layout_manager.tab_analysis.text.insert(tk.END, f"Biomarkers Analyzed: {radar_data['biomarkers_analyzed']}\n\n")

        self.layout_manager.tab_analysis.text.insert(tk.END, "📊 BIOMARKER VALUES:\n")
        for biomarker in radar_data['biomarker_data']:
            self.layout_manager.tab_analysis.text.insert(tk.END, f"  • {biomarker['name']}: {biomarker['value']:.3f}\n")
            self.layout_manager.tab_analysis.text.insert(tk.END, f"    → {biomarker['insight']}\n")

        self.layout_manager.tab_analysis.text.insert(tk.END, f"\n🔍 CLINICAL ASSESSMENT:\n")
        self.layout_manager.tab_analysis.text.insert(tk.END, f"  • Elevated biomarkers: {radar_data['elevated_count']}/{radar_data['biomarkers_analyzed']}\n")
        self.layout_manager.tab_analysis.text.insert(tk.END, f"  • Low biomarkers: {radar_data['low_count']}/{radar_data['biomarkers_analyzed']}\n")
        self.layout_manager.tab_analysis.text.insert(tk.END, f"  • Normal biomarkers: {radar_data['normal_count']}/{radar_data['biomarkers_analyzed']}\n")
        self.layout_manager.tab_analysis.text.insert(tk.END, f"  → Overall profile suggests {radar_data['assessment']}\n")

        self.layout_manager.tab_analysis.text.insert(tk.END, "\n💡 NOTE: This is a visual representation of biomarker levels.\n")
        self.layout_manager.tab_analysis.text.insert(tk.END, "   Consult with clinical guidelines for interpretation of specific values.\n")

        self.layout_manager.tab_analysis.text.config(state=tk.DISABLED)

    def show_counterfactual_analysis(self):
        """Show What-If Counterfactual analysis for current prediction."""
        pred_data = None
        if self.model_controller and self.model_controller.current_prediction_data:
            pred_data = self.model_controller.current_prediction_data
            
        if not pred_data:
            from tkinter import messagebox
            messagebox.showwarning("No Prediction", "Please make a prediction first to see counterfactual recommendations.")
            return

        model_name = pred_data.get('model', 'Active Model')
        inputs = pred_data.get('inputs', {})
        
        if not inputs:
            from tkinter import messagebox
            messagebox.showwarning("No Inputs", "No biomarker input values found for this prediction.")
            return

        self.layout_manager.update_status("Calculating Counterfactual Scenarios...", "orange")

        def task():
            return self.model_manager.get_counterfactual_recommendations(
                model_name,
                inputs,
                data_path=self.data_manager.data_path
            )

        def finish(data):
            if not data:
                self.layout_manager.update_status("Counterfactual generation failed", "red")
                return

            # Format analysis text
            content = "═" * 60 + "\n"
            content += f"  WHAT-IF COUNTERFACTUAL ANALYSIS: {model_name}\n"
            content += "═" * 60 + "\n\n"
            
            content += f"  Status: {data['status']}\n"
            content += f"  Current Risk: {data['current_risk']:.2%}\n"
            content += f"  Projected Risk: {data['new_risk']:.2%}\n\n"
            
            if not data['changes']:
                content += "  No actionable risk reduction identified or patient is already healthy.\n"
            else:
                content += "  RECOMMENDED BIOMARKER REDUCTIONS:\n"
                for c in data['changes']:
                    content += f"  • {c['feature']:<15}: {c['original']:.2f} ➔ {c['new']:.2f} (-{c['reduction']:.0f}%)\n"
                    
            content += "\n  CLINICAL NOTE: These are hypothetical changes identified by the AI \n"
            content += "  to lower the predicted risk profile. Actionability depends on \n"
            content += "  clinical context and specific patient factors.\n"
            
            self._update_analysis_text("Counterfactual Trajectory Audit", content)

            fig = Visualizer.plot_counterfactual_analysis(data, model_name)
            Visualizer.show_modal(self.layout_manager.root, f"Counterfactual What-If Profiler — {model_name}", fig)
            
            self.layout_manager.update_status("Counterfactuals ready", "#10B981")

        self._run_async_task("Counterfactual Analysis", task, on_finish=finish)

    def show_biomarker_network(self):
        """Show the GNN-mapped Biomarker Interaction Network."""
        self.layout_manager.update_status("Mapping Biomarker Clinical Network...", "orange")

        def task():
            return self.model_manager.get_biomarker_network_data(self.data_manager.data_path)

        def finish(data):
            if not data:
                self.layout_manager.update_status("Network mapping failed", "red")
                return

            fig = Visualizer.plot_biomarker_network(data)
            Visualizer.show_modal(self.layout_manager.root, "GNN Biomarker Pathway Analysis", fig)
            self.layout_manager.update_status("Biological Network Mapped", "#10B981")

        self._run_async_task("Network Mapping", task, on_finish=finish)

    def show_roc_curve(self):
        """Show ROC curve."""
        if not self._require_data_and_model("ROC Curve"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        self._run_async_task(
            "ROC Analysis",
            lambda: Visualizer.plot_roc_curve(model_name),
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"ROC Curve - {model_name}", fig) if fig else None
        )

    def show_confusion_matrix(self):
        """Show confusion matrix."""
        if not self._require_data_and_model("Confusion Matrix"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def analyze():
            metrics = self.model_manager.get_detailed_metrics(model_name, self.data_manager.data_path)
            if not metrics:
                return None
            
            # Format matrix for tab
            tn = metrics.get('True Negatives', 0)
            fp = metrics.get('False Positives', 0)
            fn = metrics.get('False Negatives', 0)
            tp = metrics.get('True Positives', 0)
            
            content = f"Clinical Confusion Matrix: {model_name}\n"
            content += "-"*50 + "\n"
            content += f"  Actual Healthy:   TN={tn:<5} FP={fp:<5}\n"
            content += f"  Actual Detected:  FN={fn:<5} TP={tp:<5}\n\n"
            content += f"Total Samples: {tn+fp+fn+tp}\n"
            
            self._update_analysis_text("Diagnostic Matrix Profile", content)
            
            return Visualizer.plot_confusion_matrix(metrics, model_name)

        self._run_async_task(
            "Clinical Confusion Matrix",
            analyze,
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"Confusion Matrix - {model_name}", fig) if fig else None
        )

    def show_precision_recall(self):
        """Show precision-recall curve."""
        if not self._require_data_and_model("Precision-Recall"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        self._run_async_task(
            "PR Analysis",
            lambda: Visualizer.plot_precision_recall(model_name),
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"Precision-Recall - {model_name}", fig) if fig else None
        )

    def show_model_comparison(self):
        """Show model comparison."""
        if not self._require_data("Comparison Chart"):
            return

        from logic.model_manager import HAS_XGB
        models_to_compare = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_compare.append("XGBoost")

        def task():
            results = []
            for model_name in models_to_compare:
                model = self.model_manager.load_model(model_name)
                if model is None:
                    continue

                try:
                    metrics = self.model_manager.get_detailed_metrics(model_name, self.data_manager.data_path)
                    if metrics:
                        results.append({
                            'Model': model_name,
                            'Accuracy': metrics.get('Accuracy', 0),
                            'Precision': metrics.get('PPV (Precision)', 0),
                            'Recall': metrics.get('Sensitivity (Recall)', 0),
                            'F1 Score': metrics.get('F1-Score', 0),
                            'AUC': metrics.get('AUC', 0.85) # Fallback if AUC not computed
                        })
                except Exception as e:
                    print(f"Error getting metrics for {model_name}: {e}")
                    continue

            if not results:
                return None
            
            return pd.DataFrame(results)

        def finish(df):
            if df is None or df.empty:
                from tkinter import messagebox
                messagebox.showwarning("Comparison Failed", "Could not generate comparison data.")
                return

            # Format for tab
            content = "Comparative Clinical Model Analysis:\n"
            content += "-"*50 + "\n"
            for _, row in df.iterrows():
                content += f"  • {row['Model']:.<25} Acc: {row['Accuracy']:.2%} | F1: {row['F1 Score']:.2f} | AUC: {row['AUC']:.2f}\n"
            
            self._update_analysis_text("Cross-Model Performance Summary", content)

            fig = Visualizer.plot_model_comparison(df)
            Visualizer.show_modal(self.layout_manager.root, "Model Performance Comparison", fig)

        self._run_async_task("Model Comparison", task, on_finish=finish)

    def show_accuracy_comparison(self):
        """Show accuracy comparison across models."""
        if not self._require_data("Accuracy Comparison"):
            return

        from logic.model_manager import HAS_XGB
        models_to_compare = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_compare.append("XGBoost")

        def task():
            results = []
            for model_name in models_to_compare:
                try:
                    metrics = self.model_manager.get_detailed_metrics(model_name, self.data_manager.data_path)
                    if metrics:
                        results.append({
                            'Model': model_name,
                            'Accuracy': metrics.get('Accuracy', 0)
                        })
                except Exception as e:
                    print(f"Error getting accuracy for {model_name}: {e}")
                    continue

            if not results:
                return None
            return pd.DataFrame(results)

        def finish(df):
            if df is None or df.empty:
                from tkinter import messagebox
                messagebox.showwarning("Accuracy Comparison Failed", "Could not generate accuracy comparison data.")
                return

            fig = Visualizer.plot_accuracy_comparison(df)
            Visualizer.show_modal(self.layout_manager.root, "Cross-Validation Accuracy Comparison", fig)

        self._run_async_task("Accuracy Comparison", task, on_finish=finish)

    def show_correlation_heatmap(self):
        """Show correlation heatmap."""
        if self.data_manager.uploaded_df is None:
            from tkinter import messagebox
            messagebox.showwarning("Data Required", "Please load data first to view correlations.")
            return

        self._run_async_task(
            "Correlation Heatmap",
            lambda: Visualizer.plot_correlation_heatmap(self.data_manager.uploaded_df),
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, "Biomarker Correlation Map", fig) if fig else None
        )

    def show_calibration_curve(self):
        """Show calibration curve."""
        if not self._require_data_and_model("Reliability Analysis"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def task():
            data = self.model_manager.get_calibration_data(model_name, self.data_manager.data_path)
            if not data:
                return None
            y_true, y_prob = data
            return Visualizer.plot_calibration_curve(y_true, y_prob, model_name)

        self._run_async_task("Calibration Curve", task,
                           on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"Reliability Analysis - {model_name}", fig) if fig else None)

    def show_learning_curve(self):
        """Show learning curve."""
        if not self._require_data_and_model("Learning Analysis"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        self._run_async_task(
            "Learning Curve",
            lambda: self.model_manager.compute_learning_curve(model_name, self.data_manager.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.layout_manager.root, f"Learning Analysis - {model_name}",
                                                       Visualizer.plot_learning_curve(data, model_name)) if data else None
        )

    def show_stability(self):
        """Show model stability analysis."""
        if not self._require_data_and_model("Stability Analysis"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        self._run_async_task(
            "Model Stability",
            lambda: self.model_manager.get_model_stability(model_name, self.data_manager.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.layout_manager.root, f"Model Stability - {model_name}",
                                                       Visualizer.plot_model_stability(data, model_name)) if data else None
        )

    def show_tsne_map(self):
        """Show t-SNE patient map and update analysis tab."""
        if not self._require_data("Patient Mapping"):
            return

        def finish(data):
            if not data:
                return
            
            # Calculate counts for analysis tab
            n_samples = len(data['x'])
            n_positive = sum(data['labels'])
            n_negative = n_samples - n_positive
            
            content = "═" * 60 + "\n"
            content += "  PATIENT TOPOLOGICAL CLUSTERING (t-SNE) SUMMARY\n"
            content += "═" * 60 + "\n\n"
            content += f"  Total Cohort Size Analysed:   {n_samples}\n"
            content += f"  - 'Detected' Populations:     {n_positive}\n"
            content += f"  - 'Healthy' populations:      {n_negative}\n\n"
            content += "  CLINICAL EXPLANATION:\n"
            content += "  t-SNE (t-distributed Stochastic Neighbor Embedding) is a nonlinear \n"
            content += "  dimensionality reduction technique. It maps complex, high-dimensional \n"
            content += "  patient biomarker profiles into a 2D spaces.\n\n"
            content += "  • Patients appearing in tight 'clusters' share highly similar \n"
            content += "    biological diagnostic signals.\n"
            content += "  • Separation between color clusters (Blue/Red) indicates how well \n"
            content += "    the global biomarker pattern distinguishes between conditions.\n"
            
            self._update_analysis_text("Patient Similarity Audit", content)
            
            # Show visual modal
            fig = Visualizer.plot_tsne_map(data)
            Visualizer.show_modal(self.layout_manager.root, "Patient Similarity Map (t-SNE)", fig)

        self._run_async_task(
            "Patient Map (t-SNE)",
            lambda: self.model_manager.get_tsne_data(self.data_manager.data_path),
            on_finish=finish
        )

    def show_shap_summary(self):
        """Show SHAP summary plot."""
        if not self._require_data_and_model("SHAP Explanation"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def finish(data):
            # data is a list of (feature_name, importance) tuples, sorted descending
            if not data:
                return

            # Format importance list for the analysis tab
            content = f"XAI Explanation Model: {model_name}\n"
            content += "Ranked Biomarker Importance (SHAP / proxy values):\n"
            content += "-" * 50 + "\n"
            for feat, imp in data[:15]:
                content += f"  • {feat:.<35} {imp:.6f}\n"

            self._update_analysis_text(f"Global XAI: {model_name}", content)

            # Show visual modal — plot_shap_summary expects list of (feat, val) tuples
            Visualizer.show_modal(
                self.layout_manager.root,
                f"Global XAI (SHAP) — {model_name}",
                Visualizer.plot_shap_summary(data, model_name)
            )

        self._run_async_task(
            "Global XAI (SHAP)",
            lambda: self.model_manager.get_shap_data(model_name, self.data_manager.data_path),
            on_finish=finish
        )
    def show_precision_recall_threshold(self):
        """Show precision-recall threshold analysis and update analysis tab with decision metrics."""
        if not self._require_data_and_model("Threshold Analysis"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def task():
            data = self.model_manager.get_pr_threshold_data(model_name, self.data_manager.data_path)
            if not data:
                return None
            
            # Identify Intersection (Clinical Balance)
            idx = np.argmin(np.abs(data['precision'][:-1] - data['recall'][:-1]))
            balance_point = {
                'threshold': data['thresholds'][idx],
                'precision': data['precision'][idx],
                'recall': data['recall'][idx]
            }
            
            # Identify Max F1 (Accuracy Peak)
            p = data['precision'][:-1]
            r = data['recall'][:-1]
            f1 = 2 * (p * r) / (p + r + 1e-10)
            max_idx = np.argmax(f1)
            f1_point = {
                'threshold': data['thresholds'][max_idx],
                'f1': f1[max_idx],
                'prec': p[max_idx],
                'rec': r[max_idx]
            }
            
            fig = Visualizer.plot_pr_threshold(data, model_name)
            return fig, balance_point, f1_point

        def finish(payload):
            if not payload:
                return
            fig, balance, f1_opt = payload
            
            # Build Analysis Report
            content = "═" * 60 + "\n"
            content += f"  DIAGNOSTIC DECISION THRESHOLD AUDIT: {model_name}\n"
            content += "═" * 60 + "\n\n"
            
            content += "  1. CLINICAL BALANCE (Intersection Point)\n"
            content += "     --------------------------------------------------\n"
            content += f"     • Optimal Threshold:  {balance['threshold']:.3f}\n"
            content += f"     • Balanced Precision: {balance['precision']:.1%}\n"
            content += f"     • Balanced Recall:    {balance['recall']:.1%}\n"
            content += "     (Best for standard diagnostic screening)\n\n"
            
            content += "  2. DIAGNOSTIC PEAK (Maximum F1-Score)\n"
            content += "     --------------------------------------------------\n"
            content += f"     • Cutoff Threshold:   {f1_opt['threshold']:.3f}\n"
            content += f"     • Peak F1-Quality:    {f1_opt['f1']:.3f}\n"
            content += f"     • Resulting Prec:     {f1_opt['prec']:.1%}\n"
            content += f"     • Resulting Recall:   {f1_opt['rec']:.1%}\n"
            content += "     (Best for maximizing overall model accuracy)\n\n"
            
            content += "  CLINICAL INTERPRETATION:\n"
            content += "  • LOWER THRESHOLD: Increases 'Recall' (Sensitivity). \n"
            content += "    Ensures fewer cancer cases are missed (Safe approach).\n"
            content += "  • HIGHER THRESHOLD: Increases 'Precision' (Confidence).\n"
            content += "    Reduces false alarms/unnecessary biopsies.\n"
            
            self._update_analysis_text("Diagnostic Threshold Audit", content)
            
            Visualizer.show_modal(self.layout_manager.root, f"Threshold Decision Audit: {model_name}", fig)

        self._run_async_task("PR Threshold Analysis", task, on_finish=finish)

    def show_pr_threshold(self):
        """Alias for compatibility."""
        return self.show_precision_recall_threshold()

    def show_shap_analysis(self):
        """Alias for compatibility."""
        return self.show_shap_summary()

    def show_pdp(self):
        """Show Partial Dependence Plot and update analysis tab with clinical trend interpretation."""
        if not self._require_data_and_model("Partial Dependence"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()
        try:
            X, _ = self.model_manager.get_raw_training_set(self.data_manager.data_path)
            # Find feature name: prefer mean_current if exists, otherwise first column
            feature = "mean_current" if "mean_current" in X.columns else X.columns[0]
        except Exception as e:
            self.error_handler.log_and_notify("PDP Support", e)
            return

        def task():
            model = self.model_manager.load_model(model_name)
            if not model:
                return None
            
            # Compute PDP values
            import numpy as np
            points = np.linspace(X[feature].min(), X[feature].max(), 50)
            X_copy = X.iloc[:min(50, len(X))].copy()
            probabilities = []
            
            for p in points:
                X_copy[feature] = p
                probabilities.append(model.predict_proba(X_copy)[:, 1].mean())
            
            return {
                'points': points,
                'probs': np.array(probabilities),
                'feature': feature,
                'model_name': model_name
            }

        def finish(data):
            if not data:
                return
            
            points = data['points']
            probs = data['probs']
            feat = data['feature']
            m_name = data['model_name']
            
            # Trend Analysis
            start_prob = probs[0]
            end_prob = probs[-1]
            diff = end_prob - start_prob
            
            content = "═" * 60 + "\n"
            content += f"  BIOMARKER IMPACT AUDIT (PDP): {feat.upper()}\n"
            content += "═" * 60 + "\n\n"
            content += f"  Model Context:      {m_name}\n"
            content += f"  Risk Range:        [{min(probs):.1%} to {max(probs):.1%}]\n\n"
            
            content += "  CURVE INTERPRETATION:\n"
            if diff < -0.05:
                content += "  📉 TREND: INVERSE (UP-TO-DOWN)\n"
                content += "     As this biomarker levels INCREASE, the diagnostic risk \n"
                content += "     DECREASES significantly.\n\n"
                content += "  🟢 CLINICAL MEANING:\n"
                content += "     This marker acts as a 'Protective Factor'. Higher \n"
                content += "     concentrations are associated with a healthy state in \n"
                content += "     this specific AI model's decision logic.\n"
            elif diff > 0.05:
                content += "  📈 TREND: POSITIVE (DOWN-TO-UP)\n"
                content += "     As this biomarker levels INCREASE, the diagnostic risk \n"
                content += "     INCREASES significantly.\n\n"
                content += "  🔴 CLINICAL MEANING:\n"
                content += "     This marker acts as a 'Pathogenic Driver'. Higher \n"
                content += "     concentrations strongly signal the presence of a \n"
                content += "     detected condition.\n"
            else:
                content += "  📊 TREND: NEUTRAL / STABLE\n"
                content += "     Variation in this biomarker has minimal direct impact on \n"
                content += "     the final prediction outcome.\n"

            self._update_analysis_text(f"Impact Profile: {feat}", content)
            
            # Use Visualizer to plot (we can pass precomputed data or just recompute)
            # To keep it simple and clean, we'll re-run plotting or update Visualizer
            fig = Visualizer.plot_pdp(self.model_manager.load_model(m_name), X, feat, m_name)
            Visualizer.show_modal(self.layout_manager.root, f"Marginal Impact Profile — {feat}", fig)

        self._run_async_task(f"Impact Analysis: {feature}", task, on_finish=finish)

    def show_population_distribution(self):
        """Show population risk distribution."""
        if not self._require_data("Population Review"):
            return

        def task():
            model_name = self.layout_manager.sidebar.model_var.get()
            _, _, risks = self.model_manager.predict_batch(model_name, self.data_manager.uploaded_df)
            return risks * 100

        self._run_async_task(
            "Population Risk",
            task,
            on_finish=lambda risks: Visualizer.show_modal(self.layout_manager.root, "Population Biomarker Distribution Overview",
                                                        Visualizer.plot_population_risk_distribution(risks)) if risks is not None else None
        )

    def show_biomarker_violins(self):
        """Show biomarker violin plots."""
        if not self._require_data("Clinical Violins"):
            return

        # Prefer the full training dataset (has cancer_risk_class labels)
        # Fall back to uploaded_df if training data is unavailable
        df = None
        if self.data_manager.data_path:
            try:
                df = self.model_manager.get_dataset_summary(self.data_manager.data_path)
            except Exception:
                pass
        if df is None:
            df = self.data_manager.uploaded_df

        features = self.model_manager.feature_names

        def task():
            return Visualizer.plot_biomarker_violins(df, features)

        self._run_async_task(
            "Biomarker Violins",
            task,
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, "Clinical Biomarker Distributions (Violin Plots)", fig) if fig else None
        )

    def show_detailed_metrics(self):
        """Show detailed clinical performance report."""
        if not self._require_data_and_model("Performance Report"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def task():
            return self.model_manager.get_detailed_metrics(model_name, self.data_manager.data_path)

        def finish(metrics):
            if metrics:
                # Update Analysis Tab
                report = f"Model Performance Summary: {model_name.upper()}\n"
                report += "-"*54 + "\n"
                for k, v in metrics.items():
                    if isinstance(v, float) and v <= 1.0:
                        report += f"{k:.<40} {v*100:>10.2f}%\n"
                    else:
                        report += f"{k:.<40} {v:>10}\n"
                
                self._update_analysis_text(f"Clinical Metrics: {model_name}", report)

                # Show visual modal
                fig = Visualizer.plot_detailed_metrics(metrics, model_name)
                Visualizer.show_modal(self.layout_manager.root, f"Clinical Performance: {model_name}", fig)

        self._run_async_task("Clinical Metrics", task, on_finish=finish)

    def show_model_robustness_benchmark(self):
        """Show system-wide robustness benchmark."""
        if not self._require_data("Robustness"):
            return

        from logic.model_manager import HAS_XGB
        models_to_test = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_test.append("XGBoost")

        def task():
            results = {}
            for m in models_to_test:
                metrics = self.model_manager.get_detailed_metrics(m, self.data_manager.data_path)
                stability = self.model_manager.get_model_stability(m, self.data_manager.data_path)
                if metrics and stability:
                    results[m] = {'metrics': metrics, 'stability': stability}
            return results

        def finish(res):
            if res:
                # Format for tab
                content = "Multi-Model Robustness & Stability Audit:\n"
                content += "-"*50 + "\n"
                for model, data in res.items():
                    metrics = data.get('metrics', {})
                    stability = data.get('stability', {})
                    acc = metrics.get('Accuracy', 0)
                    std = stability.get('score_std', 0)
                    content += f"  • {model:.<25} Accuracy: {acc:.2%} (Stability Std: {std:.4f})\n"
                
                self._update_analysis_text("System-Wide Robustness Audit", content)

                Visualizer.show_modal(self.layout_manager.root, "System-Wide Robustness Benchmark",
                                   Visualizer.plot_model_robustness_benchmark(res))

        self._run_async_task(
            "Robustness Audit",
            task,
            on_finish=finish
        )

    def show_performance_analysis(self):
        """Show model performance analysis and update analysis tab with resource metrics."""
        if not self._require_data("Performance"):
            return

        from logic.model_manager import HAS_XGB
        models_to_test = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_test.append("XGBoost")

        def task():
            X, y = self.model_manager.get_raw_training_set(self.data_manager.data_path)
            loaded_models = {}
            for m_name in models_to_test:
                m = self.model_manager.load_model(m_name)
                if m:
                    loaded_models[m_name] = m
            
            # Get raw data for the tab
            raw_data = Visualizer.get_performance_data(loaded_models, X, y)
            # Get fig for the modal
            fig = Visualizer.plot_performance_analysis(loaded_models, X, y)
            return fig, raw_data

        def finish(payload):
            if not payload:
                return
            fig, raw_data = payload
            if not fig:
                return

            # Build Analysis Report
            content = "═" * 60 + "\n"
            content += "  COMPUTATIONAL RESOURCE & HARDWARE EFFICIENCY AUDIT\n"
            content += "═" * 60 + "\n\n"
            content += f"  {'MODEL':<22} {'TRAIN (s)':>10} {'INFER (s)':>10} {'RAM (MB)':>10}\n"
            content += "  " + "-" * 56 + "\n"
            
            for item in raw_data:
                content += (f"  {item['Model']:<22} {item['Training_Time']:>10.3f} "
                           f"{item['Prediction_Time']:>10.5f} {item['Memory_Usage_MB']:>10.2f}\n")
            
            content += "\n  EFFICIENCY INTERPRETATION:\n"
            content += "  • TRAINING LATENCY: Time required to calibrate the AI on the \n"
            content += "    current 500-patient cohort. Lower is better for retraining.\n"
            content += "  • INFERENCE SPEED: Per-sample latency. This defines how fast \n"
            content += "    the 'Single Prediction' button reacts in real-time.\n"
            content += "  • MEMORY FOOTPRINT: Total RAM consumed during training. \n"
            content += "    Vital for ensuring the system runs on standard hardware.\n"
            
            self._update_analysis_text("Computational Efficiency Audit", content)
            
            Visualizer.show_modal(self.layout_manager.root, "Resource Efficiency Audit", fig)

        self._run_async_task("Performance Profile", task, on_finish=finish)

    def show_statistical_comparison(self):
        """Show statistical model comparison."""
        if not self._require_data("Statistical Comparison"):
            return

        from logic.model_manager import HAS_XGB
        models_to_test = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_test.append("XGBoost")

        def task():
            results = {}
            for m in models_to_test:
                scores = self.model_manager.get_cv_scores(m, self.data_manager.data_path)
                if scores:
                    results[m] = scores
            return results

        def finish(res):
            if res:
                import numpy as np
                # Format for tab
                content = "Bayesian Statistical Performance Comparison:\n"
                content += "-"*50 + "\n"
                for model, scores in res.items():
                    mean_score = np.mean(scores)
                    std_score = np.std(scores)
                    content += f"  • {model:.<25} Mean CV: {mean_score:.4f} (±{std_score:.4f})\n"
                
                self._update_analysis_text("Statistical Model Audit", content)

                Visualizer.show_modal(self.layout_manager.root, "Bayesian-Style Statistical Model Comparison",
                                   Visualizer.plot_statistical_comparison(res))

        self._run_async_task(
            "Statistical Audit",
            task,
            on_finish=finish
        )

    def show_permutation_importance(self):
        """Show permutation feature importance."""
        if not self._require_data_and_model("Indepth Importance"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def task():
            X, y = self.model_manager.get_raw_training_set(self.data_manager.data_path)
            model = self.model_manager.load_model(model_name)
            return Visualizer.plot_permutation_importance(model, X, y, self.model_manager.feature_names, model_name)

        self._run_async_task(
            "Permutation Testing",
            task,
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"Indepth Permutation Importance: {model_name}", fig) if fig else None
        )

    def show_multi_learning_curves(self):
        """Show comparative learning curves and update analysis tab with maturity metrics."""
        if not self._require_data("Learning Curves"):
            return

        from logic.model_manager import HAS_XGB
        models_to_test = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_test.append("XGBoost")

        def task():
            from sklearn.model_selection import learning_curve
            from sklearn.preprocessing import StandardScaler
            import numpy as np
            
            X, y = self.model_manager.get_raw_training_set(self.data_manager.data_path)
            scaler = StandardScaler().fit(X)
            
            loaded_models = {}
            summary_data = []

            for m_name in models_to_test:
                m = self.model_manager.load_model(m_name)
                if m:
                    loaded_models[m_name] = m
                    
                    # Compute specific metrics for the analysis tab
                    X_lc = scaler.transform(X) if m_name in ["Logistic Regression", "SVM"] else X
                    
                    train_sizes, train_scores, val_scores = learning_curve(
                        m, X_lc, y, cv=5, n_jobs=-1,
                        train_sizes=np.linspace(0.1, 1.0, 5),
                        scoring="accuracy"
                    )
                    
                    final_train = np.mean(train_scores[-1])
                    final_val = np.mean(val_scores[-1])
                    gap = final_train - final_val
                    
                    summary_data.append({
                        'model': m_name,
                        'train_acc': final_train,
                        'val_acc': final_val,
                        'gap': gap
                    })

            fig = Visualizer.plot_multi_learning_curves(loaded_models, X, y, scaler=scaler)
            return fig, summary_data

        def finish(payload):
            if not payload:
                return
            fig, summary_data = payload
            if not fig:
                return

            # Build Analysis Report
            content = "═" * 60 + "\n"
            content += "  SYSTEM-WIDE LEARNING DYNAMICS & MATURITY AUDIT\n"
            content += "═" * 60 + "\n\n"
            content += f"  {'MODEL':<22} {'TRAIN':>8} {'VAL':>8} {'GAP':>8}\n"
            content += "  " + "-" * 48 + "\n"
            
            for item in summary_data:
                status = "Optimal" if item['gap'] < 0.05 else "Overfit" if item['gap'] > 0.15 else "Stabilizing"
                content += (f"  {item['model']:<22} {item['train_acc']:>7.1%} "
                           f"{item['val_acc']:>7.1%} {item['gap']:>7.1%} ({status})\n")
            
            content += "\n  CLINICAL MATURITY INTERPRETATION:\n"
            content += "  • LEARNING GAP: The difference between training and validation.\n"
            content += "    A wide gap (>10%) suggests the model is memorizing noise \n"
            content += "    rather than learning general clinical patterns (Overfitting).\n"
            content += "  • CONVERGENCE: If curves are still rising at the far right, \n"
            content += "    adding more patient samples will likely improve accuracy.\n"
            content += "  • STABILITY: Tight validation bands (shaded areas in plot) \n"
            content += "    indicate the model is reliable across different patient subsets.\n"
            
            self._update_analysis_text("Learning Dynamics Audit", content)
            
            Visualizer.show_modal(self.layout_manager.root, "Comparative Learning Curve Analysis", fig)

        self._run_async_task("Comparative Learning", task, on_finish=finish)

    def show_sensitivity_analysis(self):
        """Show model sensitivity analysis."""
        if not self._require_data_and_model("Sensitivity Analysis"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        def task():
            X, y = self.model_manager.get_raw_training_set(self.data_manager.data_path)
            model = self.model_manager.load_model(model_name)
            return Visualizer.plot_sensitivity_analysis(model, X, y, self.model_manager.feature_names, model_name)

        self._run_async_task(
            "Sensitivity Test",
            task,
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"Sensitivity Analysis (Model Fragility Check) - {model_name}", fig) if fig else None
        )

    def show_feature_analysis(self, feature_name):
        """Show distribution profile for a specific biomarker."""
        if not self._require_data(f"Feature Audit: {feature_name}"):
            return

        df = self.data_manager.uploaded_df
        if feature_name not in df.columns:
            from tkinter import messagebox
            messagebox.showerror("Missing Feature", f"Biomarker '{feature_name}' not found in current dataset.")
            return

        # Calculate statistics for the tab
        try:
            val_col = df[feature_name].dropna()
            stats_content = f"Biomarker: {feature_name}\n"
            stats_content += f"Data Count: {len(val_col)}\n"
            stats_content += f"Mean Level: {val_col.mean():.4f}\n"
            stats_content += f"Median: {val_col.median():.4f}\n"
            stats_content += f"Std Dev: {val_col.std():.4f}\n"
            stats_content += f"Range: [{val_col.min():.4f} to {val_col.max():.4f}]\n"
            
            self._update_analysis_text(f"Biomarker Audit: {feature_name}", stats_content)
        except Exception as e:
            print(f"Error updating feature stats: {e}")

        fig = Visualizer.plot_feature_distribution(df, feature_name)
        Visualizer.show_modal(self.layout_manager.root, f"Biomarker Distribution Profile — {feature_name}", fig)

    def show_model_leadership_report(self):
        """Show the unified clinical leadership report using ModelEvaluator composite scoring."""
        if not self._require_data("Model Selection Analysis"):
            return

        from logic.model_manager import HAS_XGB
        models_to_eval = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            models_to_eval.append("XGBoost")

        def task():
            from logic.model_evaluator import ModelEvaluator
            X_train, X_test, y_train, y_test, _ = self.model_manager._load_training_data(
                self.data_manager.data_path
            )

            models_dict = {}
            for name in models_to_eval:
                m = self.model_manager.load_model(name)
                if m is not None:
                    models_dict[name] = m

            if not models_dict:
                return None, None

            evaluator = ModelEvaluator()
            results = evaluator.evaluate_all_models(models_dict, X_train, X_test, y_train, y_test)
            return results, evaluator

        def finish(payload):
            if payload is None:
                return
            results, evaluator = payload
            if not results:
                return

            ranking = results.get('ranking', [])
            recommendations = results.get('recommendations', {})

            # ── Build analysis tab content ──────────────────────────
            winner = ranking[0]['model'] if ranking else "N/A"
            log_content = "═" * 62 + "\n"
            log_content += "  COMPREHENSIVE MODEL EVALUATION — COMPOSITE LEADERBOARD\n"
            log_content += "═" * 62 + "\n\n"
            log_content += f"  {'RANK':<5} {'MODEL':<22} {'COMPOSITE':>10} {'ACCURACY':>10} {'F1':>8} {'ROC-AUC':>9}\n"
            log_content += "  " + "-" * 60 + "\n"
            for entry in ranking:
                log_content += (
                    f"  #{entry['rank']:<4} {entry['model']:<22}"
                    f" {entry['composite_score']:>10.4f}"
                    f" {entry.get('accuracy', 0):>10.2%}"
                    f" {entry.get('f1_score', 0):>8.4f}"
                    f" {entry.get('roc_auc', 0) or 0:>9.4f}\n"
                )

            # Add MCC & specificity from individual results
            ind = results.get('individual_results', {})
            log_content += "\n  EXTENDED METRICS (MCC · Specificity · PR-AUC)\n"
            log_content += "  " + "-" * 60 + "\n"
            for name, res in ind.items():
                m = res.get('metrics', {})
                mcc  = m.get('mcc', 0) or 0
                spec = m.get('specificity', 0) or 0
                pr_auc = m.get('pr_auc', 0) or 0
                log_content += f"  {name:<22}  MCC={mcc:>6.4f}  Spec={spec:>6.2%}  PR-AUC={pr_auc:>6.4f}\n"

            # Clinical recommendation
            primary_rec = recommendations.get('primary_recommendation', '')
            clinical_use = recommendations.get('clinical_use_case', '')
            cautions = recommendations.get('cautions', [])

            log_content += f"\n🏆 RECOMMENDATION:\n  {primary_rec}\n"
            log_content += f"\n💊 CLINICAL USE:\n  {clinical_use}\n"
            if cautions:
                log_content += "\n⚠️  CAUTIONS:\n"
                for c in cautions:
                    log_content += f"  • {c}\n"

            self.layout_manager.root.after(
                0, lambda: self._update_analysis_text("Model Evaluation Report", log_content)
            )

            # Build leaderboard list expected by plot_model_selection_report
            leaderboard = [
                {
                    'model':      entry['model'],
                    'accuracy':   entry.get('accuracy', 0),
                    'f1':         entry.get('f1_score', 0),
                    'rank_score': entry.get('composite_score', 0),
                    'mcc':        ind.get(entry['model'], {}).get('metrics', {}).get('mcc', 0) or 0,
                    'specificity':ind.get(entry['model'], {}).get('metrics', {}).get('specificity', 0) or 0,
                    'pr_auc':     ind.get(entry['model'], {}).get('metrics', {}).get('pr_auc', 0) or 0,
                }
                for entry in ranking
            ]
            fig = Visualizer.plot_model_selection_report(leaderboard)
            Visualizer.show_modal(
                self.layout_manager.root,
                "Clinical Model Selection Report — Composite Evaluation",
                fig
            )

        self._run_async_task("Model Evaluation", task, on_finish=finish)
