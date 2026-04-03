import os
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton, QLabel, 
                             QSpacerItem, QSizePolicy, QHBoxLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

class ControlPanel(QFrame):
    """Modern Clinical Action Sidebar (Right Column)."""
    
    # Action Signals
    upload_requested = Signal()
    train_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ControlPanel")
        self.setFixedWidth(240)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(15)

        # ── 1. Committee Status HUD (Top) ──
        self.status_hud = QFrame()
        self.status_hud.setFixedHeight(140)
        self.status_hud.setObjectName("StatusHUD")
        sh_layout = QVBoxLayout(self.status_hud)
        sh_layout.setContentsMargins(15, 15, 15, 15)
        
        sh_title = QLabel("AI COMMITTEE STATUS")
        sh_title.setStyleSheet("font-weight: 800; font-size: 10px; color: #3B82F6; border: none; letter-spacing: 0.5px;")
        sh_layout.addWidget(sh_title)
        
        # This will be populated with model.pkl names
        self.models_list = QLabel("No Experts Detected")
        self.models_list.setWordWrap(True)
        self.models_list.setStyleSheet("font-size: 11px; color: #A1A1AA; border: none; line-height: 1.4;")
        sh_layout.addWidget(self.models_list)
        sh_layout.addStretch()
        
        layout.addWidget(self.status_hud)
        layout.addSpacing(10)

        # ── 2. Strategic Actions ──
        sec_actions = QLabel("RESEARCH & CLINICAL OPS")
        sec_actions.setStyleSheet("color: #52525B; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;")
        layout.addWidget(sec_actions)

        self.btn_upload = self._create_action_btn(" IMPORT CLINICAL DATA", "📁", self.upload_requested)
        self.btn_train = self._create_action_btn(" RE-TRAIN COMMITTEE", "🧠", self.train_requested)
        self.btn_reset = self._create_action_btn(" SECURE CLINICAL WIPE", "🧼", self.reset_requested)
        
        layout.addStretch()

        # ── Dashboard Visibility HUD (Bottom) ──
        self.lbl_ver = QLabel("VERSION 1.1.0 (QT6)")
        self.lbl_ver.setStyleSheet("color: #3F3F46; font-size: 10px; font-weight: bold; text-align: center;")
        self.lbl_ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_ver)

    def _create_action_btn(self, text, icon, signal):
        btn = QPushButton(f" {icon}  {text}")
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.03);
                color: #E4E4E7;
                border: 1px solid #27272A;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid #3F3F46;
            }
        """)
        btn.clicked.connect(signal.emit)
        self.layout().addWidget(btn)
        return btn

    def refresh_models(self, models_dir):
        """Scan clinical environment for trained Experts."""
        if not os.path.exists(models_dir):
            self.models_list.setText("No Trained Models Found")
            return
        
        models = [f for f in os.listdir(models_dir) if f.endswith(".pkl")]
        if not models:
            self.models_list.setText("Awaiting Calibration...")
        else:
            txt = "\n".join([f"✓ {m.replace('.pkl','').upper()}" for m in models[:5]])
            if len(models) > 5: txt += f"\n+ {len(models)-5} more expert(s)"
            self.models_list.setText(txt)
            self.models_list.setStyleSheet("font-size: 11px; color: #10B981; border: none; font-weight: bold;")

    def apply_theme(self, p):
        txt = p['text_main']
        dim = p['text_dim']
        acc = p['accent']
        self.setStyleSheet(f"QFrame#ControlPanel {{ background-color: {p['bg_sidebar']}; border-left: 1px solid {p['border']}; }}")
        self.status_hud.setStyleSheet(f"QFrame#StatusHUD {{ background-color: rgba(0,0,0,0.15); border: 1px solid {p['border']}; border-radius: 12px; }}")
        
        # Dynamic Action Buttons
        for btn in [self.btn_upload, self.btn_train, self.btn_reset]:
            btn.setStyleSheet(f"QPushButton {{ background-color: {p['card_bg']}; color: {txt}; border: 1px solid {p['border']}; border-radius: 8px; font-weight: bold; font-size: 11px; text-align: left; padding-left: 15px; }} "
                             f"QPushButton:hover {{ background-color: {p['border']}; color: {p['accent']}; }}")
