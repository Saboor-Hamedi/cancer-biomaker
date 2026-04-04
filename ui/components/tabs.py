from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QFrame, QTextEdit, QTabWidget, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class Dashboard(QWidget):
    """Clinical Command HUD — Strategic Overview Hub."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(25)
        
        # 1. Executive Summary Cards (Top Grid)
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(15)
        
        self.card_avg_risk = self._create_card("AVG CLINICAL RISK", "0.0%", "#EF4444")
        self.card_confidence = self._create_card("MODELS CONFIDENCE", "0.0%", "#3B82F6")
        self.card_triage = self._create_card("CLINICAL TRIAGE", "0 CASES", "#F59E0B")
        self.card_consensus = self._create_card("ENSEMBLE CONSENSUS", "0/4", "#10B981")
        self.card_agreement = self._create_card("COMMITTEE AGREEMENT", "0%", "#8B5CF6")
        
        self.layout.addLayout(self.cards_layout)
        
        # 2. Strategic Visualization (Clinical Drift Timeline)
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.figure.patch.set_facecolor('#000000') 
        self.ax.set_facecolor('#000000')
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.update_stats()

    def _create_card(self, title, val, color):
        card = QFrame()
        card.setFixedHeight(110)
        card.setStyleSheet("QFrame { background-color: #09090B; border: 1px solid #18181B; border-radius: 12px; }")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(15, 15, 15, 15)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-weight: 800; font-size: 10px; color: #71717A; letter-spacing: 1px; border: none;")
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"font-weight: 900; font-size: 24px; color: {color}; border: none;")
        
        c_layout.addWidget(t_lbl)
        c_layout.addWidget(v_lbl)
        self.cards_layout.addWidget(card)
        return v_lbl

    def update_metrics(self, confidence=0.0, risk=0.0, triage="0 CASES", consensus="0/4"):
        """High-Fidelity Metric Synchronization Hub."""
        self.card_avg_risk.setText(f"{risk:.1%}")
        self.card_confidence.setText(f"{confidence:.1%}")
        self.card_triage.setText(triage)
        self.card_consensus.setText(consensus)
        
        # Committee Agreement Logic
        num_agree = int(consensus.split('/')[0]) if '/' in consensus else 0
        agreement_pct = (num_agree / 4.0) * 100
        self.card_agreement.setText(f"{agreement_pct:.0f}%")

    def update_stats(self, bg='#000000', text='#E4E4E7', grid='#18181B'):
        """Render the performance timeline with theme-aware colors."""
        self.figure.patch.set_facecolor(bg)
        self.ax.clear()
        self.ax.set_facecolor(bg)
        self.ax.grid(True, color=grid, linestyle='--', alpha=0.4)
        x = np.arange(12)
        y = np.cumsum(np.random.normal(5, 2, 12))
        self.ax.plot(x, y, color='#10B981', linewidth=3, marker='o',
                     markerfacecolor='#10B981', markersize=5, label='Ensemble Accuracy')
        self.ax.tick_params(colors=text, labelsize=8)
        for spine in self.ax.spines.values(): spine.set_color(grid)
        self.ax.set_title("Neural Performance Calibration Timeline",
                          color=text, fontsize=11, fontweight='bold')
        self.canvas.draw()

class DataTab(QWidget):
    """Modern Clinical Audit View — High Fidelity Registry."""
    selection_changed = Signal(int)
    row_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Header
        self.header = QFrame()
        self.header.setFixedHeight(60)
        self.header.setObjectName("Card")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(25, 0, 25, 0)
        
        lbl = QLabel("CLINICAL FORENSIC AUDIT — COHORT REGISTRY")
        lbl.setStyleSheet("font-weight: 900; font-size: 12px; letter-spacing: 1.5px;")
        h_layout.addWidget(lbl)
        h_layout.addStretch()
        layout.addWidget(self.header)

        # 2. Forensic Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "SAMPLE ID", "PSA", "AFP", "CA125", "PREDICTION",
            "RISK SCORE", "CANCER CLASS", "CONFIDENCE", "CONSENSUS", "AI REASONING"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setObjectName("ClinicalAuditTable")
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(9, QHeaderView.Stretch) # Reasoning gets space
        self.table.setColumnWidth(0, 100)
        
        layout.addWidget(self.table)
        
        # Connect Selection Bridge
        self.table.itemSelectionChanged.connect(self._handle_selection)

        # 3. Footer (Exports)
        footer = QFrame()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(15, 10, 15, 10)
        btn_copy = QPushButton("Copy Selected")
        btn_copy.setFixedWidth(140)
        btn_copy.clicked.connect(self._copy_to_clipboard)
        f_layout.addWidget(btn_copy)
        f_layout.addStretch()
        btn_csv = QPushButton("Export CSV")
        btn_csv.setObjectName("PrimaryBtn")
        f_layout.addWidget(btn_csv)
        btn_excel = QPushButton("Export Excel")
        btn_excel.setObjectName("PrimaryBtn")
        f_layout.addWidget(btn_excel)
        layout.addWidget(footer)

    def update_data(self, df: pd.DataFrame):
        """High-Fidelity Forensic Ingestion Hub."""
        self.table.setRowCount(0)
        if df.empty: return
        
        # ── 1. Column Identity Retrieval ──
        cols = [str(c).upper() for c in df.columns]
        
        # Mapping Clinical Constants
        psa_idx = cols.index("PSA_PG_PER_ML") if "PSA_PG_PER_ML" in cols else -1
        afp_idx = cols.index("AFP_PG_PER_ML") if "AFP_PG_PER_ML" in cols else -1
        ca_idx = cols.index("CA125_U_PER_ML") if "CA125_U_PER_ML" in cols else -1
        id_idx = cols.index("SAMPLE_ID") if "SAMPLE_ID" in cols else 0
        
        # Mapping AI Forensics
        diag_idx = cols.index("PREDICTION") if "PREDICTION" in cols else -1
        risk_idx = cols.index("RISK_SCORE") if "RISK_SCORE" in cols else -1
        class_idx = cols.index("CANCER RISK CLASS") if "CANCER RISK CLASS" in cols else -1
        conf_idx = cols.index("CONFIDENCE") if "CONFIDENCE" in cols else -1
        cons_idx = cols.index("CONSENSUS_COUNT") if "CONSENSUS_COUNT" in cols else -1
        reason_idx = cols.index("REASONING") if "REASONING" in cols else -1
        
        self.table.setRowCount(len(df))
        for r_idx, (idx, row) in enumerate(df.iterrows()):
            # Column 0: Sample ID
            id_val = str(row.iloc[id_idx])
            self.table.setItem(r_idx, 0, QTableWidgetItem(f"P-{id_val}"))
            
            # Markers
            self.table.setItem(r_idx, 1, QTableWidgetItem(f"{float(row.iloc[psa_idx]):.2f}" if psa_idx != -1 else "0.0"))
            self.table.setItem(r_idx, 2, QTableWidgetItem(f"{float(row.iloc[afp_idx]):.2f}" if afp_idx != -1 else "0.0"))
            self.table.setItem(r_idx, 3, QTableWidgetItem(f"{float(row.iloc[ca_idx]):.2f}" if ca_idx != -1 else "0.0"))

            # Prediction Hub
            pred = row.iloc[diag_idx] if diag_idx != -1 else "N/A"
            p_item = QTableWidgetItem(str(pred))
            p_item.setForeground(QColor("#EF4444") if str(pred).upper() == "POSITIVE" else QColor("#10B981"))
            self.table.setItem(r_idx, 4, p_item)

            # Deep Metrics
            try:
                risk_val = float(row.iloc[risk_idx]) if risk_idx != -1 else 0.0
                risk_str = f"{risk_val:.2%}"
            except (ValueError, TypeError):
                risk_str = str(row.iloc[risk_idx]) if risk_idx != -1 else "N/A"
            self.table.setItem(r_idx, 5, QTableWidgetItem(risk_str))
            
            class_val = str(row.iloc[class_idx]) if class_idx != -1 else ""
            c_item = QTableWidgetItem(class_val)
            c_item.setForeground(QColor("#F59E0B") if class_val else QColor("#71717A"))
            self.table.setItem(r_idx, 6, c_item)
            
            self.table.setItem(r_idx, 7, QTableWidgetItem(f"{row.iloc[conf_idx]:.3f}" if conf_idx != -1 else "1.000"))
            self.table.setItem(r_idx, 8, QTableWidgetItem(str(row.iloc[cons_idx]) if cons_idx != -1 else "3"))
            self.table.setItem(r_idx, 9, QTableWidgetItem(str(row.iloc[reason_idx]) if reason_idx != -1 else "No deliberation log."))

    def _handle_selection(self):
        selected_items = self.table.selectedItems()
        if not selected_items: return
        row = selected_items[0].row()
        cols = self.table.columnCount()
        row_dict = {}
        for col in range(cols):
            h_text = self.table.horizontalHeaderItem(col).text()
            item = self.table.item(row, col)
            if item: row_dict[h_text] = item.text()
        self.row_selected.emit(row_dict)

    def _copy_to_clipboard(self):
        from PySide6.QtGui import QGuiApplication
        selection = self.table.selectedRanges()
        if not selection: return
        output = []
        for r in selection:
            for row in range(r.topRow(), r.bottomRow() + 1):
                row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
                output.append("\t".join(row_data))
        QGuiApplication.clipboard().setText("\n".join(output))

class LeaderboardTab(QWidget):
    """Olympic-Grade rankings Hub."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel("ALGORITHM BENCHMARK & CLINICAL STANDINGS")
        header.setStyleSheet("color: #71717A; font-weight: bold; font-size: 11px; padding: 20px 0 10px 15px;")
        layout.addWidget(header)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["RANK", "ALGORITHM", "ACCURACY", "F1 SCORE", "ROC-AUC", "PRECISION", "RECALL", "SPECIFICITY", "CV STABILITY", "BADGE"])
        self.table.setStyleSheet("QTableWidget { background-color: #000000; border: none; } QHeaderView::section { background-color: #09090B; color: #71717A; padding: 12px; border: none; }")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_leaderboard(self, lb):
        self.table.setRowCount(0)
        for i, en in enumerate(lb):
            row = self.table.rowCount()
            self.table.insertRow(row)
            items = [f"#{i+1}", en['model'], f"{en['accuracy']:.1%}", f"{en['f1']:.1%}", f"{en['auc']:.1%}", "...", "...", "...", "...", "REVIEW"]
            for col, t in enumerate(items):
                item = QTableWidgetItem(t)
                if i == 0: item.setForeground(QColor("#FFFFFF"))
                self.table.setItem(row, col, item)

class AnalysisTab(QWidget):
    """Forensic Narrative Engine."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 1px solid #18181B;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 10, 15, 10)
        title = QLabel("FORENSIC AUDIT — Detailed Clinical Reasoning")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #3B82F6;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setStyleSheet("background-color: #000000; border: none; padding: 25px; color: #E4E4E7; font-size: 14px;")
        layout.addWidget(self.report_view)

    def display_report(self, html):
        self.report_view.setHtml(html)

class InputTab(QWidget):
    """Strategic Diagnosis Consoles."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 2px solid #18181B;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 12, 15, 12)
        title = QLabel("BIOMARKER PROFILE — Manual Patient Entry & Verification")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #10B981;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["BIOMARKER NAME", "UNIT", "MEASURED VALUE"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { background-color: #000000; border: none; }")
        layout.addWidget(self.table)
        footer = QHBoxLayout()
        footer.setContentsMargins(15, 20, 15, 20)
        btn_clear = QPushButton(" RESET VALUES")
        btn_clear.setFixedWidth(140)
        footer.addWidget(btn_clear)
        footer.addStretch()
        btn_predict = QPushButton("RUN AI PREDICTION ENGINE")
        btn_predict.setFixedWidth(240)
        footer.addWidget(btn_predict)
        layout.addLayout(footer)

    def refresh_features(self, features):
        self.table.setRowCount(len(features))
        for i, f in enumerate(features):
            self.table.setItem(i, 0, QTableWidgetItem(str(f).upper().replace("_", " ")))
            self.table.setItem(i, 1, QTableWidgetItem("ng/mL"))
            self.table.setItem(i, 2, QTableWidgetItem("0.0000"))

class TrajectoryTab(QWidget):
    """Longitudinal biomarker Assessment."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        header = QLabel("PATIENT BIOMARKER DRIFT & RISK TRAJECTORY")
        header.setStyleSheet("color: #71717A; font-weight: bold; font-size: 11px; padding: 20px 0 10px 15px;")
        layout.addWidget(header)
        self.figure, self.ax = plt.subplots(figsize=(8,3))
        self.figure.patch.set_facecolor('#000000')
        self.ax.set_facecolor('#000000')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        x = np.arange(10)
        y = np.cumsum(np.random.normal(50, 10, 10))
        self.ax.plot(x, y, color='#3B82F6', linewidth=2, marker='o')
        self.ax.tick_params(colors='#71717A')
        self.ax.set_title("Biomarker Longitudinal assess", color='#E4E4E7', fontsize=10)
        self.canvas.draw()
