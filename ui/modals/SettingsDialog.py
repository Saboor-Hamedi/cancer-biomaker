from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
                               QWidget, QFormLayout, QCheckBox, QDoubleSpinBox, 
                               QComboBox, QPushButton, QScrollArea)
from PySide6.QtCore import Qt
from ui.styles import Styles

class SettingsDialog(QDialog):
    """
    Industrial-Grade Clinical Settings Hub.
    Synchronized with the AI Research Copilot aesthetic for high-fidelity mission control.
    """
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.sm = settings_manager
        
        self.setWindowTitle("SYSTEM CALIBRATION & CLINICAL SETTINGS")
        self.resize(650, 750)
        self.setMinimumSize(550, 650)
        self.setObjectName("SettingsDialog")
        
        # ── Step 0: Windowing Architecture (Mission Specific) ──
        self.setWindowFlags(self.windowFlags() | 
                            Qt.WindowMinimizeButtonHint | 
                            Qt.WindowMaximizeButtonHint | 
                            Qt.WindowCloseButtonHint)
        
        # 🧪 Apply Initial Theme Skin
        theme = settings_manager.get('theme', 'pure_dark')
        self.palette = Styles.PALETTES.get(theme, Styles.PALETTES['pure_dark'])
        
        self._setup_ui()
        self.apply_theme(self.palette)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── 1. Top Header (Industrial Action Bar) ──
        self.header = QFrame()
        self.header.setFixedHeight(105)
        self.header.setObjectName("SettingsHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(40, 0, 40, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(4)
        title_v.setAlignment(Qt.AlignVCenter)
        
        self.title_lbl = QLabel("🛠️ SYSTEM CALIBRATION")
        self.title_lbl.setStyleSheet("font-weight: 900; font-size: 18px; color: #3B82F6; letter-spacing: 3px;")
        title_v.addWidget(self.title_lbl)
        
        self.sub_lbl = QLabel("CLINICAL PREPROCESSING & UI SYNC CONFIGURATION")
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #71717A; font-weight: bold; text-transform: uppercase;")
        title_v.addWidget(self.sub_lbl)
        h_layout.addLayout(title_v)
        
        h_layout.addStretch()
        self.main_layout.addWidget(self.header)

        # ── 2. Content Pane (Tactile Forms Hub) ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("SettingsScroll")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(60, 40, 60, 40)
        container_layout.setSpacing(40)
        
        # ── Preprocessing Suite ──
        prep_group = QWidget()
        prep_layout = QVBoxLayout(prep_group)
        prep_layout.setSpacing(15)
        
        prep_title = QLabel("CLINICAL PREPROCESSING")
        prep_title.setStyleSheet("font-weight: 800; font-size: 11px; color: #3B82F6; letter-spacing: 1px;")
        prep_layout.addWidget(prep_title)
        
        self.outlier_toggle = QCheckBox("Automated Clinical Outlier Winzorization")
        self.outlier_toggle.setChecked(self.sm.get('outlier_removal', True))
        prep_layout.addWidget(self.outlier_toggle)
        
        self.scaling_toggle = QCheckBox("Z-Score Multi-Feature Scaling")
        self.scaling_toggle.setChecked(self.sm.get('scaling_enabled', True))
        prep_layout.addWidget(self.scaling_toggle)
        
        container_layout.addWidget(prep_group)
        
        # ── Calibration Controls ──
        cal_group = QWidget()
        cal_layout = QFormLayout(cal_group)
        cal_layout.setSpacing(25)
        cal_layout.setVerticalSpacing(30)
        
        cal_title = QLabel("CALIBRATION PARAMETERS")
        cal_title.setStyleSheet("font-weight: 800; font-size: 11px; color: #10B981; letter-spacing: 1px;")
        cal_layout.addRow(cal_title)
        
        label_style = "font-weight: 800; font-size: 11px; letter-spacing: 0.5px; text-transform: uppercase;"
        
        lbl_ratio = QLabel("CALIBRATION SPLIT:")
        lbl_ratio.setStyleSheet(label_style)
        self.val_ratio_spin = QDoubleSpinBox()
        self.val_ratio_spin.setRange(0.1, 0.5)
        self.val_ratio_spin.setSingleStep(0.05)
        self.val_ratio_spin.setFixedHeight(45)
        self.val_ratio_spin.setValue(self.sm.get('validation_split', 0.2))
        cal_layout.addRow(lbl_ratio, self.val_ratio_spin)
        
        lbl_skin = QLabel("MISSION INTERFACE SKIN:")
        lbl_skin.setStyleSheet(label_style)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["pure_dark", "pure_light"])
        self.theme_combo.setFixedHeight(45)
        self.theme_combo.setCurrentText(self.sm.get('theme', 'pure_dark'))
        cal_layout.addRow(lbl_skin, self.theme_combo)
        
        container_layout.addWidget(cal_group)
        container_layout.addStretch()
        
        self.scroll.setWidget(container)
        self.main_layout.addWidget(self.scroll)

        # ── 3. Footer Area (Mission Command) ──
        self.footer = QFrame()
        self.footer.setFixedHeight(120)
        self.footer.setObjectName("SettingsFooter")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(40, 0, 40, 0)
        f_layout.setSpacing(20)
        
        self.abort_btn = QPushButton("ABORT MISSION")
        self.abort_btn.setFixedHeight(50)
        self.abort_btn.setFixedWidth(160)
        self.abort_btn.clicked.connect(self.reject)
        f_layout.addWidget(self.abort_btn)
        
        f_layout.addStretch()
        
        self.save_btn = QPushButton("SYNCHRONIZE SETTINGS")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setFixedWidth(280)
        self.save_btn.setObjectName("PrimaryBtn")
        self.save_btn.clicked.connect(self.accept)
        f_layout.addWidget(self.save_btn)
        
        self.main_layout.addWidget(self.footer)

    def apply_theme(self, p):
        """High-fidelity clinical theme synchronization."""
        bg = p['bg_main']
        card = p['card_bg']
        txt = p['text_main']
        dim = p['text_dim']
        acc = p['accent']
        border = p['border']
        sidebar_bg = p.get('bg_sidebar', border)

        self.setStyleSheet(f"QDialog {{ background-color: {bg}; color: {txt}; }}")
        
        self.header.setStyleSheet(f"""
            QFrame#SettingsHeader {{ background-color: {sidebar_bg}; border-bottom: 2px solid {border}; }}
        """)
        
        self.footer.setStyleSheet(f"""
            QFrame#SettingsFooter {{ background-color: {sidebar_bg}; border-top: 2px solid {border}; }}
        """)
        
        self.scroll.setStyleSheet(f"QScrollArea {{ background-color: {bg}; border: none; }}")
        
        self.title_lbl.setStyleSheet(f"font-weight: 900; font-size: 18px; color: {acc}; letter-spacing: 3px;")
        self.sub_lbl.setStyleSheet(f"font-size: 10px; color: {dim}; font-weight: bold; text-transform: uppercase;")
        
        # Checkboxes
        chk_style = f"""
            QCheckBox {{ color: {txt}; font-weight: bold; font-size: 14px; spacing: 15px; border: none; padding: 10px 0; }}
            QCheckBox::indicator {{ width: 24px; height: 24px; border: 2px solid {border}; border-radius: 7px; background: {bg}; }}
            QCheckBox::indicator:checked {{ background: {acc}; border-color: {acc}; image: url(none); }}
            QCheckBox::indicator:unchecked:hover {{ border-color: {acc}; }}
        """
        self.outlier_toggle.setStyleSheet(chk_style)
        self.scaling_toggle.setStyleSheet(chk_style)
        
        # Inputs
        inp_style = f"""
            QDoubleSpinBox, QComboBox {{ 
                background-color: {bg}; 
                color: {txt}; 
                border: 1px solid {border}; 
                border-radius: 10px; 
                padding: 0 15px; 
                font-weight: bold; 
                font-size: 13px; 
            }}
            QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {acc}; border-width: 2px; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
        """
        self.val_ratio_spin.setStyleSheet(inp_style)
        self.theme_combo.setStyleSheet(inp_style)
        
        # Buttons
        self.abort_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {border}; border-radius: 10px; color: {dim}; font-weight: 800; font-size: 11px; letter-spacing: 1px; }}
            QPushButton:hover {{ background-color: {card}; color: {txt}; border-color: {acc}; }}
        """)
        
        self.save_btn.setStyleSheet(f"""
            QPushButton#PrimaryBtn {{ background-color: {acc}; border: none; border-radius: 10px; color: white; font-weight: 900; font-size: 12px; letter-spacing: 1.5px; }}
            QPushButton#PrimaryBtn:hover {{ background-color: #2563EB; }}
        """)

    def get_settings(self):
        return {
            'outlier_removal': self.outlier_toggle.isChecked(),
            'scaling_enabled': self.scaling_toggle.isChecked(),
            'validation_split': self.val_ratio_spin.value(),
            'theme': self.theme_combo.currentText()
        }
