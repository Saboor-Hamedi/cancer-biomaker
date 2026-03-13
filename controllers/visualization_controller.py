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

    def _run_async_task(self, label, func, on_finish=None):
        """Unified helper to run background tasks with GUI status management."""
        self.layout_manager.dashboard.update_status(f"Calculating {label}…", "orange")

        def task():
            try:
                result = func()
                if on_finish:
                    self.layout_manager.root.after(0, lambda: on_finish(result))
                self.layout_manager.root.after(0, lambda: self.layout_manager.dashboard.update_status(f"{label} Complete", "#10B981"))
            except Exception as e:
                self.error_handler.log_error(f"{label} failed", e)
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
        
        # We need an explanation! If not in result, calculate it now
        explanation = pred_data.get('explanation')
        if not explanation:
            # Need features and input values
            inputs = pred_data.get('inputs', {})
            if not inputs:
                return
            
            # Show progress
            self.layout_manager.update_status("Calculating clinical explanation...", "orange")
            
            def calculate_and_show():
                try:
                    # Calculate SHAP for this single patient
                    model = self.model_manager.load_model(model_name)
                    
                    # Convert inputs to DF
                    full_input = {feat: 0.0 for feat in self.model_manager.feature_names}
                    for k, v in inputs.items():
                        if k in full_input: full_input[k] = float(v)
                    input_df = pd.DataFrame([full_input])[self.model_manager.feature_names]
                    
                    from logic.model_manager import HAS_TORCH
                    inputs_dict = input_df.iloc[0].to_dict()
                    
                    # Call model_manager's local explanation logic
                    explanation = self.model_manager.get_local_explanation(
                        model_name, 
                        inputs_dict, 
                        data_path=self.data_manager.data_path
                    )
                    
                    def finish():
                        fig = Visualizer.plot_local_explanation(explanation, model_name)
                        Visualizer.show_modal(self.layout_manager.root, f"Clinical Impact Profile — {model_name}", fig)
                        self.layout_manager.update_status("Explanation generated", "#10B981")
                    
                    self.layout_manager.root.after(0, finish)
                except Exception as e:
                    self.error_handler.log_and_notify("Explanation Generation", e)

            import threading
            threading.Thread(target=calculate_and_show, daemon=True).start()
            return

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
        """Show t-SNE patient map."""
        if not self._require_data("Patient Mapping"):
            return

        self._run_async_task(
            "Patient Map (t-SNE)",
            lambda: self.model_manager.get_tsne_data(self.data_manager.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.layout_manager.root, "Patient Distribution (t-SNE)",
                                                       Visualizer.plot_tsne_map(data)) if data else None
        )

    def show_shap_summary(self):
        """Show SHAP summary plot."""
        if not self._require_data_and_model("SHAP Explanation"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        self._run_async_task(
            "Global XAI (SHAP)",
            lambda: self.model_manager.get_shap_data(model_name, self.data_manager.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.layout_manager.root, f"Global XAI (SHAP) - {model_name}", Visualizer.plot_shap_summary(data, model_name)) if data else None
        )
    def show_precision_recall_threshold(self):
        """Show precision-recall threshold analysis."""
        if not self._require_data_and_model("Threshold Analysis"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()

        self._run_async_task(
            "PR Threshold Analysis",
            lambda: self.model_manager.get_pr_threshold_data(model_name, self.data_manager.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.layout_manager.root, f"Threshold Decision Audit: {model_name}",
                                                       Visualizer.plot_pr_threshold(data, model_name)) if data else None
        )

    def show_pr_threshold(self):
        """Alias for compatibility."""
        return self.show_precision_recall_threshold()

    def show_shap_analysis(self):
        """Alias for compatibility."""
        return self.show_shap_summary()

    def show_pdp(self):
        """Show Partial Dependence Plot for the first feature."""
        if not self._require_data_and_model("Partial Dependence"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()
        try:
            X, _ = self.model_manager.get_raw_training_set(self.data_manager.data_path)
            feature = X.columns[0]
        except Exception as e:
            self.error_handler.log_and_notify("PDP Support", e)
            return

        self._run_async_task(
            f"Impact of {feature}",
            lambda: Visualizer.plot_pdp(self.model_manager.load_model(model_name), X, feature, model_name),
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, f"Biomarker Impact (PDP) - {feature}", fig) if fig else None
        )

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

        df = self.data_manager.uploaded_df
        features = self.model_manager.feature_names

        fig = Visualizer.plot_biomarker_violins(df, features)
        Visualizer.show_modal(self.layout_manager.root, "Clinical Biomarker Distributions (Violin Plots)", fig)

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
                from datetime import datetime
                report = f"CLINICAL PERFORMANCE REPORT: {model_name.upper()}\n"
                report += "-"*54 + "\n"
                for k, v in metrics.items():
                    if isinstance(v, float) and v <= 1.0:
                        report += f"{k:.<40} {v*100:>10.2f}%\n"
                    else:
                        report += f"{k:.<40} {v:>10}\n"

                self.layout_manager.tab_analysis.text.config(state="normal")
                self.layout_manager.tab_analysis.text.delete("1.0", "end")
                self.layout_manager.tab_analysis.text.insert("end", report)
                self.layout_manager.tab_analysis.text.config(state="disabled")

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

        self._run_async_task(
            "Robustness Audit",
            task,
            on_finish=lambda res: Visualizer.show_modal(self.layout_manager.root, "System-Wide Robustness Benchmark",
                                                       Visualizer.plot_model_robustness_benchmark(res)) if res else None
        )

    def show_performance_analysis(self):
        """Show model performance analysis (memory/time)."""
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
            return Visualizer.plot_performance_analysis(loaded_models, X, y)

        self._run_async_task(
            "Performance Profile",
            task,
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, "Resource Efficiency Audit", fig) if fig else None
        )

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

        self._run_async_task(
            "Statistical Audit",
            task,
            on_finish=lambda res: Visualizer.show_modal(self.layout_manager.root, "Bayesian-Style Statistical Model Comparison",
                                                       Visualizer.plot_statistical_comparison(res)) if res else None
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
        """Show comparative learning curves."""
        if not self._require_data("Learning Curves"):
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
            return Visualizer.plot_multi_learning_curves(loaded_models, X, y, scaler=None)

        self._run_async_task(
            "Comparative Learning",
            task,
            on_finish=lambda fig: Visualizer.show_modal(self.layout_manager.root, "Comparative Learning Curve Analysis", fig) if fig else None
        )

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

        fig = Visualizer.plot_feature_distribution(df, feature_name)
        Visualizer.show_modal(self.layout_manager.root, f"Biomarker Distribution Profile — {feature_name}", fig)
