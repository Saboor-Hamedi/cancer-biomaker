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

        self.data_manager.uploaded_df = df
        self.data_path = file_path
        self.data_manager.data_path = file_path

        # Update UI
        self.update_ui_after_load()

    def handle_sample(self, sample_size=100):
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

        df = pd.read_excel(self.data_path, sheet_name='Training_Data')

        # Sample the data
        if len(df) > sample_size:
            # Use a slightly more dynamic sampling (no fixed random_state) to show variety
            df = df.sample(n=sample_size).reset_index(drop=True)

        self.data_manager.uploaded_df = df
        self.data_manager.data_path = self.data_path

        # Update UI
        self.update_ui_after_load()

    def update_ui_after_load(self):
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
        total_rows = len(df)
        total_cols = len(df.columns)
        current_samples = len(df)
        self.layout_manager.update_data_info(total_rows, total_cols, current_samples)

        # Update status and notify
        status_msg = f"Imported {current_samples} samples"
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

        # Update analysis tab with summary
        self._update_analysis_summary(df)

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
        """Update analysis tab with dataset summary."""
        summary = (
            "DATASET SUMMARY & DESCRIPTIVE STATISTICS\n"
            "------------------------------------------------------\n\n"
            f"Total Loaded Samples: {len(df)}\n"
            f"Total Features Evaluated: {len(df.columns)}\n\n"
            "Features Summary (Mean, Std, Min, Max):\n"
        )

        try:
            numeric_cols = df.select_dtypes(include=[float, int]).columns
            if len(numeric_cols) > 0:
                desc = df[numeric_cols].describe()
                for col in numeric_cols[:5]:  # Show first 5 numeric columns
                    if col in desc.columns:
                        summary += f"  {col}: Mean={desc.loc['mean', col]:.2f}, Std={desc.loc['std', col]:.2f}\n"
                if len(numeric_cols) > 5:
                    summary += f"  ... and {len(numeric_cols) - 5} more features\n"
        except Exception as e:
            summary += f"  Error computing statistics: {e}\n"

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
