from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton, QLabel, 
                             QSpacerItem, QSizePolicy, QHBoxLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
import os

class Sidebar(QFrame):
    """Modern Industrial Mission Sidebar (Left Column)."""
    
    # Tactical Signals
    tab_changed = Signal(int)
    settings_requested = Signal()
    chat_requested = Signal()
    cohort_requested = Signal()

    def __init__(self, parent=None, user_data_path=""):
        super().__init__(parent)
        self.user_data_path = user_data_path
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)
        self.mission_btns = []
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 20, 16, 20)
        self._layout.setSpacing(8)

        # ── Clinical Brand ──
        self.logo_path = os.path.join(self.user_data_path, "logo.png")
        if os.path.exists(self.logo_path):
            logo_img = QLabel()
            logo_img.setPixmap(QIcon(self.logo_path).pixmap(48, 48))
            logo_img.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(logo_img)

        logo = QLabel("AI CLINICAL")
        logo.setStyleSheet("color: #71717A; font-weight: bold; font-size: 11px; letter-spacing: 1.5px;")
        self._layout.addWidget(logo)

        brand = QLabel("COMMITTEE")
        brand.setStyleSheet("font-size: 22px; font-weight: 800; color: #3B82F6;")
        self._layout.addWidget(brand)

        # Divider
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #27272A;")
        self._layout.addWidget(line)
        self._layout.addSpacing(20)

        # ── Tactical Missions ──
        # 🎯 Mission 1: Individual Diagnose (Input Tab)
        self.btn_diag = self._create_mission_btn(" INDIVIDUAL DIAGNOSE", "🎯", "#3B82F6")
        self.btn_diag.clicked.connect(lambda: self.tab_changed.emit(4))
        
        # 📊 Mission 2: Cohort Forensics (Performance Report)
        self.btn_cohort = self._create_mission_btn(" COHORT FORENSICS", "📊", "#8B5CF6")
        self.btn_cohort.clicked.connect(self.cohort_requested.emit)
        
        # 🤖 Mission 3: AI Research Chat (Consultation)
        self.btn_chat = self._create_mission_btn(" AI RESEARCH CHAT", "🤖", "#10B981")
        self.btn_chat.clicked.connect(self.chat_requested.emit)
        
        self._layout.addSpacing(30)
        
        # ── Secondary Actions ──
        # ⚙️ Mission: System Settings
        self.btn_settings = QPushButton(" ⚙️  SYSTEM SETTINGS")
        self.btn_settings.setFixedHeight(45)
        self.btn_settings.setStyleSheet("""
            QPushButton { background-color: transparent; color: #A1A1AA; border: none; border-radius: 8px; font-weight: bold; font-size: 11px; text-align: left; padding-left: 15px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.05); color: #FFFFFF; }
        """)
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self._layout.addWidget(self.btn_settings)
        
        self._layout.addStretch()

        # ── Dashboard Visibility HUD (Bottom) ──
        self.lbl_ver = QLabel("VERSION 1.1.0 (QT6)")
        self.lbl_ver.setStyleSheet("color: #3F3F46; font-size: 10px; font-weight: bold; text-align: center;")
        self.lbl_ver.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.lbl_ver)

    def _create_mission_btn(self, text, icon, color):
        """Creates a high-fidelity clinical mission gateway."""
        btn = QPushButton(f" {icon}  {text}")
        btn.setFixedHeight(52)
        # Professional Industrial Base Style
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #18181B;
                color: {color};
                border: 1px solid #27272A;
                border-radius: 8px;
                font-weight: 800;
                font-size: 11px;
                text-align: left;
                padding-left: 15px;
            }}
            QPushButton:hover {{
                background-color: #27272A;
                border-color: {color};
            }}
        """)
        self._layout.addWidget(btn)
        self.mission_btns.append({'btn': btn, 'color': color})
        return btn

    def apply_theme(self, p):
        """Dynamic thematic skinning for high-contrast visibility."""
        txt = p['text_main']
        acc = p['accent']
        dim = p['text_dim']
        border = p['border']
        self.setStyleSheet(f"QFrame#Sidebar {{ background-color: {p['bg_sidebar']}; border-right: 1px solid {border}; }}")
        
        # Skin Mission Hub
        for entry in self.mission_btns:
            btn = entry['btn']
            clr = entry['color']
            btn.setStyleSheet(f"QPushButton {{ background-color: {p['card_bg']}; color: {clr}; border: 1px solid {border}; border-radius: 8px; font-weight: 800; font-size: 11px; text-align: left; padding-left: 15px; }} "
                             f"QPushButton:hover {{ background-color: {p['bg_main']}; border-color: {clr}; }}")
        
        # Skin Secondary Actions
        self.btn_settings.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {dim}; border: none; border-radius: 8px; font-weight: bold; font-size: 11px; text-align: left; padding-left: 15px; }} "
                                       f"QPushButton:hover {{ background-color: {p['bg_main']}; color: {txt}; }}")
