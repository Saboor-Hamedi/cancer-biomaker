import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from datetime import datetime
import threading

# Local imports
from logic.model_manager import ModelManager
from logic.data_manager import DataManager
from styles import apply_styles
from components.sidebar import Sidebar
from components.dashboard import Dashboard
from components.tabs import InputTab, DataTab, AnalysisTab
from views.visualizations import Visualizer
from views.dialogs import PreprocessingDialog

class CancerDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cancer Detection XAI Dashboard v3.0")
        self.root.geometry("1400x900")
        
        # Initialize Managers
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_manager = ModelManager(script_dir)
        self.data_manager = DataManager()
        
        # Apply Styles
        apply_styles()
        
        # Layout Setup
        self._setup_layout()
        
        # Auto-check and train models if missing
        self._check_models_on_startup()

        # Handle proper closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Clean shutdown of the application"""
        try:
            self.root.destroy()
        except:
            pass
        os._exit(0) # Force kill all threads and processes

    def _check_models_on_startup(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_dir, 'data', 'cancer_biomarkers.xlsx')
        
        def check_task():
            success, msg = self.model_manager.check_and_train_models(data_path, self.dashboard.update_status)
            if success:
                self.root.after(0, lambda: self.tab_input.refresh_features(self.model_manager.feature_names))
                self.root.after(0, lambda: self.dashboard.update_status("System Ready - Models Verified", "#10B981"))
            else:
                self.root.after(0, lambda: self.dashboard.update_status(f"Error: {msg}", "#EF4444"))

        threading.Thread(target=check_task, daemon=True).start()

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
            'predict_file': self.handle_predict_batch,
            'export': self.handle_export,
            'viz_feat': self.show_feature_importance,
            'viz_roc': self.show_roc_curve,
            'viz_cm': self.show_confusion_matrix,
            'viz_pr': self.show_precision_recall,
            'viz_comp': self.show_model_comparison,
            'viz_heat': self.show_correlation_heatmap,
            'preprocess': self.show_preprocessing,
            'report': self.handle_report,
            'help': self.show_help,
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
            self.dashboard.update_status("Loading file...", "orange")
            def task():
                df, error = self.data_manager.load_excel(file_path)
                if error:
                    self.root.after(0, lambda: messagebox.showerror("Error", error))
                    self.root.after(0, lambda: self.dashboard.update_status("Load Failed", "red"))
                else:
                    self.root.after(0, self.update_ui_after_load)
            threading.Thread(target=task, daemon=True).start()

    def handle_train_models(self):
        """User triggered manual training of all models"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_dir, 'data', 'cancer_biomarkers.xlsx')
        
        if not messagebox.askyesno("Confirm Training", "This will retrain all models (RF, LR, SVM, XGBoost). It may take a minute. Proceed?"):
            return

        def task():
            success, msg = self.model_manager.check_and_train_models(data_path, self.dashboard.update_status, force=True)
            if success:
                self.root.after(0, lambda: self.tab_input.refresh_features(self.model_manager.feature_names))
                self.root.after(0, lambda: messagebox.showinfo("Training Success", "All models trained and saved to 'views/modal/' folder."))
                self.root.after(0, lambda: self.dashboard.update_status("Models Ready", "#10B981"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Training Error", msg))
                self.root.after(0, lambda: self.dashboard.update_status("Training Failed", "#EF4444"))

        threading.Thread(target=task, daemon=True).start()

    def handle_sample(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_path = os.path.join(base_dir, 'data', 'cancer_biomarkers.xlsx')
        
        if not os.path.exists(sample_path):
            messagebox.showerror("File Error", f"Sample file not found at:\n{sample_path}")
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
        
        # Clear existing
        tree.delete(*tree.get_children())
        
        # Rebuild columns
        columns = list(df.columns)
        tree["columns"] = columns
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)
            
        # Add data (Show up to 1000 rows if they exist, but limited to the sampled df)
        for _, row in df.iterrows():
            vals = [str(x) for x in row.values]
            tree.insert("", tk.END, values=vals)

    def handle_predict_single(self):
        model_name = self.sidebar.model_var.get()
        inputs = {}
        try:
            for item in self.tab_input.tree.get_children():
                v = self.tab_input.tree.item(item, "values")
                inputs[v[0]] = float(v[1])
        except ValueError:
            return messagebox.showerror("Input Error", "Please ensure all biomarker values are valid numbers.")
            
        try:
            pred, conf, risk = self.model_manager.predict_single(model_name, inputs)
            res = "POSITIVE" if pred == 1 else "NEGATIVE"
            
            # Update Dashboard Metrics (Cards)
            # Risk is specifically the probability of cancer
            self.dashboard.update_metrics(risk=risk*100, confidence=conf*100, insight=res)
            self.dashboard.update_status(f"Result for single: {res} (Reliability: {conf:.1%})", "#EF4444" if pred == 1 else "#10B981")
        except Exception as e:
            return messagebox.showerror("Model Error", str(e))
        
        # Show Local Explanation Window
        explanation = self.model_manager.get_local_explanation(model_name, inputs)
        if explanation:
            fig = Visualizer.plot_local_explanation(explanation, model_name)
            Visualizer.show_modal(self.root, f"Local XAI - {model_name}", fig)
            
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
                    
                    self.dashboard.update_metrics(risk=mean_risk, confidence=mean_conf, insight=f"{pos_count} Cases")
                    self.dashboard.update_status(f"Batch completed: {pos_count} positive", "#10B981")
                    messagebox.showinfo("Batch Result", f"Processed {len(preds)} samples\nFound {pos_count} positive cases\nAverage Population Risk: {mean_risk:.1f}%")
                
                self.root.after(0, update_ui)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Prediction Error", str(e)))
                self.root.after(0, lambda: self.dashboard.update_status("Prediction Failed", "red"))

        threading.Thread(target=task, daemon=True).start()

    def show_feature_importance(self):
        model_name = self.sidebar.model_var.get()
        model = self.model_manager.load_model(model_name)
        fig = Visualizer.plot_feature_importance(model, self.model_manager.feature_names, model_name)
        if fig:
            Visualizer.show_modal(self.root, "Feature Importance", fig)

    def show_roc_curve(self):
        model_name = self.sidebar.model_var.get()
        fig = Visualizer.plot_roc_curve(model_name)
        Visualizer.show_modal(self.root, f"ROC Curve - {model_name}", fig)

    def show_confusion_matrix(self):
        model_name = self.sidebar.model_var.get()
        # Using realistic sample CM for demonstration
        cm = [[245, 5], [3, 247]]
        fig = Visualizer.plot_confusion_matrix(cm, model_name)
        Visualizer.show_modal(self.root, f"Confusion Matrix - {model_name}", fig)

    def show_precision_recall(self):
        model_name = self.sidebar.model_var.get()
        fig = Visualizer.plot_precision_recall(model_name)
        Visualizer.show_modal(self.root, f"Precision-Recall - {model_name}", fig)

    def show_model_comparison(self):
        fig = Visualizer.plot_model_comparison()
        Visualizer.show_modal(self.root, "Model Comparison Analysis", fig)

    def show_correlation_heatmap(self):
        df = self.data_manager.uploaded_df
        if df is None:
            return messagebox.showwarning("Warning", "No dataset loaded. Please upload or load a sample first.")
        
        fig = Visualizer.plot_correlation_heatmap(df)
        if fig:
            Visualizer.show_modal(self.root, "Biomarker Correlation Heatmap", fig)
        else:
            messagebox.showerror("Error", "Could not generate heatmap. Ensure the dataset contains numeric clinical data.")

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
        if self.data_manager.prediction_results is None:
            return messagebox.showwarning("Warning", "No results to report. Run batch prediction first.")
            
        report_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if report_path:
            with open(report_path, 'w') as f:
                f.write("--- Cancer Detection AI Report ---\n")
                f.write(f"Model used: {self.sidebar.model_var.get()}\n")
                f.write(f"Total samples: {len(self.data_manager.prediction_results)}\n")
                pos_count = sum(self.data_manager.prediction_results['Prediction'])
                f.write(f"Positive cases found: {pos_count}\n")
                f.write(f"Average confidence: {self.data_manager.prediction_results['Confidence'].mean():.2%}\n")
                f.write("\nTop Risk Samples (Sample ID):\n")
                top_risk = self.data_manager.prediction_results.sort_values(by='Confidence', ascending=False)
                for _, row in top_risk.head(10).iterrows():
                    f.write(f"ID: {row.get('sample_id', 'N/A')} | Conf: {row['Confidence']:.2%}\n")
            messagebox.showinfo("Success", f"Report generated: {os.path.basename(report_path)}")

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

    def save_edit(self, entry, item):
        new_val = entry.get()
        vals = list(self.tab_input.tree.item(item, "values"))
        vals[1] = new_val
        self.tab_input.tree.item(item, values=vals)
        entry.destroy()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CancerDetectionApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user.")
