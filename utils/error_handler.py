"""
Centralized error handling and user notification utility.
"""

import logging
import threading
import tkinter.messagebox as messagebox


class ErrorHandler:
    """Centralized error handling with logging and user notifications."""

    def __init__(self, root=None, log_instance=None):
        self.root = root
        self.log = log_instance or logging.getLogger(__name__)
        self.console_callback = None
        self.status_callback = None
        self.narrative_callback = None

    def log_and_notify(self, operation, error, title="Error", show_dialog=True):
        error_msg = f"{operation} failed: {str(error)}"
        self.log.error(error_msg)

        if self.console_callback:
            self.console_callback(error_msg, level='ERROR')

        if show_dialog:
            self.notify(error_msg, type='error')

    def notify(self, message, type='info'):
        """Show a non-intrusive internal notification (Thread Safe)."""
        if self.root and threading.current_thread() is not threading.main_thread():
            self.root.after(0, lambda: self.notify(message, type))
            return
        # 1. Internal Status Bar (Primary)
        if self.status_callback:
            color = "#10B981" if type == 'success' else "#EF4444" if type == 'error' else "#3B82F6"
            self.status_callback(message, color)

        # 2. Clinical Narrative Engine (For important updates)
        if self.narrative_callback and type in ('error', 'warning', 'success'):
            level = "SUCCESS" if type == 'success' else "DANGER" if type == 'error' else "WARNING"
            self.narrative_callback(message, level)

        # 3. Floating Toast (Only if requested and root exists, otherwise redundant)
        # We skip toast by default now to keep things "inside" as requested.
        
        # 4. Console Logic
        if self.console_callback:
            self.console_callback(message, level=type.upper())

        # 5. Last resort fallback for critical errors if no UI callbacks exist
        if not self.status_callback and not self.narrative_callback:
            if type == 'error':
                messagebox.showerror("Clinical Error", message)
            elif type == 'warning':
                messagebox.showwarning("Clinical Warning", message)

    def require_data(self, context, data_path=None):
        """
        Check if data is available and show warning if not.

        Args:
            context (str): Description of what requires data
            data_path: Path to check for data availability

        Returns:
            bool: True if data is available, False otherwise
        """
        if not data_path:
            messagebox.showwarning("Data Required",
                                 f"{context} requires data to be loaded first.\n"
                                 "Please upload a dataset using File → Upload Dataset.")
            return False
        return True

    def require_model(self, model, model_name):
        """
        Check if a model is available and show warning if not.

        Args:
            model: The model object to check
            model_name (str): Name of the model for error messages

        Returns:
            bool: True if model is available, False otherwise
        """
        if model is None:
            messagebox.showwarning("Model Required",
                                 f"'{model_name}' model could not be loaded.\n"
                                 "Please train it first via Data → Re-Train All Models.")
            return False
        return True
