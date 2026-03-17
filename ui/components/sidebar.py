import tkinter as tk
from tkinter import ttk

class Sidebar(ttk.Frame):
    """
    Enhanced Sidebar with Scrollable Container for better responsiveness.
    """
    def __init__(self, parent, callbacks):
        super().__init__(parent, style='Sidebar.TFrame', width=260)
        self.callbacks = callbacks
        self.pack_propagate(False)
        
        # State variables
        self.model_var = tk.StringVar(value="Random Forest")
        self.sample_qty = tk.IntVar(value=20)
        
        # ── Responsive Scrollable Container ──────────────────────
        self.canvas = tk.Canvas(self, bg="#0F172A", highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_content = ttk.Frame(self.canvas, style='Sidebar.TFrame')
        
        self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw", width=260)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._create_widgets()
        
        # Update scroll region
        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _create_widgets(self):
        # Removed top header label background per request
        header_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        header_frame.pack(fill=tk.X, pady=(10, 5), padx=20)

        # ── Model Selection Center ───────────────────────────────
        model_frame = ttk.LabelFrame(self.scroll_content, text="ACTIVE COMMITTEE", style='Sidebar.TLabelframe')
        model_frame.pack(fill=tk.X, padx=15, pady=10)

        list_container = ttk.Frame(model_frame, style='Sidebar.TFrame')
        list_container.pack(fill=tk.X, padx=8, pady=8)

        self.model_listbox = tk.Listbox(
            list_container,
            selectmode=tk.SINGLE,
            bg="#0F172A",
            fg="#F8FAFC",
            font=("Inter", 10, "bold"),
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#3B82F6",
            selectforeground="white",
            activestyle='none',
            relief='flat',
            height=6
        )
        self.model_listbox.pack(fill=tk.X, expand=True)

        # Populate
        models = self.callbacks.get('models', [])
        for m in models:
            self.model_listbox.insert(tk.END, f" {m}")

        if self.model_listbox.size() > 0:
            self.model_listbox.selection_set(0)
        
        self.model_listbox.bind("<<ListboxSelect>>", self._on_model_select)

        # ── Diagnostic Actions ──────────────────────────────────
        action_frame = ttk.LabelFrame(self.scroll_content, text="INTELLIGENCE", style='Sidebar.TLabelframe')
        action_frame.pack(fill=tk.X, padx=15, pady=10)

        ttk.Button(
            action_frame, text="Predict Patient",
            style='Primary.TButton',
            command=self.callbacks.get('predict_single')
        ).pack(fill=tk.X, padx=10, pady=(12, 6))

        ttk.Button(
            action_frame, text="Batch Forensic",
            command=self.callbacks.get('predict_file')
        ).pack(fill=tk.X, padx=10, pady=(0, 12))

        # ── Clinical Tools ────────────────────────────────────────
        batch_frame = ttk.LabelFrame(self.scroll_content, text="DATA GEN", style='Sidebar.TLabelframe')
        batch_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ctrl_frame = ttk.Frame(batch_frame, style='Sidebar.TFrame')
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(10, 15))
        
        spin = tk.Spinbox(
            ctrl_frame, from_=1, to=1000, textvariable=self.sample_qty, 
            width=12, bg="#1E293B", fg="white", buttonbackground="#0F172A", 
            relief='flat', font=("Inter", 11, "bold"), insertbackground="white",
            justify='center'
        )
        spin.pack(side=tk.LEFT, padx=(0, 5), fill=tk.Y)
        spin.bind("<Return>", lambda e: self.callbacks.get('sample', lambda: None)())
        
        ttk.Button(
            ctrl_frame, text="Gen Data", 
            command=self.callbacks.get('sample')
        ).pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ── Advanced Clinical XAI ────────────────────────────────
        analytics_frame = ttk.LabelFrame(self.scroll_content, text="CLINICAL XAI", style='Sidebar.TLabelframe')
        analytics_frame.pack(fill=tk.X, padx=15, pady=10)

        _btn_style = {
            "bg": "#1E293B",
            "fg": "#F8FAFC",
            "font": ("Inter", 9, "bold"),
            "relief": "flat",
            "activebackground": "#3B82F6",
            "activeforeground": "white",
            "borderwidth": 0,
            "highlightthickness": 0,
            "pady": 6
        }

        tk.Button(
            analytics_frame, text="🔍 What-If Analysis", 
            command=lambda: self.callbacks.get('show_counterfactual', lambda: None)(),
            **_btn_style
        ).pack(fill=tk.X, pady=2, padx=10)

        tk.Button(
            analytics_frame, text="🕸️ Biomarker Network", 
            command=lambda: self.callbacks.get('show_biomarker_network', lambda: None)(),
            **_btn_style
        ).pack(fill=tk.X, pady=2, padx=10)

        # ── System Maintenance ──────────────────────────────────
        reset_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        reset_frame.pack(fill=tk.X, padx=15, pady=(20, 10))

        ttk.Button(
            reset_frame, text="SYSTEM RESET",
            style='Danger.TButton',
            command=self.callbacks.get('system_reset')
        ).pack(fill=tk.X, padx=10)

        ttk.Label(self.scroll_content, text="v3.0 Verified", style='SidebarCaption.TLabel').pack(pady=20)

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
