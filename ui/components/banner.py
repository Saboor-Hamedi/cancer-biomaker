from PySide6.QtWidgets import (QFrame, QLabel, QHBoxLayout, QGraphicsOpacityEffect, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer, Property
from PySide6.QtGui import QColor, QFont

class BannerNotification(QFrame):
    """Modern Industrial Fully Opaque Obsidian Alert Banner."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BannerNotification")
        self.setFixedHeight(65)
        self.setFixedWidth(600)
        
        # Opaque Obsidian Foundation — Fixed the 'white layer' and 'ghosting'
        self.setStyleSheet("""
            QFrame#BannerNotification {
                background-color: #09090B; 
                border-radius: 12px;
                border: 2px solid #3B82F6; 
            }
        """)
        
        # Depth Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(40)
        self.shadow.setColor(QColor(0, 0, 0, 240))
        self.shadow.setOffset(0, 10)
        self.setGraphicsEffect(self.shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)
        
        self.icon = QLabel("📡")
        self.icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.icon)
        
        self.label = QLabel("SYSTEM STATUS: READY")
        self.label.setStyleSheet("""
            color: #FAFAFA; 
            font-weight: 900; 
            font-size: 16px; 
            letter-spacing: 1px;
            text-transform: uppercase;
        """)
        layout.addWidget(self.label)
        layout.addStretch()
        
        self.hide()

    def notify(self, message, color="#3B82F6"):
        """Trigger a sliding high-contrast Obsidian alert."""
        self.label.setText(message)
        self.icon.setText("📡" if "#10B981" in color else "⚠️" if "#EF4444" in color else "💡")
        
        self.setStyleSheet(f"""
            QFrame#BannerNotification {{
                background-color: #09090B;
                border-radius: 12px;
                border: 2px solid {color};
            }}
        """)
        
        if self.parent():
            px = (self.parent().width() - self.width()) // 2
            self.move(px, -200) # Start further off-screen
            self.show()
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(750)
            self.anim.setStartValue(QPoint(px, -200))
            self.anim.setEndValue(QPoint(px, 30))
            self.anim.setEasingCurve(QEasingCurve.OutExpo)
            self.anim.start()
            QTimer.singleShot(4500, self.dismiss)

    def dismiss(self):
        if not self.isVisible(): return
        px = self.pos().x()
        self.close_anim = QPropertyAnimation(self, b"pos")
        self.close_anim.setDuration(500)
        self.close_anim.setStartValue(self.pos())
        self.close_anim.setEndValue(QPoint(px, -200)) # Increased off-screen distance to purge ghosting
        self.close_anim.finished.connect(self.hide)
        self.close_anim.start()
