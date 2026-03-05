import tkinter as tk
from tkinter import ttk

class InputTab(ttk.Frame):
    def __init__(self, parent, features=None):
        super().__init__(parent)
        self.features = features or []
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

    def refresh_features(self, features):
        self.features = features
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        key_descriptions = {
            'PSA_peak_height': 'Peak height of PSA biomarker signal',
            'min_slope': 'Minimum slope in current-voltage curve',
            'PSA_concentration_pg_per_ml': 'PSA concentration in pg/mL',
            'max_slope': 'Maximum slope in current-voltage curve',
            'current_at_-0.46V': 'Current measurement at -0.46V',
            'min_current': 'Minimum current value',
            'PSA_actual_peak_current': 'Actual peak current for PSA',
            'mean_current': 'Average current across measurements',
            'area_under_curve': 'Total area under current curve',
            'peak_height_ratio_PSA_CA125': 'Ratio of PSA to CA125 peak heights'
        }
        
        for f in self.features:
            desc = key_descriptions.get(f, "Additional biomarker feature")
            self.tree.insert("", tk.END, values=(f, '0.0', desc))

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

        self.text = tk.Text(self, font=('Inter', 10), padx=20, pady=20, relief='flat', background="#F8FAFC", foreground="#334155")
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
