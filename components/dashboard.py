import tkinter as tk
from tkinter import ttk

class Dashboard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        # Header Main Title
        header_frame = ttk.Frame(self, style='Card.TFrame', padding=[20, 15])
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        title_container = ttk.Frame(header_frame, style='Card.TFrame')
        title_container.pack(side=tk.LEFT)
        
        ttk.Label(title_container, text="Cancer Biomarker AI", style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(title_container, text="Predictive diagnostics & explainable clinical analysis", style='SubHeader.TLabel').pack(anchor=tk.W)

        # Status Bar with Data Info Labels
        self.status_frame = ttk.Frame(self, style='Card.TFrame', padding=[15, 5])
        self.status_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Left side: Message Status
        status_inner = ttk.Frame(self.status_frame, style='Card.TFrame')
        status_inner.pack(side=tk.LEFT)
        ttk.Label(status_inner, text="System Status:", font=("Inter", 9, "bold"), foreground="#64748B", background="#FFFFFF").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_inner, text="System Ready", font=("Inter", 9, "bold"), foreground="#3B82F6", background="#FFFFFF")
        self.status_label.pack(side=tk.LEFT)

        # Right side: Data Stats labels
        stats_outer = ttk.Frame(self.status_frame, style='Card.TFrame')
        stats_outer.pack(side=tk.RIGHT)
        
        def add_stat(label, value_attr):
            container = ttk.Frame(stats_outer, style='Card.TFrame')
            container.pack(side=tk.LEFT, padx=10)
            ttk.Label(container, text=f"{label}:", font=("Inter", 9), foreground="#64748B", background="#FFFFFF").pack(side=tk.LEFT)
            val_lb = ttk.Label(container, text="0", font=("Inter", 9, "bold"), foreground="#1E293B", background="#FFFFFF")
            val_lb.pack(side=tk.LEFT, padx=2)
            setattr(self, value_attr, val_lb)

        add_stat("Number of Rows", "rows_label")
        add_stat("Number of Columns", "cols_label")
        add_stat("Row Samples", "samples_label")

        # Metric Cards Row
        self.metrics_frame = ttk.Frame(self)
        self.metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Use more modern colors from palette
        self.risk_card_val    = self._create_metric_card(self.metrics_frame, "Avg Risk", "0.0%", "#EF4444")
        self.conf_card_val    = self._create_metric_card(self.metrics_frame, "Confidence", "0.0%", "#10B981")
        self.triage_card_val  = self._create_metric_card(self.metrics_frame, "Triage Priority", "Pending", "#F59E0B")
        self.consensus_card_val = self._create_metric_card(self.metrics_frame, "AI Consensus", "N/A", "#6366F1")
        self.insight_card_val = self._create_metric_card(self.metrics_frame, "Result Insight", "Ready", "#3B82F6")

        # Notebook for content
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.input_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.input_tab, text="Input Features")
        self.notebook.add(self.data_tab, text="Data View")
        self.notebook.add(self.analysis_tab, text="Performance Analysis")

    def _create_metric_card(self, parent, title, value, color):
        card = ttk.Frame(parent, style='Card.TFrame', padding=20)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(card, text=title.upper(), font=("Inter", 8, "bold"), foreground="#94A3B8", background="#FFFFFF").pack()
        val_label = ttk.Label(card, text=value, font=("Inter", 18, "bold"), foreground=color, background="#FFFFFF")
        val_label.pack(pady=(5, 0))
        return val_label

    def update_data_info(self, rows=None, cols=None, samples=None):
        if rows is not None: self.rows_label.config(text=str(rows))
        if cols is not None: self.cols_label.config(text=str(cols))
        if samples is not None: self.samples_label.config(text=str(samples))

    def update_metrics(self, risk=None, confidence=None, insight=None, triage=None, consensus=None):
        if risk is not None: self.risk_card_val.config(text=f"{risk:.1f}%")
        if confidence is not None: self.conf_card_val.config(text=f"{confidence:.1f}%")
        if triage is not None: self.triage_card_val.config(text=str(triage))
        if consensus is not None: self.consensus_card_val.config(text=str(consensus))
        if insight is not None: self.insight_card_val.config(text=str(insight))

    def update_status(self, text, color="#3B82F6"):
        # Map simple color names to hex if needed or pass directly
        self.status_label.config(text=text, foreground=color)
