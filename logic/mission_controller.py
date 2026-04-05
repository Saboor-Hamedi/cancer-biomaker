from PySide6.QtCore import QObject, Signal, QThread
import os
import pandas as pd
from typing import Optional, List, Dict, Union, Any
from logic.data_manager import DataManager
from logic.model_manager import ModelManager
from logic.settings_manager import SettingsManager
from logic.db_manager import DBManager
from logic.forensic_worker import ForensicWorker
from logic.model_worker import ModelWorker

class MissionController(QObject):
    """
    Strategic Analytical Orchestrator for Clinical Forensic Missions.
    
    This controller decouples high-dimensional biomarker processing from the UI shell,
    managing a high-fidelity Task Registry for background ensemble deliberations.
    
    Attributes
    ----------
    user_data_path : str
        Absolute path to the clinical mission persistent vault.
    last_dataset_path : str
        Path to the most recently ingested research cohort.
    _active_tasks : Dict[str, QThread]
        Registry of mission-critical background deliberations.
    """
    
    # Signals for UI synchronization
    status_changed = Signal(str, str)
    notification = Signal(str, str)
    log_emitted = Signal(str, str)
    
    training_finished = Signal(tuple)
    audit_finished = Signal(dict)
    prediction_finished = Signal(object, object)
    counterfactual_ready = Signal(object)
    session_restored = Signal(object)
    system_purged = Signal() # 🧪 Strategic Signal for UI purification

    def __init__(self, user_data_path: str):
        """
        Initialize the Research Command Center.

        Parameters
        ----------
        user_data_path : str
            The primary workspace for clinical models and biomarker registries.
        """
        super().__init__()
        self.user_data_path = user_data_path
        self._active_tasks: Dict[str, Union[QThread, Any]] = {}
        
        self.db_manager = DBManager(self.user_data_path)
        self.data_manager = DataManager(user_data_path=self.user_data_path, db_manager=self.db_manager)
        self.settings_manager = SettingsManager(self.user_data_path)
        self.model_manager = ModelManager(self.user_data_path)
        self.last_dataset_path: str = self.settings_manager.get('last_dataset_path', "")
        
        # ── Step 3: Forensic Laboratory Vault (Audit Trails) ──
        self.forensic_log_dir = os.path.join(self.user_data_path, "forensic_logs")
        os.makedirs(self.forensic_log_dir, exist_ok=True)

    def _log_forensic_entry(self, patient_id: str, results: Dict[str, Any]) -> None:
        """
        Secure Audit Trail: Record diagnostic impact log.

        Parameters
        ----------
        patient_id : str
            Clinical patient identifier.
        results : Dict[str, Any]
            Mission results including consensus and risk.
        """
        try:
            import json
            from datetime import datetime
            
            log_path = os.path.join(self.forensic_log_dir, f"deliberation_{datetime.now().strftime('%Y%m%d')}.jsonl")
            entry = {
                "timestamp": datetime.now().isoformat(),
                "patient_id": patient_id,
                "verdict": "MALIGNANT" if results['prediction'] == 1 else "BENIGN",
                "risk_index": f"{results['risk']:.1%}",
                "consensus": results['consensus'],
                "committee_breakdown": results['individual_results']
            }
            
            with open(log_path, 'a') as f:
                f.write(json.dumps(entry) + "\n")
            
            self.log_emitted.emit(f"FORENSIC LOG: Audit trail secured for Patient {patient_id}.", "gray")
        except Exception as e:
            self.log_emitted.emit(f"AUDIT ERROR: Failed to secure forensic log: {str(e)}", "red")

    def _register_mission(self, name: str, worker: QThread) -> None:
        """
        Strategic Registry: Track and terminate existing deliberations.

        Parameters
        ----------
        name : str
            Clinical mission identifier (e.g., 'calibration', 'audit').
        worker : QThread
            The background task assigned to the mission.
        """
        if name in self._active_tasks:
            try:
                old_worker = self._active_tasks[name]
                if old_worker.isRunning():
                    old_worker.abort()
                    old_worker.terminate()
                    old_worker.wait()
            except: pass
        self._active_tasks[name] = worker

    def _handle_prediction_ready(self, result: Dict, row_context: Any) -> None:
        """Process AI deliberation results and secure forensic audit trail."""
        if not result:
            self.log_emitted.emit("AI MISSION FAILED: Committee could not reach consensus. Ensure models are trained.", "red")
            self.notification.emit("DIAGNOSIS FAILED ⚠️ - Models might be uncalibrated.", "#EF4444")
            self.status_changed.emit("Analysis Failed", "red")
            self.prediction_finished.emit((0, 0, 0), row_context) # Unlock UI
            return
        
        # 1. Secure Forensic Log Entry
        patient_id = str(row_context.get('patient_id', row_context.get('ID', 'RECORD_X')))
        self._log_forensic_entry(patient_id, result)
        
        # 2. Strategic Signal Emission for UI Hub
        # Convert internal result list to tuple for UI compatibility if needed
        # (pred, conf, risk)
        res_tuple = (result['prediction'], result['confidence'], result['risk'])
        self.prediction_finished.emit(res_tuple, row_context)

    def cancel_all_missions(self) -> None:
        """Global Abort Signal: Purge all active clinical deliberations."""
        for name, worker in list(self._active_tasks.items()):
            try:
                if worker.isRunning():
                    worker.abort()
                    worker.terminate()
                    worker.wait()
            except: pass
        self._active_tasks.clear()
        self.log_emitted.emit("MISSION CONTROL: All active background deliberations aborted.", "red")

    # ── Clinical Workflows (Refactored for Task Registry) ──

    def restore_session(self) -> bool:
        """
        Auto-load last clinical research session.

        Returns
        -------
        bool
            True if clinic records were successfully restored from the vault.
        """
        restored = self.data_manager.restore_session()
        if restored and self.data_manager.uploaded_df is not None:
            self.last_dataset_path = self.data_manager.data_path
            self.session_restored.emit(self.data_manager.uploaded_df)
            self.log_emitted.emit(f"Session Restored: {len(self.data_manager.uploaded_df)} records loaded.", "green")
            return True
        return False

    def handle_ingestion(self, file_path: str) -> bool:
        """
        Ingest a new clinical research cohort.

        Parameters
        ----------
        file_path : str
            Physical path to the CSV or Excel clinical record.

        Returns
        -------
        bool
            Success of the data ingestion mission.
        """
        self.status_changed.emit(f"Ingesting clinical cohort: {os.path.basename(file_path)}", "blue")
        df, error = self.data_manager.load_data(file_path)
        
        if df is not None:
            self.last_dataset_path = file_path
            self.settings_manager.set('last_dataset_path', file_path)
            self.data_manager.data_path = file_path
            self.session_restored.emit(df)
            self.log_emitted.emit(f"INGESTION SUCCESS: {len(df)} patient records registered.", "green")
            self.notification.emit("CLINICAL COHORT LOADED 📁", "#10B981")
            return True
        else:
            self.log_emitted.emit(f"INGESTION FAILED: {error}", "red")
            self.notification.emit("INGESTION ERROR ⚠️", "#EF4444")
            return False

    def handle_train_mission(self, dataset_path: Optional[str] = None) -> bool:
        """
        Initiate AI Committee Synchronization with Pre-Flight Validation.

        Parameters
        ----------
        dataset_path : Optional[str]
            Path to the training cohort. Defaults to the last loaded dataset.

        Returns
        -------
        bool
            Initial success of mission launch.
        """
        ds_path = dataset_path or self.last_dataset_path
        # 🛡️ FATAL GUARD: Prevent ensemble deliberation on empty data (Prevents SegFault)
        if not ds_path or not os.path.exists(ds_path) or self.data_manager.uploaded_df is None:
            self.notification.emit("DATASET REQUIRED ⚠️ - Upload clinical data before training.", "#EF4444")
            self.log_emitted.emit("TRAIN ABORTED: No active cohort in memory.", "red")
            return False

        # 1. Strategic Pre-Flight Validation
        if self.data_manager.uploaded_df is not None:
            report = self.data_manager.pre_flight_report(self.data_manager.uploaded_df)
            if report['status'] == 'FAILED':
                self.notification.emit(f"MISSION HALTED: {report['issues'][0]}", "#EF4444")
                return False
            elif report['status'] == 'CAUTION':
                self.log_emitted.emit(f"DATA INTEGRITY WARNING: {', '.join(report['issues'])}", "orange")
                self.notification.emit("PROCEEDING WITH CAUTION — Anomalies detected.", "#F59E0B")

        self.last_dataset_path = ds_path
        self.status_changed.emit("Synchronizing AI Decision Committee...", "orange")
        
        worker = ModelWorker("train", self.model_manager, data=ds_path)
        self._register_mission("calibration", worker)
        worker.status.connect(self.log_emitted)
        worker.finished.connect(self.training_finished)
        worker.start()
        return True

    def handle_forensic_audit(self, is_light: bool = False) -> bool:
        """
        Execute longitudinal cohort deliberation.

        Parameters
        ----------
        is_light : bool
            Whether to use high-contrast laboratory styling for the report.

        Returns
        -------
        bool
            Initial success of mission launch.
        """
        ds_path = self.last_dataset_path
        if not ds_path:
            self.notification.emit("MISSION ABORTED ⚠️ - Dataset missing.", "#EF4444")
            return False

        self.status_changed.emit("GENERATING CLINICAL FORENSIC AUDIT...", "orange")
        self.log_emitted.emit("Strategic Audit: Launching Orbital Background Thread.", "blue")
        
        worker = ForensicWorker(self.data_manager, self.model_manager, ds_path, self.settings_manager, is_light=is_light)
        self._register_mission("audit", worker)
        worker.finished.connect(self.audit_finished)
        worker.start()
        return True

    def handle_individual_prediction(self, input_data: Union[Dict, pd.Series], row_context: Optional[Any] = None) -> None:
        """
        Invoke patient-level AI consensus.

        Parameters
        ----------
        input_data : Union[Dict, pd.Series]
            Raw patient biomarkers for diagnostic deliberation.
        row_context : Optional[Any]
            Original clinical record for forensic mapping.
        """
        self.status_changed.emit("AI Expert Committee analyzing biomarkers...", "orange")
        worker = ModelWorker("predict", self.model_manager, data=input_data)
        self._register_mission("prediction", worker)
        worker.status.connect(self.log_emitted)
        worker.finished.connect(lambda r: self._handle_prediction_ready(r, row_context or input_data))
        worker.start()

    def handle_counterfactual_mission(self, input_data: Union[Dict, pd.Series]) -> None:
        """
        Generate 'What-If' hypothetical scenarios (XAI).

        Parameters
        ----------
        input_data : Union[Dict, pd.Series]
            Patient baseline biomarkers.
        """
        worker = ModelWorker("counterfactual", self.model_manager, data={'inputs': input_data, 'data_path': self.last_dataset_path})
        self._register_mission("xai_counter", worker)
        worker.finished.connect(self.counterfactual_ready)
        worker.start()

    def purge_system(self) -> bool:
        """
        Secure Clinical Wipe — Restore system to uncalibrated factory state.

        Returns
        -------
        bool
            Success of the purification mission.
        """
        try:
            self.cancel_all_missions()
            self.data_manager.uploaded_df = None
            self.data_manager.data_path = None
            self.last_dataset_path = ""
            self.settings_manager.set('last_dataset_path', "")
            
            # Wipe model artifacts and clear analytics cache
            self.model_manager.delete_all_models()
            
            # 🧼 Secure Clinical Wipe: Purge local database and session registries
            self.data_manager.purge_registry()
            
            self.system_purged.emit() # 🧬 Trigger Global UI Reset
            self.log_emitted.emit("SYSTEM PURIFIED: All clinical and algorithmic state wiped.", "green")
            self.notification.emit("FACTORY RESET COMPLETE — SYSTEM PURIFIED 🧼", "#EF4444")
            self.status_changed.emit("System Purified — Ready for new cohort.", "green")
            return True
        except Exception as e:
            self.log_emitted.emit(f"Purge Error: {str(e)}", "red")
            return False
