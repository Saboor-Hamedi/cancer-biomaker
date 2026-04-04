from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt
from ui.styles import Styles
import os

class ClinicalDocumentationModal(QDialog):
    """
    Industrial-Grade Clinical Documentation Viewer.
    Renders DOCUMENTATION.md with high-fidelity markdown support.
    """
    
    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.settings_manager = settings_manager
        
        self.setWindowTitle("CLINICAL SYSTEM DOCUMENTATION (v1.1.0)")
        self.resize(1000, 800)
        
        self._setup_ui()
        
        # Apply initial theme skin
        theme = settings_manager.get('theme', 'pure_dark') if settings_manager else 'pure_dark'
        self.apply_theme(Styles.PALETTES.get(theme))
        
        self._load_documentation()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── 1. Header Hub ──
        self.header = QFrame()
        self.header.setFixedHeight(80)
        self.header.setObjectName("DocHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(30, 0, 30, 0)

        title_v = QVBoxLayout()
        self.title_lbl = QLabel("📖 CLINICAL DOCUMENTATION")
        self.title_lbl.setStyleSheet("font-weight: 900; font-size: 15px; letter-spacing: 1.5px;")
        title_v.addWidget(self.title_lbl)
        
        self.sub_lbl = QLabel("SYSTEM ARCHITECTURE & WORKFLOW GUIDE (QC-VERIFIED)")
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #71717A; font-weight: bold; text-transform: uppercase;")
        title_v.addWidget(self.sub_lbl)
        h_layout.addLayout(title_v)
        
        h_layout.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(35, 35)
        self.close_btn.clicked.connect(self.close)
        h_layout.addWidget(self.close_btn)

        self.main_layout.addWidget(self.header)

        # ── 2. Content View (Markdown Feed) ──
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.setObjectName("DocContent")
        self.main_layout.addWidget(self.content_view)

        # ── 3. Footer Hub ──
        self.footer = QFrame()
        self.footer.setFixedHeight(50)
        self.footer.setObjectName("DocFooter")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(30, 0, 30, 0)
        
        self.status_lbl = QLabel("BIO-RECON ANALYTICS — SECURE CLINICAL WORKSPACE v1.1.0")
        self.status_lbl.setStyleSheet("font-size: 9px; font-weight: 800; color: #52525B;")
        f_layout.addWidget(self.status_lbl)
        
        f_layout.addStretch()
        
        self.main_layout.addWidget(self.footer)

    def apply_theme(self, p):
        bg = p['bg_main']
        card = p['card_bg']
        txt = p['text_main']
        acc = p['accent']
        border = p['border']
        dim = p['text_dim']

        self.setStyleSheet(f"QDialog {{ background-color: {bg}; }}")
        self.header.setStyleSheet(f"QFrame#DocHeader {{ background-color: {p['bg_sidebar']}; border-bottom: 2px solid {border}; }}")
        self.footer.setStyleSheet(f"QFrame#DocFooter {{ background-color: {p['bg_sidebar']}; border-top: 1px solid {border}; }}")
        
        self.title_lbl.setStyleSheet(f"font-weight: 900; font-size: 15px; letter-spacing: 1.5px; color: {acc};")
        
        self.content_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg};
                border: none;
                color: {txt};
                padding: 40px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 15px;
                line-height: 1.6;
            }}
        """)
        
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {dim};
                font-size: 20px;
                border: none;
            }}
            QPushButton:hover {{
                color: {txt};
            }}
        """)

    def _load_documentation(self):
        """Read and render DOCUMENTATION.md."""
        # Find path to DOCUMENTATION.md relative to this file's location
        # or assuming it is in the root as described by the user
        doc_path = os.path.join(os.getcwd(), "DOCUMENTATION.md")
        if not os.path.exists(doc_path):
            # Fallback for parent dir
            doc_path = os.path.join(os.path.dirname(os.getcwd()), "DOCUMENTATION.md")

        if os.path.exists(doc_path):
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.content_view.setMarkdown(content)
            except Exception as e:
                self.content_view.setHtml(f"<h1 style='color:red;'>System Error</h1><p>Failed to load clinical documentation: {str(e)}</p>")
        else:
            self.content_view.setHtml(f"<h1 style='color:orange;'>Technical Fault</h1><p>File <code>DOCUMENTATION.md</code> not found in clinical workspace roots.</p><p>Search path: <code>{doc_path}</code></p>")
