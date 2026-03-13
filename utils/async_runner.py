"""
Async task runner utility for background operations with UI feedback.
"""

import threading
import tkinter as tk


class AsyncRunner:
    """Utility class for running background tasks with UI status updates."""

    def __init__(self, root):
        self.root = root

    def run_async(self, label, func, on_finish=None, on_error=None):
        """
        Run a function asynchronously with status updates.

        Args:
            label (str): Description of the task for status updates
            func (callable): Function to run (should not take arguments)
            on_finish (callable, optional): Callback when task completes successfully
            on_error (callable, optional): Callback when task fails
        """
        def task():
            try:
                result = func()
                if on_finish:
                    self.root.after(0, lambda: on_finish(result))
            except Exception as e:
                if on_error:
                    self.root.after(0, lambda: on_error(e))
                else:
                    # Default error handling
                    self.root.after(0, lambda: print(f"Async task failed: {e}"))

        def update_status():
            # This would be handled by the caller, but we can provide a hook
            pass

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

        return thread
