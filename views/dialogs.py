import tkinter as tk
from tkinter import ttk, messagebox

class PreprocessingDialog:
    def __init__(self, parent, data_status, on_apply):
        self.modal = tk.Toplevel(parent)
        self.modal.title("Preprocessing Options")
        self.modal.geometry("500x400")
        self.on_apply = on_apply

        ttk.Label(self.modal, text="Data Preprocessing", font=('Arial', 12, 'bold')).pack(pady=10)
        
        status_text = f"Samples: {data_status['rows']} | Features: {data_status['cols']} | NaN: {data_status['nan']}"
        ttk.Label(self.modal, text=status_text, foreground="blue").pack(pady=5)

        self.normalize_var = tk.BooleanVar(value=True)
        self.scale_var = tk.BooleanVar(value=False)
        self.outlier_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(self.modal, text="Normalize features (0-1)", variable=self.normalize_var).pack(anchor=tk.W, padx=50, pady=5)
        ttk.Checkbutton(self.modal, text="Standard scaling (z-score)", variable=self.scale_var).pack(anchor=tk.W, padx=50, pady=5)
        ttk.Checkbutton(self.modal, text="Remove outliers (IQR)", variable=self.outlier_var).pack(anchor=tk.W, padx=50, pady=5)

        ttk.Button(self.modal, text="Apply Changes", command=self._apply).pack(pady=20)

    def _apply(self):
        options = {
            'normalize': self.normalize_var.get(),
            'scale': self.scale_var.get(),
            'outlier': self.outlier_var.get()
        }
        self.on_apply(options)
        self.modal.destroy()
