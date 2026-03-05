import tkinter as tk
from tkinter import ttk

class Sidebar(ttk.Frame):
    """
    Minimal sidebar: only interactive controls that require constant access.
    All data management & analytics are in the menubar.
    """
    def __init__(self, parent, callbacks):
        super().__init__(parent, style='Sidebar.TFrame', width=220)
        self.callbacks = callbacks
        self.pack_propagate(False)
        self._create_widgets()

    def _create_widgets(self):
        # ── Header ───────────────────────────────────────────────
        ttk.Label(
            self, text="🧬 AI Engine",
            style='Sidebar.TLabel'
        ).pack(pady=(28, 18), padx=10)

        # ── Model Selector ───────────────────────────────────────
        model_frame = ttk.LabelFrame(self, text="ACTIVE MODEL", style='Sidebar.TLabelframe')
        model_frame.pack(fill=tk.X, padx=12, pady=6)

        self.model_var = tk.StringVar(value="Random Forest")
        self.model_combo = ttk.Combobox(
            model_frame, textvariable=self.model_var,
            values=self.callbacks.get('models', ["Random Forest"]),
            state="readonly"
        )
        self.model_combo.pack(fill=tk.X, padx=8, pady=8)

        # ── Batch Controls ───────────────────────────────────────
        batch_frame = ttk.LabelFrame(self, text="BATCH SETTINGS", style='Sidebar.TLabelframe')
        batch_frame.pack(fill=tk.X, padx=12, pady=6)

        ttk.Label(batch_frame, text="Sample Quantity:", style='SidebarCaption.TLabel').pack(anchor=tk.W, padx=8, pady=(6, 2))
        self.sample_qty = tk.IntVar(value=20)
        tk.Spinbox(batch_frame, from_=1, to=1000, textvariable=self.sample_qty).pack(fill=tk.X, padx=8, pady=(0, 8))

        # ── Predictions ──────────────────────────────────────────
        pred_frame = ttk.LabelFrame(self, text="PREDICTIONS", style='Sidebar.TLabelframe')
        pred_frame.pack(fill=tk.X, padx=12, pady=6)

        ttk.Button(pred_frame, text="▶  Single Prediction",
                   command=self.callbacks.get('predict_single')).pack(fill=tk.X, padx=8, pady=(6, 3))
        ttk.Button(pred_frame, text="⚡  Batch Prediction",
                   command=self.callbacks.get('predict_file')).pack(fill=tk.X, padx=8, pady=(3, 8))

        # ── Quick XAI ────────────────────────────────────────────
        xai_frame = ttk.LabelFrame(self, text="QUICK XAI", style='Sidebar.TLabelframe')
        xai_frame.pack(fill=tk.X, padx=12, pady=6)

        ttk.Button(xai_frame, text="Local Explainability",
                   command=self.callbacks.get('viz_feat')).pack(fill=tk.X, padx=8, pady=(6, 3))
        ttk.Button(xai_frame, text="Global SHAP",
                   command=self.callbacks.get('viz_shap')).pack(fill=tk.X, padx=8, pady=(3, 8))
