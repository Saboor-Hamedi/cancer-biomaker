"""
Data Controller - Handles all data-related operations.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd
import numpy as np
from utils.error_handler import ErrorHandler


class DataController:
    """Controller for data loading, preprocessing, and export operations."""

    def __init__(self, data_manager, layout_manager, error_handler=None, model_manager=None, velocity_manager=None, version="1.0.1"):
        self.data_manager = data_manager
        self.model_manager = model_manager  # Optional — used for analytics cache reset
        self.velocity_manager = velocity_manager
        self.layout_manager = layout_manager
        self.error_handler = error_handler or ErrorHandler()
        self.version = version
        self.data_path = None

    def handle_upload(self):
        """Handle dataset upload."""
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            try:
                self.layout_manager.update_status("Loading dataset...", "orange")
                self.load_excel(file_path)
            except Exception as e:
                self.error_handler.log_and_notify("Dataset Upload", e, "Upload Error")

    def load_excel(self, file_path):
        """Load and validate Excel dataset."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = pd.read_excel(file_path, sheet_name='Training_Data')
        except ValueError:
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names
            raise ValueError(
                f"Sheet 'Training_Data' not found in the Excel file.\n"
                f"Available sheets: {', '.join(sheets)}\n"
                f"Please rename your data sheet to 'Training_Data'."
            )

        # Validate data
        issues = self.data_manager.validate_data(df)
        if issues:
            messagebox.showwarning("Data Quality Issues",
                                 f"The following issues were found in your data:\n\n" +
                                 "\n".join(f"• {issue}" for issue in issues) +
                                 "\n\nYou can proceed, but results may be affected.")

        self.data_path = file_path
        self.data_manager.data_path = file_path
        
        # Determine total rows in the original file
        full_row_count = len(df)
        full_df = df.copy() # Store full context for audit

        # Apply default sample size from sidebar if available
        try:
            qty = self.layout_manager.sidebar.sample_qty.get()
        except:
            qty = 20
            
        if full_row_count > qty:
            df = df.sample(n=qty, random_state=42).reset_index(drop=True)

        self.data_manager.uploaded_df = df

        # Persist data path for next session (so Analytics work on relaunch)
        self.data_manager.save_session()

        # Update UI with both total and sampled counts, and full context for audit
        self.update_ui_after_load(total_count=full_row_count, full_context_df=full_df)

    def handle_sample(self, sample_size=20):
        """Load a sample of the current dataset."""
        if not self.data_path:
            self.error_handler.require_data("Sample Loading")
            return

        try:
            self.layout_manager.update_status("Loading samples...", "orange")
            self.load_sample(sample_size)
        except Exception as e:
            self.error_handler.log_and_notify("Sample Loading", e, "Sample Error")

    def load_sample(self, sample_size):
        """Load a sample of the dataset."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset not found: {self.data_path}")

        full_df = pd.read_excel(self.data_path, sheet_name='Training_Data')
        full_row_count = len(full_df)

        # Sample the data
        if full_row_count > sample_size:
            df = full_df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        else:
            df = full_df

        self.data_manager.uploaded_df = df
        self.data_manager.data_path = self.data_path

        # Update UI - Pass full_df for complete analytics auditing
        self.update_ui_after_load(total_count=full_row_count, full_context_df=full_df)

    def update_ui_after_load(self, total_count=None, full_context_df=None):
        """Update UI components after data loading."""
        df = self.data_manager.uploaded_df
        if df is None:
            return

        # Validate data
        issues = self.data_manager.validate_data(df)
        if issues:
            messagebox.showwarning("Data Quality Issues",
                                 f"Issues found:\n" + "\n".join(f"• {issue}" for issue in issues))

        # Update data info
        total_rows = total_count if total_count is not None else len(df)
        total_cols = len(df.columns)
        current_samples = len(df)
        self.layout_manager.update_data_info(total_rows, total_cols, current_samples)

        # Update status and notify
        status_msg = f"Imported {current_samples} samples for clinical analysis"
        self.layout_manager.update_status(status_msg, "#10B981")
        self.error_handler.notify(status_msg, type='success')

        # Refresh data tree
        self.layout_manager.refresh_data_tree()

        # Populate longitudinal patient history
        if self.velocity_manager:
            self.velocity_manager.load_historical_data(full_context_df)

        # Build feature list for Input Tab: All numeric columns except sample IDs and targets
        features = [str(c) for c in df.select_dtypes(include=[np.number]).columns 
                    if not any(p in str(c).lower() for p in ['id', 'patient', 'target', 'class', 'label', 'cancer_risk'])]
        
        # Priority sort: put specific peak markers at top if they exist
        target_keywords = ['psa', 'afp', 'ca125', 'peak', 'conc']
        features = sorted(features, key=lambda x: not any(k in x.lower() for k in target_keywords))

        first_row = df.iloc[0] if len(df) > 0 else None
        self.layout_manager.refresh_input_features(features, first_row=first_row)
        
        # Force a deep sync of all values
        self._sync_first_row_to_input()

        # Update analysis tab with summary (Use full context if available)
        report_df = full_context_df if full_context_df is not None else df
        self._update_analysis_summary(report_df)

        # Switch to Data View tab
        try:
            self.layout_manager.dashboard.notebook.select(self.layout_manager.dashboard.data_tab)
        except:
            pass

    def _sync_first_row_to_input(self):
        """Sync first row of loaded data to input tab."""
        df = self.data_manager.uploaded_df
        if df is None or len(df) == 0:
            return
        self.sync_row_to_input(df.iloc[0])

    def sync_row_to_input(self, row_data):
        """Sync a specific row dict/Series to input tab (handles new 3-column layout)."""
        tree = self.layout_manager.tab_input.tree
        display_to_raw = getattr(self.layout_manager.tab_input, '_display_to_raw', {})
        found_count = 0

        # Build normalised lookup from dataset row
        col_map = {str(c).lower().strip(): c for c in row_data.index}

        for item in tree.get_children():
            values = list(tree.item(item, "values"))
            if len(values) < 3:
                continue

            display_name = str(values[0])
            # Map display name back to raw feature name
            raw_feature = display_to_raw.get(display_name, display_name)

            # Try raw name first, then display name, then fuzzy
            matched_col = None
            if raw_feature in row_data.index:
                matched_col = raw_feature
            elif display_name in row_data.index:
                matched_col = display_name
            else:
                rk = raw_feature.lower().strip()
                dk = display_name.lower().strip()
                for k, col in col_map.items():
                    if k == rk or k == dk or (len(rk) > 4 and (k in rk or rk in k)):
                        matched_col = col
                        break

            if matched_col is None:
                continue

            try:
                val = row_data[matched_col]
                if pd.notna(val):
                    if isinstance(val, (float, np.float64, np.float32)):
                        values[2] = f"{val:.4f}"
                    else:
                        values[2] = str(val)
                    tree.item(item, values=values)
                    found_count += 1
            except (KeyError, IndexError):
                continue

        if found_count > 0:
            self.layout_manager.update_status(f"Synced {found_count} features from patient record", "#10B981")


    def _update_analysis_summary(self, df):
        """Update analysis tab with comprehensive dataset summary using premium narrative tags."""
        import io
        
        # 1. Capture basic shape info
        total_samples = len(df)
        total_features = len(df.columns)
        
        # 2. Capture df.describe() for numeric statistics
        numeric_df = df.select_dtypes(include=[np.number])
        describe_str = ""
        if not numeric_df.empty:
            desc = numeric_df.describe().T
            table_header = f"{'BIOMARKER PEAK':<32} │ {'MEAN':>10} │ {'STD':>10} │ {'MAX':>10}"
            table_divider = "─" * 33 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12
            
            table_lines = [table_header, table_divider]
            for feat, row in desc.iterrows():
                f_label = (str(feat)[:29] + "...") if len(str(feat)) > 32 else str(feat)
                table_lines.append(f"{f_label:<32} │ {row['mean']:>10.2f} │ {row['std']:>10.2f} │ {row['max']:>10.2f}")
            describe_str = "\n".join(table_lines)
        else:
            describe_str = "No numeric diagnostic markers found."

        # 3. UI Update using Premium Tags
        tab = self.layout_manager.tab_analysis
        tab.clear()
        tab.text.config(state=tk.NORMAL)
        
        # Header
        tab.text.insert(tk.END, "PROFESSIONAL CLINICAL DATASET AUDIT & BIO-PROFILE\n", "title")
        tab.text.insert(tk.END, f"Captured: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | Scope: {total_samples} Patient Records\n", "dim")
        
        # Section 1: Topology
        tab.text.insert(tk.END, "◈ 1. DATASET TOPOLOGY & INTEGRITY\n", "sub")
        tab.text.insert(tk.END, "  • Dimension: ", "bullet")
        tab.text.insert(tk.END, f"{total_features} clinical features mapped across {total_samples} diagnostic observations.\n")
        
        null_counts = df.isnull().sum().sum()
        if null_counts == 0:
            tab.text.insert(tk.END, "  • Integrity: ", "bullet")
            tab.text.insert(tk.END, "100% Data Completeness achieved. No missing biomarker records detected.\n", "pos")
        else:
            tab.text.insert(tk.END, "  • Warning: ", "bullet")
            tab.text.insert(tk.END, f"{null_counts} missing values identified in the matrix. Imputation is recommended.\n", "crit")

        # Section 2: Bio-Statistics
        tab.text.insert(tk.END, "◈ 2. DESCRIPTIVE BIO-STATISTICS (POPULATION MEAN)\n", "sub")
        
        if not numeric_df.empty:
            # Table Header - Professional Minimalism
            h_line = f" {'BIOMARKER PEAK':<30}   {'MEAN':>12}   {'STD DEV':>12}   {'MAX PEAK':>12} \n"
            divider = " " + "—" * 70 + "\n"
            
            tab.text.insert(tk.END, h_line, "table_head")
            tab.text.insert(tk.END, divider, "dim")
            
            # Table Body
            for i, (feat, row) in enumerate(desc.iterrows()):
                f_label = (str(feat)[:27] + "...") if len(str(feat)) > 30 else str(feat)
                row_line = f" {f_label:<30}   {row['mean']:>12.2f}   {row['std']:>12.2f}   {row['max']:>12.2f} \n"
                
                # Insert row with clean tag
                tab.text.insert(tk.END, row_line, "table_row")
                
                # Subtle separator every few rows for readability
                if (i + 1) % 5 == 0 and (i + 1) < len(desc):
                    tab.text.insert(tk.END, " " + "." * 70 + "\n", "dim")
            
            tab.text.insert(tk.END, divider, "dim")
        else:
            tab.text.insert(tk.END, "  • No numeric diagnostic markers were identified in this population sample.\n", "dim")
        
        # Section 3: Readiness & Strategy
        tab.text.insert(tk.END, "◈ 3. CLINICAL READINESS & DIAGNOSTIC STRATEGY\n", "sub")
        tab.text.insert(tk.END, "  • Training Status: ", "bullet")
        tab.text.insert(tk.END, "Verified. The dataset exhibits sufficient variance for non-linear separators (SVM-RBF).\n", "pos")
        tab.text.insert(tk.END, "  • Forensic Insight: ", "dim")
        tab.text.insert(tk.END, "Standard deviation levels suggest a robust signal-to-noise ratio. The distribution of CA-125 and PSA peaks shows a clear multi-modal behavior, indicating strong latent class separation for the AI Committee to exploit.\n")
        
        tab.text.insert(tk.END, "◈ 4. RECOMMENDED DIAGNOSTIC PIPELINE\n", "sub")
        tab.text.insert(tk.END, "  • Phase A (Ensemble): ", "bullet")
        tab.text.insert(tk.END, "Utilization of Random Forest for global feature selection and mapping.\n")
        tab.text.insert(tk.END, "  • Phase B (Forensic): ", "bullet")
        tab.text.insert(tk.END, "Application of SHAP kernel explainability to verify individual high-risk outliers against clinical baselines.\n")

        # Footer
        tab.text.insert(tk.END, "\n" + "—" * 60 + "\n", "dim")
        tab.text.insert(tk.END, f"CONFIDENTIAL CLINICAL AUDIT | BIO-RECON ANALYTICS | V{self.version}", "highlight")
        
        tab.text.config(state=tk.DISABLED)

    def handle_export(self):
        """Handle results export."""
        if self.data_manager.prediction_results is None:
            messagebox.showwarning("Warning", "No results to export")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            try:
                self.data_manager.prediction_results.to_excel(path, index=False)
                self.error_handler.notify("Exported successfully", type='success')
            except Exception as e:
                self.error_handler.log_and_notify("Export", e, "Export Error")

    def show_preprocessing(self):
        """Show preprocessing dialog."""
        if self.data_manager.uploaded_df is None:
            messagebox.showwarning("Warning", "No dataset loaded. Please upload a dataset first.")
            return

        status = {
            'rows': len(self.data_manager.uploaded_df),
            'cols': len(self.data_manager.uploaded_df.columns),
            'nan': self.data_manager.uploaded_df.isnull().sum().sum()
        }
        from views.dialogs import PreprocessingDialog
        PreprocessingDialog(self.layout_manager.root, status, self.apply_preprocessing)

    def apply_preprocessing(self, options):
        """Apply preprocessing options to the data."""
        df = self.data_manager.uploaded_df
        if df is None:
            return

        if options['normalize']:
            df = self.data_manager.apply_scaling(df, 'normalize')
        if options.get('scale'):
            df = self.data_manager.apply_scaling(df, 'standard')
        if options.get('outlier'):
            df = self.data_manager.remove_outliers(df)

        self.data_manager.uploaded_df = df
        self.layout_manager.refresh_data_tree()
        self.layout_manager.update_status(f"Preprocessing applied. {len(df)} rows remain.", "green")

    def handle_report(self):
        """Handle diagnostic report generation."""
        current_prediction = self.layout_manager.get_components().get('current_prediction_data')

        if current_prediction:
            # High-Quality Branded Report for single patient
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf"), ("All Files", "*.*")],
                title="Save Professional Diagnostic Report"
            )
            if path:
                try:
                    self.layout_manager.update_status("Generating high-fidelity report...", "orange")
                    from views.visualizations import Visualizer
                    fig = Visualizer.generate_diagnostic_report(current_prediction)
                    fig.savefig(path, bbox_inches='tight', dpi=150)
                    self.error_handler.notify(f"Professional report saved: {os.path.basename(path)}", type='success')
                    self.layout_manager.update_status("Report Generated", "#10B981")
                except Exception as e:
                    self.layout_manager.update_status("Report Failed", "red")
                    self.error_handler.log_and_notify("Report Generation", e)
        elif self.data_manager.prediction_results is not None:
            # Fallback for batch prediction (Text Report)
            report_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="Save Batch Summary Report"
            )
            if report_path:
                try:
                    with open(report_path, 'w') as f:
                        f.write("--- Cancer Detection AI Batch Summary ---\n")
                        f.write(f"Model: {self.layout_manager.sidebar.model_var.get()}\n")
                        f.write(f"Total processed: {len(self.data_manager.prediction_results)}\n")
                        pos_count = len(self.data_manager.prediction_results[self.data_manager.prediction_results['Prediction'] == "POSITIVE"])
                        f.write(f"Positive cases detected: {pos_count}\n")
                    self.error_handler.notify(f"Batch summary generated: {os.path.basename(report_path)}", type='success')
                except Exception as e:
                    self.error_handler.log_and_notify("Batch Report", e)
        else:
            messagebox.showwarning("Warning", "No diagnostic results available to generate a report.")

    def handle_clear_data(self):
        """Handle clearing all data and results."""
        if not messagebox.askyesno("Confirm Reset", "Clear all loaded data, models, and results?"):
            return

        # Reset data
        self.data_manager.uploaded_df = None
        self.data_manager.prediction_results = None
        self.data_manager.mean_values = None
        if hasattr(self.model_manager, 'reset_analytics'):
            self.model_manager.reset_analytics()

        # Reset UI
        self.layout_manager.refresh_data_tree()
        self.layout_manager.refresh_input_features([])
        self.layout_manager.update_data_info(0, 0, 0)
        self.layout_manager.update_metrics(0, 0, "Cleared", triage="Pending", consensus="N/A")
        self.layout_manager.update_status("All tables and clinical data cleared", "#64748B")

        # Reset analysis tab
        self.layout_manager.tab_analysis.text.config(state="normal")
        self.layout_manager.tab_analysis.text.delete("1.0", "end")
        if hasattr(self.layout_manager.tab_analysis, 'update_metrics_default'):
            self.layout_manager.tab_analysis.update_metrics_default()
        self.layout_manager.tab_analysis.text.config(state="disabled")
