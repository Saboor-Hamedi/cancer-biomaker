from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QFrame, QTableWidgetSelectionRange, QTextEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import pandas as pd

class DataTab(QWidget):
    """Modern Clinical Registry View for PySide6."""
    
    # Selection/Forensic Signals
    selection_changed = Signal(set)
    row_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.selection_indices = set()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(10)

        # ── Header Title ──
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 1px solid #27272A;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 10, 15, 10)
        
        title = QLabel("CLINICAL PATIENT REGISTRY — Primary Forensic Database")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #A1A1AA; letter-spacing: 0.5px;")
        h_layout.addWidget(title)
        
        layout.addWidget(header)

        # ── The Primary Registry Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        
        self.table.itemSelectionChanged.connect(self._handle_selection)
        layout.addWidget(self.table)

        # ── Forensic Export Footer ──
        footer = QFrame()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(15, 5, 15, 5)
        
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
        """Populate the table with fresh clinical cohort data."""
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1] + 1)
        
        headers = ["[✓]"] + [str(c).upper() for c in df.columns]
        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, (idx, row) in enumerate(df.iterrows()):
            check_item = QTableWidgetItem("[ ]")
            check_item.setTextAlignment(Qt.AlignCenter)
            check_item.setData(Qt.UserRole, idx)
            self.table.setItem(row_idx, 0, check_item)
            
            for col_idx, value in enumerate(row):
                val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                item = QTableWidgetItem(val_str)
                item.setTextAlignment(Qt.AlignCenter)
                
                if "[RISK]" in headers[col_idx+1] or "PROBABILITY" in headers[col_idx+1]:
                    try:
                        v = float(value)
                        if v > 0.7: item.setBackground(Qt.red)
                    except: pass
                
                self.table.setItem(row_idx, col_idx + 1, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _handle_selection(self):
        selected_items = self.table.selectedItems()
        if not selected_items: return
        row = selected_items[0].row()
        cols = self.table.columnCount()
        row_dict = {}
        idx_item = self.table.item(row, 0)
        if idx_item: row_dict['_index'] = idx_item.data(Qt.UserRole)
        for col in range(1, cols):
            h_text = self.table.horizontalHeaderItem(col).text()
            item = self.table.item(row, col)
            if item: row_dict[h_text] = item.text()
        self.row_selected.emit(row_dict)

    def _copy_to_clipboard(self):
        from PySide6.QtGui import QGuiApplication
        selection = self.table.selectedRanges()
        if not selection: return
        output = []
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        output.append("\t".join(headers))
        for r in selection:
            for row in range(r.topRow(), r.bottomRow() + 1):
                row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" 
                          for col in range(self.table.columnCount())]
                output.append("\t".join(row_data))
        QGuiApplication.clipboard().setText("\n".join(output))

class LeaderboardTab(QWidget):
    """Clinical AI Ranking System."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 2px solid #27272A;")
        h_layout = QHBoxLayout(header)
        title = QLabel("ALGORITHM LEADERBOARD — Forensic Performance Rankings")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #10B981; letter-spacing: 0.5px;")
        h_layout.addWidget(title)
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ALGORITHM MODEL", "ACCURACY", "F1-SCORE", "SV-STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        layout.addWidget(self.table)

    def update_leaderboard(self, leaderboard_data: list):
        self.table.setRowCount(len(leaderboard_data))
        for i, entry in enumerate(leaderboard_data):
            acc = entry.get('Accuracy', 0.0)
            f1 = entry.get('F1 Score', 0.0)
            item_name = QTableWidgetItem(entry.get('Algorithm', 'N/A'))
            item_acc = QTableWidgetItem(f"{acc:.2%}")
            if acc > 0.85: item_acc.setForeground(QColor("#10B981"))
            elif acc > 0.70: item_acc.setForeground(QColor("#F59E0B"))
            else: item_acc.setForeground(QColor("#EF4444"))
            item_acc.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item_f1 = QTableWidgetItem(f"{f1:.2%}")
            item_status = QTableWidgetItem("VERIFIED" if acc > 0.8 else "CALIBRATING")
            if acc > 0.8: item_status.setForeground(QColor("#3B82F6"))
            self.table.setItem(i, 0, item_name)
            self.table.setItem(i, 1, item_acc)
            self.table.setItem(i, 2, item_f1)
            self.table.setItem(i, 3, item_status)

class AnalysisTab(QWidget):
    """Forensic Narrative Engine."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 1px solid #27272A;")
        h_layout = QHBoxLayout(header)
        title = QLabel("FORENSIC AUDIT — Detailed Clinical Reasoning")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #F59E0B;")
        h_layout.addWidget(title)
        btn_copy = QPushButton("Copy Report")
        btn_copy.setFixedWidth(120)
        btn_copy.clicked.connect(self._handle_copy_report)
        h_layout.addWidget(btn_copy)
        layout.addWidget(header)
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setStyleSheet("background-color: #09090B; border: none; padding: 10px; color: #E4E4E7; font-family: 'Inter', 'Segoe UI'; font-size: 14px; line-height: 1.6;")
        layout.addWidget(self.report_view)

    def display_report(self, html_content):
        self.report_view.setHtml(html_content)

    def _handle_copy_report(self):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(self.report_view.toPlainText())

class InputTab(QWidget):
    """Modern Biomarker Entry Console."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 2px solid #27272A;")
        h_layout = QHBoxLayout(header)
        title = QLabel("BIOMARKER PROFILE — Manual Patient Entry & Verification")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #3B82F6;")
        h_layout.addWidget(title)
        layout.addWidget(header)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["BIOMARKER NAME", "UNIT", "MEASURED VALUE"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        hh.resizeSection(1, 100)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        hh.resizeSection(2, 150)
        layout.addWidget(self.table)
        footer = QHBoxLayout()
        footer.setContentsMargins(15, 10, 15, 0)
        btn_clear = QPushButton("Reset Values")
        btn_clear.setFixedWidth(120)
        footer.addWidget(btn_clear)
        footer.addStretch()
        btn_predict = QPushButton("RUN AI PREDICTION")
        btn_predict.setObjectName("PrimaryBtn")
        btn_predict.setFixedWidth(200)
        footer.addWidget(btn_predict)
        layout.addLayout(footer)

    def refresh_features(self, features: list):
        self.table.setRowCount(len(features))
        for idx, f_name in enumerate(features):
            display_name = str(f_name).upper().replace("_", " ")
            name_item = QTableWidgetItem(display_name)
            name_item.setFlags(Qt.ItemIsEnabled)
            if "PSA" in display_name: name_item.setForeground(QColor("#3B82F6"))
            elif "AFP" in display_name: name_item.setForeground(QColor("#10B981"))
            elif "CA125" in display_name: name_item.setForeground(QColor("#F59E0B"))
            self.table.setItem(idx, 0, name_item)
            unit_item = QTableWidgetItem("ng/mL")
            unit_item.setTextAlignment(Qt.AlignCenter)
            unit_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(idx, 1, unit_item)
            val_item = QTableWidgetItem("0.0000")
            val_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 2, val_item)
