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
        self.resize(550, 600)
        self.setMinimumSize(450, 500)
        self.setObjectName("SettingsDialog")
        
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
        self.header.setFixedHeight(95)
        self.header.setObjectName("SettingsHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(35, 0, 35, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(4)
        self.title_lbl = QLabel("🛠️ SYSTEM CALIBRATION")
        self.title_lbl.setStyleSheet("font-weight: 900; font-size: 16px; color: #3B82F6; letter-spacing: 2px;")
        title_v.addWidget(self.title_lbl)
        
        self.sub_lbl = QLabel("CLINICAL PREPROCESSING & UI SYNC CONFIGURATION")
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #71717A; font-weight: bold; text-transform: uppercase;")
        title_v.addWidget(self.sub_lbl)
        h_layout.addLayout(title_v)
        
        h_layout.addStretch()
        self.main_layout.addWidget(self.header)

        # ── 2. Content Pane (Tactile Forms) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(45, 35, 45, 35)
        container_layout.setSpacing(30)
        
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(25)
        form.setVerticalSpacing(30)
        
        # Preprocessing Suite
        self.outlier_toggle = QCheckBox("Automated Clinical Outlier Winzorization")
        self.outlier_toggle.setChecked(self.sm.get('outlier_removal', True))
        form.addRow(self.outlier_toggle)
        
        self.scaling_toggle = QCheckBox("Z-Score Multi-Feature Scaling")
        self.scaling_toggle.setChecked(self.sm.get('scaling_enabled', True))
        form.addRow(self.scaling_toggle)
        
        # Calibration Controls
        label_style = "font-weight: 800; font-size: 11px; letter-spacing: 0.5px; text-transform: uppercase;"
        
        lbl_ratio = QLabel("CALIBRATION SPLIT:")
        lbl_ratio.setStyleSheet(label_style)
        self.val_ratio_spin = QDoubleSpinBox()
        self.val_ratio_spin.setRange(0.1, 0.5)
        self.val_ratio_spin.setSingleStep(0.05)
        self.val_ratio_spin.setFixedHeight(38)
        self.val_ratio_spin.setValue(self.sm.get('val_ratio', 0.2))
        form.addRow(lbl_ratio, self.val_ratio_spin)
        
        lbl_skin = QLabel("MISSION INTERFACE SKIN:")
        lbl_skin.setStyleSheet(label_style)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["pure_dark", "pure_light"])
        self.theme_combo.setFixedHeight(38)
        self.theme_combo.setCurrentText(self.sm.get('theme', 'pure_dark'))
        form.addRow(lbl_skin, self.theme_combo)
        
        container_layout.addWidget(form_widget)
        container_layout.addStretch()
        
        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)

        # ── 3. Footer Area (Mission Command) ──
        self.footer = QFrame()
        self.footer.setFixedHeight(100)
        self.footer.setObjectName("SettingsFooter")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(35, 0, 35, 0)
        f_layout.setSpacing(20)
        
        self.abort_btn = QPushButton("ABORT")
        self.abort_btn.setFixedHeight(45)
        self.abort_btn.setFixedWidth(110)
        self.abort_btn.clicked.connect(self.reject)
        f_layout.addWidget(self.abort_btn)
        
        f_layout.addStretch()
        
        self.save_btn = QPushButton("SYNCHRONIZE SETTINGS")
        self.save_btn.setFixedHeight(45)
        self.save_btn.setFixedWidth(240)
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

        self.setStyleSheet(f"QDialog {{ background-color: {bg}; color: {txt}; }}")
        
        self.header.setStyleSheet(f"""
            QFrame#SettingsHeader {{ background-color: {p['bg_sidebar']}; border-bottom: 2px solid {border}; }}
        """)
        
        self.footer.setStyleSheet(f"""
            QFrame#SettingsFooter {{ background-color: {p['bg_sidebar']}; border-top: 2px solid {border}; }}
        """)
        
        self.title_lbl.setStyleSheet(f"font-weight: 900; font-size: 16px; color: {acc}; letter-spacing: 2px;")
        self.sub_lbl.setStyleSheet(f"font-size: 10px; color: {dim}; font-weight: bold; text-transform: uppercase;")
        
        # Checkboxes
        chk_style = f"""
            QCheckBox {{ color: {txt}; font-weight: bold; font-size: 13px; spacing: 12px; }}
            QCheckBox::indicator {{ width: 22px; height: 22px; border: 2px solid {border}; border-radius: 6px; background: {bg}; }}
            QCheckBox::indicator:checked {{ background: {acc}; border-color: {acc}; }}
        """
        self.outlier_toggle.setStyleSheet(chk_style)
        self.scaling_toggle.setStyleSheet(chk_style)
        
        # Inputs
        inp_style = f"""
            QDoubleSpinBox, QComboBox {{ background-color: {bg}; color: {txt}; border: 1px solid {border}; border-radius: 8px; padding: 0 12px; font-weight: bold; font-size: 13px; }}
            QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {acc}; }}
        """
        self.val_ratio_spin.setStyleSheet(inp_style)
        self.theme_combo.setStyleSheet(inp_style)
        
        # Buttons
        self.abort_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {border}; border-radius: 8px; color: {dim}; font-weight: 800; font-size: 11px; }}
            QPushButton:hover {{ background-color: {card}; color: {txt}; border-color: {acc}; }}
        """)
        
        self.save_btn.setStyleSheet(f"""
            QPushButton#PrimaryBtn {{ background-color: {acc}; border: none; border-radius: 8px; color: white; font-weight: 900; font-size: 11px; letter-spacing: 1px; }}
            QPushButton#PrimaryBtn:hover {{ background-color: #2563EB; }}
        """)

    def get_settings(self):
        return {
            'outlier_removal': self.outlier_toggle.isChecked(),
            'scaling_enabled': self.scaling_toggle.isChecked(),
            'val_ratio': self.val_ratio_spin.value(),
            'theme': self.theme_combo.currentText()
        }

    def get_settings(self):
        return {
            'outlier_removal': self.outlier_toggle.isChecked(),
            'scaling_enabled': self.scaling_toggle.isChecked(),
            'val_ratio': self.val_ratio_spin.value(),
            'theme': self.theme_combo.currentText()
        }
