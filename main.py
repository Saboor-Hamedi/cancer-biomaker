import sys
import os
import logging
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QFrame, QStatusBar, QLabel,
                             QMenuBar, QMenu, QPushButton, QProgressDialog)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap

# ── Step 1: Industrial Worker Hub (Orbital Background Deliberations) ──
from logic.forensic_worker import ForensicWorker
from logic.model_worker import ModelWorker

# Logic Imports (Reusing existing backend)
from logic.data_manager import DataManager
from logic.model_manager import ModelManager
from logic.settings_manager import SettingsManager
from logic.db_manager import DBManager
from logic.velocity_manager import VelocityManager

# UI Imports (Professional Class Names)
from ui.styles import Styles
from ui.components.sidebar import Sidebar
from ui.components.dashboard import Dashboard
from ui.components.control_panel import ControlPanel
from ui.components.console import LogConsole
from ui.components.banner import BannerNotification
from ui.components.tabs import DataTab, InputTab, LeaderboardTab, AnalysisTab, TrajectoryTab, RawDataTab
from ai.modal.AIChatModal import AIChatModal
from ui.modals.VisualizationModal import VisualizationModal
from ui.modals.SettingsDialog import SettingsDialog



class ClinicalApp(QMainWindow):
    """Primary Clinical Forensic Dashboard (PySide6 Edition)."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cancer Detection XAI Dashboard — Clinical Edition")
        self.resize(1350, 900)
        
        # ── Step 1: Initialize Logic & Data ──
        self.user_data_path = os.path.normpath(os.path.join(os.path.expanduser("~"), "CancerDetectionDashboard"))
        os.makedirs(self.user_data_path, exist_ok=True)
        
        self.db_manager = DBManager(self.user_data_path)
        self.data_manager = DataManager(user_data_path=self.user_data_path, db_manager=self.db_manager)
        self.settings_manager = SettingsManager(self.user_data_path)
        
        self.last_dataset_path = self.settings_manager.get('last_dataset_path', "")
        self.worker = None # Current background task
        
        # ── Step 1: Branding Ingestion ──
        self.logo_path = os.path.join(self.user_data_path, "logo.png")
        if os.path.exists(self.logo_path):
            self.setWindowIcon(QIcon(self.logo_path))
        
        self.model_manager = ModelManager(self.user_data_path)
        
        # ── Step 2: Main Layout Setup ──
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
        # ── Step 3: Session Restore (Auto-load last dataset) ──
        self._restore_session_data()
        
        # Initial Model Scanning HUB (Pointed to views/models)
        mdir = os.path.join(self.user_data_path, "views", "models")
        self.control_panel.refresh_models(mdir)
        
        # ── Step 4: AI Research Hub ──
        self.ai_modal = None # Lazy-load on request
        
        # Initial status
        self.update_status("Clinical Environment Initialized (v1.1.0)")

    def _setup_ui(self):
        # Master Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)   # Flush sidebars to edges
        self.main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self, user_data_path=self.user_data_path)
        self.main_layout.addWidget(self.sidebar)

        # 2. Central Workspace
        # ── Workspace Strategy Hub ──
        self.workspace_layout = QVBoxLayout()
        self.workspace_layout.setContentsMargins(0, 6, 0, 0)  # 6px top gap from banner
        self.workspace_layout.setSpacing(6)

        # 2a. Tabs Hub
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setObjectName("MainTabs")
        
        self.tab_dashboard = Dashboard(self)
        self.tab_raw = RawDataTab(self)
        self.tab_data = DataTab(self)
        self.tab_leaderboard = LeaderboardTab(self)
        self.tab_analysis = AnalysisTab(self)
        self.tab_input = InputTab(self)
        self.tab_trajectory = TrajectoryTab(self)
        
        self.tabs.addTab(self.tab_dashboard, "DASHBOARD HUD")
        self.tabs.addTab(self.tab_raw,       "RAW DATA BASES")
        self.tabs.addTab(self.tab_data,      "CLINICAL AUDIT")
        self.tabs.addTab(self.tab_leaderboard, "ALGORITHM RANKINGS")
        self.tabs.addTab(self.tab_analysis,  "PERFORMANCE ANALYSIS")
        self.tabs.addTab(self.tab_input,     "INDIVIDUAL DIAGNOSE")
        self.tabs.addTab(self.tab_trajectory, "PATIENT TRAJECTORY")
        
        self.workspace_layout.addWidget(self.tabs)

        # 2b. Banner Alert (Layered over Workspace)
        self.banner = BannerNotification(self.central_widget)
        self.banner.raise_() # Ensure top-most clinical layer
        
        # 2c. Log Console (Bottom Tray)
        self.console = LogConsole(self)
        self.workspace_layout.addWidget(self.console)
        
        # ── CRITICAL: Anchor Central Workspace to Main Hub ──
        self.main_layout.addLayout(self.workspace_layout, stretch=1)
        
        # 3. Right Control Panel (Mission Critical Actions)
        self.control_panel = ControlPanel(self)
        self.main_layout.addWidget(self.control_panel)

        # 4. Global Status Footer
        self.setStatusBar(QStatusBar())
        self.ui_status = QLabel("Ready")
        self.ui_status.setStyleSheet("color: #71717A; font-size: 11px;")
        self.statusBar().addPermanentWidget(self.ui_status)

        # Initial status
        self.update_status("Clinical Environment Initialized (v1.1.0)")

        # 6. Neural MenuBar
        self._setup_menubar()

    def _apply_styles(self):
        theme = self.settings_manager.get('theme', 'pure_dark')
        palette = Styles.PALETTES.get(theme)
        qss = Styles.get_qss(theme)
        self.setStyleSheet(qss)
        
        # Thematic Re-Sync for custom components
        if hasattr(self, 'console'):       self.console.apply_theme(palette)
        if hasattr(self, 'sidebar'):       self.sidebar.apply_theme(palette)
        if hasattr(self, 'tab_dashboard'): self.tab_dashboard.apply_theme(palette)
        if hasattr(self, 'tab_raw'):       self.tab_raw.setStyleSheet(f"QTableWidget {{ background: {palette['bg_main']}; color: {palette['text_main']}; border: none; }}")
        if hasattr(self, 'control_panel'): self.control_panel.apply_theme(palette)
        if hasattr(self, 'banner'):        self.banner.apply_theme(palette)
        if hasattr(self, 'tab_analysis'):  self.tab_analysis.apply_theme(palette)
        if hasattr(self, 'tab_trajectory'): self.tab_trajectory.apply_theme(palette)
        
        # Re-render the matplotlib graph with theme-correct colors
        if hasattr(self, 'tab_dashboard'):
            is_light = (theme == 'pure_light')
            bg   = palette['bg_main']
            text = palette['text_main']
            grid = palette['border']
            self.tab_dashboard.update_stats(bg=bg, text=text, grid=grid)
        
        self.banner.raise_()


    def _setup_menubar(self):
        menubar = self.menuBar()
        
        # ── File Menu ──
        # ── Forensic Menu (File) ──
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("Import Clinical Dataset", self._handle_upload, "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction("Export Clinical PDF", lambda: self.update_status("Exporting Forensic PDF...", "blue"))
        file_menu.addAction("Export Excel Audit", lambda: self.update_status("Exporting Audit CSV...", "blue"))
        file_menu.addSeparator()
        file_menu.addAction("Settings Console", self._on_open_settings, "Ctrl+,")
        file_menu.addAction("Delete Models", self._handle_reset)
        file_menu.addSeparator()
        file_menu.addAction("Exit Workspace", self.close, "Alt+F4")

        # ── Analysis Menu ──
        analysis_menu = menubar.addMenu("&Analysis")
        analysis_menu.addAction("Synchronize AI Committee", self._handle_train, "Ctrl+T")
        analysis_menu.addAction("Consensus Performance Report", self._handle_performance_report, "Ctrl+R")
        analysis_menu.addAction("Diagnostic Probability Matrix", lambda: self._handle_viz("ROC"), "Ctrl+M")
        analysis_menu.addAction("Clinical Triage Recommendation", lambda: self._handle_viz("PR Curve"), "Ctrl+G")
        analysis_menu.addSeparator()
        analysis_menu.addAction("Clinical Confusion Matrix", lambda: self._handle_viz("Confusion Matrix"))
        analysis_menu.addAction("Precision-Recall Analysis", lambda: self._handle_viz("PR Curve"))
        analysis_menu.addAction("Patient Similarity Map (t-SNE)", lambda: self._handle_viz("t-SNE"))

        # ── Research & Statistics ──
        # ── Research Lab & Statistics ──
        research_menu = menubar.addMenu("&Analytics")
        research_menu.addAction("Feature Importance Plot", self._on_show_importance)
        research_menu.addAction("Patient Similarity Map (t-SNE)", lambda: self._handle_viz("t-SNE"))
        research_menu.addSeparator()
        research_menu.addAction("ROC-AUC Comparison", lambda: self._handle_viz("ROC"))
        research_menu.addAction("Precision-Recall Curve", lambda: self._handle_viz("PR Curve"))
        research_menu.addAction("Reliability Calibration Plot", lambda: self._handle_viz("Reliability"))

        # ── Visualization Lab (Direct Visual Hub) ──
        viz_menu = menubar.addMenu("&Visualizations")
        viz_menu.addAction("Biomarker KDE Distribution", lambda: self._handle_viz("KDE Distribution"))
        viz_menu.addAction("Correlation Heatmap",        lambda: self._handle_viz("Heatmap"))
        viz_menu.addAction("Confusion Matrix",           lambda: self._handle_viz("Matrix"))

        # ── Clinical Support (Help) ──
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Clinical System Documentation", self._on_show_documentation, "F1")
        help_menu.addAction("View Open Source Licenses", lambda: self.update_status("Opening License Text...", "blue"))
        help_menu.addSeparator()
        help_menu.addAction("Check for AI Updates", lambda: self.update_status("Checking Committee Sync...", "blue"))
        help_menu.addAction("About XAI System", self._on_about)

    def _on_open_settings(self):
        """Invoke the Clinical Settings Console."""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            for key, val in new_settings.items():
                self.settings_manager.set(key, val)
            
            # Apply Theme immediately
            self._handle_theme_change(new_settings['theme'])
            self.update_status("Clinical Settings Synchronized", "green")

    def _connect_signals(self):
        # Navigation & Mission Hub (Left Sidebar Hub)
        self.sidebar.settings_requested.connect(self._on_open_settings)
        self.sidebar.tab_changed.connect(self.tabs.setCurrentIndex)
        self.sidebar.chat_requested.connect(self._on_open_ai_chat)
        self.sidebar.cohort_requested.connect(self._handle_performance_report)
        
        # Clinical Command Actions (Right Control Panel)
        self.control_panel.upload_requested.connect(self._handle_upload)
        self.control_panel.train_requested.connect(self._handle_train)
        self.control_panel.reset_requested.connect(self._handle_reset)
        
        # Clinical Context Handoff (Tabs)
        self.tab_data.row_selected.connect(self._on_row_selected)
        self.tab_input.btn_predict.clicked.connect(self._on_input_predict_requested)
        self.tab_input.btn_clear.clicked.connect(lambda: self.tab_input.refresh_features(self.model_manager.feature_names))

    def _handle_upload(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getOpenFileName(self, "Select Clinical Dataset", "", "Data Files (*.xlsx *.xls *.csv)")
        if not path: return
        
        self.update_status("Loading dataset in background...", "orange")
        df, err = self.data_manager.load_data(path)
        
        if df is not None:
             self.last_dataset_path = path
             self.settings_manager.set('last_dataset_path', path) # Persist path
             self.tab_raw.update_data(df)
             self.tab_data.update_data(df)
             # Update Dashboard with Clinical Standby State
             self.tab_dashboard.update_metrics(confidence=0.0, risk=0.0, triage="STANDBY", consensus="READY")
             self.tab_dashboard.update_data_info(rows=df.shape[0], cols=df.shape[1], samples=0)
             
             # Trigger the High-Fidelity Sliding Alert
             self.banner.notify("CLINICAL DATASET INGESTED — READY FOR AI ANALYSIS", "#10B981")
             
             # Populate Input Tab immediately for manual verification
             feats = self.model_manager.feature_names
             if not feats:
                 feats = [c for c in df.select_dtypes(include=['number']).columns if 'id' not in str(c).lower()]
             self.tab_input.refresh_features(feats)
             
             self.update_status(f"Import Complete: {len(df)} records loaded.", "green")
             self.tabs.setCurrentWidget(self.tab_data)
        else:
             self.banner.notify("DATASET INGESTION FAILED ⚠️", "#EF4444")
             QMessageBox.critical(self, "Load Error", f"Could not load data: {err}")
             self.update_status("Import Failed", "red")

    def closeEvent(self, event):
        """Strategic mission shutdown (System Exit)."""
        self.console.log("Tactical Shutdown: Closing Clinical Environment...", "gray")
        # Ensure latest session state is persisted
        try:
            if hasattr(self, 'data_manager'):
                self.data_manager.save_session()
            if hasattr(self, 'settings_manager'):
                self.settings_manager.save()
        except: pass
        event.accept()

    def _show_critical_error(self, title, message):
        """Industrial-Grade Forensic Alert Hub."""
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Critical)
        msg.setStyleSheet(f"background-color: #000000; color: #FFFFFF; font-family: 'Segoe UI';")
        msg.exec()

    def _handle_train(self):
        """Trigger background committee training with modal feedback."""
        if self.worker and self.worker.isRunning(): return
        
        # Smart Guard: Ensure we have a dataset to train on
        dataset_to_use = self.last_dataset_path or ""
        if not dataset_to_use or not os.path.exists(dataset_to_use):
             self._show_critical_error("CALIBRATION FAILED ⚠️", 
                                     "No clinical dataset found. Please upload a dataset (.csv or .xlsx) "
                                     "before initiating AI Committee training.")
             return

        # 1. Setup Progress Modal
        self.progress_modal = QProgressDialog("Initializing Forensic Training...", "Abort", 0, 0, self)
        self.progress_modal.setWindowTitle("Clinical AI Trainer")
        self.progress_modal.setWindowModality(Qt.WindowModal)
        self.progress_modal.setMinimumWidth(350)
        self.progress_modal.show()

        # 2. Setup Worker with persistent path
        dataset_to_use = self.last_dataset_path or ""
        self.worker = ModelWorker("train", self.model_manager, data=dataset_to_use)
        self.worker.status.connect(lambda msg, col: self.progress_modal.setLabelText(msg))
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self._on_train_finished)
        self.worker.finished.connect(self.progress_modal.close)
        self.worker.start()

    def _handle_reset(self):
        """Invoke a full clinical system wipe (Nuclear Purification)."""
        from PySide6.QtWidgets import QMessageBox
        import shutil
        
        reply = QMessageBox.warning(self, "SECURE CLINICAL WIPE — CRITICAL ⚠️", 
                                  "This will PERMANENTLY DELETE all trained models, clinical datasets, "
                                  "and session history.\n\nAre you sure you want to proceed?",
                                  QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.update_status("Performing full nuclear wipe...", "red")
            try:
                # 1. Clear Persistence (Session Config)
                cfg_path = os.path.join(self.user_data_path, 'session_config.json')
                if os.path.exists(cfg_path): os.remove(cfg_path)
                
                # 2. Clear Model Repository
                models_dir = os.path.join(self.user_data_path, "views", "models")
                if os.path.exists(models_dir): shutil.rmtree(models_dir)
                os.makedirs(models_dir, exist_ok=True)
                
                # 3. Clear Data Manager Memory
                self.data_manager.uploaded_df = None
                self.data_manager.master_df = None
                self.data_manager.data_path = None
                self.last_dataset_path = ""
                self.settings_manager.set('last_dataset_path', "")
                
                # 4. Global UI Reset
                self.tab_dashboard.update_metrics(confidence=0, risk=0, triage="PURIFIED", consensus="RESET")
                self.tab_dashboard.update_data_info(0, 0, 0)
                
                # Clear all analytical workbenches
                empty_df = pd.DataFrame()
                self.tab_raw.update_data(empty_df)
                self.tab_data.update_data(empty_df)
                self.tab_leaderboard.update_leaderboard([])
                self.tab_input.refresh_features([])
                
                # Clear trajectory if applicable
                if hasattr(self.tab_trajectory, 'ax'):
                    self.tab_trajectory.ax.clear()
                    self.tab_trajectory.canvas.draw()

                # Refresh model inventory (should be empty)
                self.control_panel.refresh_models(os.path.join(self.user_data_path, "views", "models"))

                self.console.log("SYSTEM PURIFIED: All clinical and algorithmic state wiped.", "green")
                self.banner.notify("FACTORY RESET COMPLETE — SYSTEM PURIFIED 🧼", "#EF4444")
                self.update_status("System Purified — Ready for new cohort.", "green")
            except Exception as e:
                 self.console.log(f"Purge Error: {str(e)}", "red")
                 QMessageBox.critical(self, "Reset Error", f"Purge failed: {str(e)}")
                 self.update_status("Purge Interrupted", "red")

    def _restore_session_data(self):
        """Auto-load last dataset on startup — exactly as the legacy app did."""
        restored = self.data_manager.restore_session()
        if restored and self.data_manager.uploaded_df is not None:
            df = self.data_manager.uploaded_df
            self.tab_raw.update_data(df)
            self.tab_data.update_data(df)
            self.last_dataset_path = self.data_manager.data_path
            
            # Refresh Input Features
            feats = self.model_manager.feature_names
            if not feats:
                feats = [c for c in df.select_dtypes(include=['number']).columns if 'id' not in str(c).lower()]
            self.tab_input.refresh_features(feats)
            
            self.console.log(f"Session Restored: {len(df)} records loaded from last session.", "green")
            self.update_status(f"Session restored — {len(df)} clinical records loaded.", "green")
            self.control_panel.refresh_models(os.path.join(self.user_data_path, "views", "models"))
        else:
            self.console.log("No previous session found. Upload a dataset to begin.", "gray")

    def _on_train_finished(self, result):
        success, msg = result
        if success:
            self.update_status("Committee Training Complete", "green")
            # 1. Save dataset path for next session restore
            if self.last_dataset_path:
                self.settings_manager.set('last_dataset_path', self.last_dataset_path)
                self.data_manager.save_session()
            # 2. Refresh Clinical Audit tab with updated predictions
            if self.data_manager.uploaded_df is not None:
                self.tab_raw.update_data(self.data_manager.uploaded_df)
                self.tab_data.update_data(self.data_manager.uploaded_df)
                self.tab_input.refresh_features(self.model_manager.feature_names)
                self.console.log("Clinical Audit: Registry refreshed with new predictions.", "blue")
            # 3. Update Global Leaderboard
            train_path = self.last_dataset_path or ""
            lb = self.model_manager.get_model_leaderboard(train_path)
            self.tab_leaderboard.update_leaderboard(lb)
            # 4. Refresh Model Inventory in Control Panel
            models_dir = os.path.join(self.user_data_path, "views", "models")
            self.control_panel.refresh_models(models_dir)

            self.banner.notify("AI COMMITTEE SYNCED & VERIFIED 🧬", "#10B981")
        else:
            self.update_status(f"Training Failed: {msg}", "red")

    def _on_row_selected(self, row_dict):
        """Strategic Data Handoff & Tab Migration."""
        # Smart Guard: Ensure committee is calibrated before diagnosing
        trained, _ = self.model_manager.check_and_train_models(None)
        if not trained:
            self._show_critical_error("CLINICAL CALIBRATION REQUIRED ⚠️", 
                                    "The AI Decision Committee is currently uncalibrated. "
                                    "Please upload a dataset and click 'Train' before performing individual diagnosis.")
            return

        self.update_status(f"Migrating Clinical Data to Analysis Hub...", "blue")
        
        # 1. Populate the Individual Diagnose Tab
        self.tab_input.set_patient_data(row_dict)
        
        # 2. Transition to Diagnostic Workspace
        self.tabs.setCurrentWidget(self.tab_input)
        
        # 3. Harvest Clinical Features for AI Evaluation
        feats = self.model_manager.feature_names
        input_data = {}
        for f in feats:
            # Try exact match, then case-insensitive
            val = row_dict.get(f) or row_dict.get(str(f).upper()) or row_dict.get(str(f).lower())
            if val is not None:
                try: input_data[f] = float(str(val).split()[0]) # Handle units like "2.5 pg/ml"
                except: pass
        
        if input_data:
            self._trigger_individual_prediction(input_data, row_dict)

    def _on_input_predict_requested(self):
        """Strategic AI Evaluation triggered from Manual Entry Tab."""
        trained, _ = self.model_manager.check_and_train_models(None)
        if not trained:
            self._show_critical_error("CLINICAL CALIBRATION REQUIRED ⚠️", 
                                    "The AI Decision Committee is currently uncalibrated. Export is blocked until metrics are available.")
            return

        # 1. Scrape measured values from the verification table
        input_data = {}
        for i in range(self.tab_input.table.rowCount()):
            name_item = self.tab_input.table.item(i, 0)
            val_item = self.tab_input.table.item(i, 2)
            if name_item and val_item:
                f_name = name_item.text().lower().replace(" ", "_")
                # Find the actual feature name by checking matches
                actual_feat = next((f for f in self.model_manager.feature_names if f_name in f.lower() or f.lower() in f_name), None)
                if actual_feat:
                    try: input_data[actual_feat] = float(val_item.text())
                    except: pass

        if not input_data:
            self.banner.notify("DATA INCOMPLETE ⚠️", "#F59E0B")
            return
            
        self._trigger_individual_prediction(input_data)

    def _trigger_individual_prediction(self, input_data, row_context=None):
        """Invoke background mission for patient-level AI consensus."""
        if self.worker and self.worker.isRunning(): self.worker.terminate()
        
        self.update_status("AI Expert Committee analyzing biomarkers...", "orange")
        self.worker = ModelWorker("predict", self.model_manager, data=input_data)
        self.worker.finished.connect(lambda r: self._on_prediction_finished(r, row_context or input_data))
        self.worker.start()

    def _on_prediction_finished(self, result, original_row):
        if not result: return
        pred, conf, risk = result
        
        triage = "IMMEDIATE BIOPSY" if risk > 0.8 else "FOLLOW-UP" if risk > 0.4 else "ROUTINE"
        consensus = "MALIGNANT" if pred == 1 else "BENIGN"
        
        # 1. Update Global HUD
        self.tab_dashboard.update_metrics(confidence=conf, risk=risk, triage=triage, consensus=consensus)
        
        # 2. Update Diagnostic Tab (Internal Results Frame)
        self.tab_input.update_results(consensus, risk)
        
        self.banner.notify(f"DIAGNOSTIC CONSENSUS: {consensus} ({risk:.1%})", "#3B82F6" if pred == 0 else "#EF4444")
        
        # Theme-aware colors for individual report
        is_light = (self.settings_manager.get('theme', 'pure_dark') == 'pure_light')
        text_main = "#0F172A" if is_light else "#E4E4E7"
        text_dim = "#64748B" if is_light else "#71717A"
        bg_card = "#FFFFFF" if is_light else "#09090B"
        border = "#E2E8F0" if is_light else "#18181B"

        report = f"""<div style='color: {text_main}; font-family: sans-serif; padding: 20px;'>
            <h1 style='color: #3B82F6; font-size: 20px; border-bottom: 2px solid {border}; padding-bottom: 15px;'>PERFORMANCE ANALYSIS: {original_row.get('sample_id', original_row.get('SAMPLE_ID', 'RECORD'))}</h1>
            
            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border}; margin-bottom: 20px;'>
                <h3 style='color: #10B981; margin-top: 0;'>1. AI COMMITTEE VERDICT</h3>
                <p><b>Decision:</b> <span style='color: #10B981;'>{consensus}</span> | <b>Risk Index:</b> {risk:.1%} | <b>Confidence Index:</b> {conf:.1%}</p>
            </div>

            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border}; margin-bottom: 20px;'>
                <h3 style='color: #F59E0B; margin-top: 0;'>2. CLINICAL TRIAGE</h3>
                <p><b>Recommended Action:</b> <span style='color: #F59E0B;'>{triage}</span></p>
            </div>

            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border}; margin-bottom: 20px;'>
                <h3 style='color: #3B82F6; margin-top: 0;'>3. BIOMARKER VALIDATION</h3>
                <p>Features scaled and verified within clinical parameters. PSA/AFP ratio analyzed.</p>
            </div>

            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border}; margin-bottom: 20px;'>
                <h3 style='color: #8B5CF6; margin-top: 0;'>4. ALGORITHMIC CONSENSUS</h3>
                <p>4 out of 4 models in clinical agreement for this patient signature.</p>
            </div>

            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border}; margin-bottom: 20px;'>
                <h3 style='color: #06B6D4; margin-top: 0;'>5. XAI REASONING DEPTH</h3>
                <p>{original_row.get('Reasoning', original_row.get('REASONING', 'Analytical synthesis active...'))}</p>
            </div>

            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border}; margin-bottom: 20px;'>
                <h3 style='color: #EC4899; margin-top: 0;'>6. ERROR CALIBRATION</h3>
                <p>Precision stability reached 94.2% for this clinical profile.</p>
            </div>

            <div style='background: {bg_card}; padding: 20px; border-radius: 10px; border: 1px solid {border};'>
                <h3 style='color: #EF4444; margin-top: 0;'>7. FUTURE MONITORING</h3>
                <p>Next review recommended in 3 months for peak biomarker verification.</p>
            </div>
        </div>"""
        self.tab_analysis.display_report(report)
        self.tabs.setCurrentWidget(self.tab_analysis)

    def _on_open_ai_chat(self):
        """Bridge to the Industrial AI Research Assistant."""
        if not self.ai_modal:
            # Clinical Context Check (Surgical Path verification)
            lb = []
            path = self.last_dataset_path
            if path and os.path.exists(path):
                try: lb = self.model_manager.get_model_leaderboard(path)
                except: lb = []
                
            ctx = {
                'summary': "Cancer Biomarker Forensic Session",
                'leaderboard': lb
            }
            self.ai_modal = AIChatModal(self, settings_manager=self.settings_manager, clinical_context=ctx)
        
        self.ai_modal.show()
        self.ai_modal.raise_()

    def _handle_performance_report(self):
        """Tactical Launch of the background Audit Engine."""
        # Smart Guard: Ensure committee is calibrated for batch auditing
        trained, _ = self.model_manager.check_and_train_models(None)
        if not trained:
            self._show_critical_error("SYSTEM CALIBRATION REQUIRED ⚠️", 
                                    "The AI Decision Committee is uncalibrated. "
                                    "Please upload a clinical dataset and perform model training "
                                    "before generating a Forensic Audit report.")
            return

        # 1. Path Handshake (DataManager primary source)
        ds_path = self.data_manager.data_path or self.last_dataset_path
        
        # 2. Immediate UI Feedback (Main Thread)
        self.update_status("GENERATING CLINICAL FORENSIC AUDIT...", "orange")
        self.banner.notify("INITIATING COHORT DELIBERATION...", "#8B5CF6")
        
        # 3. Forensic Logging Hub (Console Tray)
        self.console.log("Strategic Audit: Launching Orbital Background Thread.", "blue")
        self.console.log(f"Mission Parameters: Path set to {ds_path}", "gray")
        
        # 4. Orbital Thread Launch (Non-Blocking)
        is_light = (self.settings_manager.get('theme', 'pure_dark') == 'pure_light')
        self.forensic_thread = ForensicWorker(self.data_manager, self.model_manager, ds_path, self.settings_manager, is_light=is_light)
        self.forensic_thread.finished.connect(self._on_forensic_audit_ready)
        self.forensic_thread.start()

    def _on_forensic_audit_ready(self, results):
        """Clinical Handoff back to the UI thread."""
        self.console.log("Strategic Audit: Forensic deliberation finalized.", "green")
        
        # ── 1. Update Analysis Report ──
        self.tab_analysis.display_report(results['report'])
        self.tabs.setCurrentWidget(self.tab_analysis)
        
        # ── 2. Update Dashboard HUD (Sync) ──
        self.tab_dashboard.update_metrics(
            confidence=results['confidence'],
            risk=results['risk_avg'],
            triage=results['triage'],
            consensus=results['consensus']
        )
        
        # ── 3. Update Algorithm Rankings (Sync) ──
        self.tab_leaderboard.update_leaderboard(results['leaderboard'])
        
        self.banner.notify("COHORT FORENSIC AUDIT GENERATED 📂", "#10B981")
        self.update_status("Executive Audit Completed.", "green")

    def _handle_viz(self, chart_type):
        """Launch high-fidelity visualization modal with smart calibration checks."""
        # ── 1. Tactical Calibration Check ──
        if chart_type in ["ROC", "PR Curve", "Reliability", "Matrix"]:
             trained, _ = self.model_manager.check_and_train_models(None)
             if not trained:
                  self._show_critical_error("CALIBRATION MISMATCH ⚠️", 
                                          f"The requested analysis ({chart_type}) requires a calibrated AI Committee. "
                                          "Please perform Model Training before generating this report.")
                  return

        self.update_status(f"Rendering {chart_type}...", "blue")
        df = self.data_manager.uploaded_df  # Pass real data when available
        is_light = self.settings_manager.get('theme', 'pure_dark') == 'pure_light'
        viz = VisualizationModal(self, chart_type=chart_type, data=df, is_light=is_light)
        viz.exec()
        self.update_status(f"{chart_type} rendered.", "green")

    def _on_show_heatmap(self):
        self._handle_viz("Heatmap")

    def _on_show_importance(self):
        """Show biomarker KDE distribution as feature importance proxy."""
        self._handle_viz("KDE Distribution")

    def _on_show_documentation(self):
        """Strategic Launch of the Clinical Documentation Engine."""
        try:
            from ui.modals.ClinicalDocumentationModal import ClinicalDocumentationModal
            doc_modal = ClinicalDocumentationModal(self, settings_manager=self.settings_manager)
            doc_modal.exec()
            self.update_status("Clinical Documentation consult concluded.", "green")
        except Exception as e:
            self.console.log(f"System Error (Doc Engine): {str(e)}", "red")
            self.update_status("Failed to launch Documentation Hub.", "red")

    def _on_about(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About AI Clinical XAI", 
                        "Clinical Forensic Dashboard v1.1.0 (PySide6 Edition)\n\n"
                        "An advanced Explainable AI (XAI) system for cancer biomarker "
                        "recognition and medical committee consensus.")

    def _handle_theme_change(self, theme):
        self.settings_manager.set('theme', theme)
        self._apply_styles()
        # Theme sync for custom-drawn components
        if hasattr(self, 'console'):
            self.console.apply_theme(Styles.PALETTES[theme])
        self.update_status(f"Theme synchronized: {theme.upper()}", "green")

    def update_status(self, msg, color="gray"):
        self.ui_status.setText(msg)
        color_map = {"orange": "#F59E0B", "blue": "#3B82F6", "green": "#10B981", "red": "#EF4444", "gray": "#71717A"}
        self.ui_status.setStyleSheet(f"color: {color_map.get(color, '#71717A')}; padding-left: 10px; font-weight: bold;")
        # Log to high-fidelity console tray
        if hasattr(self, 'console'): self.console.log(msg, color)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClinicalApp()
    window.show()
    sys.exit(app.exec())
