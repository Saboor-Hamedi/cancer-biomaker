"""
Centralized error handling and user notification utility.
"""

import logging
import tkinter.messagebox as messagebox


class ErrorHandler:
    """Centralized error handling with logging and user notifications."""

    def __init__(self, log_instance=None):
        self.log = log_instance or logging.getLogger(__name__)

    def log_and_notify(self, operation, error, title="Error", show_dialog=True):
        """
        Log an error and optionally show a user dialog.

        Args:
            operation (str): Description of the operation that failed
            error (Exception): The exception that occurred
            title (str): Title for the error dialog
            show_dialog (bool): Whether to show a messagebox to the user
        """
        error_msg = f"{operation} failed: {str(error)}"
        self.log.error(error_msg)

        if show_dialog:
            messagebox.showerror(title, error_msg)

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
