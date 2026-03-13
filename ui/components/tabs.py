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

        columns = ("Feature", "Value", "Unit", "Description")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        # Style headings
        for col in columns:
            self.tree.heading(col, text=col.upper())
            width = 150
            if col == "Description": width = 350
            if col == "Unit": width = 100
            self.tree.column(col, width=width)

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

        key_metadata = {
            'mean_current_smooth': {'unit': 'nA', 'desc': 'Avg current across signal'},
            'std_current_smooth': {'unit': 'nA', 'desc': 'Signal noise/variability'},
            'area_under_curve_smooth': {'unit': 'nA·V', 'desc': 'Integrated signal energy'},
            'PSA_smooth_peak_current': {'unit': 'nA', 'desc': 'Primary PSA peak height'},
            'PSA_smooth_peak_potential': {'unit': 'V', 'desc': 'PSA redox potential'},
            'PSA_smooth_peak_area': {'unit': 'nA·V', 'desc': 'PSA charge transfer'},
            'PSA_concentration_pg_per_ml': {'unit': 'pg/mL', 'desc': 'PSA Protein Concentration'},
            'AFP_concentration_pg_per_ml': {'unit': 'pg/mL', 'desc': 'AFP Protein Concentration'},
            'CA125_concentration_U_per_ml': {'unit': 'U/mL', 'desc': 'CA125 Protein Concentration'},
            'mean_slope_smooth': {'unit': 'nA/V', 'desc': 'Avg sensitivity slope'},
            'avg_snr': {'unit': 'dB', 'desc': 'Signal-to-Noise Ratio'}
        }

        # Shared units for current measurements
        for i in range(-5, 10):
            v = i/10.0
            key_metadata[f'current_smooth_{v}V'] = {'unit': 'nA', 'desc': f'Current at {v}V'}

        for f in self.features:
            meta = key_metadata.get(f, {'unit': '-', 'desc': 'Clinical biomarker'})
            unit = meta['unit']
            desc = meta['desc']
            
            val = '0.0'
            if first_row is not None and f in first_row.index:
                val_raw = first_row[f]
                try:
                    val = str(round(float(val_raw), 4))
                except:
                    val = str(val_raw)
            self.tree.insert("", tk.END, values=(f, val, unit, desc))

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
