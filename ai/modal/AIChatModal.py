import os
import sys
import threading
import re
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QComboBox, 
                             QFrame, QScrollArea, QSizePolicy, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEvent
from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon
from ui.styles import Styles

# Forensic Ingestion Hub
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.insert(0, parent_dir)

try:
    from MultiAIManager import MultiAIManager
except ImportError:
    # Build context fallback
    try:
        from ai.MultiAIManager import MultiAIManager
    except: pass

class AIChatModal(QDialog):
    """
    Industrial-Grade AI Clinical Research Assistant (Full Thematic Integration).
    State-of-the-art PySide6 edition with Multi-AI orchestration and high-fidelity themes.
    """
    
    def __init__(self, parent=None, settings_manager=None, clinical_context=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.clinical_context = clinical_context or {}
        
        self.setWindowTitle("AI CLINICAL RESEARCH ASSISTANT (QC-VERIFIED)")
        self.resize(1050, 850)
        self.setMinimumSize(850, 650)
        self.setObjectName("AIChatModal")
        
        # ── Step 0: Windowing Architecture ──
        self.setWindowFlags(self.windowFlags() | 
                            Qt.WindowMinimizeButtonHint | 
                            Qt.WindowMaximizeButtonHint | 
                            Qt.WindowCloseButtonHint)
        
        # AI Orchestration State
        self.ai_clients = {}
        self.stop_requested = False
        self.current_full_response = ""
        self.stream_cursor = None # Fixed: Clinical Cursor tracker
        
        # 🛡️ FATAL GUARD: Pre-initialize systemic context to ensure AI response
        self.update_context(self.clinical_context)
        
        self._setup_ui()
        
        # 🧪 Apply Initial Theme Skin
        theme = settings_manager.get('theme', 'pure_dark') if settings_manager else 'pure_dark'
        palette = Styles.PALETTES.get(theme)
        self.apply_theme(palette)
        
        # Load Last Provider & Context
        self._load_saved_keys()
        self.update_context(self.clinical_context)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── 1. Top Header (Industrial Action Bar) ──
        self.header = QFrame()
        self.header.setFixedHeight(85)
        self.header.setObjectName("AssistantHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(30, 0, 30, 0)

        title_v = QVBoxLayout()
        self.title_lbl = QLabel("🤖 AI RESEARCH COPILOT")
        self.title_lbl.setStyleSheet("font-weight: 900; font-size: 15px; color: #10B981; letter-spacing: 2px;")
        title_v.addWidget(self.title_lbl)
        
        self.sub_lbl = QLabel("CLINICAL FORENSIC CONSULTATION HUB")
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #71717A; font-weight: bold; text-transform: uppercase;")
        title_v.addWidget(self.sub_lbl)
        h_layout.addLayout(title_v)
        
        h_layout.addStretch()

        self.provider_menu = QComboBox()
        self.provider_menu.addItems(["ChatGPT", "Claude", "DeepSeek", "Gemini"])
        self.provider_menu.setFixedWidth(140)
        self.provider_menu.setFixedHeight(35)
        self.provider_menu.currentTextChanged.connect(self._on_provider_change)
        h_layout.addWidget(self.provider_menu)

        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("Enter Provider API Key...")
        self.key_entry.setEchoMode(QLineEdit.Password)
        self.key_entry.setFixedWidth(240)
        self.key_entry.setFixedHeight(35)
        self.key_entry.textChanged.connect(self._on_key_changed)
        self.key_entry.installEventFilter(self) # Install interceptor for key entry
        h_layout.addWidget(self.key_entry)

        self.main_layout.addWidget(self.header)

        # ── 2. Chat Display (Forensic Feed) ──
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.document().setDocumentMargin(0) # 🛡️ Alignment Hardening: Zero cumulative indentation
        self.chat_display.setObjectName("AssistantChatFeed")
        self.main_layout.addWidget(self.chat_display)

        # ── 3. Footer Input Area (Mission Command) ──
        self.footer = QFrame()
        self.footer.setFixedHeight(180)
        self.footer.setObjectName("AssistantFooter")
        f_layout = QVBoxLayout(self.footer)
        f_layout.setContentsMargins(35, 20, 35, 20)

        self.user_input = QTextEdit()
        self.user_input.setPlaceholderText("Describe clinical context or ask for forensic analysis... (Enter to Send, Shift+Enter for New Line)")
        self.user_input.setObjectName("AssistantInputField")
        self.user_input.installEventFilter(self) # Install tactical event interceptor
        f_layout.addWidget(self.user_input)

        btn_row = QHBoxLayout()
        
        self.export_btn = QPushButton(" 📁 EXPORT RESEARCH NOTE")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setAutoDefault(False) # Disable accidental Enter-trigger
        self.export_btn.setDefault(False)
        self.export_btn.clicked.connect(self._handle_export)
        btn_row.addWidget(self.export_btn)
        
        btn_row.addStretch()

        self.send_btn = QPushButton("SEND")
        self.send_btn.setFixedHeight(40)
        self.send_btn.setObjectName("PrimaryBtn")
        self.send_btn.setAutoDefault(False)
        self.send_btn.setDefault(False)
        self.send_btn.clicked.connect(self._handle_send)
        btn_row.addWidget(self.send_btn)

        f_layout.addLayout(btn_row)
        self.main_layout.addWidget(self.footer)
        
    def eventFilter(self, obj, event):
        """Tactical Event Interceptor: Handle clinical hotkeys."""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # ── Case A: Hitting Enter in API Key Field ──
                if obj is self.key_entry:
                    self.user_input.setFocus() # Jump to prompt field
                    return True # Stop the event here
                
                # ── Case B: Hitting Enter in Prompt Field ──
                if obj is self.user_input:
                    if not (event.modifiers() & Qt.ShiftModifier):
                        self._handle_send()
                        return True
        return super().eventFilter(obj, event)

    def apply_theme(self, p):
        """High-fidelity clinical theme synchronization."""
        bg = p['bg_main']
        card = p['card_bg']
        txt = p['text_main']
        dim = p['text_dim']
        acc = p['accent']
        border = p['border']

        self.setStyleSheet(f"QDialog {{ background-color: {bg}; }}")
        self.header.setStyleSheet(f"QFrame#AssistantHeader {{ background-color: {p['bg_sidebar']}; border-bottom: 2px solid {border}; }}")
        self.footer.setStyleSheet(f"QFrame#AssistantFooter {{ background-color: {p['bg_sidebar']}; border-top: 2px solid {border}; }}")
        self.title_lbl.setStyleSheet(f"font-weight: 900; font-size: 15px; color: {acc}; letter-spacing: 2px;")
        
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{ background-color: {bg}; border: none; font-family: 'Inter', sans-serif; font-size: 15px; padding: 40px; color: {txt}; }}
        """)
        
        self.user_input.setStyleSheet(f"""
            QTextEdit {{ background-color: {bg}; border: 1px solid {border}; border-radius: 12px; padding: 15px; color: {txt}; font-size: 14px; }}
            QTextEdit:focus {{ border-color: {acc}; }}
        """)
        
        self.provider_menu.setStyleSheet(f"""
            QComboBox {{ background-color: {bg}; border: 1px solid {border}; border-radius: 8px; padding: 6px; color: {txt}; font-weight: bold; }}
        """)

        self.key_entry.setStyleSheet(f"""
            QLineEdit {{ background-color: {bg}; border: 1px solid {border}; border-radius: 8px; padding: 6px 12px; color: {dim}; font-family: 'Consolas'; }}
            QLineEdit:focus {{ border-color: {acc}; color: {txt}; }}
        """)

        self.export_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {border}; border-radius: 8px; color: {dim}; font-weight: 800; font-size: 10px; padding: 8px 15px; }}
            QPushButton:hover {{ background-color: {card}; border-color: {acc}; color: {txt}; }}
        """)

        self.send_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {acc}; border: none; border-radius: 8px; color: white; font-weight: 900; font-size: 11px; padding: 10px 40px; }}
            QPushButton:hover {{ background-color: #2563EB; }}
        """)

    def update_context(self, clinical_context):
        """Syncs the AI consultation with live dashboard diagnostics."""
        self.clinical_context = clinical_context
        ctx = clinical_context
        features_str = "\n".join([f"- {f}: {v}" for f, v in ctx.get('features', {}).items()]) or "N/A"
        
        lb_lines = []
        for i, en in enumerate(ctx.get('leaderboard', [])):
            m = f"- Rank #{i+1}: {en['model']} (F1: {en.get('f1',0):.2%})"
            lb_lines.append(m)
        leaderboard_str = "\n".join(lb_lines) or "Awaiting Calibration"

        self.SYSTEM_PROMPT = f"""You are the 'Clinical Research Copilot' for the Cancer Biomarker XAI Dashboard.
        Tone: Professional, clinical deliberation.
        Current Patient Profile: {features_str}
        Lab Leaderboard: {leaderboard_str}
        Rules: cite specific model performance and disclaimer that this is research help, not medical advice.
        """

    def _load_saved_keys(self):
        """Clinical Token Retrieval Engine & Provider Restoration."""
        if self.settings_manager:
            # First, restore the last used provider from the vault
            last_p = self.settings_manager.last_ai_provider
            if last_p:
                index = self.provider_menu.findText(last_p)
                if index >= 0:
                    self.provider_menu.setCurrentIndex(index)

            p = self.provider_menu.currentText()
            # Surgical restoration of the ai_keys ingestion
            keys = getattr(self.settings_manager, 'ai_keys', {})
            self.key_entry.setText(keys.get(p, ""))

    def _on_provider_change(self, provider):
        """Sync provider selection to clinical persistence vault."""
        if self.settings_manager:
            self.settings_manager.set_last_ai_provider(provider)
        self._load_saved_keys()

    def _on_key_changed(self, key):
        """Tactical Persistence: Lock the API key into the clinical vault instantly."""
        if self.settings_manager:
            provider = self.provider_menu.currentText()
            # This calls settings_manager.set_ai_key which handles the JSON write
            self.settings_manager.set_ai_key(provider, key.strip())

    def _handle_send(self):
        # ── Toggle Logic: One Button, Two Missions ──
        if self.send_btn.text() == "STOP":
            self._handle_stop()
            return

        prompt = self.user_input.toPlainText().strip()
        if not prompt: return
        
        provider = str(self.provider_menu.currentText()).lower().strip()
        api_key = self.key_entry.text().strip()
        
        if not api_key:
            QMessageBox.critical(self, "CREDENTIAL ERROR", f"Clinical API Key required for {provider}.")
            return
            
        self.user_input.clear()
        self.user_input.setReadOnly(True) # 🛡️ Clinical Lock: Prevent dual-mission collision
        self._append_message("RESEARCHER", prompt, is_ai=False)
        
        # UI Transformation: Enter 'Active Mission' Mode
        self.send_btn.setText("STOP")
        self.send_btn.setStyleSheet("QPushButton { background-color: #EF4444; color: white; border: none; border-radius: 8px; font-weight: bold; }")
        
        self.current_full_response = ""
        self.stop_requested = False
        self.stream_active = True # Track mission state
        
        threading.Thread(target=self._fetch_ai_stream, args=(provider, api_key, prompt), daemon=True).start()

    def _append_message(self, sender, text, is_ai=True):
        emoji = "🤖" if is_ai else "🧬"
        color = "#10B981" if is_ai else "#3B82F6"
        bg = "#18181B" if is_ai else "#09090B"
        
        # 🧪 Surgical HTML Insertion: Resets layout flow to fix the 'Staircase Indent' bug
        html = f"""
        <div style="clear: both; width: 100%; margin-bottom: 25px;">
            <div style="padding: 12px; background-color: {bg}; border-radius: 12px; border: 1px solid #27272A; display: inline-block; min-width: 60%; max-width: 95%;">
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 16px; margin-right: 10px;">{emoji}</span>
                    <b style="color: {color}; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; font-family: 'Inter', sans-serif;">{sender}</b>
                </div>
                <div style="color: #E4E4E7; font-size: 14px; line-height: 1.6; margin-left: 28px;">
                    {text.replace('\n', '<br>')}
                </div>
            </div>
        </div>
        """
        # Ensure clinician can visualize the conversation history horizontally aligned
        self.chat_display.moveCursor(QTextCursor.End)
        self.chat_display.insertHtml(html)
        self.chat_display.moveCursor(QTextCursor.End)

    def _fetch_ai_stream(self, provider, api_key, prompt):
        """Multi-AI Strategic Deliberation Engine."""
        try:
            # 🧬 Identity Hardening: Provider was sometimes case-mismatched
            client = MultiAIManager.create_client(provider.lower(), api_key)
            if not client: 
                raise ValueError(f"AI Infrastructure Fail: Could not resolve '{provider}' interface.")
            
            QTimer.singleShot(0, self.prepare_stream)
            
            # Explicit Stream Consumption
            for chunk in client.generate_stream(prompt, system_instruction=self.SYSTEM_PROMPT):
                if self.stop_requested: break
                if chunk:
                    # FIXED: Variable binding in lambda to ensure chunks arrive in UI
                    QTimer.singleShot(0, lambda c=chunk: self._on_chunk_received(c))
                
            QTimer.singleShot(0, self.finalize_stream)
        except Exception as e:
            QTimer.singleShot(0, lambda: self._handle_error(str(e)))

    def prepare_stream(self):
        # Professional Emoji-Header for Streaming (Surgical HTML Insertion)
        html = f"""
        <div style="margin-bottom: 20px; padding: 10px; background-color: #18181B; border-radius: 12px; border: 1px solid #27272A;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <span style="font-size: 16px; margin-right: 8px;">🤖</span>
                <b style="color: #10B981; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;">AI ASSISTANT</b>
            </div>
            <div id="ai_content" style="color: #E4E4E7; font-size: 14px; line-height: 1.5; margin-left: 28px;">
        """
        self.chat_display.append(html)
        self.stream_cursor = self.chat_display.textCursor()
        self.stream_cursor.movePosition(QTextCursor.End)

    def _on_chunk_received(self, chunk):
        if not chunk or self.stream_cursor is None: return
        self.current_full_response += chunk
        # 🧪 Thread-Safe Atomic Insertion
        self.stream_cursor.insertText(chunk)
        self.chat_display.moveCursor(QTextCursor.End)

    def finalize_stream(self):
        if not hasattr(self, 'stream_active') or not self.stream_active:
            return

        # Securely close the high-fidelity clinical bubble
        if self.stream_cursor:
            self.stream_cursor.insertHtml("</div></div>")
        
        if not self.current_full_response.strip():
             if self.stream_cursor:
                 self.stream_cursor.insertText("No response received from clinical provider.")
        
        # UI Transformation: Back to 'Ready' Mode
        self.user_input.setReadOnly(False)
        self.user_input.setFocus()
        self.send_btn.setEnabled(True)
        self.send_btn.setText("SEND")
        self.apply_theme(Styles.PALETTES[self.settings_manager.get('theme', 'pure_dark')])
        self.stop_requested = False
        self.stream_active = False
        self.stream_cursor = None

    def _handle_error(self, msg):
        self._append_message("SYSTEM FAIL", msg, is_ai=False)
        self.finalize_stream()

    def _handle_stop(self):
        self.stop_requested = True
        self.finalize_stream()

    def _handle_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Research Note", "", "Markdown Files (*.md)")
        if not path: return
        with open(path, "w", encoding='utf-8') as f:
            f.write(self.chat_display.toPlainText())
        QMessageBox.information(self, "Export Success", "Clinical Deliberation Saved.")
