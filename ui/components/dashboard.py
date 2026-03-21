import tkinter as tk
from tkinter import ttk

class Dashboard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Explicitly declare all UI component members for linter and runtime clarity
        self.status_frame = None
        self.rows_label = None
        self.cols_label = None
        self.samples_label = None
        self.risk_card_val = None
        self.conf_card_val = None
        self.triage_card_val = None
        self.consensus_card_val = None
        self.narrative_text = None
        self.notebook = None
        self.input_tab = None
        self.data_tab = None
        self.validation_tab = None
        self.leaderboard_tab = None
        self.velocity_tab = None
        self.analysis_tab = None
        self.settings_tab = None
        self.log_tab_frame = None
        self.console = None
        self.metrics_frame = None
        self.status_label = None
        
        self._create_widgets()

    def _create_widgets(self):
        from ui.styles import StyleManager
        # We'll use the default theme for initial values, or better, let main.py update these.
        # But for now, we remove the hardcoded #FFFFFF
        
        # Header Main Title - REMOVED per user request to save vertical space
        # header_frame = ttk.Frame(self, style='Card.TFrame', padding=(20, 15))
        # header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        # ...

        # Status Bar with Grid Layout - FIXED HEIGHT to prevent UI shifts
        self.status_frame = ttk.Frame(self, style='Card.TFrame', padding=(15, 8))
        self.status_frame.pack(fill=tk.X, padx=15, pady=5)
        self.status_frame.update_idletasks() # Ensure it calculates natural height
        # Lock vertical growth
        h = self.status_frame.winfo_reqheight()
        self.status_frame.configure(height=h)
        self.status_frame.pack_propagate(False)
        self.status_frame.columnconfigure(0, weight=1) # Status side
        self.status_frame.columnconfigure(1, weight=0) # Stats side
        
        # Left side: Message Status
        status_inner = ttk.Frame(self.status_frame, style='Card.TFrame')
        status_inner.grid(row=0, column=0, sticky='w')
        ttk.Label(status_inner, text="System Status:", font=("Inter", 9, "bold"), style='Card.TLabel').pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_inner, text="System Ready", font=("Inter", 9, "bold"), style='Card.TLabel')
        self.status_label.pack(side=tk.LEFT)

        # Right side: Data Stats labels
        stats_outer = ttk.Frame(self.status_frame, style='Card.TFrame')
        stats_outer.grid(row=0, column=1, sticky='e')
        
        def add_stat(label, value_attr):
            container = ttk.Frame(stats_outer, style='Card.TFrame')
            container.pack(side=tk.LEFT, padx=10)
            ttk.Label(container, text=f"{label}:", font=("Inter", 8), style='Card.TLabel').pack(side=tk.LEFT)
            val_lb = ttk.Label(container, text="0", font=("Inter", 8, "bold"), style='Card.TLabel')
            val_lb.pack(side=tk.LEFT, padx=2)
            setattr(self, value_attr, val_lb)

        add_stat("Rows", "rows_label")
        add_stat("Cols", "cols_label")
        add_stat("Samples", "samples_label")

        # Metric Cards Row
        self.metrics_frame = ttk.Frame(self)
        self.metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.risk_card_val    = self._create_metric_card(self.metrics_frame, "Avg Risk", "0.0%", "#EF4444")
        self.conf_card_val    = self._create_metric_card(self.metrics_frame, "Confidence", "0.0%", "#10B981")
        self.triage_card_val  = self._create_metric_card(self.metrics_frame, "Triage", "Pending", "#F59E0B")
        self.consensus_card_val = self._create_metric_card(self.metrics_frame, "Consensus", "N/A", "#6366F1")

        # ── Clinical Analysis Narrative ──
        analysis_frame = ttk.LabelFrame(self, text="CLINICAL NARRATIVE & BIOMARKER INTERPRETATION", style='Card.TFrame', padding=15)
        analysis_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.narrative_text = tk.Text(
            analysis_frame, height=3, bg="white", fg="#475569",
            font=("Inter", 10), wrap=tk.WORD, borderwidth=0, highlightthickness=0,
            selectbackground="#E2E8F0", selectforeground="#0F172A"
        )
        self.narrative_text.pack(fill=tk.X, expand=True)
        self.narrative_text.insert(tk.END, "Awaiting clinical data...")
        self.narrative_text.config(state=tk.DISABLED)

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        # ... (rest of the tab initialization remains same)

        self.input_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.validation_tab = ttk.Frame(self.notebook)
        self.leaderboard_tab = ttk.Frame(self.notebook)
        self.velocity_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)
        self.log_tab_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.input_tab, text="Input Features", sticky='nsew')
        self.notebook.add(self.data_tab, text="Data View", sticky='nsew')
        self.notebook.add(self.validation_tab, text="AI Consensus", sticky='nsew')
        self.notebook.add(self.leaderboard_tab, text="Algorithm Leaderboard", sticky='nsew')
        self.notebook.add(self.velocity_tab, text="Patient Trajectory", sticky='nsew')
        self.notebook.add(self.analysis_tab, text="Performance Analysis", sticky='nsew')
        self.notebook.add(self.log_tab_frame, text="System Logs", sticky='nsew')

    def _create_metric_card(self, parent, title, value, color):
        card = ttk.Frame(parent, style='Card.TFrame', padding=15)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=5)
        
        ttk.Label(card, text=title.upper(), font=("Inter", 9, "bold"), style='Card.TLabel').pack()
        val_label = ttk.Label(card, text=value, font=("Inter", 16, "bold"), foreground=color, style='Card.TLabel')
        val_label.pack(pady=(5, 0))
        return val_label

    def update_data_info(self, rows=None, cols=None, samples=None):
        if self.rows_label and rows is not None: self.rows_label.config(text=str(rows))
        if self.cols_label and cols is not None: self.cols_label.config(text=str(cols))
        if self.samples_label and samples is not None: self.samples_label.config(text=str(samples))

    def update_metrics(self, risk=None, confidence=None, insight=None, triage=None, consensus=None):
        if self.risk_card_val and risk is not None: self.risk_card_val.config(text=f"{risk:.1f}%")
        if self.conf_card_val and confidence is not None: self.conf_card_val.config(text=f"{confidence:.1f}%")
        if self.triage_card_val and triage is not None: self.triage_card_val.config(text=str(triage))
        if self.consensus_card_val and consensus is not None: self.consensus_card_val.config(text=str(consensus))

    def update_narrative(self, text, level="INFO"):
        """Updates the clinical narrative analysis engine with qualitative insights."""
        if not self.narrative_text: return
        self.narrative_text.config(state=tk.NORMAL)
        self.narrative_text.delete("1.0", tk.END)
        
        # High Contrast mapping for narrative
        from ui.styles import StyleManager
        palette = StyleManager.get_palette() # Default or current 
        # Better: use explicit high-contrast constants
        color = "#3B82F6" if level == "INFO" else "#10B981"
        if level == "DANGER": color = "#EF4444"
        elif level == "WARNING": color = "#F59E0B"
        elif level == "SUCCESS": color = "#10B981"
        
        self.narrative_text.tag_configure("level", foreground=color, font=("Inter", 10, "bold"))
        
        prefix = f"[{level}] CLINICAL ANALYSIS: "
        self.narrative_text.insert(tk.END, prefix, "level")
        self.narrative_text.insert(tk.END, text)
        
        self.narrative_text.config(state=tk.DISABLED)

    def update_status(self, text, color="#3B82F6"):
        if self.status_label:
            self.status_label.config(text=text, foreground=color)

    def log_message(self, message, level="INFO"):
        """Log a message to the internal console tab."""
        if self.console:
            self.console.log(message, level)

    def refresh_theme(self, theme_name):
        """Dynamic theme refresh for dashboard cards and text engines."""
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        
        self.configure(style='TFrame')
        self.notebook.configure(style='TNotebook')
        self.status_frame.configure(style='Card.TFrame')
        self.status_label.config(style='Card.TLabel')
        self.metrics_frame.configure(style='TFrame')
        
        if self.narrative_text:
            self.narrative_text.config(
                bg=palette['bg_main'],
                fg=palette['text_main'],
                insertbackground=palette['text_main'],
                selectbackground=palette['medic_brand'],
                selectforeground="white"
            )
            # Force tags to refresh in case data is present
            self.narrative_text.tag_configure("level", foreground=palette['medic_brand'])
        
        # Update any other custom elements if necessary
        self.update_status("Theme synchronized across clinical panels.", palette['medic_brand'])
