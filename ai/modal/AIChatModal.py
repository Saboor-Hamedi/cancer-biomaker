import threading
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QLineEdit, QPushButton, QLabel, QFrame, 
                               QComboBox, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer, QEvent, Signal
from PySide6.QtGui import QTextCursor, QFont, QIcon
from ui.styles import Styles
from ai.MultiAIManager import MultiAIManager

class AIChatModal(QDialog):
    """Clinical Research Copilot: Multi-AI Strategic Deliberation Engine."""
    
    stream_started_signal = Signal()
    stream_chunk_signal = Signal(str)
    stream_finished_signal = Signal()
    stream_error_signal = Signal(str)
    
    SYSTEM_PROMPT = """
    You are the Clinical Research Copilot for the Cancer Biomarker XAI Dashboard.
    Your mission is to assist researchers in interpreting electrochemical biomarker data (PSA, AFP, CA125), 
    analyzing AI committee consensus, and exploring model explainability (SHAP/Counterfactuals).
    
    Current Research Context:
    - Biomarkers: PSA (Prostate Specific), AFP (Liver), CA125 (Ovarian/General).
    - AI Committee: Logistic Regression, SVM, Random Forest, XGBoost.
    - Focus: Diagnostic clarity, outlier detection, and clinical justification.
    
    Always maintain a professional, analytical, and supportive research-focused tone. 
    Remind researchers that all insights are for analytical support and must be clinically validated.
    """

    def __init__(self, parent=None, settings_manager=None, clinical_context=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.clinical_context = clinical_context or {}
        self.current_full_response = ""
        self.stop_requested = False
        self.stream_active = False
        self.stream_cursor = None
        self.last_user_prompt = ""
        
        self.setWindowTitle("🧬 CLINICAL RESEARCH COPILOT")
        self.setMinimumSize(900, 750)
        self._init_ui()
        
        self.stream_started_signal.connect(self.prepare_stream)
        self.stream_chunk_signal.connect(self._on_chunk_received)
        self.stream_finished_signal.connect(self.finalize_stream)
        self.stream_error_signal.connect(self._handle_error)
        
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # ── 1. Tactical Header ──
        self.header = QFrame()
        self.header.setFixedHeight(110)
        self.header.setObjectName("AssistantHeader")
        h_layout = QVBoxLayout(self.header)
        h_layout.setContentsMargins(25, 20, 25, 15)
        
        top_row = QHBoxLayout()
        title_group = QVBoxLayout()
        title = QLabel("AI RESEARCH COPILOT")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Strategic Deliberation & Biomarker Analysis")
        subtitle.setObjectName("HeaderSubtitle")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        top_row.addLayout(title_group)
        top_row.addStretch()
        
        # 🛡️ Mission Hardening: Restoring ALL providers including DeepSeek
        self.provider_menu = QComboBox()
        self.provider_menu.addItems(["DeepSeek", "Gemini", "OpenAI", "Anthropic", "Ollama"])
        self.provider_menu.setFixedWidth(140)
        self.provider_menu.setFixedHeight(35)
        top_row.addWidget(self.provider_menu)
        h_layout.addLayout(top_row)
        
        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("Enter Provider API Key...")
        self.key_entry.setEchoMode(QLineEdit.Password)
        self.key_entry.setFixedHeight(35)
        self.key_entry.textChanged.connect(self._on_key_changed)
        self.key_entry.installEventFilter(self)
        h_layout.addWidget(self.key_entry)

        self.main_layout.addWidget(self.header)

        # ── 2. Chat Display ──
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.document().setDocumentMargin(15)
        self.chat_display.setObjectName("AssistantChatFeed")
        self.main_layout.addWidget(self.chat_display)

        # ── 3. Footer Input Area ──
        self.footer = QFrame()
        self.footer.setFixedHeight(180)
        self.footer.setObjectName("AssistantFooter")
        f_layout = QVBoxLayout(self.footer)
        f_layout.setContentsMargins(35, 20, 35, 20)

        self.user_input = QTextEdit()
        self.user_input.setPlaceholderText("Describe clinical context or ask for forensic analysis...")
        self.user_input.setObjectName("AssistantInputField")
        self.user_input.installEventFilter(self)
        f_layout.addWidget(self.user_input)

        btn_row = QHBoxLayout()
        self.export_btn = QPushButton(" 📁 EXPORT RESEARCH NOTE")
        self.export_btn.setFixedHeight(40)
        self.export_btn.clicked.connect(self._handle_export)
        btn_row.addWidget(self.export_btn)
        
        btn_row.addStretch()

        self.send_btn = QPushButton("SEND")
        self.send_btn.setFixedHeight(40)
        self.send_btn.setObjectName("PrimaryBtn")
        self.send_btn.setFixedWidth(180)
        self.send_btn.clicked.connect(self._handle_send)
        btn_row.addWidget(self.send_btn)

        f_layout.addLayout(btn_row)
        self.main_layout.addWidget(self.footer)

    def apply_theme(self, palette):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {palette['bg_main']}; }}
            #AssistantHeader {{ background-color: {palette['bg_sidebar']}; border-bottom: 1px solid {palette['border']}; }}
            #AssistantChatFeed {{ background-color: {palette['bg_main']}; border: none; color: {palette['text_main']}; }}
            #AssistantFooter {{ background-color: {palette['bg_sidebar']}; border-top: 1px solid {palette['border']}; }}
            #AssistantInputField {{ background-color: {palette['card_bg']}; border: 1px solid {palette['border']}; border-radius: 12px; color: {palette['text_main']}; padding: 10px; font-size: 14px; }}
            #HeaderTitle {{ font-weight: bold; font-size: 14px; color: {palette['text_main']}; }}
            #HeaderSubtitle {{ font-size: 10px; color: {palette['text_dim']}; text-transform: uppercase; letter-spacing: 1px; }}
            QComboBox, QLineEdit {{ background-color: {palette['card_bg']}; border: 1px solid {palette['border']}; border-radius: 8px; color: {palette['text_main']}; padding: 5px; }}
            QPushButton {{ background-color: {palette['bg_main']}; border: 1px solid {palette['border']}; border-radius: 8px; color: {palette['text_main']}; font-weight: bold; }}
            #PrimaryBtn {{ background-color: {palette['accent']}; color: white; border: none; }}
        """)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if obj is self.key_entry:
                    self.user_input.setFocus()
                    return True
                if obj is self.user_input and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._handle_send()
                    return True
        return super().eventFilter(obj, event)

    def _on_key_changed(self, key):
        if self.settings_manager:
            provider = self.provider_menu.currentText()
            self.settings_manager.set_ai_key(provider, key.strip())

    def _handle_send(self):
        if self.stream_active:
            self._handle_stop()
            return

        prompt = self.user_input.toPlainText().strip()
        if not prompt: return
        
        provider = str(self.provider_menu.currentText()).lower().strip()
        api_key = self.key_entry.text().strip()
        
        if not api_key:
            QMessageBox.critical(self, "CREDENTIAL ERROR", f"API Key required for {provider}.")
            return
            
        self.user_input.clear()
        self.user_input.setReadOnly(True)
        self.last_user_prompt = prompt
        self._append_message("RESEARCHER", prompt, is_ai=False)
        
        self.send_btn.setText("STOP")
        self.send_btn.setStyleSheet("background-color: #EF4444; color: white; border: none;")
        self.current_full_response = ""
        self.stop_requested = False
        self.stream_active = True
        
        threading.Thread(target=self._fetch_ai_stream, args=(provider, api_key, prompt), daemon=True).start()

    def _append_message(self, sender, text, is_ai=True):
        is_dark = self.settings_manager.get('theme', 'pure_dark') == 'pure_dark'
        emoji = "🤖" if is_ai else "🧬"
        
        if is_ai:
            color = "#10B981" 
            bg = "#18181B" if is_dark else "#F1F5F9"
        else:
            color = "#3B82F6"
            bg = "#09090B" if is_dark else "#FFFFFF"
            
        msg_html = f"""
        <div style="margin: 0; padding: 0; clear: both; width: 100%;">
            <div style="margin-bottom: 25px; padding: 15px; background-color: {bg}; border-radius: 12px; border: 1px solid #27272A; display: inline-block; width: 85%;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 16px; margin-right: 10px;">{emoji}</span>
                    <b style="color: {color}; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;">{sender}</b>
                </div>
                <div style="color: {'#E4E4E7' if is_dark else '#0F172A'}; font-size: 14px; line-height: 1.6; margin-left: 28px;">
                    {text.replace('\\n', '<br>')}
                </div>
            </div>
        </div>
        <div style='clear:both; height:1px;'></div>
        """
        self.chat_display.append(msg_html)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def _fetch_ai_stream(self, provider, api_key, prompt):
        try:
            client = MultiAIManager.create_client(provider.lower(), api_key)
            if not client: raise ValueError("AI Infrastructure Fail.")
            
            print(f"\\n[AI DEBUG] MISSION LAUNCH: {provider}...")
            self.stream_started_signal.emit()
            
            for chunk in client.generate_stream(prompt, system_instruction=self.SYSTEM_PROMPT):
                if self.stop_requested: break
                if chunk:
                    print(chunk, end="", flush=True)
                    self.stream_chunk_signal.emit(chunk)
                
            print("\\n[AI DEBUG] MISSION SUCCESS.")
            self.stream_finished_signal.emit()
        except Exception as e:
            print(f"\\n[AI DEBUG] MISSION FAILURE: {str(e)}")
            self.stream_error_signal.emit(str(e))

    def prepare_stream(self):
        self.current_full_response = ""
        self.pre_stream_html = self.chat_display.toHtml()
        self.chat_display.append("<br><div style='color:#71717A; font-style:italic;' id='thinking_tag'>AI is analyzing clinical context...</div>")

    def _on_chunk_received(self, chunk):
        if not chunk: return
        self.current_full_response += chunk
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def finalize_stream(self):
        if not self.stream_active: return
        
        # Restore pre-stream history to clear out raw stream output
        self.chat_display.setHtml(self.pre_stream_html)
        
        final_msg = self.current_full_response if self.current_full_response.strip() else "Deliberation complete."
        self._append_message("AI ASSISTANT", final_msg, is_ai=True)
        
        self.user_input.setReadOnly(False)
        self.user_input.setFocus()
        self.send_btn.setEnabled(True)
        self.send_btn.setText("SEND")
        self.send_btn.setStyleSheet("")
        self.stop_requested = False
        self.stream_active = False

    def _handle_error(self, msg):
        self._append_message("SYSTEM FAIL", msg, is_ai=False)
        self.finalize_stream()

    def _handle_stop(self):
        self.stop_requested = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("STOPPING...")

    def _handle_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Note", "", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding='utf-8') as f:
                f.write(self.chat_display.toPlainText())
            QMessageBox.information(self, "Export Success", "Saved.")