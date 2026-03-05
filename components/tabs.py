import tkinter as tk
from tkinter import ttk

class InputTab(ttk.Frame):
    def __init__(self, parent, features=None):
        super().__init__(parent)
        self.features = features or []
        self._create_widgets()

    def _create_widgets(self):
        ttk.Label(self, text="Biomarker Inputs (Double-click to edit)", font=('Arial', 11, 'bold')).pack(pady=10)
        
        columns = ("Feature", "Value", "Description")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        self.tree.heading("Feature", text="Feature")
        self.tree.heading("Value", text="Value")
        self.tree.heading("Description", text="Description")
        
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10))

        # Initial features
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
        # Create a container frame for layout control
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Initialize with dummy columns to ensure it's visible even when empty
        self.tree = ttk.Treeview(container, show="headings", height=20, columns=("status",))
        self.tree.heading("status", text="No data loaded yet")
        self.tree.column("status", width=400, anchor=tk.CENTER)

        vscroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        hscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        
        # Proper grid layout for scrollbars
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
        self.text = tk.Text(self, font=('Courier', 10), padx=10, pady=10)
        scroll = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_metrics_default()

    def update_metrics_default(self):
        self.text.insert(tk.END, "Model Performance (Static Validation Data):\n\n")
        self.text.insert(tk.END, "Random Forest:  99.2% Acc | 99.1% Prec | 99.3% Rec\n")
        self.text.insert(tk.END, "Logistic Reg:   98.8% Acc | 98.7% Prec | 98.9% Rec\n")
        self.text.config(state=tk.DISABLED)
