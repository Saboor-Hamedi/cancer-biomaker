import logging
import os
import sys
import threading
import tkinter as tk
import warnings
from datetime import datetime
from tkinter import filedialog, messagebox

import pandas as pd

# Local imports
from components.dashboard import Dashboard
from components.sidebar import Sidebar
from components.tabs import AnalysisTab, DataTab, InputTab
from logic.data_manager import DataManager
from logic.model_manager import ModelManager
from styles import apply_styles
from views.dialogs import PreprocessingDialog
from views.visualizations import Visualizer

warnings.filterwarnings('ignore', message='.*use_label_encoder.*')

# ── Logging: writes to app.log in the script folder ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'app.log'), encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


class CancerDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cancer Detection XAI Dashboard v3.0")
        self.root.geometry("1400x900")

        # Initialize Managers
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_manager = ModelManager(script_dir)
        self.data_manager = DataManager()
        self.current_prediction_data = None

        # Apply Styles
        apply_styles()

        # Layout Setup
        self._setup_layout()

        # Menu Bar
        self._build_menubar()

        # Auto-check and train models if missing
        self._check_models_on_startup()

        # Handle proper closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Clean shutdown of the application"""
        try:
            # Close all modal windows first
            from views.visualizations import Visualizer
            Visualizer.close_all_modals()


            self.root.destroy()
        except:
            pass
        os._exit(0) # Force kill all threads and processes

    def _check_models_on_startup(self):
        self.data_path = None # No dataset by default

        def check_task():
            # Only check if models already exist in views/modal, don't auto-train
            success, msg = self.model_manager.check_and_train_models("", self.dashboard.update_status, force=False)
            if success:
                self.root.after(0, lambda: self.tab_input.refresh_features(self.model_manager.feature_names))
                self.root.after(0, lambda: self.dashboard.update_status("System Ready - Models Verified", "#10B981"))
            else:
                self.root.after(0, lambda: self.dashboard.update_status("Ready - Upload dataset to enable analytics", "#3B82F6"))

        threading.Thread(target=check_task, daemon=True).start()

    def _build_menubar(self):
        """Native OS-style menu bar for data management and system utilities"""
        menubar = tk.Menu(self.root)

        # ── File ──────────────────────────────────────────
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Upload Dataset...",      command=self.handle_upload,  accelerator="Ctrl+O")
        file_menu.add_command(label="Load Sample Batch",       command=self.handle_sample)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results to Excel", command=self.handle_export,  accelerator="Ctrl+S")
        file_menu.add_command(label="Generate Report...",      command=self.handle_report)
        file_menu.add_separator()
        file_menu.add_command(label="Clear All Data",           command=self.handle_clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",                     command=self.on_close,       accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)

        # Keyboard shortcuts
        self.root.bind_all("<Control-o>", lambda e: self.handle_upload())
        self.root.bind_all("<Control-s>", lambda e: self.handle_export())

        # ── Data ──────────────────────────────────────────
        data_menu = tk.Menu(menubar, tearoff=0)
        data_menu.add_command(label="Re-Train All Models",    command=self.handle_train_models)
        data_menu.add_command(label="Data Optimization...",   command=self.show_preprocessing)
        menubar.add_cascade(label="Data", menu=data_menu)

        # ── Analytics ─────────────────────────────────────
        analytics_menu = tk.Menu(menubar, tearoff=0)
        analytics_menu.add_command(label="Local Patient Diagnosis",    command=self.show_local_explanation)
        analytics_menu.add_command(label="Patient Radar Profile",       command=self.show_patient_radar)
        analytics_menu.add_command(label="Detailed Clinical Metrics",  command=self.show_detailed_metrics)
        analytics_menu.add_command(label="Cross-Model Comparison",     command=self.show_model_comparison)
        analytics_menu.add_command(label="Accuracy Comparison",        command=self.show_accuracy_comparison)
        analytics_menu.add_separator()
        analytics_menu.add_command(label="Correlation Heatmap",        command=self.show_correlation_heatmap)
        analytics_menu.add_command(label="Reliability Chart",          command=self.show_calibration_curve)
        analytics_menu.add_command(label="Learning Analysis",          command=self.show_learning_curve)
        analytics_menu.add_command(label="Stability Analysis",         command=self.show_stability)
        analytics_menu.add_command(label="Performance Analysis",       command=self.show_performance_analysis)
        analytics_menu.add_command(label="Multi-Model Learning Curves", command=self.show_multi_learning_curves)
        analytics_menu.add_separator()
        analytics_menu.add_command(label="Patient Map (t-SNE)",        command=self.show_tsne_map)
        analytics_menu.add_command(label="Biomarker Impact (PDP)",     command=self.show_pdp)
        menubar.add_cascade(label="Analytics", menu=analytics_menu)

        # ── Statistics ────────────────────────────────────
        stats_menu = tk.Menu(menubar, tearoff=0)
        stats_menu.add_command(label="Statistical Model Comparison", command=self.show_statistical_comparison)
        stats_menu.add_command(label="Permutation Feature Importance", command=self.show_permutation_importance)
        stats_menu.add_command(label="SHAP Feature Analysis",       command=self.show_shap_analysis)
        stats_menu.add_command(label="Model Robustness Analysis",   command=self.show_robustness_analysis)
        stats_menu.add_command(label="Sensitivity Analysis",        command=self.show_sensitivity_analysis)
        menubar.add_cascade(label="Statistics", menu=stats_menu)

        # ── Features ─────────────────────────────────────
        features_menu = tk.Menu(menubar, tearoff=0)
        features = [
            'PSA_peak_height',
            'min_slope',
            'PSA_concentration_pg_per_ml',
            'max_slope',
            'current_at_-0.46V',
            'min_current',
            'PSA_actual_peak_current',
            'mean_current',
            'area_under_curve',
            'peak_height_ratio_PSA_CA125'
        ]
        for feature in features:
            features_menu.add_command(label=feature, command=lambda f=feature: self.show_feature_analysis(f))
        menubar.add_cascade(label="Features", menu=features_menu)

        # ── Help ──────────────────────────────────────────
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help & Documentation",   command=self.show_help,      accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.bind_all("<F1>", lambda e: self.show_help())

        self.root.config(menu=menubar)

    def _setup_layout(self):
        # Create Sidebar (Right side)
        from logic.model_manager import HAS_XGB
        model_list = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: model_list.append("XGBoost")

        callbacks = {
            'upload': self.handle_upload,
            'sample': self.handle_sample,
            'train_models': self.handle_train_models,
            'predict_single': self.handle_predict_single,
            'predict_silent': lambda: self.handle_predict_single(silent=True),
            'predict_file': self.handle_predict_batch,
            'export': self.handle_export,
            'viz_local': self.show_local_explanation,
            'viz_radar': self.show_patient_radar,
            'viz_feat': self.show_feature_importance,
            'viz_shap': self.show_shap_summary,
            'viz_roc': self.show_roc_curve,
            'viz_cm': self.show_confusion_matrix,
            'viz_pr': self.show_precision_recall,
            'viz_pr_thresh': self.show_pr_threshold,
            'viz_comp': self.show_model_comparison,
            'viz_heat': self.show_correlation_heatmap,
            'viz_calib': self.show_calibration_curve,
            'viz_learn': self.show_learning_curve,
            'viz_stability': self.show_stability,
            'viz_tsne': self.show_tsne_map,
            'viz_pdp': self.show_pdp,
            'viz_metrics': self.show_detailed_metrics,
            'viz_dist': self.show_population_distribution,
            'viz_violin': self.show_biomarker_violins,
            'viz_robust': self.show_robustness_benchmark,
            'preprocess': self.show_preprocessing,
            'report': self.handle_report,
            'help': self.show_help,
            'clear': self.handle_clear_all,
            'models': model_list
        }

        self.sidebar = Sidebar(self.root, callbacks)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create Dashboard (Main area left)
        self.dashboard = Dashboard(self.root)
        self.dashboard.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate Tabs
        self.tab_input = InputTab(self.dashboard.input_tab, features=self.model_manager.feature_names)
        self.tab_input.pack(fill=tk.BOTH, expand=True)

        self.tab_data = DataTab(self.dashboard.data_tab)
        self.tab_data.pack(fill=tk.BOTH, expand=True)

        self.tab_analysis = AnalysisTab(self.dashboard.analysis_tab)
        self.tab_analysis.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.tab_input.tree.bind("<Double-1>", self.edit_input_value)

    # --- Handlers ---
    def handle_upload(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.dashboard.update_status("Loading file…", "orange")
            def task():
                df, error = self.data_manager.load_excel(file_path)
                if error:
                    log.error("Upload failed: %s", error)
                    self.root.after(0, lambda: messagebox.showerror("Load Error", error))
                    self.root.after(0, lambda: self.dashboard.update_status("Load Failed", "red"))
                else:
                    self.data_path = file_path
                    self.model_manager.reset_analytics()
                    # Feature mismatch check — item #4
                    ok, msg = self.model_manager.check_feature_compatibility(df.columns)
                    if not ok:
                        self.root.after(0, lambda m=msg: messagebox.showwarning("Feature Mismatch", m))

                    # Instead of rendering all rows which causes lag, auto-load a sample
                    self.root.after(0, self.handle_sample)
            threading.Thread(target=task, daemon=True).start()

    def handle_train_models(self):
        """User triggered manual training of all models"""
        if self.data_path is None:
            return messagebox.showwarning("No Data", "Please upload a dataset or load a sample first.")

        if not messagebox.askyesno("Confirm Training", "This will retrain all models (RF, LR, SVM, XGBoost) using the current dataset. Proceed?"):
            return

        def task():
            success, msg = self.model_manager.check_and_train_models(self.data_path, self.dashboard.update_status, force=True)
            if success:
                self.root.after(0, lambda: self.tab_input.refresh_features(self.model_manager.feature_names))
                self.root.after(0, lambda: messagebox.showinfo("Training Success", "All models trained and saved successfully."))
                self.root.after(0, lambda: self.dashboard.update_status("Models Ready", "#10B981"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Training Error", msg))
                self.root.after(0, lambda: self.dashboard.update_status("Training Failed", "#EF4444"))

        threading.Thread(target=task, daemon=True).start()

    def handle_sample(self):
        """Load a subset of the currently active dataset"""
        if self.data_path is None:
            return messagebox.showwarning("No Data", "Please upload a dataset file first.")

        sample_path = self.data_path

        if not os.path.exists(sample_path):
            messagebox.showerror("File Error", f"File path has become invalid:\n{sample_path}")
            return

        self.dashboard.update_status("Loading samples...", "orange")
        def task():
            df, error = self.data_manager.load_excel(sample_path, sheet_name='Training_Data')
            if error:
                self.root.after(0, lambda: messagebox.showerror("Load Error", f"Excel loading failed:\n{error}"))
                self.root.after(0, lambda: self.dashboard.update_status("Sample Load Failed", "red"))
            else:
                # Get size from sidebar
                size = self.sidebar.sample_qty.get()
                total_rows = len(df)
                size = min(max(1, size), total_rows)

                # Randomly pick rows
                sampled_df = df.sample(n=size).reset_index(drop=True)
                self.data_manager.uploaded_df = sampled_df
                self._total_dataset_rows = total_rows # Store the large number
                self.root.after(0, self.update_ui_after_load)
                self.root.after(0, lambda: self.dashboard.update_status(f"Imported {size} random samples.", "blue"))

        threading.Thread(target=task, daemon=True).start()

    def update_ui_after_load(self):
        df = self.data_manager.uploaded_df
        if df is None: return

        issues = self.data_manager.validate_data(df)
        if issues:
            messagebox.showwarning("Validation", "\n".join(issues))

        # 1. NEW: Dynamically refresh the input feature list to match the dataset
        # We exclude metadata/target columns
        ignored = ['sample_id', 'cancer_risk_class']
        actual_features = [col for col in df.columns if col not in ignored]

        # Only refresh if the features have changed or list is the fallback one
        if len(self.tab_input.tree.get_children()) <= 10 or set(actual_features) != set(self.tab_input.features):
            self.tab_input.refresh_features(actual_features)
            # Update ModelManager's feature list as well
            self.model_manager.feature_names = actual_features

        # Update New Header Labels
        # If we just loaded a sample, we might not know the absolute total rows of the file
        # But we can try to guess or use the data manager's state
        total_rows = getattr(self, '_total_dataset_rows', len(df))
        total_cols = len(df.columns)
        current_samples = len(df)
        self.dashboard.update_data_info(rows=total_rows, cols=total_cols, samples=current_samples)

        self.dashboard.update_status(f"Imported {current_samples} samples", "#10B981")
        self._refresh_data_tree()
        self._sync_first_row_to_input()

        # Update Analysis Tab with DataFrame Summary
        summary = (
            "DATASET SUMMARY & DESCRIPTIVE STATISTICS\n"
            "------------------------------------------------------\n\n"
            f"Total Loaded Samples: {current_samples}\n"
            f"Total Features Evaluated: {total_cols}\n\n"
            "Features Summary (Mean, Std, Min, Max):\n"
        )
        try:
            # Transpose so features are rows, making it much more readable for many columns
            desc = df.describe().T
            formatted_desc = desc.to_string(float_format="{:.3f}".format, justify='right')
            summary += formatted_desc

            # Print to terminal/console as a structured table as well
            print("\n" + "="*80)
            print("DATASET DESCRIPTIVE STATISTICS OVERVIEW")
            print("="*80)
            print(formatted_desc)
            print("="*80 + "\n")
        except Exception as e:
            summary += f"Could not compute descriptive statistics: {e}"

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)
        self.tab_analysis.text.insert(tk.END, summary)
        self.tab_analysis.text.config(state=tk.DISABLED)

        # Switch to Data View tab
        try:
            self.dashboard.notebook.select(1)
        except:
            pass

    def _sync_first_row_to_input(self):
        """Take the first row of loaded data and put it into the Input Features tab"""
        df = self.data_manager.uploaded_df
        if df is None or len(df) == 0:
            return

        first_row = df.iloc[0]
        tree = self.tab_input.tree
        found_count = 0

        # Create a mapping for fuzzy column matching (to handle spaces/case)
        col_map = {str(c).lower().strip(): c for c in first_row.index}

        for item in tree.get_children():
            feature_name = str(tree.item(item, "values")[0])
            search_key = feature_name.lower().strip()

            if search_key in col_map:
                actual_col = col_map[search_key]
                val_raw = first_row[actual_col]
                try:
                    val = str(round(float(val_raw), 4))
                except:
                    val = str(val_raw)

                desc = tree.item(item, "values")[2]
                tree.item(item, values=(feature_name, val, desc))
                found_count += 1

        if found_count > 0:
            msg = f"SUCCESS: Synced {found_count} clinical biomarkers from data."
            self.dashboard.update_status(msg, "#10B981")

    def _refresh_data_tree(self):
        tree = self.tab_data.tree
        df = self.data_manager.uploaded_df

        # Clear existing rows
        tree.delete(*tree.get_children())

        if df is None or len(df.columns) == 0:
            # Reset to blank state
            tree["columns"] = ("status",)
            tree.heading("status", text="NO DATA LOADED")
            tree.column("status", width=400, anchor=tk.CENTER)
            return

        # Rebuild columns
        columns = list(df.columns)
        tree["columns"] = columns

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)

        # Add data
        for _, row in df.iterrows():
            vals = [str(x) for x in row.values]
            tree.insert("", tk.END, values=vals)

    def handle_predict_single(self, silent=False):
        model_name = self.sidebar.model_var.get()
        inputs = {}
        try:
            for item in self.tab_input.tree.get_children():
                v = self.tab_input.tree.item(item, "values")
                inputs[v[0]] = float(v[1])
        except ValueError:
            if not silent:
                return messagebox.showerror("Input Error", "Please ensure all biomarker values are valid numbers.")
            return

        try:
            pred, conf, risk = self.model_manager.predict_single(model_name, inputs)
            res = "POSITIVE" if pred == 1 else "NEGATIVE"

            # 1. Clinical Triage Logic
            if risk < 0.30: triage = "Surveillance"
            elif risk < 0.70: triage = "Monitor"
            else: triage = "URGENT ACTION"

            # 2. Ensemble Consensus Logic
            all_preds = []
            models_to_check = ["Random Forest", "Logistic Regression", "SVM"]
            from logic.model_manager import HAS_XGB
            if HAS_XGB: models_to_check.append("XGBoost")

            for m in models_to_check:
                if self.model_manager.load_model(m):
                    p, _, _ = self.model_manager.predict_single(m, inputs)
                    all_preds.append(p)

            if len(all_preds) >= 2:
                match_count = all_preds.count(pred)
                total = len(all_preds)
                if match_count == total: consensus = f"Strong ({total}/{total})"
                elif match_count >= total - 1: consensus = f"Moderate ({match_count}/{total})"
                else: consensus = "Mixed/Low"
            else:
                consensus = "Single Model"

            # Update Dashboard Metrics (Cards)
            self.dashboard.update_metrics(
                risk=risk*100,
                confidence=conf*100,
                insight=res,
                triage=triage,
                consensus=consensus
            )

            # --- Diagnostic Report for Analysis Tab ---
            from datetime import datetime
            report = (
                f"🔬 PATIENT DIAGNOSTIC REPORT: {res}\n"
                f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "======================================================\n\n"
                f"Active Predictor:   {model_name.upper()}\n"
                f"Result Insight:     {res}\n"
                f"Risk Probability:   {risk*100:.2f}%\n"
                f"Model Confidence:   {conf*100:.2f}%\n\n"
                "CLINICAL INTERPRETATION & TRIAGE SUMMARY:\n"
                "------------------------------------------------------\n"
                f"Triage Priority:    {triage.upper()}\n"
                f"AI Consensus Status: {consensus}\n\n"
                "GUIDANCE FOR PRIORITIZATION:\n"
            )

            if triage == "Surveillance":
                report += "- Biomarker signals are low/normal.\n- Routine monitoring (every 6-12 months) recommended.\n"
            elif triage == "Monitor":
                report += "- Borderline clinical indicators detected.\n- Secondary laboratory tests advised for verification.\n"
            else:
                report += "- CRITICAL: High biomarker signal patterns.\n- Immediate oncology consult and biopsy recommended.\n"

            report += "\n" + "="*54 + "\n"
            report += f"Note: Consensus analysis cross-validated against {len(all_preds)} models."

            self.tab_analysis.text.config(state=tk.NORMAL)
            self.tab_analysis.text.delete("1.0", tk.END)
            self.tab_analysis.text.insert(tk.END, report)
            self.tab_analysis.text.config(state=tk.DISABLED)

            # Switch to Analysis Tab so user sees the report (skip if silent)
            if not silent:
                try:
                    self.dashboard.notebook.select(2)
                except:
                    pass

            self.dashboard.update_status(f"Analysis Complete: {res} Status", "#EF4444" if pred == 1 else "#10B981")

            # Save for Professional Report generation and Local XAI
            explanation = self.model_manager.get_local_explanation(model_name, inputs, self.data_path)
            self.current_prediction_data = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'model': model_name,
                'result': res,
                'risk': risk * 100,
                'conf': conf * 100,
                'triage': triage,
                'consensus': consensus,
                'inputs': inputs,
                'explanation': explanation
            }
        except Exception as e:
            if not silent:
                return messagebox.showerror("Model Error", str(e))
            return

    def handle_predict_batch(self):
        if self.data_manager.uploaded_df is None:
            return messagebox.showwarning("Warning", "Load data first")

        model_name = self.sidebar.model_var.get()
        self.dashboard.update_status(f"Predicting with {model_name}...", "orange")

        def task():
            try:
                preds, confs, risks = self.model_manager.predict_batch(model_name, self.data_manager.uploaded_df)

                results = self.data_manager.uploaded_df.copy()
                results['Prediction'] = ["POSITIVE" if p == 1 else "NEGATIVE" for p in preds]
                results['Confidence'] = [f"{c:.1%}" for c in confs]
                results['RiskProb'] = risks
                self.data_manager.prediction_results = results

                def update_ui():
                    pos_count = sum(preds)
                    mean_risk = (sum(risks) / len(risks)) * 100
                    mean_conf = (sum(confs) / len(confs)) * 100

                    self.dashboard.update_metrics(
                        risk=mean_risk,
                        confidence=mean_conf,
                        insight=f"{pos_count} Cases",
                        triage="Multi-Patient",
                        consensus="Population"
                    )

                    # --- Batch Analysis Report for Analysis Tab ---
                    from datetime import datetime
                    report = (
                        f"📊 BATCH ANALYSIS SUMMARY: {model_name.upper()}\n"
                        f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        "======================================================\n\n"
                        f"Samples Processed:   {len(preds)}\n"
                        f"Positive Detections: {pos_count}\n"
                        f"Negative Detections: {len(preds) - pos_count}\n"
                        f"Avg Clinical Risk:   {mean_risk:.2f}%\n"
                        f"Avg Model Confidence: {mean_conf:.2f}%\n\n"
                        "POPULATION RISK EXPOSURE:\n"
                        "------------------------------------------------------\n"
                        f"Min Risk Score:      {min(risks)*100:.2f}%\n"
                        f"Max Risk Score:      {max(risks)*100:.2f}%\n"
                        f"Spread (Max-Min):    {(max(risks)-min(risks))*100:.2f}%\n\n"
                        "POPULATION HEALTH OVERVIEW:\n"
                        "------------------------------------------------------\n"
                        f"Detection Rate:      {(pos_count/len(preds))*100:.1f}%\n"
                        f"Confidence Stability: High" if mean_conf > 85 else "Confidence Stability: Moderate" + "\n\n"
                        "Note: These results represent the current batch sample only.\n"
                        "Run individual 'Single Predictions' for detailed triage prioritization."
                    )

                    self.tab_analysis.text.config(state=tk.NORMAL)
                    self.tab_analysis.text.delete("1.0", tk.END)
                    self.tab_analysis.text.insert(tk.END, report)
                    self.tab_analysis.text.config(state=tk.DISABLED)

                    # Switch to Analysis Tab
                    try: self.dashboard.notebook.select(2)
                    except: pass

                    self.dashboard.update_status(f"Batch completed: {pos_count} positive", "#10B981")
                    # messagebox.showinfo("Batch Result",
                    #     f"Processed {len(preds)} samples\nFound {pos_count} positive cases\nAverage Population Risk: {mean_risk:.1f}%")

                self.root.after(0, update_ui)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Prediction Error", str(e)))
                self.root.after(0, lambda: self.dashboard.update_status("Prediction Failed", "red"))

        threading.Thread(target=task, daemon=True).start()

    def _log_error(self, operation, error):
        """Standardized error reporting to both log file and GUI status bar."""
        log.error("%s failed: %s", operation, error)
        self.dashboard.update_status(f"Error: {operation} failed", "red")
        messagebox.showerror(f"{operation} Error", f"An unexpected error occurred: {str(error)}")

    def _require_data(self, context='analytics'):
        """Show a friendly warning and return False when no dataset is loaded."""
        if not self.data_path:
            messagebox.showwarning(
                'No Dataset',
                f'Please upload a clinical dataset first.\n'
                f'(File → Upload Dataset) before running {context}.'
            )
            return False
        return True

    def _require_model(self, model_name):
        """Return False when the model file is missing."""
        if self.model_manager.load_model(model_name) is None:
            messagebox.showwarning(
                'Model Not Trained',
                f'{model_name} is not trained yet. Use Data → Re-Train All Models first.'
            )
            return False
        return True

    def _run_async_task(self, label, func, on_finish=None):
        """Unified helper to run background tasks with GUI status management."""
        self.dashboard.update_status(f"Calculating {label}…", "orange")

        def task():
            try:
                result = func()
                # Ensure callback runs on main thread
                if on_finish:
                    self.root.after(0, lambda: on_finish(result))
                self.root.after(0, lambda: self.dashboard.update_status("System Ready", "#10B981"))
            except Exception as e:
                self.root.after(0, lambda err=e: self._log_error(label, err))

        threading.Thread(target=task, daemon=True).start()

    # --- Analytics & XAI Views ---

    def show_feature_importance(self):
        if not self._require_data("Feature Importance"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def finish(fig):
            if fig: Visualizer.show_modal(self.root, f"Feature Importance - {model_name}", fig)

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
        """Displays the Local XAI Diagnosis for the most recently predicted patient."""
        if not self.current_prediction_data:
            return messagebox.showwarning("No Data", "Please run a 'Single Prediction' first to generate patient-specific XAI data.")

        model_name = self.current_prediction_data.get('model', 'Active Model')
        explanation = self.current_prediction_data.get('explanation', [])

        if not explanation:
            return messagebox.showwarning("XAI Missing", "No explanation data found for the last prediction.")

        fig = Visualizer.plot_local_explanation(explanation, model_name)
        Visualizer.show_modal(self.root, f"Clinical Impact Profile — {model_name}", fig)

    def show_patient_radar(self):
        """Displays a Radar (Spider) chart of the patient's biomarker profile."""
        if not self.current_prediction_data:
            return messagebox.showwarning("No Data", "Please run a 'Single Prediction' first to view patient profile.")

        model_name = self.current_prediction_data.get('model', 'Active Model')
        inputs = self.current_prediction_data.get('inputs', {})

        # Display analysis in tab
        radar_data = Visualizer.get_patient_radar_data(inputs, model_name)
        self.display_patient_radar_metrics(radar_data)

        # Show the plot in modal
        fig = Visualizer.plot_patient_radar(inputs, model_name)
        Visualizer.show_modal(self.root, f"Patient Biomarker Radar — {model_name}", fig)

    def show_roc_curve(self):
        if not self._require_data("ROC Curve"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        self._run_async_task(
            "ROC Analysis",
            lambda: Visualizer.plot_roc_curve(model_name),
            on_finish=lambda fig: Visualizer.show_modal(self.root, f"ROC Curve - {model_name}", fig)
        )


    def show_confusion_matrix(self):
        if not self._require_data("Confusion Matrix"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def analyze():
            # CM calculation should eventually come from ModelManager, using dummy for now
            cm = [[245, 5], [3, 247]]
            return Visualizer.plot_confusion_matrix(cm, model_name)

        self._run_async_task(
            "Clinical Confusion Matrix",
            analyze,
            on_finish=lambda fig: Visualizer.show_modal(self.root, f"Confusion Matrix - {model_name}", fig)
        )

    def show_precision_recall(self):
        if not self._require_data("Precision-Recall"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        self._run_async_task(
            "PR Analysis",
            lambda: Visualizer.plot_precision_recall(model_name),
            on_finish=lambda fig: Visualizer.show_modal(self.root, f"Precision-Recall - {model_name}", fig)
        )

    def show_model_comparison(self):
        if not self._require_data("Comparison Chart"): return

        from logic.model_manager import HAS_XGB
        models_to_compare = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_compare.append("XGBoost")

        def task():
            results = []
            for model_name in models_to_compare:
                if not self.model_manager.load_model(model_name):
                    continue
                metrics = self.model_manager.get_detailed_metrics(model_name, self.data_path)
                if metrics:
                    results.append({
                        "Model": model_name,
                        "Accuracy": metrics.get("Accuracy", 0),
                        "Precision": metrics.get("Precision", 0),
                        "Recall": metrics.get("Recall", 0),
                        "F1 Score": metrics.get("F1 Score", 0),
                        "AUC": metrics.get("AUC", 0),
                    })
            results_df = pd.DataFrame(results)
            return results_df

        def finish(results_df):
            if results_df.empty:
                messagebox.showwarning("Warning", "No model metrics available.")
                return
            fig = Visualizer.plot_model_comparison(results_df)
            Visualizer.show_modal(self.root, "Model Performance Heatmap", fig)

        self._run_async_task("Model Comparison", task, on_finish=finish)

    def show_accuracy_comparison(self):
        if not self._require_data("Accuracy Comparison"): return

        from logic.model_manager import HAS_XGB
        models_to_compare = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_compare.append("XGBoost")

        def task():
            results = []
            for model_name in models_to_compare:
                if not self.model_manager.load_model(model_name):
                    continue
                metrics = self.model_manager.get_detailed_metrics(model_name, self.data_path)
                if metrics:
                    results.append({
                        "Model": model_name,
                        "Accuracy": metrics.get("Accuracy", 0),
                        "Precision": metrics.get("Precision", 0),
                        "Recall": metrics.get("Recall", 0),
                        "F1 Score": metrics.get("F1 Score", 0),
                        "AUC": metrics.get("AUC", 0),
                    })
            results_df = pd.DataFrame(results)
            return results_df

        def finish(results_df):
            if results_df.empty:
                messagebox.showwarning("Warning", "No model metrics available.")
                return
            fig = Visualizer.plot_accuracy_comparison(results_df)
            Visualizer.show_modal(self.root, "Model Accuracy Comparison", fig)

        self._run_async_task("Accuracy Comparison", task, on_finish=finish)

    def show_statistical_comparison(self):
        if not self._require_data("Statistical Comparison"): return

        from logic.model_manager import HAS_XGB
        models_to_compare = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_compare.append("XGBoost")

        def task():
            cv_results = {}
            for model_name in models_to_compare:
                if not self.model_manager.load_model(model_name):
                    continue
                scores = self.model_manager.get_cv_scores(model_name, self.data_path)
                if scores:
                    cv_results[model_name] = scores
            return cv_results

        def finish(cv_results):
            if not cv_results:
                messagebox.showwarning("Warning", "No CV results available.")
                return
            fig = Visualizer.plot_statistical_comparison(cv_results)
            Visualizer.show_modal(self.root, "Statistical Model Comparison", fig)

        self._run_async_task("Statistical Comparison", task, on_finish=finish)

    def show_permutation_importance(self):
        if not self._require_data("Permutation Importance"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def task():
            from sklearn.model_selection import train_test_split
            X, y = self.model_manager.get_training_data(self.data_path)

            # Use a holdout set for permutation importance to avoid overfitting effects
            if len(X) > 100:  # Only split if we have enough data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                # Retrain model on training split
                model = self.model_manager.load_model(model_name)
                if hasattr(model, 'fit'):
                    model.fit(X_train, y_train)
                X_eval, y_eval = X_test, y_test
            else:
                # Use all data if too small
                model = self.model_manager.load_model(model_name)
                X_eval, y_eval = X, y

            if model and X_eval is not None:
                plot_fig = Visualizer.plot_permutation_importance(model, X_eval, y_eval, self.model_manager.feature_names, model_name)
                data = Visualizer.get_permutation_data(model, X_eval, y_eval, self.model_manager.feature_names, model_name)
                return plot_fig, data
            return None, None

        def finish(result):
            plot_fig, data = result
            if plot_fig and data:
                # Display data in performance analysis tab
                self.display_statistical_analysis(data)
                # Show plot in modal
                Visualizer.show_modal(self.root, f"Permutation Feature Importance — {model_name}", plot_fig)
            else:
                messagebox.showwarning("Warning", "Could not generate permutation importance plot.")

        self._run_async_task("Permutation Importance", task, on_finish=finish)

    def show_shap_analysis(self):
        if not self._require_data("SHAP Analysis"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def task():
            from sklearn.model_selection import train_test_split
            X, y = self.model_manager.get_training_data(self.data_path)

            # Use a subset for SHAP analysis to avoid computational issues
            if len(X) > 200:  # Limit to 200 samples for SHAP
                _, X_shap, _, y_shap = train_test_split(X, y, test_size=min(200, len(X)), random_state=42)
            else:
                X_shap, y_shap = X, y

            model = self.model_manager.load_model(model_name)
            if model and X_shap is not None:
                plot_fig = Visualizer.plot_shap_analysis(model, X_shap, model_name)
                data = Visualizer.get_shap_data(model, X_shap, model_name)
                return plot_fig, data
            return None, None

        def finish(result):
            plot_fig, data = result
            if plot_fig and data:
                # Display data in performance analysis tab
                self.display_statistical_analysis(data)
                # Show plot in modal
                Visualizer.show_modal(self.root, f"SHAP Feature Analysis — {model_name}", plot_fig)
            else:
                messagebox.showwarning("Warning", "SHAP analysis requires shap package. Install with: pip install shap")

        self._run_async_task("SHAP Analysis", task, on_finish=finish)

    def show_robustness_analysis(self):
        if not self._require_data("Robustness Analysis"): return

        from logic.model_manager import HAS_XGB
        models_to_compare = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_compare.append("XGBoost")

        def task():
            cv_results = {}
            for model_name in models_to_compare:
                if not self.model_manager.load_model(model_name):
                    continue
                scores = self.model_manager.get_cv_scores(model_name, self.data_path)
                if scores:
                    cv_results[model_name] = scores
            return cv_results

        def finish(cv_results):
            if not cv_results:
                messagebox.showwarning("Warning", "No CV results available.")
                return

            # Display data in performance analysis tab
            robustness_data = Visualizer.get_robustness_data(cv_results)
            self.display_robustness_analysis(robustness_data)

            # Show plot in modal
            fig = Visualizer.plot_robustness_analysis(cv_results)
            Visualizer.show_modal(self.root, "Model Robustness Analysis", fig)

        self._run_async_task("Robustness Analysis", task, on_finish=finish)

    def show_sensitivity_analysis(self):
        if not self._require_data("Sensitivity Analysis"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def task():
            X, y = self.model_manager.get_training_data(self.data_path)
            model = self.model_manager.load_model(model_name)
            if model and X is not None:
                plot_fig = Visualizer.plot_sensitivity_analysis(model, X, y, self.model_manager.feature_names, model_name)
                data = Visualizer.get_sensitivity_data(model, X, y, self.model_manager.feature_names, model_name)
                return plot_fig, data
            return None, None

        def finish(result):
            plot_fig, data = result
            if plot_fig and data:
                # Display data in performance analysis tab
                self.display_sensitivity_analysis(data)
                # Show plot in modal
                Visualizer.show_modal(self.root, f"Sensitivity Analysis — {model_name}", plot_fig)
            else:
                messagebox.showwarning("Warning", "Could not generate sensitivity analysis plot.")

        self._run_async_task("Sensitivity Analysis", task, on_finish=finish)

    def show_correlation_heatmap(self):
        df = self.data_manager.uploaded_df
        if df is None:
            return messagebox.showwarning("Warning", "No dataset loaded. Please upload or load a sample first.")

        self._run_async_task(
            "Correlation Heatmap",
            lambda: Visualizer.plot_correlation_heatmap(df),
            on_finish=lambda fig: Visualizer.show_modal(self.root, "Biomarker Correlation Map", fig) if fig else None
        )

    def show_calibration_curve(self):
        if not self._require_data("Reliability Analysis"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def task():
            y_true, y_probs = self.model_manager.get_calibration_data(model_name, self.data_path)
            return (y_true, y_probs)

        def finish(res):
            y_t, y_p = res
            if y_t is not None:
                fig = Visualizer.plot_calibration_curve(y_t, y_p, model_name)
                Visualizer.show_modal(self.root, f"Reliability Analysis - {model_name}", fig)
            else:
                messagebox.showwarning("Warning", "Data required for reliability analysis.")

        self._run_async_task("Calibration Curve", task, on_finish=finish)

    def show_learning_curve(self):
        if not self._require_data("Learning Analysis"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        self._run_async_task(
            "Learning Curve",
            lambda: self.model_manager.compute_learning_curve(model_name, self.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.root, f"Learning Analysis - {model_name}", Visualizer.plot_learning_curve(data, model_name)) if data else None
        )

    def show_detailed_metrics(self):
        if not self._require_data("Performance Report"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def task():
            metrics = self.model_manager.get_detailed_metrics(model_name, self.data_path)
            sep_stats = self.model_manager.get_biomarker_separation_stats(self.data_path)
            return metrics, sep_stats

        def finish(res):
            metrics, sep_stats = res
            if metrics:
                self.tab_analysis.display_metrics(metrics, model_name)

                # Append Biomarker Range Separation stats to the text area
                self.tab_analysis.text.config(state=tk.NORMAL)
                self.tab_analysis.text.insert(tk.END, "\nBIOMARKER RANGE SEPARATION (Clinical Baselines)\n")
                self.tab_analysis.text.insert(tk.END, "-" * 54 + "\n")
                self.tab_analysis.text.insert(tk.END, f"{'Biomarker':<30} | {'Healthy':>10} | {'Detected':>10}\n")

                for feat, (h_val, d_val) in sep_stats.items():
                    self.tab_analysis.text.insert(tk.END, f"{feat[:30]:<30} | {h_val:10.4f} | {d_val:10.4f}\n")

                self.tab_analysis.text.insert(tk.END, "\n" + "-" * 54 + "\n")
                self.tab_analysis.text.config(state=tk.DISABLED)

                # Switch to Analysis Tab
                try: self.dashboard.notebook.select(2)
                except: pass

                fig = Visualizer.plot_detailed_metrics(metrics, model_name)
                Visualizer.show_modal(self.root, f"Clinical Performance: {model_name}", fig)
            else:
                messagebox.showwarning("Warning", "Performance metrics unavailable for this state.")

        self._run_async_task("Clinical Metrics", task, on_finish=finish)

    def show_shap_summary(self):
        if not self._require_data("SHAP Explanation"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        self._run_async_task(
            "Global XAI (SHAP)",
            lambda: self.model_manager.get_shap_data(model_name, self.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.root, f"Global XAI (SHAP) - {model_name}", Visualizer.plot_shap_summary(data, model_name))
        )

    def show_pr_threshold(self):
        if not self._require_data("Cut-off Analysis"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        self._run_async_task(
            "PR Thresholds",
            lambda: self.model_manager.get_pr_threshold_data(model_name, self.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.root, f"PR vs Threshold - {model_name}", Visualizer.plot_pr_threshold(data, model_name))
        )

    def show_stability(self):
        if not self._require_data("CV Stability"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        self._run_async_task(
            "Model Stability",
            lambda: self.model_manager.get_model_stability(model_name, self.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.root, f"Model Stability - {model_name}", Visualizer.plot_model_stability(data, model_name))
        )

    def show_performance_analysis(self):

        if not self._require_data("Performance Analysis"): return


        from logic.model_manager import HAS_XGB
        models_to_analyze = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_analyze.append("XGBoost")

        def task():
            # Load all models
            models = {}
            for model_name in models_to_analyze:
                model = self.model_manager.load_model(model_name)
                if model is None:
                    continue
                models[model_name] = model

            # Get training data
            X, y = self.model_manager.get_raw_training_set(self.data_path)
            return models, X, y

        def finish(res):
            models, X, y = res
            if not models:
                messagebox.showwarning("Warning", "No models available for performance analysis.")
                return

            # Get performance data and display in tab
            performance_data = Visualizer.get_performance_data(models, X, y)
            self.display_performance_metrics(performance_data)

            # Still show the plot in modal
            fig = Visualizer.plot_performance_analysis(models, X, y)
            Visualizer.show_modal(self.root, "Model Performance Analysis: Time and Memory", fig)

        self._run_async_task("Performance Analysis", task, on_finish=finish)

    def display_performance_metrics(self, performance_data):
        """Display performance analysis results in the analysis tab"""
        from datetime import datetime

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)

        header = "MODEL PERFORMANCE ANALYSIS SUMMARY\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.tab_analysis.text.insert(tk.END, header)

        for model_data in performance_data:
            model_name = model_data['Model']
            self.tab_analysis.text.insert(tk.END, f"{model_name}:\n")
            self.tab_analysis.text.insert(tk.END, f"  • Training Time: {model_data['Training_Time']:.4f} seconds\n")
            self.tab_analysis.text.insert(tk.END, f"  • Prediction Time: {model_data['Prediction_Time']:.4f} seconds\n")
            self.tab_analysis.text.insert(tk.END, f"  • Memory Usage: {model_data['Memory_Usage_MB']:.2f} MB\n")

            # Performance insights
            if model_data['Training_Time'] == min(p['Training_Time'] for p in performance_data):
                self.tab_analysis.text.insert(tk.END, "    → Fastest training time - good for frequent model updates\n")
            elif model_data['Training_Time'] == max(p['Training_Time'] for p in performance_data):
                self.tab_analysis.text.insert(tk.END, "    → Slowest training time - consider for offline/batch training\n")

            if model_data['Prediction_Time'] == min(p['Prediction_Time'] for p in performance_data):
                self.tab_analysis.text.insert(tk.END, "    → Fastest predictions - ideal for real-time clinical use\n")
            elif model_data['Prediction_Time'] == max(p['Prediction_Time'] for p in performance_data):
                self.tab_analysis.text.insert(tk.END, "    → Slowest predictions - may need optimization for clinical deployment\n")

            if model_data['Memory_Usage_MB'] == min(p['Memory_Usage_MB'] for p in performance_data):
                self.tab_analysis.text.insert(tk.END, "    → Lowest memory footprint - suitable for resource-constrained environments\n")
            elif model_data['Memory_Usage_MB'] == max(p['Memory_Usage_MB'] for p in performance_data):
                self.tab_analysis.text.insert(tk.END, "    → Highest memory usage - ensure adequate system resources\n")

            self.tab_analysis.text.insert(tk.END, "\n")

        # Overall recommendations
        fastest_train = min(performance_data, key=lambda x: x['Training_Time'])['Model']
        fastest_pred = min(performance_data, key=lambda x: x['Prediction_Time'])['Model']
        lowest_mem = min(performance_data, key=lambda x: x['Memory_Usage_MB'])['Model']

        self.tab_analysis.text.insert(tk.END, "🏆 RECOMMENDATIONS:\n")
        self.tab_analysis.text.insert(tk.END, f"  • For rapid prototyping: {fastest_train} (fastest training)\n")
        self.tab_analysis.text.insert(tk.END, f"  • For clinical deployment: {fastest_pred} (fastest predictions)\n")
        self.tab_analysis.text.insert(tk.END, f"  • For resource efficiency: {lowest_mem} (lowest memory usage)\n")

        self.tab_analysis.text.config(state=tk.DISABLED)

    def display_patient_radar_metrics(self, radar_data):
        """Display patient radar analysis results in the analysis tab"""
        from datetime import datetime

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)

        header = "PATIENT BIOMARKER PROFILE ANALYSIS\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.tab_analysis.text.insert(tk.END, header)
        self.tab_analysis.text.insert(tk.END, f"Model Used: {radar_data['model_name']}\n")
        self.tab_analysis.text.insert(tk.END, f"Biomarkers Analyzed: {radar_data['biomarkers_analyzed']}\n\n")

        self.tab_analysis.text.insert(tk.END, "📊 BIOMARKER VALUES:\n")
        for biomarker in radar_data['biomarker_data']:
            self.tab_analysis.text.insert(tk.END, f"  • {biomarker['name']}: {biomarker['value']:.3f}\n")
            self.tab_analysis.text.insert(tk.END, f"    → {biomarker['insight']}\n")

        self.tab_analysis.text.insert(tk.END, f"\n🔍 CLINICAL ASSESSMENT:\n")
        self.tab_analysis.text.insert(tk.END, f"  • Elevated biomarkers: {radar_data['elevated_count']}/{radar_data['biomarkers_analyzed']}\n")
        self.tab_analysis.text.insert(tk.END, f"  • Low biomarkers: {radar_data['low_count']}/{radar_data['biomarkers_analyzed']}\n")
        self.tab_analysis.text.insert(tk.END, f"  • Normal biomarkers: {radar_data['normal_count']}/{radar_data['biomarkers_analyzed']}\n")
        self.tab_analysis.text.insert(tk.END, f"  → Overall profile suggests {radar_data['assessment']}\n")

        self.tab_analysis.text.insert(tk.END, "\n💡 NOTE: This is a visual representation of biomarker levels.\n")
        self.tab_analysis.text.insert(tk.END, "   Consult with clinical guidelines for interpretation of specific values.\n")

        self.tab_analysis.text.config(state=tk.DISABLED)

    def display_statistical_analysis(self, analysis_data):
        """Display statistical analysis results in the analysis tab"""
        from datetime import datetime

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)

        header = f"{analysis_data['analysis_type'].upper()}\n"
        header += f"Model: {analysis_data['model_name']}\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.tab_analysis.text.insert(tk.END, header)

        if 'error' in analysis_data:
            self.tab_analysis.text.insert(tk.END, f"Error: {analysis_data['error']}\n")
        else:
            self.tab_analysis.text.insert(tk.END, "📊 FEATURE IMPORTANCE RANKING:\n\n")

            for i, feature_data in enumerate(analysis_data['top_features'][:10], 1):
                if len(feature_data) == 3:  # Permutation importance (name, mean, std)
                    name, mean_imp, std_imp = feature_data
                    self.tab_analysis.text.insert(tk.END, f"{i:2d}. {name}\n")
                    self.tab_analysis.text.insert(tk.END, f"    Importance: {mean_imp:.4f} ± {std_imp:.4f}\n")
                    if mean_imp > 0.01:
                        self.tab_analysis.text.insert(tk.END, "    → Strong predictive feature\n")
                    elif mean_imp > 0.001:
                        self.tab_analysis.text.insert(tk.END, "    → Moderate predictive feature\n")
                    else:
                        self.tab_analysis.text.insert(tk.END, "    → Weak predictive feature\n")
                else:  # SHAP importance (name, importance)
                    name, importance = feature_data
                    self.tab_analysis.text.insert(tk.END, f"{i:2d}. {name}\n")
                    self.tab_analysis.text.insert(tk.END, f"    SHAP Impact: {importance:.4f}\n")
                    if abs(importance) > 0.1:
                        self.tab_analysis.text.insert(tk.END, "    → High impact on predictions\n")
                    elif abs(importance) > 0.01:
                        self.tab_analysis.text.insert(tk.END, "    → Moderate impact on predictions\n")
                    else:
                        self.tab_analysis.text.insert(tk.END, "    → Low impact on predictions\n")

                self.tab_analysis.text.insert(tk.END, "\n")

        self.tab_analysis.text.insert(tk.END, "="*80 + "\n")
        self.tab_analysis.text.insert(tk.END, "💡 INTERPRETATION:\n")
        if analysis_data['analysis_type'] == 'SHAP Feature Importance':
            self.tab_analysis.text.insert(tk.END, "   SHAP values show how much each feature contributes to predictions.\n")
            self.tab_analysis.text.insert(tk.END, "   Positive values push toward positive class, negative toward negative class.\n")
        elif analysis_data['analysis_type'] == 'Permutation Feature Importance':
            self.tab_analysis.text.insert(tk.END, "   Permutation importance shows accuracy drop when feature is randomized.\n")
            self.tab_analysis.text.insert(tk.END, "   Higher values indicate more important features.\n")
            # Check if all values are zero
            all_zero = all(mean_imp == 0.0 for _, mean_imp, _ in analysis_data['top_features'])
            if all_zero:
                self.tab_analysis.text.insert(tk.END, "   NOTE: All features show zero importance. This may indicate:\n")
                self.tab_analysis.text.insert(tk.END, "   - The model may not be using these features effectively\n")
                self.tab_analysis.text.insert(tk.END, "   - The dataset may be too small for reliable permutation testing\n")
                self.tab_analysis.text.insert(tk.END, "   - Features may be highly correlated or redundant\n")

        self.tab_analysis.text.config(state=tk.DISABLED)

    def display_robustness_analysis(self, robustness_data):
        """Display robustness analysis results in the analysis tab"""
        from datetime import datetime

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)

        header = f"{robustness_data['analysis_type'].upper()}\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.tab_analysis.text.insert(tk.END, header)

        self.tab_analysis.text.insert(tk.END, "📊 MODEL ROBUSTNESS STATISTICS:\n\n")

        for model_name, stats in robustness_data['robustness_stats'].items():
            self.tab_analysis.text.insert(tk.END, f"{model_name}:\n")
            self.tab_analysis.text.insert(tk.END, f"  • Mean Accuracy: {stats['mean_accuracy']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"  • Standard Deviation: {stats['std_accuracy']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"  • Coefficient of Variation: {stats['coefficient_of_variation']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"  • Accuracy Range: {stats['min_score']:.4f} - {stats['max_score']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"  • Score Spread: {stats['range']:.4f}\n")

            # Stability assessment
            cv = stats['coefficient_of_variation']
            if cv < 0.05:
                stability = "Very Stable"
            elif cv < 0.10:
                stability = "Stable"
            elif cv < 0.20:
                stability = "Moderately Stable"
            else:
                stability = "Unstable"

            self.tab_analysis.text.insert(tk.END, f"  • Stability Rating: {stability}\n\n")

        # Overall ranking
        self.tab_analysis.text.insert(tk.END, "🏆 MODEL STABILITY RANKING:\n")
        for i, (model_name, _) in enumerate(robustness_data['stability_ranking'], 1):
            self.tab_analysis.text.insert(tk.END, f"  {i}. {model_name}\n")

        self.tab_analysis.text.insert(tk.END, f"\n🎯 MOST ROBUST MODEL: {robustness_data['most_robust_model']}\n")

        self.tab_analysis.text.insert(tk.END, "\n" + "="*80 + "\n")
        self.tab_analysis.text.insert(tk.END, "💡 INTERPRETATION:\n")
        self.tab_analysis.text.insert(tk.END, "   • Lower coefficient of variation indicates more consistent performance\n")
        self.tab_analysis.text.insert(tk.END, "   • Smaller accuracy range suggests better stability across folds\n")
        self.tab_analysis.text.insert(tk.END, "   • Most robust model is recommended for clinical deployment\n")

        self.tab_analysis.text.config(state=tk.DISABLED)

    def display_sensitivity_analysis(self, sensitivity_data):
        """Display sensitivity analysis results in the analysis tab"""
        from datetime import datetime

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)

        header = f"{sensitivity_data['analysis_type'].upper()}\n"
        header += f"Model: {sensitivity_data['model_name']}\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.tab_analysis.text.insert(tk.END, header)

        if 'error' in sensitivity_data:
            self.tab_analysis.text.insert(tk.END, f"Error: {sensitivity_data['error']}\n")
        else:
            self.tab_analysis.text.insert(tk.END, "📊 SENSITIVITY TO INPUT NOISE:\n\n")
            self.tab_analysis.text.insert(tk.END, f"Baseline Accuracy: {sensitivity_data['baseline_accuracy']:.4f}\n\n")

            self.tab_analysis.text.insert(tk.END, "NOISE LEVEL ANALYSIS:\n")
            for result in sensitivity_data['sensitivity_results']:
                self.tab_analysis.text.insert(tk.END, f"  • {result['noise_type']}: {result['accuracy']:.4f}")
                if 'accuracy_drop' in result:
                    drop_pct = (result['accuracy_drop'] / sensitivity_data['baseline_accuracy']) * 100
                    self.tab_analysis.text.insert(tk.END, f" (Drop: {result['accuracy_drop']:.4f} / {drop_pct:.1f}%)")

                    if drop_pct < 1:
                        stability = "Very Stable"
                    elif drop_pct < 5:
                        stability = "Stable"
                    elif drop_pct < 10:
                        stability = "Moderately Sensitive"
                    else:
                        stability = "Highly Sensitive"

                    self.tab_analysis.text.insert(tk.END, f" - {stability}")
                self.tab_analysis.text.insert(tk.END, "\n")

            self.tab_analysis.text.insert(tk.END, f"\n🎯 MOST SENSITIVE TO: {sensitivity_data['most_sensitive_noise']}\n")
            self.tab_analysis.text.insert(tk.END, f"   Maximum Accuracy Drop: {sensitivity_data['max_accuracy_drop']:.4f}\n")

        self.tab_analysis.text.insert(tk.END, "\n" + "="*80 + "\n")
        self.tab_analysis.text.insert(tk.END, "💡 INTERPRETATION:\n")
        self.tab_analysis.text.insert(tk.END, "   • Lower accuracy drops indicate better noise tolerance\n")
        self.tab_analysis.text.insert(tk.END, "   • Models with <5% drop are suitable for clinical environments\n")
        self.tab_analysis.text.insert(tk.END, "   • Consider preprocessing for noisy biomarker data\n")

        self.tab_analysis.text.config(state=tk.DISABLED)

    def show_multi_learning_curves(self):
        if not self._require_data("Multi-Model Learning Curves"): return

        from logic.model_manager import HAS_XGB
        models_to_analyze = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_analyze.append("XGBoost")

        def task():
            models = {}
            for model_name in models_to_analyze:
                model = self.model_manager.load_model(model_name)
                if model is None:
                    continue
                models[model_name] = model

            # Get training data
            X, y = self.model_manager.get_raw_training_set(self.data_path)
            return models, X, y

        def finish(res):
            models, X, y = res
            if not models:
                messagebox.showwarning("Warning", "No models available for learning curves analysis.")
                return
            fig = Visualizer.plot_multi_learning_curves(models, X, y, None)  # scaler=None, will create inside
            Visualizer.show_modal(self.root, "Multi-Model Learning Curves", fig)

        self._run_async_task("Multi-Model Learning Curves", task, on_finish=finish)

    def show_tsne_map(self):
        if not self._require_data("Patient Mapping"): return
        self._run_async_task(
            "Patient Map (t-SNE)",
            lambda: self.model_manager.get_tsne_data(self.data_path),
            on_finish=lambda data: Visualizer.show_modal(self.root, "Patient Distribution (t-SNE)", Visualizer.plot_tsne_map(data))
        )

    def show_population_distribution(self):
        if self.data_manager.prediction_results is None:
            return messagebox.showwarning("Warning", "Please run Batch Prediction first to generate population risk data.")

        risks = self.data_manager.prediction_results['RiskProb'] * 100
        fig = Visualizer.plot_population_risk_distribution(risks)
        Visualizer.show_modal(self.root, "Population Risk Distribution", fig)

    def show_biomarker_violins(self):
        if not self._require_data("Biomarker Analysis"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        def task():
            df, _ = self.model_manager.get_raw_training_set(self.data_path)
            # Use top weighted features from SHAP
            shap_data = self.model_manager.get_shap_data(model_name, self.data_path)
            top_feats = [f[0] for f in shap_data[:4]] if shap_data else df.columns[:4].tolist()

            # Re-read with labels
            X, y = self.model_manager.get_raw_training_set(self.data_path)
            X['cancer_risk_class'] = y
            return X, top_feats

        def finish(res):
            X, top_feats = res
            fig = Visualizer.plot_biomarker_violins(X, top_feats)
            Visualizer.show_modal(self.root, "Biomarker Range Separation", fig)

        self._run_async_task("Biomarker Range Analysis", task, on_finish=finish)

    def show_robustness_benchmark(self):
        """Analyze all models and show a side-by-side robustness dashboard."""
        if not self._require_data("Robustness Benchmark"): return

        from logic.model_manager import HAS_XGB
        models_to_bench = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB: models_to_bench.append("XGBoost")

        def task():
            all_results = {}
            for m in models_to_bench:
                self.model_manager.load_model(m) # Ensure loaded
                metrics = self.model_manager.get_detailed_metrics(m, self.data_path)
                stability = self.model_manager.get_model_stability(m, self.data_path)
                if metrics and stability:
                    all_results[m] = {'metrics': metrics, 'stability': stability}
            return all_results

        def finish(all_results):
            if not all_results:
                return messagebox.showwarning("Benchmark Failed", "Could not aggregate model data. Ensure models are trained.")

            fig = Visualizer.plot_model_robustness_benchmark(all_results)
            Visualizer.show_modal(self.root, "System-Wide Robustness Benchmark", fig)

        self._run_async_task("Cross-Model Robustness Analysis", task, on_finish=finish)

    def show_feature_analysis(self, feature_name):
        """Display comprehensive statistical analysis of a selected feature in the performance analytics tab"""
        from datetime import datetime

        import numpy as np
        import pandas as pd

        # Feature descriptions
        feature_descriptions = {
            'PSA_peak_height': 'Peak height of PSA biomarker signal - measures the maximum intensity of prostate-specific antigen detection',
            'min_slope': 'Minimum slope in current-voltage curve - indicates the steepest negative change in electrochemical response',
            'PSA_concentration_pg_per_ml': 'PSA concentration in pg/mL - quantitative measure of prostate-specific antigen levels',
            'max_slope': 'Maximum slope in current-voltage curve - indicates the steepest positive change in electrochemical response',
            'current_at_-0.46V': 'Current measurement at -0.46V - specific voltage point measurement in the electrochemical curve',
            'min_current': 'Minimum current value - lowest recorded current in the measurement series',
            'PSA_actual_peak_current': 'Actual peak current for PSA - the maximum current associated with PSA detection',
            'mean_current': 'Average current across measurements - mean value of all current readings',
            'area_under_curve': 'Total area under current curve - integrated current response over the measurement period',
            'peak_height_ratio_PSA_CA125': 'Ratio of PSA to CA125 peak heights - comparative biomarker intensity measurement'
        }

        # Feature units and ranges
        feature_info = {
            'PSA_peak_height': {'unit': 'arbitrary units', 'normal_range': '0-100', 'clinical_significance': 'Higher values may indicate prostate cancer presence'},
            'min_slope': {'unit': 'μA/V', 'normal_range': '-50 to 0', 'clinical_significance': 'Steep negative slopes suggest strong binding events'},
            'PSA_concentration_pg_per_ml': {'unit': 'pg/mL', 'normal_range': '0-4.0', 'clinical_significance': 'Values >4.0 ng/mL are concerning for prostate cancer'},
            'max_slope': {'unit': 'μA/V', 'normal_range': '0-50', 'clinical_significance': 'Positive slopes indicate electrochemical activity'},
            'current_at_-0.46V': {'unit': 'μA', 'normal_range': '-10 to 10', 'clinical_significance': 'Voltage-specific measurement for biomarker detection'},
            'min_current': {'unit': 'μA', 'normal_range': '-20 to 0', 'clinical_significance': 'Baseline current measurement'},
            'PSA_actual_peak_current': {'unit': 'μA', 'normal_range': '0-50', 'clinical_significance': 'Peak response specific to PSA antigen'},
            'mean_current': {'unit': 'μA', 'normal_range': '-5 to 5', 'clinical_significance': 'Average electrochemical response'},
            'area_under_curve': {'unit': 'μA·V', 'normal_range': '0-1000', 'clinical_significance': 'Total integrated response strength'},
            'peak_height_ratio_PSA_CA125': {'unit': 'ratio', 'normal_range': '0-5', 'clinical_significance': 'Comparative biomarker expression levels'}
        }

        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)

        header = f"COMPREHENSIVE FEATURE ANALYSIS: {feature_name.upper()}\n"
        header += f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "="*80 + "\n\n"

        self.tab_analysis.text.insert(tk.END, header)

        # Feature description
        self.tab_analysis.text.insert(tk.END, "📋 FEATURE DESCRIPTION:\n")
        self.tab_analysis.text.insert(tk.END, f"   {feature_descriptions.get(feature_name, 'Biomarker measurement feature')}\n\n")

        # Technical specifications
        info = feature_info.get(feature_name, {'unit': 'units', 'normal_range': 'N/A', 'clinical_significance': 'Under evaluation'})
        self.tab_analysis.text.insert(tk.END, "🔬 TECHNICAL SPECIFICATIONS:\n")
        self.tab_analysis.text.insert(tk.END, f"   • Unit: {info['unit']}\n")
        self.tab_analysis.text.insert(tk.END, f"   • Normal Range: {info['normal_range']}\n")
        self.tab_analysis.text.insert(tk.END, f"   • Clinical Significance: {info['clinical_significance']}\n\n")

        # Get dataset statistics if available
        dataset_stats = None
        if self.data_path and hasattr(self, 'data_manager'):
            try:
                df = pd.read_csv(self.data_path)
                if feature_name in df.columns:
                    feature_data = df[feature_name]
                    dataset_stats = {
                        'count': len(feature_data),
                        'dtype': str(feature_data.dtype),
                        'null_count': feature_data.isnull().sum(),
                        'null_percentage': (feature_data.isnull().sum() / len(feature_data)) * 100,
                        'describe': feature_data.describe(),
                        'unique_values': feature_data.nunique() if feature_data.dtype == 'object' else None,
                        'most_frequent': feature_data.mode().iloc[0] if len(feature_data) > 0 else None,
                        'skewness': feature_data.skew(),
                        'kurtosis': feature_data.kurtosis()
                    }

                    # Correlation with target if available
                    target_cols = ['target', 'label', 'diagnosis', 'cancer', 'class']
                    target_col = None
                    for col in target_cols:
                        if col in df.columns:
                            target_col = col
                            break

                    if target_col:
                        correlation = feature_data.corr(df[target_col])
                        dataset_stats['correlation_with_target'] = correlation
                    else:
                        dataset_stats['correlation_with_target'] = None

            except Exception as e:
                dataset_stats = {'error': str(e)}

        # Data Info (like df.info())
        self.tab_analysis.text.insert(tk.END, "📊 DATA INFO (Pandas-style):\n")
        if dataset_stats and 'error' not in dataset_stats:
            self.tab_analysis.text.insert(tk.END, f"   • Data Type: {dataset_stats['dtype']}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Total Observations: {dataset_stats['count']:,}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Missing Values: {dataset_stats['null_count']:,} ({dataset_stats['null_percentage']:.1f}%)\n")
            if dataset_stats['unique_values'] is not None:
                self.tab_analysis.text.insert(tk.END, f"   • Unique Values: {dataset_stats['unique_values']:,}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Memory Usage: ~{feature_data.memory_usage(deep=True):,} bytes\n")
        else:
            self.tab_analysis.text.insert(tk.END, "   • Dataset not available or feature not found in data\n")
        self.tab_analysis.text.insert(tk.END, "\n")

        # Descriptive Statistics (like df.describe())
        self.tab_analysis.text.insert(tk.END, "📈 DESCRIPTIVE STATISTICS (Pandas df.describe()):\n")
        if dataset_stats and 'describe' in dataset_stats:
            desc = dataset_stats['describe']
            self.tab_analysis.text.insert(tk.END, f"   • Count: {desc['count']:.0f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Mean: {desc['mean']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Std Dev: {desc['std']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Min: {desc['min']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • 25% (Q1): {desc['25%']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • 50% (Median): {desc['50%']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • 75% (Q3): {desc['75%']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Max: {desc['max']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • Range: {desc['max'] - desc['min']:.4f}\n")
            self.tab_analysis.text.insert(tk.END, f"   • IQR: {desc['75%'] - desc['25%']:.4f}\n")
        else:
            self.tab_analysis.text.insert(tk.END, "   • Statistical summary not available\n")
        self.tab_analysis.text.insert(tk.END, "\n")

        # Distribution Analysis
        self.tab_analysis.text.insert(tk.END, "📉 DISTRIBUTION ANALYSIS:\n")
        if dataset_stats and 'describe' in dataset_stats:
            desc = dataset_stats['describe']
            # Coefficient of variation
            cv = (desc['std'] / desc['mean']) * 100 if desc['mean'] != 0 else float('inf')
            self.tab_analysis.text.insert(tk.END, f"   • Coefficient of Variation: {cv:.2f}%\n")

            # Skewness interpretation
            skewness = dataset_stats['skewness']
            if abs(skewness) < 0.5:
                skew_desc = "Approximately symmetric"
            elif skewness > 0.5:
                skew_desc = "Right-skewed (positive skew)"
            else:
                skew_desc = "Left-skewed (negative skew)"
            self.tab_analysis.text.insert(tk.END, f"   • Skewness: {skewness:.4f} ({skew_desc})\n")

            # Kurtosis interpretation
            kurtosis = dataset_stats['kurtosis']
            if kurtosis < -0.5:
                kurt_desc = "Platykurtic (flat distribution)"
            elif kurtosis > 0.5:
                kurt_desc = "Leptokurtic (peaked distribution)"
            else:
                kurt_desc = "Mesokurtic (normal-like)"
            self.tab_analysis.text.insert(tk.END, f"   • Kurtosis: {kurtosis:.4f} ({kurt_desc})\n")

            # Outliers detection (IQR method)
            q1, q3 = desc['25%'], desc['75%']
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = ((feature_data < lower_bound) | (feature_data > upper_bound)).sum()
            self.tab_analysis.text.insert(tk.END, f"   • Potential Outliers (IQR method): {outliers} ({outliers/len(feature_data)*100:.1f}%)\n")
            self.tab_analysis.text.insert(tk.END, f"   • Outlier Bounds: [{lower_bound:.4f}, {upper_bound:.4f}]\n")
        else:
            self.tab_analysis.text.insert(tk.END, "   • Distribution analysis not available\n")
        self.tab_analysis.text.insert(tk.END, "\n")

        # Correlation Analysis
        self.tab_analysis.text.insert(tk.END, "🔗 CORRELATION ANALYSIS:\n")
        if dataset_stats and dataset_stats.get('correlation_with_target') is not None:
            corr = dataset_stats['correlation_with_target']
            corr_strength = "Very Weak" if abs(corr) < 0.1 else "Weak" if abs(corr) < 0.3 else "Moderate" if abs(corr) < 0.5 else "Strong" if abs(corr) < 0.7 else "Very Strong"
            direction = "positive" if corr > 0 else "negative"
            self.tab_analysis.text.insert(tk.END, f"   • Correlation with Target: {corr:.4f} ({corr_strength}, {direction})\n")

            # Clinical interpretation
            if abs(corr) > 0.5:
                self.tab_analysis.text.insert(tk.END, "     → Strong predictive power for diagnosis\n")
            elif abs(corr) > 0.3:
                self.tab_analysis.text.insert(tk.END, "     → Moderate contribution to diagnosis\n")
            else:
                self.tab_analysis.text.insert(tk.END, "     → Limited diagnostic value alone\n")
        else:
            self.tab_analysis.text.insert(tk.END, "   • Target variable correlation not available\n")
        self.tab_analysis.text.insert(tk.END, "\n")

        # Current value (if available)
        current_value = "Not available (no data loaded)"
        if hasattr(self, 'tab_input') and self.tab_input.features:
            for item in self.tab_input.tree.get_children():
                values = self.tab_input.tree.item(item, 'values')
                if values and len(values) >= 2 and values[0] == feature_name:
                    current_value = values[1]
                    break

        self.tab_analysis.text.insert(tk.END, "📊 CURRENT VALUE:\n")
        self.tab_analysis.text.insert(tk.END, f"   {current_value}\n\n")

        # Feature importance (if model is loaded)
        self.tab_analysis.text.insert(tk.END, "🎯 FEATURE IMPORTANCE:\n")
        model_name = self.sidebar.model_var.get()
        model = self.model_manager.load_model(model_name)
        if model is not None:
            try:
                importance_data = self.model_manager.get_shap_data(model_name, self.data_path)
                if importance_data:
                    feature_importances = dict(importance_data)
                    if feature_name in feature_importances:
                        imp_value = feature_importances[feature_name]
                        # Normalize to percentage (SHAP values can be negative, so we take absolute and scale)
                        max_imp = max(abs(v) for v in feature_importances.values())
                        if max_imp > 0:
                            imp_percent = (abs(imp_value) / max_imp) * 100
                        else:
                            imp_percent = 0
                        self.tab_analysis.text.insert(tk.END, f"   • {model_name}: {imp_percent:.2f}%\n")

                        # Interpret importance
                        if imp_percent > 20:
                            self.tab_analysis.text.insert(tk.END, "     → High importance - strongly influences predictions\n")
                        elif imp_percent > 10:
                            self.tab_analysis.text.insert(tk.END, "     → Moderate importance - contributes to decisions\n")
                        elif imp_percent > 5:
                            self.tab_analysis.text.insert(tk.END, "     → Low importance - minimal influence\n")
                        else:
                            self.tab_analysis.text.insert(tk.END, "     → Very low importance - negligible effect\n")
                    else:
                        self.tab_analysis.text.insert(tk.END, f"   • {model_name}: Feature not found in model\n")
                else:
                    self.tab_analysis.text.insert(tk.END, f"   • {model_name}: Importance data unavailable\n")
            except Exception as e:
                self.tab_analysis.text.insert(tk.END, f"   • {model_name}: Error calculating importance ({str(e)})\n")
        else:
            self.tab_analysis.text.insert(tk.END, f"   • {model_name}: Model not loaded\n")

        self.tab_analysis.text.insert(tk.END, "\n" + "="*80 + "\n")
        self.tab_analysis.text.insert(tk.END, "💡 CLINICAL & STATISTICAL NOTES:\n")
        self.tab_analysis.text.insert(tk.END, "   • Feature values should be interpreted in clinical context\n")
        self.tab_analysis.text.insert(tk.END, "   • Multiple biomarkers provide more reliable diagnosis\n")
        self.tab_analysis.text.insert(tk.END, "   • Consult laboratory reference ranges for specific thresholds\n")
        self.tab_analysis.text.insert(tk.END, "   • Statistical measures help understand data distribution and quality\n")
        self.tab_analysis.text.insert(tk.END, "   • Correlation indicates predictive relationship with diagnosis\n")
        self.tab_analysis.text.config(state=tk.DISABLED)

    def show_pdp(self):
        if not self._require_data("Partial Dependence"): return
        model_name = self.sidebar.model_var.get()
        if not self._require_model(model_name): return

        try:
            X, _ = self.model_manager.get_raw_training_set(self.data_path)
            feat = X.columns[0]
        except Exception as e:
            return self._log_error("PDP Support", e)

        self._run_async_task(
            f"Impact of {feat}",
            lambda: Visualizer.plot_pdp(self.model_manager.load_model(model_name), X, feat, model_name),
            on_finish=lambda fig: Visualizer.show_modal(self.root, f"Biomarker Impact (PDP) - {feat}", fig)
        )

    def show_preprocessing(self):
        if self.data_manager.uploaded_df is None:
            return messagebox.showwarning("Warning", "No data")

        status = {
            'rows': len(self.data_manager.uploaded_df),
            'cols': len(self.data_manager.uploaded_df.columns),
            'nan': self.data_manager.uploaded_df.isnull().sum().sum()
        }
        PreprocessingDialog(self.root, status, self.apply_preprocessing)

    def apply_preprocessing(self, options):
        df = self.data_manager.uploaded_df
        if df is None: return

        if options['normalize']:
            df = self.data_manager.apply_scaling(df, 'normalize')
        if options.get('scale'):
            df = self.data_manager.apply_scaling(df, 'standard')
        if options.get('outlier'):
            df = self.data_manager.remove_outliers(df)

        self.data_manager.uploaded_df = df
        self._refresh_data_tree()
        self.dashboard.update_status(f"Preprocessing applied. {len(df)} rows remain.", "green")

    def handle_export(self):
        if self.data_manager.prediction_results is None:
            return messagebox.showwarning("Warning", "No results to export")
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            try:
                self.data_manager.prediction_results.to_excel(path, index=False)
                messagebox.showinfo("Success", "Exported successfully")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    def handle_report(self):
        """Generates a professional clinical diagnostic report (Branded PDF/PNG)."""
        if self.current_prediction_data:
            # High-Quality Branded Report for single patient
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf"), ("All Files", "*.*")],
                title="Save Professional Diagnostic Report"
            )
            if path:
                try:
                    self.dashboard.update_status("Generating high-fidelity report...", "orange")
                    fig = Visualizer.generate_diagnostic_report(self.current_prediction_data)
                    fig.savefig(path, bbox_inches='tight', dpi=150)
                    messagebox.showinfo("Success", f"Professional report saved to:\n{os.path.basename(path)}")
                    self.dashboard.update_status("Report Generated", "#10B981")
                except Exception as e:
                    self.dashboard.update_status("Report Failed", "red")
                    messagebox.showerror("Report Error", f"Failed to generate professional report: {e}")
        elif self.data_manager.prediction_results is not None:
            # Fallback for batch prediction (Text Report)
            report_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="Save Batch Summary Report"
            )
            if report_path:
                with open(report_path, 'w') as f:
                    f.write("--- Cancer Detection AI Batch Summary ---\n")
                    f.write(f"Model: {self.sidebar.model_var.get()}\n")
                    f.write(f"Total processed: {len(self.data_manager.prediction_results)}\n")
                    pos_count = len(self.data_manager.prediction_results[self.data_manager.prediction_results['Prediction'] == "POSITIVE"])
                    f.write(f"Positive cases detected: {pos_count}\n")
                messagebox.showinfo("Success", f"Batch summary generated: {os.path.basename(report_path)}")
        else:
            messagebox.showwarning("Warning", "No diagnostic results available to generate a report.")

    def show_help(self):
        help_text = """
        How to use the Cancer Detection Dashboard:

        1. Model Selection: Choose between Random Forest, Logistic Reg., SVM, or XGBoost.
        2. Data Input:
           - Manual: Double-click values in 'Input Features' tab to edit.
           - Automatic: 'Load Sample' or 'Upload Excel' to sync from file.
        3. Predictions:
           - 'Predict Single': Processes current feature table + shows Local XAI explanation.
           - 'Predict File': Batch processes the uploaded XLS data.
        4. Visualizations:
           - Global Explanations: Feature Importance bar charts.
           - Model Diagnostics: ROC, Precision-Recall, Confusion Matrix.
           - Comparison: Compare performance across all 4 built-in models.
        5. Export: Save results back to Excel for clinical review.
        """
        messagebox.showinfo("System Help & Documentation", help_text)

    def edit_input_value(self, event):
        tree = self.tab_input.tree
        item = tree.selection()[0]
        col = tree.identify_column(event.x)
        if col == "#2":
            x, y, w, h = tree.bbox(item, col)
            val = tree.item(item, "values")[1]
            entry = tk.Entry(tree)
            entry.place(x=x, y=y, width=w, height=h)
            entry.insert(0, val)
            entry.focus()
            entry.bind("<Return>", lambda e: self.save_edit(entry, item))
            entry.bind("<FocusOut>", lambda e: entry.destroy())

    def handle_clear_all(self):
        """Total system reset"""
        if not messagebox.askyesno("Confirm Reset", "Clear all loaded data, models, and results?"):
            return

        self.data_path = None
        self.data_manager.uploaded_df = None
        self.data_manager.prediction_results = None
        self.model_manager.reset_analytics()

        # Clear UI
        self._refresh_data_tree()
        self.tab_input.refresh_features([]) # Truly empty features
        self.dashboard.update_data_info(0, 0, 0)
        self.dashboard.update_metrics(0, 0, "Cleared", triage="Pending", consensus="N/A")
        self.dashboard.update_status("All tables and features cleared", "#64748B")

        # Reset analysis tab text
        self.tab_analysis.text.config(state=tk.NORMAL)
        self.tab_analysis.text.delete("1.0", tk.END)
        self.tab_analysis.update_metrics_default()
        self.tab_analysis.text.config(state=tk.DISABLED)

    def save_edit(self, entry, item):
        new_val = entry.get()
        vals = list(self.tab_input.tree.item(item, "values"))
        vals[1] = new_val
        self.tab_input.tree.item(item, values=vals)
        entry.destroy()

        # --- What-If Clinical Simulator ---
        # Automatically update metrics in the background when a value is changed
        self.handle_predict_single(silent=True)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CancerDetectionApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user.")
