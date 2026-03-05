import tkinter as tk
from tkinter import ttk

class Dashboard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        # Header Main Title
        header_frame = ttk.Frame(self, style='Card.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(header_frame, text="🧬 Cancer Biomarker AI Dashboard", font=('Arial', 16, 'bold')).pack(pady=10)

        # Status Bar with Data Info Labels
        self.status_frame = ttk.Frame(self, style='Card.TFrame')
        self.status_frame.pack(fill=tk.X, padx=10, pady=2)
        
        # Left side: Message Status
        status_container = ttk.Frame(self.status_frame)
        status_container.pack(side=tk.LEFT, padx=5)
        ttk.Label(status_container, text="📊 Status:").pack(side=tk.LEFT, padx=2)
        self.status_label = ttk.Label(status_container, text="System Ready", font=("Arial", 10, "bold"), foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=2)

        # Right side: Data Stats labels (Exact user-requested text)
        stats_container = ttk.Frame(self.status_frame)
        stats_container.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(stats_container, text="Number of Rows:").pack(side=tk.LEFT, padx=2)
        self.rows_label = ttk.Label(stats_container, text="0", font=("Arial", 9, "bold"))
        self.rows_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_container, text="Number of Columns:").pack(side=tk.LEFT, padx=2)
        self.cols_label = ttk.Label(stats_container, text="0", font=("Arial", 9, "bold"))
        self.cols_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(stats_container, text="Number of Simple:").pack(side=tk.LEFT, padx=2)
        self.samples_label = ttk.Label(stats_container, text="0", font=("Arial", 9, "bold"))
        self.samples_label.pack(side=tk.LEFT, padx=5)

        # Metric Cards Row
        self.metrics_frame = ttk.Frame(self)
        self.metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.risk_card_val = self._create_metric_card(self.metrics_frame, "Avg Risk", "0.0%", "#e74c3c")
        self.conf_card_val = self._create_metric_card(self.metrics_frame, "Confidence", "0.0%", "#2ecc71")
        self.insight_card_val = self._create_metric_card(self.metrics_frame, "Result Insight", "Ready", "#3498db")

        # Notebook for content
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.input_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.input_tab, text="📝 Input Features")
        self.notebook.add(self.data_tab, text="📊 Data View")
        self.notebook.add(self.analysis_tab, text="📈 Performance Analysis")

    def _create_metric_card(self, parent, title, value, color):
        card = ttk.Frame(parent, style='Card.TFrame', padding=10)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(card, text=title, font=("Arial", 10)).pack()
        val_label = ttk.Label(card, text=value, font=("Arial", 14, "bold"), foreground=color)
        val_label.pack()
        return val_label

    def update_data_info(self, rows=None, cols=None, samples=None):
        if rows is not None: self.rows_label.config(text=str(rows))
        if cols is not None: self.cols_label.config(text=str(cols))
        if samples is not None: self.samples_label.config(text=str(samples))

    def update_metrics(self, risk=None, confidence=None, insight=None):
        if risk is not None: self.risk_card_val.config(text=f"{risk:.1f}%")
        if confidence is not None: self.conf_card_val.config(text=f"{confidence:.1f}%")
        if insight is not None: self.insight_card_val.config(text=str(insight))

    def update_status(self, text, color="blue"):
        self.status_label.config(text=text, foreground=color)
