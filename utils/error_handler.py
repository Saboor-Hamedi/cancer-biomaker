"""
Centralized error handling and user notification utility.
"""

import logging
import tkinter.messagebox as messagebox


class ErrorHandler:
    """Centralized error handling with logging and user notifications."""

    def __init__(self, root=None, log_instance=None):
        self.root = root
        self.log = log_instance or logging.getLogger(__name__)

    def log_and_notify(self, operation, error, title="Error", show_dialog=True):
        error_msg = f"{operation} failed: {str(error)}"
        self.log.error(error_msg)

        if show_dialog:
            self.notify(error_msg, type='error')

    def notify(self, message, type='info'):
        """Show a non-intrusive toast notification."""
        if self.root:
            try:
                from ui.components.toast import show_toast
                show_toast(self.root, message, type=type)
            except Exception as e:
                self.log.error(f"Failed to show toast: {e}")
                # Fallback to standard messagebox for critical errors if toast fails
                if type == 'error':
                    messagebox.showerror("Error", message)
        else:
            if type == 'error':
                messagebox.showerror("Error", message)
            else:
                messagebox.showinfo("Information", message)

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
