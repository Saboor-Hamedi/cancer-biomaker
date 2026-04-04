from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QProgressBar, QScrollArea, QLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

class Card(QFrame):
    """Premium UI Card component for clinical metrics."""
    def __init__(self, title, help_text="", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(140)
        self._setup_ui(title, help_text)

    def _setup_ui(self, title, help_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Header
        h_layout = QHBoxLayout()
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #71717A; font-weight: 800; font-size: 10px; letter-spacing: 0.5px;")
        h_layout.addWidget(self.title_label)
        h_layout.addStretch()
        
        # Help Info
        if help_text:
            self.info_btn = QLabel("ⓘ")
            self.info_btn.setToolTip(help_text)
            self.info_btn.setStyleSheet("color: #3F3F46; font-size: 12px;")
            h_layout.addWidget(self.info_btn)
        
        layout.addLayout(h_layout)

        # Value Section
        self.value_label = QLabel("—")
        self.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: white; padding: 5px 0;")
        layout.addWidget(self.value_label)

        # Bottom Bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.subtext = QLabel("")
        self.subtext.setStyleSheet("color: #71717A; font-size: 11px;")
        layout.addWidget(self.subtext)

    def apply_theme(self, text_color, border_color, card_bg):
        """Dynamic skinning for individual cards."""
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {text_color}; padding: 5px 0;")
        self.setStyleSheet(f"QFrame#Card {{ background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 12px; }}")

    def update_value(self, val_str, progress_val=None, color=None):
        """Update diagnostic metric with forensic clarity."""
        self.value_label.setText(val_str)
        if progress_val is not None:
             self.progress.setValue(int(progress_val))
        if color:
             # Force status color override
             self.value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color}; padding: 5px 0;")
             self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 2px; }}")

class Dashboard(QWidget):
    """Clinical Forensic Dashboard View for PySide6."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # ── Row 1: Metrics Cards ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.card_conf = Card("Diagnostic Confidence", "AI Ensemble Agreement Strength")
        self.card_risk = Card("Aggregated Risk Index", "Pathogen Probability")
        self.card_triage = Card("Clinical Triage Action", "Immediate Medical Recommendation")
        self.card_consensus = Card("Committee Consensus", "Majority Vote Outcome")

        cards_layout.addWidget(self.card_conf)
        cards_layout.addWidget(self.card_risk)
        cards_layout.addWidget(self.card_triage)
        cards_layout.addWidget(self.card_consensus)
        
        main_layout.addLayout(cards_layout)

        # ── Row 2: Clinical Narrative ──
        reason_frame = QFrame()
        reason_frame.setObjectName("Card")
        reason_layout = QVBoxLayout(reason_frame)
        reason_layout.setContentsMargins(20, 20, 20, 20)
        
        reason_header = QLabel("AI CLINICAL REASONING & FORENSIC NARRATIVE")
        reason_header.setStyleSheet("color: #3B82F6; font-weight: 800; font-size: 11px;")
        reason_layout.addWidget(reason_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.narrative_label = QLabel("Awaiting clinical data upload...")
        self.narrative_label.setWordWrap(True)
        self.narrative_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.narrative_label.setStyleSheet("font-size: 15px; color: #E4E4E7; line-height: 1.6;")
        
        scroll.setWidget(self.narrative_label)
        reason_layout.addWidget(scroll)
        main_layout.addWidget(reason_frame, stretch=1)

        # ── Row 3: Status Summary ──
        status_footer = QHBoxLayout()
        self.lbl_data_info = QLabel("Master DB: Standby")
        self.lbl_data_info.setStyleSheet("color: #71717A; font-size: 11px;")
        status_footer.addWidget(self.lbl_data_info)
        status_footer.addStretch()
        self.lbl_status = QLabel("System Status: Ready")
        self.lbl_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
        status_footer.addWidget(self.lbl_status)
        main_layout.addLayout(status_footer)

    def apply_theme(self, p):
        """Invoke theme synchronization for the entire dashboard."""
        txt = p['text_main']
        border = p['border']
        bg = p['card_bg']
        
        # Header Info
        self.lbl_data_info.setStyleSheet(f"color: {p['text_dim']}; font-size: 11px;")
        self.lbl_status.setStyleSheet(f"color: {p['success']}; font-weight: bold; font-size: 11px;")
        
        # Sub-Cards
        for card in [self.card_conf, self.card_risk, self.card_triage, self.card_consensus]:
             card.apply_theme(txt, border, bg)

    def update_metrics(self, confidence=0, risk=0, triage="—", consensus="—"):
        c_val = f"{confidence:.1%}" if isinstance(confidence, float) else str(confidence) + "%"
        r_val = f"{risk:.1%}" if isinstance(risk, float) else str(risk) + "%"
        self.card_conf.update_value(c_val, confidence if isinstance(confidence, (int, float)) else 0, "#3B82F6")
        risk_color = "#EF4444" if risk > 0.7 else "#F59E0B" if risk > 0.3 else "#10B981"
        self.card_risk.update_value(r_val, risk if isinstance(risk, (int, float)) else 0, risk_color)
        self.card_triage.update_value(triage)
        self.card_consensus.update_value(consensus)

    def update_data_info(self, rows=0, cols=0, samples=0):
        self.lbl_data_info.setText(f"Master DB: {rows} Records | Features: {cols} | Samples: {samples}")

    def update_stats(self, bg='#09090B', text='#E4E4E7', grid='#27272A'):
        """Re-render the performance timeline with theme-aware colors."""
        pass  # Dashboard class uses narrative label, no matplotlib canvas here
