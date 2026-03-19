import os
import tkinter as tk
from tkinter import ttk

class ModelExplorer(ttk.Frame):
    """
    Enhanced Model Explorer with Scrollable Container for better responsiveness.
    """
    def __init__(self, parent, model_dir, callbacks):
        super().__init__(parent, style='Sidebar.TFrame', width=260)
        self.model_dir = model_dir
        self.callbacks = callbacks
        self.pack_propagate(False)
        
        # ── Responsive Scrollable Container ──────────────────────
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_content = ttk.Frame(self.canvas, style='Sidebar.TFrame')
        
        self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw", width=260)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._create_widgets()
        self._start_monitoring()
        
        # Update scroll region
        self.scroll_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def _create_widgets(self):
        # Removed top header label background per request
        header_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        header_frame.pack(fill=tk.X, pady=(10, 5), padx=20)

        # Removed header labels as requested
        # ttk.Label(
        #     header_frame, text="DISK FORENSIC",
        #     style='Sidebar.TLabel',
        #     font=("Inter", 14, "bold"),
        #     foreground="#10B981"
        # ).pack(anchor=tk.W)
        
        # ttk.Label(
        #     header_frame, text="Proof of Training",
        #     style='SidebarCaption.TLabel',
        #     font=("Inter", 8, "bold")
        # ).pack(anchor=tk.W, pady=(2, 0))

        # ── Files Center ──────────────────────────────────────────
        file_frame = ttk.LabelFrame(self.scroll_content, text="ARTIFACTS (.PKL)", style='Sidebar.TLabelframe')
        file_frame.pack(fill=tk.X, padx=15, pady=10)

        list_container = ttk.Frame(file_frame, style='Sidebar.TFrame')
        list_container.pack(fill=tk.X, padx=8, pady=8)

        self.file_listbox = tk.Listbox(
            list_container,
            selectmode=tk.SINGLE,
            bg="#000000",
            fg="#10B981",
            font=("Consolas", 10, "bold"),
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#10B981",
            selectforeground="#0F172A",
            activestyle='none',
            relief='flat',
            height=8
        )
        self.file_listbox.pack(fill=tk.X, expand=True)

        # ── Feedback ──────────────────────────────────────────────
        status_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        status_frame.pack(fill=tk.X, padx=15, pady=20)

        self.status_label = ttk.Label(
            status_frame, text="Scanning...",
            style='SidebarCaption.TLabel',
            font=("Inter", 9)
        )
        self.status_label.pack(anchor=tk.CENTER)

        self.verify_icon = ttk.Label(
            status_frame, text="DISK VERIFIED",
            style='SidebarCaption.TLabel',
            font=("Inter", 7, "bold"),
            foreground="#10B981"
        )
        self.verify_icon.pack(anchor=tk.CENTER, pady=(5, 0))

        # ── Quick Action Buttons (NEW) ───────────────────────────
        action_frame = ttk.Frame(self.scroll_content, style='Sidebar.TFrame')
        action_frame.pack(fill=tk.X, padx=15, pady=20)

        upload_btn = ttk.Button(
            action_frame, text="UPLOAD DATA",
            style='Primary.TButton',
            command=self.callbacks.get('upload')
        )
        upload_btn.pack(fill=tk.X, pady=5)

        train_btn = ttk.Button(
            action_frame, text="TRAIN ALL MODELS",
            command=self.callbacks.get('train_all')
        )
        train_btn.pack(fill=tk.X, pady=5)

        ttk.Label(
            action_frame, text="⚡ Clinical session required",
            style='SidebarCaption.TLabel', font=("Inter", 7, "italic")
        ).pack(pady=2)

    def _start_monitoring(self):
        def monitor():
            self.refresh()
            self.after(2000, monitor)
        monitor()

    def refresh(self):
        """Public method to manually refresh the artifact list from disk."""
        try:
            if not os.path.exists(self.model_dir):
                return
            
            files = [f for f in os.listdir(self.model_dir) if f.endswith('.pkl')]
            files.sort()
            
            # Extract names for comparison
            current_items = [self.file_listbox.get(i).replace(" ➤", "").strip() for i in range(self.file_listbox.size())]
            
            if set(files) != set(current_items):
                self.file_listbox.delete(0, tk.END)
                for f in files:
                    self.file_listbox.insert(tk.END, f" {f} ➤")
                
                count = len(files)
                self.status_label.config(text=f"Detected: {count} models")
                self.verify_icon.config(text="✓ VERIFIED" if count > 0 else "⚠ NO MODELS")
        except Exception:
            pass

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        is_dark = theme_name == 'pure_dark'
        
        self.configure(style='Sidebar.TFrame', width=260)
        self.canvas.config(bg=palette['bg_main'])
        self.scroll_content.configure(style='Sidebar.TFrame')
        
        # Listbox sync
        self.file_listbox.config(
            bg=palette['bg_main'], 
            fg="#10B981" if is_dark else "#059669",
            selectbackground="#10B981",
            selectforeground=palette['bg_main']
        )
        
        # Ensure scrollregion is correct after color shift
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
