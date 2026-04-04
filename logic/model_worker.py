from PySide6.QtCore import QThread, Signal

class ModelWorker(QThread):
    """Background worker to prevent UI freezing during AI analysis."""
    finished = Signal(object)
    status = Signal(str, str)
    
    def __init__(self, task_type, model_manager, data=None):
        super().__init__()
        self.task_type = task_type
        self.mm = model_manager
        self.data = data
        self._is_cancelled = False

    def abort(self):
        """Strategic AI Mission Abort Command."""
        self._is_cancelled = True

    def run(self):
        if self._is_cancelled: return
        try:
            if self.task_type == "train":
                self.status.emit("Initiating Clinical AI Calibration...", "orange")
                path_to_train = str(self.data)
                # Corrected: Accept both message and color from the backend callback
                success, msg = self.mm.check_and_train_models(
                    path_to_train, 
                    lambda m, c: self.status.emit(m, c), 
                    force=True
                )
                self.finished.emit((success, msg))
            elif self.task_type == "predict":
                self.status.emit("AI Committee Consensus in progress...", "blue")
                result = self.mm.predict_ensemble(self.data, is_single=True)
                # Emit full clinical analysis dictionary for forensic logging
                self.finished.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status.emit(f"Error: {str(e)}", "red")
            self.finished.emit(None)


