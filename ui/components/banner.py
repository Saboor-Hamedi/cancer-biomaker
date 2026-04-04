from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PySide6.QtGui import QColor


class BannerNotification(QFrame):
    """Minimal, theme-aware notification banner — centered text, no border, no icon."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BannerNotification")
        self.setFixedHeight(48)
        self.setFixedWidth(520)

        # ── Soft shadow only (no border) ──
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("SYSTEM STATUS: READY")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Start hidden and off-screen
        self._theme = 'pure_dark'
        self._accent = "#3B82F6"
        self._apply_style()
        self.hide()

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────
    def apply_theme(self, palette: dict):
        """Sync with the active theme palette."""
        self._theme = 'pure_light' if palette.get('bg_main', '#000') == '#F8FAFC' else 'pure_dark'
        self._apply_style()

    def notify(self, message: str, color: str = "#3B82F6"):
        """Slide in a clean notification with theme-aware styling."""
        self._accent = color
        self.label.setText(message)
        self._apply_style(color)

        if self.parent():
            px = (self.parent().width() - self.width()) // 2
            self.move(px, -80)
            self.show()
            self.raise_()

            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(600)
            self.anim.setStartValue(QPoint(px, -80))
            self.anim.setEndValue(QPoint(px, 10))
            self.anim.setEasingCurve(QEasingCurve.OutCubic)
            self.anim.start()

            QTimer.singleShot(3800, self.dismiss)

    def dismiss(self):
        if not self.isVisible():
            return
        px = self.pos().x()
        self.close_anim = QPropertyAnimation(self, b"pos")
        self.close_anim.setDuration(400)
        self.close_anim.setStartValue(self.pos())
        self.close_anim.setEndValue(QPoint(px, -80))
        self.close_anim.setEasingCurve(QEasingCurve.InCubic)
        self.close_anim.finished.connect(self.hide)
        self.close_anim.start()

    # ─────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────
    def _apply_style(self, color: str = None):
        accent = color or self._accent
        is_light = (self._theme == 'pure_light')

        if is_light:
            bg       = "#FFFFFF"
            txt      = "#0F172A"          # Dark text on white
            font_weight = "700"
        else:
            bg       = "#18181B"
            txt      = "#FAFAFA"
            font_weight = "800"

        self.setStyleSheet(f"""
            QFrame#BannerNotification {{
                background-color: {bg};
                border-radius: 10px;
                border: none;
            }}
        """)

        self.label.setStyleSheet(f"""
            color: {txt};
            font-weight: {font_weight};
            font-size: 13px;
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
        """)
