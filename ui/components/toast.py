"""
Toast Notifications - Non-intrusive UI alerts for status updates and errors.
"""
import tkinter as tk
from tkinter import ttk

class NotificationToast(tk.Toplevel):
    """A floating toast notification that automatically disappears."""
    
    def __init__(self, parent, message, type='info', duration=3000):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)  # Start transparent for fade-in
        
        # Colors based on type
        colors = {
            'success': {'bg': '#10B981', 'fg': '#FFFFFF'},
            'error':   {'bg': '#EF4444', 'fg': '#FFFFFF'},
            'info':    {'bg': '#3B82F6', 'fg': '#FFFFFF'},
            'warning': {'bg': '#F59E0B', 'fg': '#FFFFFF'}
        }
        config = colors.get(type, colors['info'])
        
        frame = tk.Frame(self, bg=config['bg'], padx=20, pady=10, 
                         highlightthickness=1, highlightbackground="#FFFFFF")
        frame.pack()
        
        tk.Label(frame, text=message, bg=config['bg'], fg=config['fg'], 
                 font=("Inter", 10, "bold")).pack()
        
        # Position at top center
        self.update_idletasks()
        w = self.winfo_width()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + 50
        self.geometry(f"+{x}+{y}")
        
        # Fade in
        self._fade_in()
        
        # Auto-dismiss
        self.after(duration, self._fade_out)

    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 0.95:
            self.attributes("-alpha", alpha + 0.1)
            self.after(20, self._fade_in)

    def _fade_out(self):
        alpha = self.attributes("-alpha")
        if alpha > 0.05:
            self.attributes("-alpha", alpha - 0.1)
            self.after(20, self._fade_out)
        else:
            self.destroy()

def show_toast(parent, message, type='info', duration=3000):
    """Helper to create and show a toast."""
    NotificationToast(parent, message, type, duration)
