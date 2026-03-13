import tkinter as tk
from tkinter import ttk
from datetime import datetime

class ConsoleTab(ttk.Frame):
    """A persistent logging console for errors and system notifications."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
        
    def _create_widgets(self):
        # Toolbar for console actions
        toolbar = ttk.Frame(self, style='Card.TFrame', padding=5)
        toolbar.pack(fill=tk.X)
        
        ttk.Label(toolbar, text="SYSTEM DIAGNOSTICS LOGS", font=("Inter", 9, "bold"), 
                  foreground="#64748B", background="#FFFFFF").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(toolbar, text="Clear Logs", command=self.clear, style='Action.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Copy All", command=self.copy_all, style='Action.TButton').pack(side=tk.RIGHT, padx=5)

        # Text area with scrollbar
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text = tk.Text(container, font=("Consolas", 10), wrap=tk.WORD, 
                            state=tk.DISABLED, undo=True, borderwidth=1, relief="flat",
                            background="#F8FAFC", foreground="#1E293B")
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Simple tags for coloring
        self.text.tag_configure("INFO", foreground="#3B82F6")
        self.text.tag_configure("SUCCESS", foreground="#10B981")
        self.text.tag_configure("WARNING", foreground="#F59E0B")
        self.text.tag_configure("ERROR", foreground="#EF4444")
        self.text.tag_configure("TIMESTAMP", foreground="#94A3B8")

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
