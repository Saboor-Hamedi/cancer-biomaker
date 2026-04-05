import sys
import os
import logging
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QFrame, QStatusBar, QLabel,
                             QMenuBar, QMenu, QPushButton, QProgressDialog, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap

# ─────────────────────────────────────────────────────────────────────────
# GLOBAL PLATFORM VERSION
# ─────────────────────────────────────────────────────────────────────────
APP_VERSION = "1.0.4"

# ── Step 1: Industrial Analytical Architecture ──
from logic.mission_controller import MissionController

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
        
        # ── Step 1: Initialize Project Logic Hub ──
        self.user_data_path = os.path.normpath(os.path.join(os.path.expanduser("~"), "CancerDetectionDashboard"))
        os.makedirs(self.user_data_path, exist_ok=True)
        
        # ── MISSION CONTROLLER: The Logical Nerve Center ──
        self.mc = MissionController(self.user_data_path)
        
        # ── Step 2: Main Layout Setup ──
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
        # ── Step 3: Session Restore (Auto-load last dataset) ──
        self.mc.restore_session()
        
        # Initial Model Scanning HUB
        mdir = os.path.join(self.user_data_path, "views", "models")
        self.control_panel.refresh_models(mdir)
        
        # ── Step 4: AI Research Hub ──
        self.ai_modal = None 
        
        # Initial status
        self.update_status(f"Clinical Environment Calibrated (v{APP_VERSION})")

    def _setup_ui(self):
        # Master Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)   
        self.main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self, user_data_path=self.user_data_path)
        self.main_layout.addWidget(self.sidebar)

        # 2. Central Workspace
        self.workspace_layout = QVBoxLayout()
        self.workspace_layout.setContentsMargins(0, 0, 0, 0)
        self.workspace_layout.setSpacing(0)

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

        # 2b. Banner Alert
        self.banner = BannerNotification(self.central_widget)
        self.banner.raise_() 
        
        # 2c. Log Console
        self.console = LogConsole(self)
        self.workspace_layout.addWidget(self.console)
        
        self.main_layout.addLayout(self.workspace_layout, stretch=1)
        
        # 3. Right Control Panel
        self.control_panel = ControlPanel(self)
        self.main_layout.addWidget(self.control_panel)

        # 4. Global Status Footer
        self.setStatusBar(QStatusBar())
        self.ui_status = QLabel("Ready")
        self.ui_status.setStyleSheet("color: #71717A; font-size: 11px;")
        self.statusBar().addPermanentWidget(self.ui_status)

        # 6. Neural MenuBar
        self._setup_menubar()

    def _apply_styles(self):
        theme = self.mc.settings_manager.get('theme', 'pure_dark')
        self.setStyleSheet(Styles.get_qss(theme))
        self.sidebar.apply_theme(Styles.PALETTES[theme])
        self.tab_dashboard.apply_theme(Styles.PALETTES[theme])
        self.tab_input.apply_theme(Styles.PALETTES[theme])
        self.tab_data.apply_theme(Styles.PALETTES[theme])
        self.tab_raw.apply_theme(Styles.PALETTES[theme])
        self.tab_leaderboard.apply_theme(Styles.PALETTES[theme])
        self.tab_analysis.apply_theme(Styles.PALETTES[theme])
        self.console.apply_theme(Styles.PALETTES[theme])
        self.control_panel.apply_theme(Styles.PALETTES[theme])

    def _connect_signals(self):
        """Strategic UI-Logic Handoff Hub."""
        # ── Controller Signals (Orchestration) ──
        self.mc.status_changed.connect(self.update_status)
        self.mc.notification.connect(self.banner.notify)
        self.mc.log_emitted.connect(lambda m, c: self.console.log(m, c))
        
        self.mc.session_restored.connect(self._on_session_restored)
        self.mc.training_finished.connect(self._on_train_finished)
        self.mc.audit_finished.connect(self._on_forensic_audit_ready)
        self.mc.prediction_finished.connect(self._on_prediction_finished)
        self.mc.counterfactual_ready.connect(self._on_counterfactual_ready)

        # ── UI Command Signals ──
        self.sidebar.tab_changed.connect(self._on_nav_requested)
        self.sidebar.chat_requested.connect(self._on_show_ai_chat)
        self.sidebar.cohort_requested.connect(self._trigger_forensic_audit)
        self.sidebar.settings_requested.connect(self._on_settings_requested)
        
        self.control_panel.upload_requested.connect(self._handle_upload)
        self.control_panel.train_requested.connect(self._handle_train)
        self.control_panel.purge_requested.connect(self._handle_purge)

        
        # Inter-tab communication
        self.tab_data.row_selected.connect(self._on_row_selected)
        self.tab_input.predict_requested.connect(self._on_manual_predict_requested)
        self.tab_input.reset_requested.connect(lambda: self.tab_input.refresh_features(self.mc.model_manager.feature_names))

    # ── Signal Handlers: Mission Callbacks ──

    def _on_session_restored(self, df):
        """Strategic UI Linkage for session restoration."""
        self.tab_raw.update_data(df)
        self.tab_data.update_data(df)
        feats = self.mc.model_manager.feature_names
        if not feats:
            feats = [c for c in df.select_dtypes(include=['number']).columns if 'id' not in str(c).lower()]
        self.tab_input.refresh_features(feats)
        self.control_panel.refresh_models(os.path.join(self.user_data_path, "views", "models"))

    def _on_train_finished(self, result):
        success, msg = result
        if success:
            df = self.mc.data_manager.uploaded_df
            if df is not None:
                self.tab_raw.update_data(df)
                self.tab_data.update_data(df)
                self.tab_input.refresh_features(self.mc.model_manager.feature_names)
            
            lb = self.mc.model_manager.get_model_leaderboard(self.mc.last_dataset_path)
            self.tab_leaderboard.update_leaderboard(lb)
            self.control_panel.refresh_models(os.path.join(self.user_data_path, "views", "models"))
            self.banner.notify("AI COMMITTEE SYNCED & VERIFIED 🧬", "#10B981")
            self.update_status("Mission Calibrated", "green")
        else:
            self.update_status(f"Training Failed: {msg}", "red")

    def _on_forensic_audit_ready(self, results):
        self.tab_analysis.display_report(results['report'])
        self.tabs.setCurrentWidget(self.tab_analysis)
        self.tab_dashboard.update_metrics(confidence=results['confidence'], risk=results['risk_avg'], triage=results['triage'], consensus=results['consensus'])
        
        # Inject Cohort Audit Narrative
        narrative = f"""
        <b style='color:#3B82F6;'>[SYSTEM AUDIT COMPLETE]</b><br><br>
        The AI Committee has successfully audited the clinical cohort.<br><br>
        <b>Volume:</b> {results['triage']}<br>
        <b>Risk Quotient:</b> {results['risk_avg']:.1%}<br>
        <b>Consensus Validation:</b> {results['consensus']}<br><br>
        <i>Action:</i> Refer to the Performance Analysis hub for the deep metric breakdown.
        """
        self.tab_dashboard.update_narrative(narrative)
        
        self.tab_leaderboard.update_leaderboard(results['leaderboard'])
        self.banner.notify("COHORT FORENSIC AUDIT GENERATED 📂", "#10B981")

    def _on_prediction_finished(self, result, original_row):
        if not result: return
        pred, conf, risk = result
        triage = "IMMEDIATE BIOPSY" if risk > 0.8 else "FOLLOW-UP" if risk > 0.4 else "ROUTINE"
        consensus = "MALIGNANT" if pred == 1 else "BENIGN"
        
        self.tab_dashboard.update_metrics(confidence=conf, risk=risk, triage=triage, consensus=consensus)
        self.tab_input.update_results(consensus, risk)
        self.banner.notify(f"DIAGNOSTIC CONSENSUS: {consensus} ({risk:.1%})", "#3B82F6" if pred == 0 else "#EF4444")
        
        # Show Detailed Report in Analysis Tab
        theme = self.mc.settings_manager.get('theme', 'pure_dark')
        is_light = (theme == 'pure_light')
        p = Styles.PALETTES[theme]
        
        report = f"""<div style='color: {p["text_main"]}; font-family: sans-serif; padding: 20px;'>
            <h1 style='color: #3B82F6; font-size: 20px; border-bottom: 2px solid {p["border"]}; padding-bottom: 15px;'>PATIENT DIAGNOSTIC AUDIT</h1>
            <div style='background: {p["card_bg"]}; padding: 20px; border: 1px solid {p["border"]}; margin-bottom: 20px;'>
                <p><b>Decision:</b> <span style='color: {"#EF4444" if pred == 1 else "#10B981"};'>{consensus}</span></p>
                <p><b>Confidence:</b> {conf:.1%} | <b>Risk Index:</b> {risk:.1%}</p>
                <p><b>Triage:</b> {triage}</p>
            </div>
        </div>"""
        self.tab_analysis.display_report(report)
        
        # Sync Narrative back to Dashboard HUD
        dash_narrative = f"""
        <b style='color:#10B981;'>[SINGLE PATIENT PREDICTION FIRED]</b><br><br>
        The committee successfully analyzed real-time patient biomarker logic.<br><br>
        <b>Decision:</b> <span style='color: {"#EF4444" if pred == 1 else "#10B981"};'>{consensus}</span><br>
        <b>Severity Index:</b> {risk:.1%}<br>
        <b>Recommended Triage:</b> {triage}<br><br>
        <i>Note:</i> Continue screening subsequent patients or run a full cohort audit.
        """
        self.tab_dashboard.update_narrative(dash_narrative)

    def _on_counterfactual_ready(self, cf_result):
        if cf_result:
            self.console.log("XAI: Counterfactual generation finalized.", "blue")

    # ── UI Handle Redirects ──

    def _handle_train(self): self.mc.handle_train_mission()
    def _trigger_forensic_audit(self): self.mc.handle_forensic_audit(is_light=(self.mc.settings_manager.get('theme', 'pure_dark') == 'pure_light'))
    
    def _handle_purge(self):
        reply = QMessageBox.question(self, "SECURE CLINICAL WIPE 🛡️", "Purge all records?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.mc.purge_system():
                empty_df = pd.DataFrame()
                self.tab_raw.update_data(empty_df)
                self.tab_data.update_data(empty_df)
                self.tab_leaderboard.update_leaderboard([])
                self.tab_input.reset_requested.emit()
                self.tab_dashboard.update_metrics(confidence=0, risk=0, triage="PURIFIED", consensus="RESET")
                self.control_panel.refresh_models(os.path.join(self.user_data_path, "views", "models"))

    def _on_row_selected(self, row_dict):
        self.tab_input.set_patient_data(row_dict)
        self.tabs.setCurrentWidget(self.tab_input)
        self.mc.handle_individual_prediction(row_dict)
        self.mc.handle_counterfactual_mission(row_dict)

    def _on_manual_predict_requested(self, input_data):
        self.mc.handle_individual_prediction(input_data)

    def _handle_upload(self):
        """Clinical Data Ingress: Select research cohort."""
        path, _ = QFileDialog.getOpenFileName(self, "INGEST CLINICAL COHORT", "", 
                                              "Clinical Records (*.csv *.xlsx *.xls)")
        if path:
            self.mc.handle_ingestion(path)

    def _on_show_ai_chat(self):
        """Strategic AI Research Consultation Hub."""
        if not self.ai_modal:
            # Sync with Mission Controller's Settings Hub
            self.ai_modal = AIChatModal(
                parent=self, 
                settings_manager=self.mc.settings_manager
            )
        self.ai_modal.show()
        self.ai_modal.raise_()

    def _on_settings_requested(self):
        """System Calibration & UI skinning."""
        dialog = SettingsDialog(self.mc.settings_manager, parent=self)
        if dialog.exec():
            # Synchronize systemic settings
            new_cfg = dialog.get_settings()
            for k, v in new_cfg.items():
                self.mc.settings_manager.set(k, v)
            
            # Re-Skin Mission Interface
            self._apply_styles()
            self.banner.notify("SYSTEM CALIBRATION SYNCHRONIZED ⚙️", "#3B82F6")

    def _on_nav_requested(self, tab_index):
        if tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(tab_index)

    def _handle_viz(self, chart_type):
        df = self.mc.data_manager.uploaded_df
        is_light = self.mc.settings_manager.get('theme', 'pure_dark') == 'pure_light'
        viz = VisualizationModal(self, chart_type=chart_type, data=df, is_light=is_light)
        viz.exec()

    def _setup_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("Reset Session", self._handle_purge, "Ctrl+Shift+Delete")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        analysis_menu = menubar.addMenu("&Performance Graphs")
        analysis_menu.addAction("KDE Biomarker Distribution", lambda: self._handle_viz("KDE Distribution"))
        analysis_menu.addAction("Biomarker Correlation Heatmap", lambda: self._handle_viz("Heatmap"))
        analysis_menu.addAction("Electrochemical Biosensor Wave", lambda: self._handle_viz("Electrochemical Wave"))
        analysis_menu.addAction("Biomarker Calibration Curve", lambda: self._handle_viz("Calibration"))
        analysis_menu.addAction("t-SNE Patient Dimensionality Reduction", lambda: self._handle_viz("t-SNE"))
        analysis_menu.addSeparator()
        analysis_menu.addAction("Committee ROC-AUC Curves", lambda: self._handle_viz("ROC"))
        analysis_menu.addAction("AI Committee Comparison (Bars)", lambda: self._handle_viz("Bars"))
        analysis_menu.addAction("AI Metrics Spider (Radar)", lambda: self._handle_viz("Radar"))
        analysis_menu.addAction("Precision-Recall Analysis", lambda: self._handle_viz("PR Curve"))
        analysis_menu.addAction("AI Confusion Matrix", lambda: self._handle_viz("Confusion Matrix"))
        analysis_menu.addAction("Ensemble Reliability Calibration", lambda: self._handle_viz("Reliability"))
        
        theme_menu = menubar.addMenu("&Theme")
        theme_menu.addAction("Pure Dark (MissionControl)", lambda: self._handle_theme_change("pure_dark"))
        theme_menu.addAction("Pure Light (Laboratory)", lambda: self._handle_theme_change("pure_light"))
        
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Check for Updates", self._check_for_updates)
        help_menu.addAction("Documentation", self._show_documentation)

    def _check_for_updates(self):
        from utils.update_manager import UpdateManager
        # Pass status_callback to sync with dashboard alerts
        updater = getattr(self, '_updater', None)
        if not updater:
            self._updater = UpdateManager(parent=self, status_callback=self.update_status, current_version=APP_VERSION)
        self._updater.check_for_updates(silent=False)

    def _show_documentation(self):
        from ui.modals.ClinicalDocumentationModal import ClinicalDocumentationModal
        doc_modal = ClinicalDocumentationModal(parent=self, settings_manager=self.mc.settings_manager, version=APP_VERSION)
        doc_modal.exec()

    def _handle_theme_change(self, theme):
        self.mc.settings_manager.set('theme', theme)
        self._apply_styles()
        self.update_status(f"Theme Synced: {theme.upper()}", "green")

    def _show_critical_error(self, title, msg):
        QMessageBox.critical(self, title, msg)

    def update_status(self, msg, color="gray"):
        self.ui_status.setText(msg)
        color_map = {"orange": "#F59E0B", "blue": "#3B82F6", "green": "#10B981", "red": "#EF4444", "gray": "#71717A"}
        self.ui_status.setStyleSheet(f"color: {color_map.get(color, '#71717A')}; font-weight: bold;")
        self.console.log(msg, color)

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    import ctypes
    from PySide6.QtGui import QIcon
    import os

    # Force Windows to use our custom Icon on the Taskbar instead of the default Python logo
    if sys.platform == "win32":
        try:
            myappid = 'biorecon.clinical.dashboard.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    # Apply Global Window & Taskbar Icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
    fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    elif os.path.exists(fallback_path):
        app.setWindowIcon(QIcon(fallback_path))

    window = ClinicalApp()
    window.show()
    sys.exit(app.exec())
