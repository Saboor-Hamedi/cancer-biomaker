import tkinter as tk
from tkinter import ttk

class Sidebar(ttk.Frame):
    def __init__(self, parent, callbacks):
        # We define a fixed width but will let it fill Y
        super().__init__(parent, style='Sidebar.TFrame', width=280)
        self.callbacks = callbacks
        self.pack_propagate(False)

        # Create Canvas for scrolling
        self.canvas = tk.Canvas(self, bg="#DFE6E9", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # This frame will hold the actual content
        self.scrollable_frame = ttk.Frame(self.canvas, style='Sidebar.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=250)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add mousewheel support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._create_widgets()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _create_widgets(self):
        # Header - using self.scrollable_frame now
        ttk.Label(self.scrollable_frame, text="CONTROLS", style='Sidebar.TLabel').pack(pady=15, padx=10)

        # Model Selection Group
        model_frame = ttk.LabelFrame(self.scrollable_frame, text="Model Configuration")
        model_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(model_frame, text="Select Model:").pack(anchor=tk.W, padx=5, pady=2)
        self.model_var = tk.StringVar(value="Random Forest")
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var,
                                       values=["Random Forest", "Logistic Regression", "SVM", "XGBoost"], state="readonly")
        self.model_combo.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(model_frame, text="Sample Qty:").pack(anchor=tk.W, padx=5, pady=2)
        self.sample_qty = tk.IntVar(value=20)
        tk.Spinbox(model_frame, from_=1, to=1000, textvariable=self.sample_qty).pack(fill=tk.X, padx=5, pady=5)

        # Actions Group
        action_frame = ttk.LabelFrame(self.scrollable_frame, text="Actions")
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        buttons = [
            ("📁 Upload Excel", self.callbacks.get('upload')),
            ("🔄 Load Sample", self.callbacks.get('sample')),
            ("🛠 Train All Models", self.callbacks.get('train_models')),
            ("🔮 Predict Single", self.callbacks.get('predict_single')),
            ("📋 Predict File", self.callbacks.get('predict_file')),
            ("💾 Export Results", self.callbacks.get('export'))
        ]

        for text, cmd in buttons:
            ttk.Button(action_frame, text=text, command=cmd).pack(fill=tk.X, padx=5, pady=2)

        # Visualizations Group
        viz_frame = ttk.LabelFrame(self.scrollable_frame, text="Visualizations")
        viz_frame.pack(fill=tk.X, padx=10, pady=5)

        viz_buttons = [
            ("📊 Feature Imp.", self.callbacks.get('viz_feat')),
            ("📈 ROC Curve", self.callbacks.get('viz_roc')),
            ("🔄 Confusion Mat.", self.callbacks.get('viz_cm')),
            ("📉 Prec-Recall", self.callbacks.get('viz_pr')),
            ("📊 Comparison", self.callbacks.get('viz_comp'))
        ]

        for text, cmd in viz_buttons:
            ttk.Button(viz_frame, text=text, command=cmd).pack(fill=tk.X, padx=5, pady=2)

        # Utilities Group
        util_frame = ttk.LabelFrame(self.scrollable_frame, text="Utilities")
        util_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(util_frame, text="🔧 Preprocessing", command=self.callbacks.get('preprocess')).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(util_frame, text="📋 Gen Report", command=self.callbacks.get('report')).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(util_frame, text="💡 Help", command=self.callbacks.get('help')).pack(fill=tk.X, padx=5, pady=2)
