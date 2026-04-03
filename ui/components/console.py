from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class LogConsole(QFrame):
    """Modern Diagnostic Output Console for clinical telemetry."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogConsole")
        self.setFixedHeight(180)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Industrial Header ──
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(35)
        # Border-bottom will be set in apply_theme
        h_layout = QHBoxLayout(self.header_frame)
        h_layout.setContentsMargins(15, 0, 15, 0)
        
        title = QLabel("DIAGNOSTIC OUTPUT — REAL-TIME CLINICAL TELEMETRY")
        title.setStyleSheet("font-weight: 800; font-size: 10px; color: #71717A; letter-spacing: 0.5px;")
        h_layout.addWidget(title)
        
        h_layout.addStretch()
        
        btn_clear = QPushButton("CLEAR LOG")
        btn_clear.setFixedWidth(90)
        btn_clear.setFlat(True)
        btn_clear.setStyleSheet("font-weight: bold; font-size: 10px; color: #3B82F6;")
        btn_clear.clicked.connect(self.clear_logs)
        h_layout.addWidget(btn_clear)
        
        layout.addWidget(self.header_frame)

        # ── Output View ──
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background: transparent; border: none; font-family: 'Consolas', monospace; font-size: 12px; padding: 10px;")
        layout.addWidget(self.log_view)

    def log(self, message, color="gray"):
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_view.append(f"<span style='color: #52525B;'>{timestamp}</span> <span style='color: {color};'>{message}</span>")
        # Auto-scroll
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def clear_logs(self):
        self.log_view.clear()
        self.log("Console cleared — awaiting telemetry...", "gray")

    def apply_theme(self, p):
        """Invoke theme synchronization for the console."""
        theme_bg = p['card_bg']
        theme_border = p['border']
        self.setStyleSheet(f"QFrame#LogConsole {{ background-color: {theme_bg}; border-top: 2px solid {theme_border}; }}")
        self.header_frame.setStyleSheet(f"background-color: rgba(0,0,0,0.05); border-bottom: 1px solid {theme_border};")
        self.log_view.setStyleSheet(f"background: transparent; border: none; color: {p['text_main']}; font-family: 'Consolas', monospace; font-size: 12px; padding: 10px;")
