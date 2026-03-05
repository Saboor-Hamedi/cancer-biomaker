import tkinter as tk
from tkinter import ttk

class Sidebar(ttk.Frame):
    def __init__(self, parent, callbacks):
        # Increased width slightly for a more stable look
        super().__init__(parent, style='Sidebar.TFrame', width=280)
        self.callbacks = callbacks
        self.pack_propagate(False)

        # Create Canvas for scrolling - BG color updated to match sidebar slate
        self.canvas = tk.Canvas(self, bg="#1E293B", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # This frame will hold the actual content
        self.scrollable_frame = ttk.Frame(self.canvas, style='Sidebar.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        # Window width slightly less than container to allow for scrollbar
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=260)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add mousewheel support - only when mouse is over sidebar
        self.scrollable_frame.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.scrollable_frame.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

        self._create_widgets()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _create_widgets(self):
        # Header
        header_lb = ttk.Label(self.scrollable_frame, text="CONTROL CENTER", style='Sidebar.TLabel')
        header_lb.pack(pady=(30, 20), padx=10)

        # Helper to create styled sections
        def create_section(title, buttons_data):
            frame = ttk.LabelFrame(self.scrollable_frame, text=title.upper(), style='Sidebar.TLabelframe')
            frame.pack(fill=tk.X, padx=15, pady=8)
            
            for text, callback in buttons_data:
                btn = ttk.Button(frame, text=text, command=callback)
                btn.pack(fill=tk.X, padx=8, pady=4)
                
        # Configuration Section (Special case for combo/spin)
        config_frame = ttk.LabelFrame(self.scrollable_frame, text="CONFIGURATION", style='Sidebar.TLabelframe')
        config_frame.pack(fill=tk.X, padx=15, pady=8)
        
        ttk.Label(config_frame, text="Active AI Model:", style='SidebarCaption.TLabel').pack(anchor=tk.W, padx=10, pady=(5,0))
        self.model_var = tk.StringVar(value="Random Forest")
        self.model_combo = ttk.Combobox(config_frame, textvariable=self.model_var,
                                       values=self.callbacks.get('models', ["Random Forest"]), state="readonly")
        self.model_combo.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(config_frame, text="Sample Batch Qty:", style='SidebarCaption.TLabel').pack(anchor=tk.W, padx=10, pady=(5,0))
        self.sample_qty = tk.IntVar(value=20)
        tk.Spinbox(config_frame, from_=1, to=1000, textvariable=self.sample_qty).pack(fill=tk.X, padx=10, pady=5)

        # Action Buttons
        create_section("Data Actions", [
            ("Upload New dataset", self.callbacks.get('upload')),
            ("Load Samples", self.callbacks.get('sample')),
            ("Re-Train Models", self.callbacks.get('train_models')),
            ("Start Single Pred", self.callbacks.get('predict_single')),
            ("Run Batch Pred", self.callbacks.get('predict_file'))
        ])

        # Visualization Buttons
        create_section("Analytics & XAI", [
            ("Local Explainability", self.callbacks.get('viz_feat')),
            ("Performance Curve", self.callbacks.get('viz_roc')),
            ("Confusion Matrix", self.callbacks.get('viz_cm')),
            ("PR Analytics", self.callbacks.get('viz_pr')),
            ("Cross-Model Comp", self.callbacks.get('viz_comp')),
            ("Correlation Heatmap", self.callbacks.get('viz_heat'))
        ])

        # Utility Buttons
        create_section("System", [
            ("Optimization", self.callbacks.get('preprocess')),
            ("Export Report", self.callbacks.get('report')),
            ("Help & Docs", self.callbacks.get('help'))
        ])

        # Small spacing at bottom
        ttk.Frame(self.scrollable_frame, height=20, style='Sidebar.TFrame').pack()
