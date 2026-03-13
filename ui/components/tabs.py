import tkinter as tk
from tkinter import ttk


class InputTab(ttk.Frame):
    def __init__(self, parent, features=None, data_manager=None):
        super().__init__(parent)
        self.features = features or []
        self.data_manager = data_manager
        self._create_widgets()

    def _create_widgets(self):
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="BIOMARKER INPUT FEATURES", font=('Inter', 11, 'bold'), foreground="#1E293B").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="(Double-click values to edit)", font=('Inter', 9), foreground="#64748B").pack(side=tk.LEFT, padx=10)

        columns = ("Feature", "Value", "Description")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        # Style headings
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=150 if col != "Description" else 400)

        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0), pady=(0, 15))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,15), pady=(0, 15))

    def refresh_features(self, features, first_row=None):
        self.features = features
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Use provided first_row, or fall back to dataset/mean_values
        if first_row is None and self.data_manager:
            if self.data_manager.uploaded_df is not None and not self.data_manager.uploaded_df.empty:
                first_row = self.data_manager.uploaded_df.iloc[0]
            elif self.data_manager.mean_values is not None:
                first_row = self.data_manager.mean_values

        key_descriptions = {
            'mean_current_smooth': 'Average current across measurements',
            'std_current_smooth': 'Standard deviation of current measurements',
            'min_current_smooth': 'Minimum current value',
            'max_current_smooth': 'Maximum current value',
            'area_under_curve_smooth': 'Total area under current curve',
            'PSA_smooth_peak_current': 'Actual peak current for PSA',
            'PSA_smooth_peak_potential': 'Peak potential for PSA detection',
            'PSA_smooth_peak_area': 'Peak area for PSA signal',
            'PSA_smooth_fwhm': 'Full width at half maximum for PSA peak',
            'AFP_smooth_peak_current': 'Peak current for AFP biomarker',
            'AFP_smooth_peak_potential': 'Peak potential for AFP detection',
            'AFP_smooth_peak_area': 'Peak area for AFP signal',
            'AFP_smooth_fwhm': 'Full width at half maximum for AFP peak',
            'CA125_smooth_peak_current': 'Peak current for CA125 biomarker',
            'CA125_smooth_peak_potential': 'Peak potential for CA125 detection',
            'CA125_smooth_peak_area': 'Peak area for CA125 signal',
            'CA125_smooth_fwhm': 'Full width at half maximum for CA125 peak',
            'mean_slope_smooth': 'Average slope in current-voltage curve',
            'max_slope_smooth': 'Maximum slope in current-voltage curve',
            'min_slope_smooth': 'Minimum slope in current-voltage curve',
            'current_smooth_-0.46V': 'Current measurement at -0.46V',
            'current_smooth_0.372V': 'Current measurement at 0.372V',
            'current_smooth_0.98V': 'Current measurement at 0.98V',
            'current_smooth_-0.2V': 'Current measurement at -0.2V',
            'current_smooth_0V': 'Current measurement at 0V',
            'current_smooth_0.2V': 'Current measurement at 0.2V',
            'current_smooth_0.5V': 'Current measurement at 0.5V',
            'current_smooth_0.8V': 'Current measurement at 0.8V',
            'current_smooth_0.3V': 'Current measurement at 0.3V',
            'current_smooth_0.6V': 'Current measurement at 0.6V',
            'current_smooth_-0.5V': 'Current measurement at -0.5V',
            'current_smooth_-0.3V': 'Current measurement at -0.3V',
            'avg_snr': 'Average signal-to-noise ratio',
            'peak_separation_PSA_AFP': 'Peak separation between PSA and AFP',
            'peak_separation_AFP_CA125': 'Peak separation between AFP and CA125',
            'peak_separation_PSA_CA125': 'Peak separation between PSA and CA125',
            'overlap_index_PSA_AFP': 'Overlap index between PSA and AFP peaks',
            'overlap_index_PSA_CA125': 'Overlap index between PSA and CA125 peaks',
            'overlap_index_AFP_CA125': 'Overlap index between AFP and CA125 peaks',
            'PSA_concentration_pg_per_ml': 'PSA concentration in pg/mL',
            'AFP_concentration_pg_per_ml': 'AFP concentration in pg/mL',
            'CA125_concentration_U_per_ml': 'CA125 concentration in U/mL'
        }

        for f in self.features:
            desc = key_descriptions.get(f, "Additional biomarker feature")
            val = '0.0'
            if first_row is not None and f in first_row.index:
                val_raw = first_row[f]
                try:
                    val = str(round(float(val_raw), 4))
                except:
                    val = str(val_raw)
            self.tree.insert("", tk.END, values=(f, val, desc))

    def refresh_display(self):
        """Refresh the display with current features."""
        self.refresh_features(self.features)

    def get_table_data(self):
        """Returns a dictionary of feature names and their current values from the table."""
        data = {}
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if len(values) >= 2:
                data[values[0]] = values[1]
        return data

    def update_feature_value(self, feature_name, new_value):
        """Update a specific feature value in the tree."""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            if values[0] == feature_name:
                values[1] = new_value
                self.tree.item(item, values=values)
                break

    def clear_table(self):
        """Sets all values in the table to 0.0."""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            values[1] = "0.0"
            self.tree.item(item, values=values)

class DataTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="DATASET PREVIEW & SELECTION", font=('Inter', 11, 'bold'), foreground="#1E293B").pack(side=tk.LEFT)

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.tree = ttk.Treeview(container, show="headings", height=20, columns=("status",))
        self.tree.heading("status", text="NO DATA LOADED YET")
        self.tree.column("status", width=400, anchor=tk.CENTER)

        vscroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        hscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vscroll.grid(row=0, column=1, sticky='ns')
        hscroll.grid(row=1, column=0, sticky='ew')

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

class AnalysisTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="GLOBAL PERFORMANCE METRICS", font=('Inter', 11, 'bold'), foreground="#1E293B").pack(side=tk.LEFT)

        self.text = tk.Text(self, font=('Consolas', 10), padx=20, pady=20, relief='flat', background="#F8FAFC", foreground="#334155")
        scroll = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0), pady=(0, 15))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,15), pady=(0, 15))

        self.update_metrics_default()

    def update_metrics_default(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        content = (
            "MODEL PERFORMANCE ANALYSIS (Actual Validation Results)\n"
            "------------------------------------------------------\n\n"
            "Waiting for model metrics...\n"
            "Select a model in the sidebar and run analytics to see detailed performance."
        )
        self.text.insert(tk.END, content)
        self.text.config(state=tk.DISABLED)

    def display_metrics(self, metrics, model_name):
        """Displays formatted clinical metrics in the text area"""
        from datetime import datetime
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)

        header = f"CLINICAL PERFORMANCE REPORT: {model_name.upper()}\n"
        header += f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "-" * 54 + "\n\n"

        self.text.insert(tk.END, header)

        for k, v in metrics.items():
            if isinstance(v, float) and v <= 1.0:
                line = f"{k:.<40} {v*100:>10.2f}%\n"
            else:
                line = f"{k:.<40} {v:>10}\n"
            self.text.insert(tk.END, line)

        self.text.insert(tk.END, "\n" + "-" * 54 + "\n")
        self.text.insert(tk.END, "Note: These results are based on the current validation split.")
        self.text.config(state=tk.DISABLED)

    def display_prediction_results(self, result):
        """Displays prediction results for a single patient."""
        from datetime import datetime
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)

        header = "SINGLE PATIENT DIAGNOSTIC REPORT\n"
        header += f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "=" * 54 + "\n\n"

        self.text.insert(tk.END, header)
        
        prediction = result.get('prediction', 'Unknown')
        confidence = result.get('confidence', 0.0)
        risk = result.get('risk', 0.0)
        model = result.get('model', 'Unknown')
        
        status = "POSITIVE" if prediction == 1 else "NEGATIVE"
        color = "#EF4444" if prediction == 1 else "#10B981"

        self.text.insert(tk.END, f"Model Used: {model}\n")
        self.text.insert(tk.END, f"Predicted Class: {status}\n")
        self.text.insert(tk.END, f"Diagnostic Confidence: {confidence:.2%}\n")
        self.text.insert(tk.END, f"Estimated Cancer Risk: {risk:.2%}\n\n")

        self.text.insert(tk.END, "PATIENT BIOMARKER INPUTS:\n")
        inputs = result.get('inputs', {})
        for feat, val in inputs.items():
            self.text.insert(tk.END, f"  • {feat:.<30} {val}\n")

        self.text.insert(tk.END, "\n" + "=" * 54 + "\n")
        self.text.insert(tk.END, "CLINICAL INTERPRETATION:\n")
        if prediction == 1:
            self.text.insert(tk.END, "The AI model has detected patterns strongly associated with high risk.\n")
            self.text.insert(tk.END, "Urgent clinical review and further diagnostic testing recommended.")
        else:
            self.text.insert(tk.END, "The AI model suggests the biomarker profile is within normal ranges.\n")
            self.text.insert(tk.END, "Continue with routine screening as per clinical guidelines.")

        self.text.config(state=tk.DISABLED)
