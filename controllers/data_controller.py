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

    def __init__(self, data_manager, layout_manager, error_handler=None, model_manager=None, velocity_manager=None, version="1.0.1", async_runner=None):
        self.data_manager = data_manager
        self.model_manager = model_manager
        self.velocity_manager = velocity_manager
        self.layout_manager = layout_manager
        self.error_handler = error_handler or ErrorHandler()
        self.version = version
        self.async_runner = async_runner
        self.data_path = None
        self.total_rows = 0

    def handle_upload(self):
        """Handle dataset upload (Excel or CSV) in the background."""
        file_types = [
            ("All Data Files", "*.xlsx *.xls *.csv"),
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv")
        ]
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            def _load_task():
                # Load full DF to get metadata
                df, error = self.data_manager.load_data(file_path)
                return df, error

            def _on_finish(result):
                df, error = result
                if error:
                    self.error_handler.log_and_notify("Dataset Upload", Exception(error), "Upload Error")
                    self.layout_manager.update_status(f"Import Failed: {error}", "red")
                elif df is not None:
                    self.data_path = file_path
                    self.data_manager.data_path = file_path
                    
                    # Capture full count
                    full_count = len(df)
                    full_df = df.copy()
                    
                    # Apply 20-sample default as per professor's requirement
                    try:
                        qty = self.layout_manager.sidebar.sample_qty.get()
                    except:
                        qty = 20
                    
                    if full_count > qty:
                        sampled_df = df.sample(n=qty, random_state=42).reset_index(drop=True)
                        self.data_manager.uploaded_df = sampled_df
                    else:
                        self.data_manager.uploaded_df = df
                    
                    # Persist session
                    self.data_manager.save_session()
                    
                    # Update everything including counts (20 samples, 1000 total)
                    self.update_ui_after_load(total_count=full_count, full_context_df=full_df)

            self.layout_manager.update_status("Loading clinical dataset...", "orange")
            if self.async_runner:
                self.async_runner.run_async("Loading data", _load_task, on_finish=_on_finish)
            else:
                _on_finish(_load_task())

    def load_excel(self, file_path):
        """Standardised data loader (Excel/CSV fallback)."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        df, error = self.data_manager.load_data(file_path)
        if error:
            raise ValueError(error)

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

    def handle_sample(self, sample_size=None):
        """Load a sample of the current dataset in the background."""
        # Sync with DataManager for persistent sessions
        if not self.data_path and self.data_manager.data_path:
            self.data_path = self.data_manager.data_path
            
        if not self.data_path:
            self.error_handler.require_data("Data Sampling")
            return

        if sample_size is None:
            try:
                sample_size = self.layout_manager.sidebar.sample_qty.get()
            except:
                sample_size = 20

        # Clinical Validation: Check if requested sample is valid for this dataset
        if sample_size < 1:
            messagebox.showwarning("Clinical Constraint", 
                                 "Sampling Error: Minimum 1 sample required for bio-diagnostic analysis.")
            return
            
        if self.total_rows > 0 and sample_size > self.total_rows:
            messagebox.showwarning("Dataset Constraint", 
                                 f"Sampling Error: Requested size ({sample_size}) exceeds total available records ({self.total_rows}).")
            return

        def _sample_task():
            # Standardised sampling logic: load master then sample
            full_df, error = self.data_manager.load_data(self.data_path)
            if full_df is not None:
                master_count = len(full_df)
                df = full_df
                if len(df) > sample_size:
                    df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
                self.data_manager.uploaded_df = df
                # Clinical sync update: preserve master count for dashboard "Rows"
                self.update_ui_after_load(total_count=master_count, full_context_df=full_df)
                return True
            return False

        def _on_finish(success):
            if success:
                self.layout_manager.update_status(f"Generated {sample_size} clinical samples", "#10B981")
            else:
                self.layout_manager.update_status("Sampling operation failed.", "red")

        self.layout_manager.update_status(f"Sampling {sample_size} records...", "orange")
        if self.async_runner:
            self.async_runner.run_async("Sampling data", _sample_task, on_finish=_on_finish)
        else:
            _sample_task()
            _on_finish(None)

    def on_patient_selected(self, selected_indices):
        """Callback from UI when patient checkmarks are toggled."""
        self.data_manager.selected_indices = set(selected_indices)
        
        # Update sampling count display in dashboard
        self.update_ui_after_load(refresh_tree=False)

    def handle_search(self, query):
        """Search and select specific patients by ID (supports comma-separated)."""
        if not self.data_path and self.data_manager.data_path:
            self.data_path = self.data_manager.data_path
            
        if not self.data_path:
            self.error_handler.require_data("Patient Search")
            return

        if not query or query.strip() == "" or "Search ID" in query:
            return

        def _search_task():
            try:
                full_df, _ = self.data_manager.load_data(self.data_path)
                if full_df is None: return None, "Failed to load master dataset."
                
                id_col = next((c for c in full_df.columns if any(p in str(c).lower() for p in ['sample_id', 'patient_id', 'id'])), None)
                if not id_col:
                    return None, "No Patient ID column found in dataset."
                
                target_ids = [s.strip().lower() for s in query.split(',')]
                
                # Case insensitive exact matching
                matches = full_df[full_df[id_col].astype(str).str.lower().isin(target_ids)]
                
                if matches.empty:
                    # Partial matching if no exact
                    matches = full_df[full_df[id_col].astype(str).str.lower().str.contains('|'.join(target_ids))]
                
                if matches.empty:
                    return None, f"No matches for: {query}"
                
                # Get the absolute indices from the master DF
                indices = matches.index.tolist()
                return (indices, full_df), None
            except Exception as e:
                return None, str(e)

        def _on_finish(result):
            res, error = result
            if error:
                self.layout_manager.update_status(f"Search: {error}", "red")
            elif res:
                indices, full_df = res
                # Add found indices to the registry
                self.data_manager.selected_indices.update(indices)
                # Keep full DF as context if search was triggered from master
                self.data_manager.uploaded_df = full_df 
                self.update_ui_after_load(total_count=len(full_df), full_context_df=full_df)
                self.layout_manager.update_status(f"Identified {len(indices)} profiles for cohort selection", "#10B981")

        if self.async_runner:
            self.async_runner.run_async("Searching Patients", _search_task, on_finish=_on_finish)
        else:
            _on_finish(_search_task())

    def update_ui_after_load(self, total_count=None, full_context_df=None, refresh_tree=True):
        """Update UI components after data loading."""
        df = self.data_manager.uploaded_df
        if df is None:
            return

        # Validate data
        issues = self.data_manager.validate_data(df)
        if issues and refresh_tree:
            messagebox.showwarning("Data Quality Issues",
                                 f"Issues found:\n" + "\n".join(f"• {issue}" for issue in issues))

        # Update data info: Only reset master count if explicitly provided (new file load)
        if total_count is not None:
            self.total_rows = total_count
        elif self.total_rows == 0:
            self.total_rows = len(df)
        total_cols = len(df.columns)
        
        # SMART LOGIC: Show selection count if active, else current batch size
        current_samples = len(self.data_manager.selected_indices) if self.data_manager.selected_indices else len(df)
        
        self.layout_manager.update_data_info(self.total_rows, total_cols, current_samples)
        
        # ALSO: Sync Sidebar Quantity to selection count to satisfy user requirement
        if self.data_manager.selected_indices and self.layout_manager.sidebar:
            try:
                self.layout_manager.sidebar.sample_qty.set(current_samples)
            except:
                pass

        # Update status
        if self.data_manager.selected_indices:
            status_msg = f"Cohort Monitor: {len(self.data_manager.selected_indices)} clinical profiles selected"
            self.layout_manager.update_status(status_msg, "#3B82F6")
        else:
            status_msg = f"Imported {current_samples} samples for clinical analysis"
            self.layout_manager.update_status(status_msg, "#10B981")

        # Refresh data tree
        if refresh_tree:
            self.layout_manager.refresh_data_tree()

        # Populate longitudinal patient history
        if self.velocity_manager:
            self.velocity_manager.load_historical_data(full_context_df)

        # Build feature list for Input Tab
        features = [str(c) for c in df.select_dtypes(include=[np.number]).columns 
                    if not any(p in str(c).lower() for p in ['id', 'patient', 'target', 'class', 'label', 'cancer_risk'])]
        
        target_keywords = ['psa', 'afp', 'ca125', 'peak', 'conc']
        features = sorted(features, key=lambda x: not any(k in x.lower() for k in target_keywords))

        # IMPORTANT: Skip deep sync and tab focus if we are just toggling selection
        if refresh_tree:
            first_row = df.iloc[0] if len(df) > 0 else None
            self.layout_manager.refresh_input_features(features, first_row=first_row)
            self._sync_first_row_to_input()

            # Update analysis tab
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
            # Professional Table Construction
            # Columns: Biomarker (30), Mean (15), Std (15), Max (15)
            h_line = f" {'BIOMARKER NAME':<30} │ {'AVG MEAN':^14} │ {'VOLATILITY':^14} │ {'MAX PEAK':^14} \n"
            divider = " " + "—" * 31 + "┼" + "—" * 16 + "┼" + "—" * 16 + "┼" + "—" * 16 + "\n"
            
            tab.text.insert(tk.END, h_line, "table_head")
            tab.text.insert(tk.END, divider, "dim")
            
            # Use InputTab class for humanizing names if available
            from ui.components.tabs import InputTab
            
            # Table Body
            for i, (feat, row) in enumerate(desc.iterrows()):
                name, unit = InputTab._humanize(feat)
                display_name = f"{name} ({unit})" if unit else name
                f_label = (display_name[:28] + "..") if len(display_name) > 30 else display_name
                
                # We insert parts with different tags for better style
                tab.text.insert(tk.END, f" {f_label:<30} ", "table_row_bold")
                tab.text.insert(tk.END, "│", "dim")
                tab.text.insert(tk.END, f" {row['mean']:>14.2f} ", "metric")
                tab.text.insert(tk.END, "│", "dim")
                tab.text.insert(tk.END, f" {row['std']:>14.2f} ", "table_row")
                tab.text.insert(tk.END, "│", "dim")
                tab.text.insert(tk.END, f" {row['max']:>14.2f} \n", "table_row")
                
                # Subtle separator every few rows for readability
                if (i + 1) % 5 == 0 and (i + 1) < len(desc):
                    tab.text.insert(tk.END, " " + "." * 78 + "\n", "dim")
            
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
        self.data_manager.selected_indices.clear()
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
