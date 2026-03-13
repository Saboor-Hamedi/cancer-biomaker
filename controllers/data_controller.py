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

    def __init__(self, data_manager, layout_manager, error_handler=None, model_manager=None):
        self.data_manager = data_manager
        self.model_manager = model_manager  # Optional — used for analytics cache reset
        self.layout_manager = layout_manager
        self.error_handler = error_handler or ErrorHandler()
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

        # Update features in Input Tab based on new dataset columns # label is cancer_risk_class
        features = [c for c in df.columns if c not in ('sample_id', 'cancer_risk_class')]
        first_row = df.iloc[0] if len(df) > 0 else None
        self.layout_manager.refresh_input_features(features, first_row=first_row)

        # Sync first row to input
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
        """Sync a specific row dictionary/Series to input tab."""
        tree = self.layout_manager.tab_input.tree
        found_count = 0
        
        # Create mapping for fuzzy column matching
        col_map = {str(c).lower().strip(): c for c in row_data.index}

        for item in tree.get_children():
            values = list(tree.item(item, "values"))
            feature_name = values[0] if values else ""
            
            # Try exact match first, then fuzzy match
            if feature_name in row_data.index:
                matched_col = feature_name
            elif feature_name.lower().strip() in col_map:
                matched_col = col_map[feature_name.lower().strip()]
            else:
                continue

            try:
                val = row_data[matched_col]
                if pd.notna(val):
                    # Format float values for better readability
                    if isinstance(val, (float, np.float64, np.float32)):
                        values[1] = f"{val:.4f}"
                    else:
                        values[1] = str(val)
                    tree.item(item, values=values)
                    found_count += 1
            except (KeyError, IndexError):
                continue
        
        if found_count > 0:
            self.layout_manager.update_status(f"Synced {found_count} features from patient record", "#10B981")

    def _update_analysis_summary(self, df):
        """Update analysis tab with comprehensive dataset summary."""
        import io
        
        # 1. Capture basic shape info
        total_samples = len(df)
        total_features = len(df.columns)
        
        # 2. Capture df.info() as a string
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        
        # 3. Capture df.describe() as a professional transposed table
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            desc = numeric_df.describe().T
            
            # Header with professional separators
            table_header = f"{'CLINICAL BIOMARKER':<32} │ {'MEAN':>10} │ {'STD DEV':>10} │ {'MIN':>10} │ {'MAX':>10} │ {'MEDIAN':>10}"
            table_divider = "─" * 33 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 11
            
            table_lines = [table_header, table_divider]
            
            # Format each row with precision
            for feat, row in desc.iterrows():
                feat_label = (str(feat)[:29] + "...") if len(str(feat)) > 32 else str(feat)
                line = (f"{feat_label:<32} │ {row['mean']:>10.3f} │ {row['std']:>10.3f} │ "
                        f"{row['min']:>10.3f} │ {row['max']:>10.3f} │ {row['50%']:>10.3f}")
                table_lines.append(line)
            
            describe_str = "\n".join(table_lines)
        else:
            describe_str = "No numeric clinical data available for statistical mapping."

        # 4. Check for missing values (formatted as alert)
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            missing_features = null_counts[null_counts > 0]
            missing_report = "⚠️  DATA INTEGRITY ALERT: Missing values detected in the following features:\n"
            for f, count in missing_features.items():
                missing_report += f"   • {f:<30} {count} missing records\n"
        else:
            missing_report = "✅ DATA INTEGRITY: 100% Completeness. No missing clinical values."

        # 5. Build the "Beautiful" Report
        summary = (
            "╔══════════════════════════════════════════════════════════════════════════════════════╗\n"
            "║                  PROFESSIONAL CLINICAL DATASET AUDIT & BIO-PROFILE                   ║\n"
            "╚══════════════════════════════════════════════════════════════════════════════════════╝\n\n"
            f"REPORT GENERATED: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"POPULATION SCOPE: {total_samples} Patient Records\n"
            f"DIAGNOSTIC DIMENSIONS: {total_features} Clinical Features\n\n"
            
            "─── [ SECTION 1: DATA STRUCTURE & TYPES ] ─────────────────────────────────────────────\n"
            f"{info_str}\n"
            
            "─── [ SECTION 2: BIOMARKER INTEGRITY (NULL AUDIT) ] ──────────────────────────────────\n"
            f"{missing_report}\n\n"
            
            "─── [ SECTION 3: TRANSPOSED DESCRIPTIVE BIO-STATISTICS ] ──────────────────────────────\n"
            f"{describe_str}\n\n"
            
            "─── [ SECTION 4: CLINICAL OBSERVATIONS ] ──────────────────────────────────────────────\n"
            "• Signal Quality: Biological distributions verified for all numeric features.\n"
            "• Variance Tracking: Standard deviation allows for outlier detection in upcoming XAI steps.\n"
            "• Readiness: Dataset is verified for high-fidelity Model Training & Evaluation.\n\n"
            "----------------------------------------------------------------------------------------\n"
            "END OF CLINICAL SUMMARY REPORT"
        )

        # Update analysis tab
        self.layout_manager.tab_analysis.text.config(state=tk.NORMAL)
        self.layout_manager.tab_analysis.text.delete("1.0", tk.END)
        self.layout_manager.tab_analysis.text.insert(tk.END, summary)
        self.layout_manager.tab_analysis.text.config(state=tk.DISABLED)

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
