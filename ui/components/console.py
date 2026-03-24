import tkinter as tk
from tkinter import ttk
from datetime import datetime

class ConsoleTab(ttk.Frame):
    """A persistent logging console for errors and system notifications."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.text: tk.Text = None # type: ignore
        self._create_widgets()
        
    def _create_widgets(self):
        # Toolbar for console actions
        self.toolbar_frame = ttk.Frame(self, style='Card.TFrame', padding=5)
        self.toolbar_frame.pack(fill=tk.X)
        
        self.title_label = ttk.Label(self.toolbar_frame, text="SYSTEM DIAGNOSTICS LOGS", 
                                     font=("Inter", 9, "bold"), style='Card.TLabel')
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(self.toolbar_frame, text="Clear Logs", command=self.clear, style='TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.toolbar_frame, text="Copy All", command=self.copy_all, style='TButton').pack(side=tk.RIGHT, padx=5)

        # Text area with scrollbar
        self.content_container = ttk.Frame(self)
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text = tk.Text(self.content_container, font=("Consolas", 12), wrap=tk.WORD, 
                            state=tk.DISABLED, undo=True, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_container, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Standard tags (will be updated in refresh_theme)
        self.text.tag_configure("INFO", font=("Consolas", 12, "bold"))
        self.text.tag_configure("SUCCESS", font=("Consolas", 12, "bold"))
        self.text.tag_configure("WARNING", font=("Consolas", 12, "bold"))
        self.text.tag_configure("ERROR", font=("Consolas", 12, "bold"))
        self.text.tag_configure("TIMESTAMP", font=("Consolas", 12))

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        
        self.configure(style='TFrame')
        self.toolbar_frame.configure(style='Card.TFrame')
        self.content_container.configure(style='TFrame')
        self.title_label.config(style='Card.TLabel')
        
        # Text sync
        self.text.config(
            background=palette['bg_main'], 
            foreground=palette['text_main'],
            selectbackground=palette['medic_brand'],
            selectforeground="white"
        )
        
        # Tags sync
        self.text.tag_configure("INFO",      foreground=palette['medic_brand'])
        self.text.tag_configure("SUCCESS",   foreground="#10B981")
        self.text.tag_configure("WARNING",   foreground="#F59E0B")
        self.text.tag_configure("ERROR",     foreground="#EF4444")
        self.text.tag_configure("TIMESTAMP", foreground=palette['text_muted'])

    def log(self, message, level="INFO"):
        """Add a log entry to the console."""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, f"{timestamp} ", "TIMESTAMP")
        self.text.insert(tk.END, f"[{level.upper()}] ", level.upper())
        self.text.insert(tk.END, f"{message}\n")
        
        # Auto-scroll
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        """Clear all logs."""
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def copy_all(self):
        """Copy all text to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", tk.END))
