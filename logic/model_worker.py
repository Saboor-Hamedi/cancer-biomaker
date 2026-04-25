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
        self.params = {}

    def set_params(self, **kwargs):
        """Inject clinical mission parameters."""
        self.params.update(kwargs)

    def abort(self):
        """Strategic AI Mission Abort Command."""
        self._is_cancelled = True

    def run(self):
        if self._is_cancelled: return
        try:
            if self.task_type == "train":
                self.status.emit("Initiating Clinical AI Calibration...", "orange")
                path_to_train = str(self.data)
                
                # Dynamic Hyperparameter Injection
                v_split = self.params.get('v_split', 0.25)
                outlier_on = self.params.get('outlier_removal', True)
                scale_on = self.params.get('scaling_enabled', True)

                success, msg = self.mm.check_and_train_models(
                    path_to_train, 
                    lambda m, c: self.status.emit(m, c), 
                    force=True,
                    validation_split=v_split,
                    outlier_removal=outlier_on,
                    scaling_enabled=scale_on
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


