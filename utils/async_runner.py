"""
Async task runner utility for background operations with UI feedback.
"""

import threading
import tkinter as tk


class AsyncRunner:
    """Utility class for running background tasks with UI status updates and cancellation."""

    def __init__(self, root):
        self.root = root
        self.session_id = 0  # Used for session-based task cancellation

    def cancel_all(self):
        """Invalidate all currently running background tasks by incrementing session ID."""
        self.session_id += 1

    def run_async(self, label, func, on_finish=None, on_error=None):
        """
        Run a function asynchronously with status updates and session validation.

        Args:
            label (str): Description of the task for status updates
            func (callable): Function to run (should not take arguments)
            on_finish (callable, optional): Callback when task completes successfully
            on_error (callable, optional): Callback when task fails
        """
        my_session = self.session_id

        def task():
            try:
                result = func()
                # ROBUSTNESS FIX: Only execute callbacks if the session is still active
                if self.session_id == my_session:
                    if on_finish:
                        self.root.after(0, lambda: on_finish(result))
                else:
                    print(f"Async task '{label}' was cancelled (obsolete session).")
            except Exception as e:
                if self.session_id == my_session:
                    if on_error:
                        self.root.after(0, lambda err=e: on_error(err))
                    else:
                        self.root.after(0, lambda err=e: print(f"Async task failed: {err}"))

        thread = threading.Thread(target=task, daemon=True)
        thread.start()

        return thread
