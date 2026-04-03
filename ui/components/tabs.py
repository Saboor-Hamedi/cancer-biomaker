from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QFrame, QTextEdit, QTabWidget, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class DataTab(QWidget):
    """Modern Clinical Audit View for PySide6."""
    selection_changed = Signal(set)
    row_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Header (Premium Forensic Title)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 1px solid #18181B;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 10, 15, 10)
        title = QLabel("CLINICAL AUDIT — Primary Forensic Database")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #71717A; letter-spacing: 0.5px;")
        h_layout.addWidget(title)
        layout.addWidget(header)

        # 2. Table (Obsidion Foundation)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #000000; gridline-color: #09090B; border: none; color: #E4E4E7; }
            QHeaderView::section { background-color: #09090B; color: #71717A; padding: 12px; border: none; font-weight: 800; font-size: 10px; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.table)

        # 3. Forensic Export Suite (Footer)
        footer = QFrame()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(15, 10, 15, 10)
        
        self.btn_copy = QPushButton("Copy Selected")
        self.btn_copy.setFixedWidth(140)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        f_layout.addWidget(self.btn_copy)
        
        f_layout.addStretch()
        
        self.btn_csv = QPushButton("Export CSV")
        self.btn_csv.setObjectName("PrimaryBtn")
        f_layout.addWidget(self.btn_csv)
        
        self.btn_excel = QPushButton("Export Excel")
        self.btn_excel.setObjectName("PrimaryBtn")
        f_layout.addWidget(self.btn_excel)
        
        layout.addWidget(footer)

    def update_data(self, df: pd.DataFrame):
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        headers = [str(c).upper() for c in df.columns]
        self.table.setHorizontalHeaderLabels(headers)
        for row_idx, (idx, row) in enumerate(df.iterrows()):
            for col_idx, value in enumerate(row):
                val_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                item = QTableWidgetItem(val_str)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

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
    """Olympic-Grade Clinical Rankings."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("ALGORITHM BENCHMARK & CLINICAL STANDINGS")
        header.setStyleSheet("color: #71717A; font-weight: bold; font-size: 11px; padding: 20px 0 10px 15px;")
        layout.addWidget(header)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "RANK", "ALGORITHM", "ACCURACY", "F1 SCORE", "ROC-AUC", 
            "PRECISION", "RECALL", "SPECIFICITY", "CV STABILITY", "BADGE"
        ])
        self.table.setStyleSheet("""
            QTableWidget { background-color: #000000; gridline-color: #18181B; border: none; color: #E4E4E7; }
            QHeaderView::section { background-color: #09090B; color: #71717A; padding: 12px; border: none; font-weight: 800; font-size: 10px; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def update_leaderboard(self, leaderboard):
        self.table.setRowCount(0)
        for i, entry in enumerate(leaderboard):
            row = self.table.rowCount()
            self.table.insertRow(row)
            rank_text = f"#{i+1}"
            if i == 0: rank_text = f"🥇 #1 CHAMPION"
            elif i == 1: rank_text = f"🥈 #2 RUNNER-UP"
            elif i == 2: rank_text = f"🥉 #3 CONTENDER"
            
            items = [
                rank_text,
                entry.get('model', 'Unknown'),
                f"{entry.get('accuracy', 0):.2%}",
                f"{entry.get('f1', 0):.2%}",
                f"{entry.get('auc', 0):.2%}",
                f"{entry.get('precision', 0):.2%}",
                f"{entry.get('recall', 0):.2%}",
                f"{entry.get('specificity', 0):.2%}",
                f"{entry.get('cv_mean', 0):.1%} ±{entry.get('cv_std', 0):.3f}",
                "REVIEW"
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if i == 0: item.setForeground(QColor("#FFFFFF"))
                elif col in [2,3]: item.setForeground(QColor("#10B981"))
                elif col == 9: item.setForeground(QColor("#3B82F6"))
                self.table.setItem(row, col, item)

class AnalysisTab(QWidget):
    """Forensic Narrative Engine."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Header
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 1px solid #18181B;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 10, 15, 10)
        title = QLabel("FORENSIC AUDIT — Detailed Clinical Reasoning")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #3B82F6;")
        h_layout.addWidget(title)
        
        self.btn_copy = QPushButton("Copy Report")
        self.btn_copy.setFixedWidth(120)
        self.btn_copy.clicked.connect(self._handle_copy_report)
        h_layout.addWidget(self.btn_copy)
        layout.addWidget(header)

        # 2. Report View (Obsidion Foundation)
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setStyleSheet("background-color: #000000; border: none; padding: 25px; color: #E4E4E7; font-family: 'Segoe UI'; font-size: 14px; line-height: 1.6;")
        layout.addWidget(self.report_view)

    def display_report(self, html):
        self.report_view.setHtml(html)
    
    def _handle_copy_report(self):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(self.report_view.toPlainText())

class InputTab(QWidget):
    """Strategic Diagnosis Console."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # 100% Flush Boundary
        layout.setSpacing(0)
        
        # 1. Header (Strategic Sub-title)
        header = QFrame()
        header.setStyleSheet("background-color: transparent; border-bottom: 2px solid #18181B;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(15, 12, 15, 12)
        title = QLabel("BIOMARKER PROFILE — Manual Patient Entry & Verification")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #10B981; letter-spacing: 0.5px;")
        h_layout.addWidget(title)
        layout.addWidget(header)

        # 2. Entry Table (High-Fidelity Flush)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["BIOMARKER NAME", "UNIT", "MEASURED VALUE"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False) # Purge left sidebar artifact
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: #000000; 
                gridline-color: #09090B; 
                border: none; 
                color: #E4E4E7;
                padding-left: 0px; 
            }
            QHeaderView::section { 
                background-color: #09090B; 
                color: #71717A; 
                padding: 12px; 
                border: none; 
                font-weight: 800; 
                font-size: 10px;
                text-align: left;
            }
        """)
        layout.addWidget(self.table)
        
        # 3. Clinical Prediction Tray (Strategic Footer)
        footer = QHBoxLayout()
        footer.setContentsMargins(15, 20, 15, 20)
        self.btn_clear = QPushButton(" RESET CLINICAL VALUES")
        self.btn_clear.setFixedHeight(48)
        self.btn_clear.setFixedWidth(180)
        self.btn_clear.setStyleSheet("QPushButton { background-color: #09090B; color: #EF4444; border: 1px solid #27272A; border-radius: 6px; font-weight: bold; font-size: 11px; }")
        footer.addWidget(self.btn_clear)
        
        footer.addStretch()
        
        self.btn_predict = QPushButton("RUN AI PREDICTION ENGINE")
        self.btn_predict.setObjectName("PrimaryBtn")
        self.btn_predict.setFixedHeight(48)
        self.btn_predict.setFixedWidth(240)
        footer.addWidget(self.btn_predict)
        layout.addLayout(footer)

    def refresh_features(self, features):
        self.table.setRowCount(len(features))
        for i, f in enumerate(features):
            item_n = QTableWidgetItem(str(f).upper().replace("_", " "))
            item_n.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item_n)
            item_u = QTableWidgetItem("ng/mL")
            item_u.setTextAlignment(Qt.AlignCenter)
            item_u.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, item_u)
            item_v = QTableWidgetItem("0.0000")
            item_v.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, item_v)

class TrajectoryTab(QWidget):
    """Longitudinal Biomarker Visualization."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Header
        header = QLabel("PATIENT BIOMARKER DRIFT & RISK TRAJECTORY")
        header.setStyleSheet("color: #71717A; font-weight: bold; font-size: 11px; padding: 20px 0 10px 15px;")
        layout.addWidget(header)

        # 2. Matplotlib Canvas
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.figure.patch.set_facecolor('#000000') # Pure Black Foundation
        self.ax.set_facecolor('#000000')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.grid(True, color='#18181B', linestyle='--', alpha=0.3)
        x = np.arange(10)
        y = np.cumsum(np.random.normal(50, 15, 10))
        self.ax.plot(x, y, color='#3B82F6', linewidth=3, marker='o', label='Biomarker Drift')
        self.ax.tick_params(colors='#71717A', labelsize=8)
        self.ax.set_title("Longitudinal Forensic Assessment", color='#E4E4E7', fontsize=10)
        self.ax.legend(loc='upper left', frameon=False, fontsize=8, labelcolor='#E4E4E7')
        self.canvas.draw()
