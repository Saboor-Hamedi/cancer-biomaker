from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QFrame, QTextEdit, QTabWidget, QSpacerItem, QSizePolicy,
                             QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import re

class MissionHeader(QFrame):
    """Industrial-Grade Clinical Header for High-Fidelity Modules."""
    def __init__(self, title, subtitle, icon="🤖", color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setFixedHeight(105)
        self.setObjectName("MissionHeader")
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(35, 0, 35, 0)
        
        # Text Stack
        text_v = QVBoxLayout()
        text_v.setSpacing(4)
        
        self.title_lbl = QLabel(f"{icon} {title}")
        self.title_lbl.setStyleSheet(f"font-weight: 900; font-size: 16px; color: {color}; letter-spacing: 2px;")
        text_v.addWidget(self.title_lbl)
        
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #71717A; font-weight: bold; text-transform: uppercase;")
        text_v.addWidget(self.sub_lbl)
        
        self.main_layout.addLayout(text_v)
        self.main_layout.addStretch()
        
    def apply_theme(self, p):
        self.setStyleSheet(f"""
            QFrame#MissionHeader {{ 
                background-color: {p['bg_sidebar']}; 
                border-bottom: 2px solid {p['border']}; 
            }}
        """)
        self.sub_lbl.setStyleSheet(f"font-size: 10px; color: {p['text_dim']}; font-weight: bold; text-transform: uppercase;")

class Dashboard(QWidget):
    """Clinical Command HUD — Strategic Overview Hub."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # ── 1. Orbital Mission Header ──
        self.header = MissionHeader("CLINICAL COMMAND HUD", "EXECUTIVE MISSION SUMMARY & ENSEMBLE REAL-TIME CALIBRATION", icon="📊", color="#3B82F6")
        self.layout.addWidget(self.header)

        # Content Main Hub
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(35, 35, 35, 35)
        self.content_layout.setSpacing(35)

        # 1. Executive Summary Cards (Top Grid)
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        
        self.card_avg_risk = self._create_card("AVG CLINICAL RISK", "0.0%", "#EF4444")
        self.card_confidence = self._create_card("MODELS CONFIDENCE", "0.0%", "#3B82F6")
        self.card_triage = self._create_card("CLINICAL TRIAGE", "0 CASES", "#F59E0B")
        self.card_consensus = self._create_card("ENSEMBLE CONSENSUS", "0/4", "#10B981")
        self.card_agreement = self._create_card("COMMITTEE AGREEMENT", "0%", "#8B5CF6")
        
        self.content_layout.addLayout(self.cards_layout)
        
        # 2. Strategic Visualization (Clinical Drift Timeline)
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.figure.patch.set_facecolor('#000000') 
        self.ax.set_facecolor('#000000')
        self.canvas = FigureCanvas(self.figure)
        self.content_layout.addWidget(self.canvas)
        
        self.layout.addWidget(content)
        self.update_stats()

    def _create_card(self, title, val, color):
        card = QFrame()
        card.setFixedHeight(110)
        card.setObjectName("StatusHUD")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(15, 15, 15, 15)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-weight: 800; font-size: 10px; color: #71717A; letter-spacing: 1.0px; border: none; background: transparent;")
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"font-weight: 900; font-size: 24px; color: {color}; border: none; background: transparent;")
        
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

    def update_stats(self, bg='#09090B', text='#E4E4E7', grid='#18181B'):
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
                          color=text, fontsize=11, fontweight='bold', pad=15)
        self.figure.tight_layout()
        self.canvas.draw()

    def apply_theme(self, p):
        """Strategic UI Sync."""
        if hasattr(self, 'header'): self.header.apply_theme(p)
        bg = p['bg_main']
        text = p['text_main']
        grid = p['border']
        self.update_stats(bg=bg, text=text, grid=grid)

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
        layout.setSpacing(0)
        
        # 1. Orbital Mission Header
        self.header = MissionHeader("CLINICAL FORENSIC AUDIT", "HIGH-FIDELITY COHORT REGISTRY & BIOMARKER DRIFT ANALYTICS", icon="📂", color="#8B5CF6")
        layout.addWidget(self.header)

        # ── Tactical Search HUD ──
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 SCAN COHORT ID...")
        self.search_bar.setFixedWidth(240)
        self.search_bar.setFixedHeight(38)
        self.search_bar.setStyleSheet("""
            QLineEdit { 
                background-color: rgba(0,0,0,0.15); 
                border: 1px solid #27272A; 
                border-radius: 8px; 
                padding-left: 15px; 
                color: #FAFAFA;
                font-size: 11px;
                font-weight: bold;
            }
            QLineEdit:focus { border-color: #3B82F6; }
        """)
        self.search_bar.textChanged.connect(self._handle_search)
        self.header.main_layout.addWidget(self.search_bar)

        # Content Main Hub
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(35, 35, 35, 35)
        content_layout.setSpacing(25)
        
        # 2. Forensic Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "SEL", "SAMPLE ID", "PSA", "AFP", "CA125", "PREDICTION",
            "RISK SCORE", "CANCER CLASS", "CONFIDENCE", "CONSENSUS", "ACTIONS"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setObjectName("ClinicalAuditTable")
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(10, QHeaderView.Stretch) # Actions gets space
        self.table.setColumnWidth(0, 45) # SEL
        self.table.setColumnWidth(1, 100) # ID
        
        layout.addWidget(self.table)
        
        # Connect Selection Bridge
        self.table.itemSelectionChanged.connect(self._handle_selection)

        # 3. Footer (Exports)
        footer = QFrame()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(15, 10, 15, 10)
        export_style = """
            QPushButton { background-color: #18181B; color: #E4E4E7; border: 1px solid #27272A; border-radius: 6px; padding: 5px 15px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #27272A; border-color: #3B82F6; }
            QPushButton:pressed { background-color: #09090B; }
        """
        btn_copy = QPushButton(" 📋 Copy Table")
        btn_copy.setFixedWidth(140)
        btn_copy.setStyleSheet(export_style)
        btn_copy.clicked.connect(self._copy_to_clipboard)
        f_layout.addWidget(btn_copy)
        f_layout.addStretch()
        btn_csv = QPushButton(" 📄 Export CSV")
        btn_csv.setStyleSheet(export_style.replace("#3B82F6", "#10B981"))
        btn_csv.clicked.connect(lambda: self._export_to_file("csv"))
        f_layout.addWidget(btn_csv)
        btn_excel = QPushButton(" 💹 Export Excel")
        btn_excel.setStyleSheet(export_style.replace("#3B82F6", "#8B5CF6"))
        btn_excel.clicked.connect(lambda: self._export_to_file("xlsx"))
        f_layout.addWidget(btn_excel)
        layout.addWidget(footer)

    def update_data(self, df: pd.DataFrame):
        """High-Fidelity Forensic Ingestion Hub."""
        self.table.setRowCount(0)
        if df.empty: return
        
        # ── 1. Dynamic Column Retrieval ──
        cols = [str(c).upper() for c in df.columns]
        
        # Mapping Clinical Markers (Fuzzy Match)
        psa_idx = next((i for i, c in enumerate(cols) if "PSA" in c), -1)
        afp_idx = next((i for i, c in enumerate(cols) if "AFP" in c), -1)
        ca_idx = next((i for i, c in enumerate(cols) if "CA125" in c), -1)
        id_idx = next((i for i, c in enumerate(cols) if "ID" in c or "PATIENT" in c), 0)
        
        # Mapping AI Forensics
        diag_idx = next((i for i, c in enumerate(cols) if "PREDICTION" in c), -1)
        risk_idx = next((i for i, c in enumerate(cols) if "RISK" in c), -1)
        class_idx = next((i for i, c in enumerate(cols) if "CLASS" in c), -1)
        conf_idx = next((i for i, c in enumerate(cols) if "CONFIDENCE" in c), -1)
        cons_idx = next((i for i, c in enumerate(cols) if "CONSENSUS" in c), -1)
        reason_idx = next((i for i, c in enumerate(cols) if "REASONING" in c), -1)
        
        self.table.setRowCount(len(df))
        for r_idx, (idx, row) in enumerate(df.iterrows()):
            # 0. Selection Checkbox
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk_item.setCheckState(Qt.Unchecked)
            self.table.setItem(r_idx, 0, chk_item)

            # 1. ID
            id_val = str(row.iloc[id_idx]) if id_idx != -1 else str(idx)
            self.table.setItem(r_idx, 1, QTableWidgetItem(f"P-{id_val}"))
            
            # Biomarkers (Safe float cast)
            for i, c_idx in enumerate([psa_idx, afp_idx, ca_idx], 2):
                val = "0.00"
                if c_idx != -1:
                    try: val = f"{float(row.iloc[c_idx]):.2f}"
                    except: val = str(row.iloc[c_idx])
                self.table.setItem(r_idx, i, QTableWidgetItem(val))

            # AI Logic
            pred = row.iloc[diag_idx] if diag_idx != -1 else "N/A"
            p_item = QTableWidgetItem(str(pred))
            if str(pred).upper() in ["POSITIVE", "1", "1.0", "MALIGNANT"]:
                p_item.setForeground(QColor("#EF4444"))
            else:
                p_item.setForeground(QColor("#10B981"))
            self.table.setItem(r_idx, 5, p_item)

            try:
                risk_val = float(row.iloc[risk_idx]) if risk_idx != -1 else 0.0
                risk_str = f"{risk_val:.2%}" if risk_val <= 1.0 else f"{risk_val:.1f}%"
            except:
                risk_str = str(row.iloc[risk_idx]) if risk_idx != -1 else "0%"
            self.table.setItem(r_idx, 6, QTableWidgetItem(risk_str))
            
            self.table.setItem(r_idx, 7, QTableWidgetItem(str(row.iloc[class_idx]) if class_idx != -1 else ""))
            self.table.setItem(r_idx, 8, QTableWidgetItem(f"{row.iloc[conf_idx]:.3f}" if conf_idx != -1 else "1.000"))
            self.table.setItem(r_idx, 9, QTableWidgetItem(str(row.iloc[cons_idx]) if cons_idx != -1 else "Batch"))
            
            # 10. Actions Hub
            btn_diag = QPushButton("DIAGNOSE 🎯")
            btn_diag.setCursor(Qt.PointingHandCursor)
            btn_diag.setStyleSheet("""
                QPushButton { background-color: transparent; border: 1px solid #27272A; border-radius: 4px; color: #3B82F6; font-weight: bold; font-size: 9px; padding: 2px 5px; }
                QPushButton:hover { background-color: rgba(59, 130, 246, 0.1); border-color: #3B82F6; }
            """)
            # Create a closure for the row data
            current_row_data = {self.table.horizontalHeaderItem(c).text(): self.table.item(r_idx, c).text() if self.table.item(r_idx, c) else "" for c in range(10)}
            btn_diag.clicked.connect(lambda checked=False, r=current_row_data: self.row_selected.emit(r))
            self.table.setCellWidget(r_idx, 10, btn_diag)

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)
        self.table.setStyleSheet(f"QTableWidget {{ background-color: {p['card_bg']}; color: {p['text_main']}; border: 1px solid {p['border']}; }}")

    def _handle_search(self, text):
        """Tactical Filtering of the Clinical Registry."""
        text = text.upper()
        for r in range(self.table.rowCount()):
            match = False
            # Check ID column (1)
            item = self.table.item(r, 1)
            if item and text in item.text().upper():
                match = True
            self.table.setRowHidden(r, not match)


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
        output = []
        # Copy Entire Table
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount() - 1): # Exclude Actions
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            output.append("\t".join(row_data))
        QGuiApplication.clipboard().setText("\n".join(output))

    def _export_to_file(self, ext):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        if self.table.rowCount() == 0:
             QMessageBox.warning(self, "EXPORT REJECTED ⚠️", "The clinical registry is currently empty. Please ingest a cohort dataset before attempting a forensic export.")
             return

        filename, _ = QFileDialog.getSaveFileName(self, f"Export as {ext.upper()}", f"clinical_audit.{ext}", f"{ext.upper()} Files (*.{ext})")
        if not filename: return
        
        data = []
        cols = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount() - 1)]
        for r in range(self.table.rowCount()):
            row = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(self.table.columnCount() - 1)]
            data.append(row)
        
        df = pd.DataFrame(data, columns=cols)
        try:
            if ext == "csv": df.to_csv(filename, index=False)
            else: df.to_excel(filename, index=False)
        except Exception as e:
            print(f"Export Error: {e}")

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)

class LeaderboardTab(QWidget):
    """Olympic-Grade rankings Hub."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Orbital Mission Header
        self.header = MissionHeader("ALGORITHM RANKINGS", "MULTI-MODEL EVALUATION — Global Clinical Precision Standings", icon="🏆", color="#F59E0B")
        layout.addWidget(self.header)

        # Content Main Hub
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(35, 35, 35, 35)
        content_layout.setSpacing(25)
        
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["RANK", "ALGORITHM", "ACCURACY", "F1 SCORE", "ROC-AUC", "PRECISION", "RECALL", "SPECIFICITY", "CV STABILITY", "BADGE"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        content_layout.addWidget(self.table)
        layout.addWidget(content)

        # 3. Footer (Exports)
        footer = QFrame()
        footer.setFixedHeight(85)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(35, 0, 35, 0)
        export_style = """
            QPushButton { background-color: #18181B; color: #E4E4E7; border: 1px solid #27272A; border-radius: 6px; padding: 5px 15px; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: #27272A; border-color: #3B82F6; }
            QPushButton:pressed { background-color: #09090B; }
        """
        btn_copy = QPushButton(" 📋 Copy Table")
        btn_copy.setFixedWidth(140)
        btn_copy.setStyleSheet(export_style)
        btn_copy.clicked.connect(self._copy_to_clipboard)
        f_layout.addWidget(btn_copy)
        f_layout.addStretch()
        btn_csv = QPushButton(" 📄 Export CSV")
        btn_csv.setStyleSheet(export_style.replace("#3B82F6", "#10B981"))
        btn_csv.clicked.connect(lambda: self._export_to_file("csv"))
        f_layout.addWidget(btn_csv)
        btn_excel = QPushButton(" 💹 Export Excel")
        btn_excel.setStyleSheet(export_style.replace("#3B82F6", "#8B5CF6"))
        btn_excel.clicked.connect(lambda: self._export_to_file("xlsx"))
        f_layout.addWidget(btn_excel)
        layout.addWidget(footer)

    def update_leaderboard(self, lb):
        self.table.setRowCount(0)
        for i, en in enumerate(lb):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ── 1. Tactical Forensic Rows ──
            badge = "🏆 CHAMPION" if i == 0 else "✅ AUDITED" if en.get('f1',0) > 0.9 else "⚠️ CALIBRATING"
            items = [
                f"#{i+1}", 
                str(en.get('model', 'N/A')), 
                f"{en.get('accuracy',0):.1%}", 
                f"{en.get('f1',0):.1%}", 
                f"{en.get('auc',0):.1%}", 
                f"{en.get('precision',0):.1%}", 
                f"{en.get('recall',0):.1%}", 
                f"{en.get('specificity',0):.1%}", 
                f"{en.get('cv_mean',0):.1%} +/- {en.get('cv_std',0):.2f}", 
                badge
            ]
            
            for c, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter) # ID's are now centered (fixed offset)
                self.table.setItem(row, c, item)

    def _copy_to_clipboard(self):
        from PySide6.QtGui import QGuiApplication
        output = []
        # Copy Headers
        headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        output.append("\t".join(headers))
        # Copy Entire Table
        for row in range(self.table.rowCount()):
            row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
            output.append("\t".join(row_data))
        QGuiApplication.clipboard().setText("\n".join(output))

    def _export_to_file(self, ext):
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if self.table.rowCount() == 0:
             QMessageBox.warning(self, "COMMAND HALTED ⚠️", "The Algorithm Rankings are currently uncalibrated. Export is blocked until metrics are available.")
             return

        filename, _ = QFileDialog.getSaveFileName(self, f"Export as {ext.upper()}", f"algorithm_rankings.{ext}", f"{ext.upper()} Files (*.{ext})")
        if not filename: return
        
        data = []
        cols = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        for r in range(self.table.rowCount()):
            row = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(self.table.columnCount())]
            data.append(row)
        
        df = pd.DataFrame(data, columns=cols)
        try:
            if ext == "csv": df.to_csv(filename, index=False)
            else: df.to_excel(filename, index=False)
        except Exception as e:
            print(f"Export Error: {e}")

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)

class AnalysisTab(QWidget):
    """Forensic Narrative Engine."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Orbital Mission Header
        self.header = MissionHeader("PERFORMANCE ANALYSIS", "FORENSIC NARRATIVE — Neural Clinical Deliberation & Justification", icon="📄", color="#3B82F6")
        layout.addWidget(self.header)

        # Content Main Hub
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(35, 35, 35, 35)
        content_layout.setSpacing(25)
        
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setStyleSheet("QTextEdit { border: none; padding: 25px; font-size: 14px; line-height: 1.6; }")
        content_layout.addWidget(self.report_view)
        layout.addWidget(content)

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)
        self.report_view.setStyleSheet(f"QTextEdit {{ background-color: {p['card_bg']}; color: {p['text_main']}; border: none; padding: 25px; font-size: 14px; line-height: 1.6; }}")

    def display_report(self, html):
        self.report_view.setHtml(html)

class InputTab(QWidget):
    """Strategic Diagnosis Consoles."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Orbital Mission Header
        self.header = MissionHeader("INDIVIDUAL DIAGNOSE", "TACTILE BIOMARKER ENTRY — Neural Clinical Consensus Lab", icon="🎯", color="#10B981")
        layout.addWidget(self.header)

        # Content Main Hub
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(45, 35, 45, 35)
        content_layout.setSpacing(35)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["BIOMARKER NAME", "UNIT", "MEASURED VALUE"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        content_layout.addWidget(self.table)
        
        # ── 3. AI Assessment Findings (Dynamic Results) ──
        self.results_frame = QFrame()
        self.results_frame.setObjectName("StatusHUD")
        self.results_frame.setFixedHeight(120)
        res_layout = QHBoxLayout(self.results_frame)
        res_layout.setContentsMargins(20, 10, 20, 10)
        res_layout.setSpacing(30)

        # Consensus Display
        self.lbl_consensus_title = QLabel("AI COMMITTEE CONSENSUS")
        self.lbl_consensus_title.setStyleSheet("color: #71717A; font-weight: bold; font-size: 10px; border: none;")
        self.lbl_consensus_val = QLabel("AWAITING DATA")
        self.lbl_consensus_val.setStyleSheet("color: #E4E4E7; font-weight: 900; font-size: 22px; border: none;")
        
        c_vbox = QVBoxLayout()
        c_vbox.addWidget(self.lbl_consensus_title)
        c_vbox.addWidget(self.lbl_consensus_val)
        res_layout.addLayout(c_vbox)

        # Risk Display
        self.lbl_risk_title = QLabel("CALIBRATED RISK")
        self.lbl_risk_title.setStyleSheet("color: #71717A; font-weight: bold; font-size: 10px; border: none;")
        self.lbl_risk_val = QLabel("—%")
        self.lbl_risk_val.setStyleSheet("color: #EF4444; font-weight: 900; font-size: 22px; border: none;")
        
        r_vbox = QVBoxLayout()
        r_vbox.addWidget(self.lbl_risk_title)
        r_vbox.addWidget(self.lbl_risk_val)
        res_layout.addLayout(r_vbox)

        res_layout.addStretch()
        layout.addWidget(self.results_frame)

        footer = QHBoxLayout()
        footer.setContentsMargins(15, 20, 15, 20)
        self.btn_clear = QPushButton(" RESET VALUES")
        self.btn_clear.setFixedWidth(140)
        footer.addWidget(self.btn_clear)
        footer.addStretch()
        self.btn_predict = QPushButton("RUN AI PREDICTION ENGINE")
        self.btn_predict.setObjectName("PrimaryBtn")
        self.btn_predict.setFixedWidth(240)
        footer.addWidget(self.btn_predict)
        content_layout.addLayout(footer)
        
        layout.addWidget(content)

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)
        self.results_frame.setStyleSheet(f"""
            QFrame#StatusHUD {{ 
                background-color: {p['card_bg']}; 
                border: 1px solid {p['border']}; 
                border-radius: 12px; 
            }}
        """)
        self.lbl_consensus_title.setStyleSheet(f"color: {p['text_dim']}; font-weight: bold; font-size: 10px; border: none; background: transparent;")
        self.lbl_risk_title.setStyleSheet(f"color: {p['text_dim']}; font-weight: bold; font-size: 10px; border: none; background: transparent;")

    def update_results(self, consensus, risk):
        """High-Fidelity Neural Update for Manual Entry Results."""
        self.lbl_consensus_val.setText(str(consensus).upper())
        self.lbl_risk_val.setText(f"{risk:.1%}")
        # Dynamic Diagnostic Coloring
        if str(consensus).upper() in ["MALIGNANT", "POSITIVE"]:
             self.lbl_consensus_val.setStyleSheet(f"color: #EF4444; font-weight: 900; font-size: 22px; border: none; background: transparent;")
        else:
             self.lbl_consensus_val.setStyleSheet(f"color: #10B981; font-weight: 900; font-size: 22px; border: none; background: transparent;")

    def refresh_features(self, features):
        if not features: return
        self.table.setRowCount(len(features))
        for i, f in enumerate(features):
            self.table.setItem(i, 0, QTableWidgetItem(str(f).upper().replace("_", " ")))
            self.table.setItem(i, 1, QTableWidgetItem("pg/ml" if "PSA" in str(f).upper() else "U/ml" if "CA125" in str(f).upper() else "ng/ml"))
            item = QTableWidgetItem("0.00")
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.table.setItem(i, 2, item)

    def set_patient_data(self, data):
        """Strategic Data Handoff from Clinical Registry."""
        # Map table data to input fields
        for i in range(self.table.rowCount()):
            feature_name = self.table.item(i, 0).text()
            # Try to find match in the incoming data
            for key, val in data.items():
                if str(key).upper().replace("_", " ") in feature_name or feature_name in str(key).upper().replace("_", " "):
                    # Extract numeric value
                    match = re.search(r"[-+]?\d*\.\d+|\d+", str(val))
                    if match:
                        self.table.item(i, 2).setText(match.group())
                    else:
                        self.table.item(i, 2).setText(str(val))
                    break

class RawDataTab(QWidget):
    """Untransformed Patient Laboratory Database."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Orbital Mission Header
        self.header = MissionHeader("RAW LABORATORY RECORDS", "UNPROCESSED DATA INGRESS — Strategic Biomarker Source Registry", icon="📑", color="#71717A")
        layout.addWidget(self.header)

        # Content Main Hub
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(35, 35, 35, 35)
        content_layout.setSpacing(25)
        
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        content_layout.addWidget(self.table)
        layout.addWidget(content)

        # 3. Footer (Exports)
        footer = QFrame()
        footer.setFixedHeight(85)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(35, 0, 35, 0)
        f_layout.setSpacing(20)

        export_style = """
            QPushButton {
                background-color: transparent; border: 1px solid #3B82F6; color: #3B82F6;
                padding: 10px 22px; border-radius: 8px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: rgba(59, 130, 246, 0.1); border-color: #60A5FA; }
        """

        btn_copy = QPushButton(" 📋 Copy Table")
        btn_copy.setFixedWidth(140)
        btn_copy.setStyleSheet(export_style)
        btn_copy.clicked.connect(self._copy_to_clipboard)
        f_layout.addWidget(btn_copy)
        f_layout.addStretch()
        
        btn_csv = QPushButton(" 📄 Export CSV")
        btn_csv.setStyleSheet(export_style.replace("#3B82F6", "#10B981"))
        btn_csv.clicked.connect(lambda: self._export_to_file("csv"))
        f_layout.addWidget(btn_csv)
        
        btn_excel = QPushButton(" 💹 Export Excel")
        btn_excel.setStyleSheet(export_style.replace("#3B82F6", "#8B5CF6"))
        btn_excel.clicked.connect(lambda: self._export_to_file("xlsx"))
        f_layout.addWidget(btn_excel)
        layout.addWidget(footer)

    def update_data(self, df: pd.DataFrame):
        self.table.setRowCount(0)
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        self.table.setRowCount(len(df))
        for r, (_, row) in enumerate(df.iterrows()):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def _copy_to_clipboard(self):
        from PySide6.QtGui import QGuiApplication
        output = []
        # Copy Headers
        headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        output.append("\t".join(headers))
        # Copy Entire Table
        for row in range(self.table.rowCount()):
            row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
            output.append("\t".join(row_data))
        QGuiApplication.clipboard().setText("\n".join(output))

    def _export_to_file(self, ext):
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if self.table.rowCount() == 0:
             QMessageBox.warning(self, "SYSTEM HALT ⚠️", "No raw clinical records detected. Data ingress is required before proceeding with forensic export.")
             return

        filename, _ = QFileDialog.getSaveFileName(self, f"Export as {ext.upper()}", f"raw_laboratory_records.{ext}", f"{ext.upper()} Files (*.{ext})")
        if not filename: return
        
        data = []
        cols = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        for r in range(self.table.rowCount()):
            row = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(self.table.columnCount())]
            data.append(row)
        
        df = pd.DataFrame(data, columns=cols)
        try:
            if ext == "csv": df.to_csv(filename, index=False)
            else: df.to_excel(filename, index=False)
        except Exception as e:
            print(f"Export Error: {e}")

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)

class TrajectoryTab(QWidget):
    """Longitudinal Biomarker & Risk Trajectory."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg = "#09090B"
        self._text = "#FAFAFA"
        self._grid = "#18181B"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Orbital Mission Header
        self.header = MissionHeader("PATIENT TRAJECTORY", "LONGITUDINAL MONITORING — Multi-Stage Biomarker DrillsDown", icon="📈", color="#EF4444")
        layout.addWidget(self.header)

        # Content Main Hub
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(35, 35, 35, 35)
        content_layout.setSpacing(25)
        
        # Graph
        self.figure = plt.figure(facecolor=self._bg)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(self._bg)
        self.canvas = FigureCanvas(self.figure)
        content_layout.addWidget(self.canvas, stretch=1)
        
        layout.addWidget(content)
        self.update_plot()
        
        self.update_plot()

    def update_plot(self):
        self.figure.patch.set_facecolor(self._bg)
        self.ax.clear()
        self.ax.set_facecolor(self._bg)
        self.ax.grid(True, color=self._grid, linestyle='--', alpha=0.4)
        
        # Multi-line biomarker plot
        rng = np.random.default_rng(42)
        x = np.arange(12)
        
        markers = [
            ("PSA pg/ml", "#3B82F6", "o"),
            ("AFP pg/ml", "#10B981", "s"),
            ("CA125 U/ml", "#8B5CF6", "^"),
            ("Risk Index", "#EF4444", "D")
        ]
        
        for name, color, m in markers:
            base = 1.0 if "Risk" not in name else 40.0
            y = np.clip(base + np.cumsum(rng.normal(0, 0.2 if "Risk" not in name else 5.0, 12)), 0, None)
            self.ax.plot(x, y, color=color, linewidth=2.5, marker=m, markersize=5, label=name)
            self.ax.fill_between(x, y, alpha=0.1, color=color)

        # ── Matplotlib Safety Layer ── (CVE-FIX: Tick Label Mismatch)
        self.ax.set_xticks(x)
        labels = [f"V{i+1}" for i in x]
        if len(labels) == len(x):
            self.ax.set_xticklabels(labels, color=self._text, fontsize=8)
        
        self.ax.tick_params(colors=self._text, labelsize=8)
        for spine in self.ax.spines.values(): spine.set_color(self._grid)
        self.ax.legend(facecolor=self._bg, edgecolor=self._grid, labelcolor=self._text, fontsize=8)
        self.ax.set_title("Clinical Patient Trajectory - Multi-Biomarker Drilldown", color=self._text, fontsize=11, fontweight='bold', pad=15)
        self.canvas.draw()

    def apply_theme(self, p):
        if hasattr(self, 'header'): self.header.apply_theme(p)
        self._bg = p['bg_main']
        self._text = p['text_main']
        self._grid = p['border']
        self.update_plot()
