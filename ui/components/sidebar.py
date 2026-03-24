import tkinter as tk
from tkinter import ttk

class Sidebar(ttk.Frame):
    """
    Enhanced Sidebar with Scrollable Container for better responsiveness.
    """
    def __init__(self, parent, callbacks):
        super().__init__(parent, style='Sidebar.TFrame', width=280)
        self.callbacks = callbacks
        self.pack_propagate(False)
        
        # State variables
        self.model_var = tk.StringVar(value="Random Forest")
        self.sample_qty = tk.IntVar(value=20)
        
        # ── Responsive Scrollable Container ──────────────────────
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_content = ttk.Frame(self.canvas, style='Sidebar.TFrame', borderwidth=0)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw", width=280)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize
        self._create_widgets()
        self.refresh_theme(callbacks.get('theme', 'sleek_dark'))
        
        # Update scroll region
        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        header_frame.pack(fill=tk.X, pady=(10, 5), padx=20)

        # ── Active Committee ──
        model_frame = ttk.LabelFrame(self.scroll_content, text="ACTIVE COMMITTEE", style='Sidebar.TLabelframe')
        model_frame.pack(fill=tk.X, padx=15, pady=10)

        list_container = ttk.Frame(model_frame, style='Sidebar.TFrame')
        list_container.pack(fill=tk.X, padx=8, pady=8)

        # Initialize listbox with theme-aware background
        from ui.styles import StyleManager
        initial_theme = self.callbacks.get('theme', 'sleek_dark')
        initial_palette = StyleManager.get_palette(initial_theme)
        sidebar_bg_color = initial_palette['accent_dark']
        text_fg_color = initial_palette['text_main']

        self.model_listbox = tk.Listbox(
            list_container, selectmode=tk.SINGLE, font=("Inter", 10, "bold"),
            borderwidth=0, highlightthickness=0, activestyle='none', relief='flat', height=6,
            bg=sidebar_bg_color, fg=text_fg_color, selectbackground=initial_palette['medic_brand'], selectforeground="white"
        )
        self.model_listbox.pack(fill=tk.X, expand=True)

        for m in self.callbacks.get('models', []):
            self.model_listbox.insert(tk.END, f" {m}")

        if self.model_listbox.size() > 0:
            self.model_listbox.selection_set(0)
        self.model_listbox.bind("<<ListboxSelect>>", self._on_model_select)

        # ── Intelligence ──
        action_frame = ttk.LabelFrame(self.scroll_content, text="INTELLIGENCE", style='Sidebar.TLabelframe')
        action_frame.pack(fill=tk.X, padx=15, pady=10)

        ttk.Button(action_frame, text="Individual Diagnosis", style='Primary.TButton', 
                   command=self.callbacks.get('predict_single')).pack(fill=tk.X, padx=10, pady=(12, 6))
        ttk.Button(action_frame, text="Cohort Forensic Audit", 
                   command=self.callbacks.get('predict_file')).pack(fill=tk.X, padx=10, pady=(0, 6))
        
        ttk.Button(action_frame, text="🤖 AI Research Assistant", 
                   command=self.callbacks.get('show_ai_chat')).pack(fill=tk.X, padx=10, pady=(0, 12))

        # ── Data Gen ──
        batch_frame = ttk.LabelFrame(self.scroll_content, text="DATA GEN", style='Sidebar.TLabelframe')
        batch_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ctrl_frame = ttk.Frame(batch_frame, style='Sidebar.TFrame')
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(10, 15))
        
        self.spin = tk.Spinbox(
            ctrl_frame, from_=1, to=1000, textvariable=self.sample_qty, 
            width=12, relief='flat', font=("Inter", 11, "bold"), justify='center'
        )
        self.spin.pack(side=tk.LEFT, padx=(0, 5), fill=tk.Y)
        
        ttk.Button(ctrl_frame, text="Gen Data", command=self.callbacks.get('sample')).pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ── Specific Patient Search ──
        search_frame = ttk.Frame(batch_frame, style='Sidebar.TFrame')
        search_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, font=("Inter", 10),
            relief='flat', borderwidth=0, width=15
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.Y)
        self.search_entry.insert(0, "Search ID (e.g. PAT-01)")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_var.get() == "Search ID (e.g. PAT-01)" else None)
        
        ttk.Button(search_frame, text="🔍", width=3,
                   command=lambda: self.callbacks.get('search')(self.search_var.get())).pack(side=tk.RIGHT)

        # ── Clinical XAI ──
        analytics_frame = ttk.LabelFrame(self.scroll_content, text="CLINICAL XAI", style='Sidebar.TLabelframe')
        analytics_frame.pack(fill=tk.X, padx=15, pady=10)

        self.btn_whatif = tk.Button(analytics_frame, text="🔍 What-If Analysis", relief="flat", borderwidth=0, pady=6,
                                    command=lambda: self.callbacks.get('show_counterfactual', lambda: None)())
        self.btn_whatif.pack(fill=tk.X, pady=2, padx=10)

        self.btn_biomarker = tk.Button(analytics_frame, text="🕸️ Biomarker Network", relief="flat", borderwidth=0, pady=6,
                                       command=lambda: self.callbacks.get('show_biomarker_network', lambda: None)())
        self.btn_biomarker.pack(fill=tk.X, pady=2, padx=10)

        # ── Maintenance ──
        reset_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        reset_frame.pack(fill=tk.X, padx=15, pady=(20, 10))

        ttk.Button(reset_frame, text="⚙️ SETTINGS", command=self.callbacks.get('show_settings')).pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(reset_frame, text="SYSTEM RESET", style='Danger.TButton', command=self.callbacks.get('system_reset')).pack(fill=tk.X, padx=10)

    def update_sample_qty(self, count):
        """Update the spinbox value programmatically."""
        self.sample_qty.set(count)

    def refresh_theme(self, theme_name):
        """Update static internal widgets to match theme."""
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        
        sidebar_bg = palette['accent_dark']
        self.configure(style='Sidebar.TFrame')
        self.canvas.config(bg=sidebar_bg)
        self.scroll_content.configure(style='Sidebar.TFrame')
        
        # Colors for listbox and spinbox - Visibility fix for Light Mode
        is_dark = theme_name == 'pure_dark'
        text_fg = palette['text_main']
        entry_bg = palette['bg_main']
        caret_color = palette['text_main']
        
        self.model_listbox.config(bg=sidebar_bg, fg=text_fg, selectbackground=palette['medic_brand'], selectforeground="white")
        self.spin.config(bg=entry_bg, fg=text_fg, buttonbackground=sidebar_bg, insertbackground=caret_color)
        self.search_entry.config(bg=entry_bg, fg=text_fg, insertbackground=caret_color)
        
        # Colors for XAI buttons
        for btn in [self.btn_whatif, self.btn_biomarker]:
            btn.config(bg=entry_bg, fg=text_fg, activebackground=palette['medic_brand'], activeforeground="white")

    def _on_model_select(self, event):
        selection = self.model_listbox.curselection()
        if selection:
            full_text = self.model_listbox.get(selection[0])
            self.model_var.set(full_text.strip())
            self.callbacks.get('predict_silent', lambda: None)()

    @property
    def current_model(self):
        return self.model_var.get()

    def update_model_info(self, model_name):
        pass

    def clear_input_fields(self):
        self.sample_qty.set(20)
