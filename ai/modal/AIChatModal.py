import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import sys
import os
import re
from PIL import Image, ImageTk

# Ensure the parent directory (ai/) is in sys.path for direct trial execution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from ..ChatGPTClient import ChatGPTClient
    from ..ClaudeClient import ClaudeClient
    from ..DeepSeekClient import DeepSeekClient
    from ..GeminiClient import GeminiClient
    from ..MultiAIManager import MultiAIManager
except (ImportError, ValueError):
    try:
        from ChatGPTClient import ChatGPTClient
        from ClaudeClient import ClaudeClient
        from DeepSeekClient import DeepSeekClient
        from GeminiClient import GeminiClient
        from MultiAIManager import MultiAIManager
    except ImportError:
        sys.path.append(parent_dir)
        from ChatGPTClient import ChatGPTClient
        from ClaudeClient import ClaudeClient
        from DeepSeekClient import DeepSeekClient
        from GeminiClient import GeminiClient
        from MultiAIManager import MultiAIManager

class AIChatModal(tk.Toplevel):
    """
    State-of-the-Art AI Clinical Research Assistant.
    Remembers user preferences, manages language consistency, and features a premium chat layout.
    """
    
    def _build_system_prompt(self, context=None):
        """Constructs a context-aware system instruction for the AI."""
        ctx = context or {}
        features_str = "N/A"
        stats_str = "N/A"
        leaderboard_str = "N/A"
        
        if ctx.get('features'):
            features_str = "\n".join([f"- {f}: {v}" for f, v in ctx['features'].items()])
        
        if ctx.get('stats'):
            s = ctx['stats']
            stats_str = f"Risk Prob: {s.get('avg_risk')} | Confidence: {s.get('confidence')} | Triage: {s.get('triage')}"

        if ctx.get('leaderboard'):
            lb_lines = []
            for i, en in enumerate(ctx['leaderboard']):
                m = f"- Rank #{i+1}: {en['model']} (F1: {en.get('f1',0):.2%}, AUC: {en.get('auc',0):.2%}, Acc: {en.get('accuracy',0):.2%}, Prec: {en.get('precision',0):.2%}, Rec: {en.get('recall',0):.2%})"
                lb_lines.append(m)
            leaderboard_str = "\n".join(lb_lines)

        self.SYSTEM_PROMPT = f"""You are the 'Clinical Research Copilot' for the Cancer Biomarker XAI Dashboard.
Your role is to assist oncology researchers in interpreting biomarker data and AI-driven risk predictions.

[[ CLINICAL DATA FOR CURRENT PATIENT ]]
Active Biomarkers:
{features_str}

Live Dashboard Diagnostics:
{stats_str}

[[ ALGORITHM LEADERBOARD (Performance Benchmarks) ]]
The following models have been cross-validated on the research dataset ({ctx.get('data_source', 'Active Batch')}):
{leaderboard_str}
Use these metrics to explain which models are the most reliable (prioritize High F1/AUC) and if there is a discrepancy between algorithms.

[[ RULES ]]
1. LANGUAGE: Always respond in the SAME language as the user.
2. TONE: Professional, clinical, and data-driven. 
3. DISCLAIMER: Always remind the user that your output is for research assistance and MUST be validated by a licensed physician.
4. METRIC ENFORCEMENT: When citing a model's performance, ALWAYS include its F1-Score and AUC. Specify exact values (e.g. 100.00%) rather than generic terms.
5. DATA INTEGRITY: Use ONLY the metrics provided in the [[ ALGORITHM LEADERBOARD ]] above. Even if you think a model 'usually' performs differently, you MUST report and analyze based strictly on the current research session data. Never hallucinate scores.
6. CONTEXT: If data exists, prioritize explaining how specific biomarker values relate to the risk prediction based on the performance of the top-ranked models.
"""

    def __init__(self, parent, settings_manager=None, clinical_context=None):
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        self.clinical_context = clinical_context
        self._build_system_prompt(clinical_context)
        
        self.title("AI Clinical Research Assistant")
        # Theme & Styling Synchronization
        from ui.styles import StyleManager
        self.theme = settings_manager.theme if settings_manager else 'pure_dark'
        self.palette = StyleManager.get_palette(self.theme)
        self.is_dark = (self.theme == 'pure_dark')
        
        # Scale & Font Family
        self.font_scale = settings_manager.get('font_scale', 1.0) if settings_manager else 1.0
        self.font_family = "Inter"

        # Dynamically Mapped Palette for Premium Clinical View
        self.colors = {
            'bg': self.palette['bg_main'],
            'surface': self.palette['card_bg'],
            'border': self.palette['border_light'],
            'user_header': self.palette['medic_brand'],
            'ai_header': '#10B981' if self.is_dark else '#059669', # Professional Clinical Green
            'user_text': self.palette['text_main'],
            'ai_text': self.palette['text_main'],
            'accent': self.palette['medic_brand'],
            'input_area': self.palette['bg_main'],
            'user_bubble': self.palette['border_light'] if self.is_dark else '#F1F5F9'
        }

        self.configure(bg=self.colors['bg'])
        self.protocol("WM_DELETE_WINDOW", self.on_hide)

        self.ai_clients = {}
        self.stop_requested = False
        
        # Load Last Provider State
        self.initial_provider = settings_manager.last_ai_provider if settings_manager else "ChatGPT"

        self._center_modal()
        self._setup_window_icon()
        self._setup_ui()
        self._load_saved_keys()

    def update_context(self, clinical_context):
        """Refreshes the internal clinical knowledge base without clearing the chat."""
        self.clinical_context = clinical_context
        self._build_system_prompt(clinical_context)
        # We could also log a small internal message about the context update if desired
        
    def on_hide(self):
        """Hide the assistant instead of destroying it to save conversation state."""
        self.withdraw()

    def _center_modal(self):
        self.update_idletasks()
        w, h = 800, 850 # Slightly smaller for better fit
        
        try:
            # Sync with Main App Window
            p_x = self.parent.winfo_rootx()
            p_y = self.parent.winfo_rooty()
            p_w = self.parent.winfo_width()
            p_h = self.parent.winfo_height()
            
            x = p_x + (p_w // 2) - (w // 2)
            y = p_y + (p_h // 2) - (h // 2)
            
            # Ensure it doesn't spill off screen
            x = max(10, min(x, self.winfo_screenwidth() - w - 10))
            y = max(10, min(y, self.winfo_screenheight() - h - 10))
            
            self.geometry(f"{w}x{h}+{x}+{y}")
        except:
            # Emergency Fallback to screen center
            x = (self.winfo_screenwidth() // 2) - (w // 2)
            y = (self.winfo_screenheight() // 2) - (h // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")

    def _add_hover(self, widget, color_on, color_off):
        """Standardizes interactive feedback across the clinical modal."""
        widget.bind("<Enter>", lambda e: widget.config(bg=color_on))
        widget.bind("<Leave>", lambda e: widget.config(bg=color_off))

    def _setup_window_icon(self):
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(root_dir, "logo.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.iconphoto(False, self.icon_photo)
        except: pass

    def _setup_ui(self):
        # Top Dashboard
        header = tk.Frame(self, bg=self.colors['surface'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=" CLINICAL RESEARCH COPILOT", font=(self.font_family, int(13 * self.font_scale), "bold"), 
                 fg=self.colors['ai_header'], bg=self.colors['surface']).pack(side=tk.LEFT, padx=30)
        
        # Settings Dock
        config_dock = tk.Frame(header, bg=self.colors['surface'])
        config_dock.pack(side=tk.RIGHT, padx=30)

        self.provider_var = tk.StringVar(value=self.initial_provider)
        self.provider_menu = ttk.Combobox(config_dock, textvariable=self.provider_var, 
                                          values=["ChatGPT", "Claude", "DeepSeek", "Gemini"], 
                                          state="readonly", width=12)
        self.provider_menu.pack(side=tk.LEFT, padx=10)
        self.provider_menu.bind("<<ComboboxSelected>>", self._on_provider_change)

        self.key_entry = tk.Entry(config_dock, show="*", width=25, font=("Consolas", int(10 * self.font_scale)), 
                                  bg=self.colors['bg'], fg=self.colors['ai_text'], 
                                  borderwidth=0, highlightthickness=1)
        self.key_entry.config(highlightbackground=self.colors['border'], highlightcolor=self.colors['accent'])
        self.key_entry.pack(side=tk.LEFT)
        self._add_hover(self.key_entry, self.colors['surface'], self.colors['bg'])
        self.key_entry.bind("<FocusOut>", self._save_current_key)

        # Chat Area - Main Content
        chat_container = tk.Frame(self, bg=self.colors['bg'], padx=20, pady=10)
        chat_container.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(chat_container, wrap=tk.WORD, state='disabled', 
                                                       font=(self.font_family, int(11 * self.font_scale)), bg=self.colors['bg'], 
                                                       fg=self.colors['ai_text'], borderwidth=0, 
                                                       padx=20, pady=20, highlightthickness=0)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Define Premium Tags for Message Blocks
        self.chat_display.tag_configure("user_block", spacing1=20, spacing3=10, 
                                        background=self.colors['user_bubble'] if not self.is_dark else "#111827",
                                        lmargin1=20, rmargin=20)
        self.chat_display.tag_configure("ai_block", spacing1=20, spacing3=20, lmargin1=20, rmargin=20)
        
        self.chat_display.tag_configure("user_header", font=(self.font_family, int(11 * self.font_scale), "bold"), foreground=self.colors['user_header'])
        self.chat_display.tag_configure("ai_header", font=(self.font_family, int(11 * self.font_scale), "bold"), foreground=self.colors['ai_header'])
        
        self.chat_display.tag_configure("content_user", font=(self.font_family, int(11 * self.font_scale)), spacing1=5)
        self.chat_display.tag_configure("content_ai", font=(self.font_family, int(11 * self.font_scale)), spacing1=5)
        
        # Markdown Component Tags
        self.chat_display.tag_configure("bold", font=(self.font_family, int(11 * self.font_scale), "bold"))
        self.chat_display.tag_configure("h1", font=(self.font_family, int(14 * self.font_scale), "bold"), foreground=self.colors['ai_header'], spacing1=15, spacing3=5)
        self.chat_display.tag_configure("bullet_symbol", foreground=self.colors['accent'], font=(self.font_family, int(11 * self.font_scale), "bold"))
        self.chat_display.tag_configure("error", foreground="#EF4444", font=(self.font_family, int(10 * self.font_scale), "italic"))

        # Footer Input
        input_dock = tk.Frame(self, bg=self.colors['surface'], pady=20, padx=30, borderwidth=1, relief="flat")
        input_dock.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 1. Underline-Only Entry Container
        entry_container = tk.Frame(input_dock, bg=self.colors['bg'])
        entry_container.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.user_entry = tk.Text(entry_container, height=4, font=(self.font_family, int(14 * self.font_scale)), 
                                  bg=self.colors['bg'], fg=self.colors['ai_text'], 
                                  borderwidth=0, padx=15, pady=10, insertbackground=self.colors['ai_text'],
                                  highlightthickness=0, selectbackground=self.colors['accent'],
                                  selectforeground="white", undo=True)
        self.user_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # Professional Bottom Border (Underline)
        self.underline = tk.Frame(entry_container, height=2, bg=self.colors['border'])
        self.underline.pack(side=tk.TOP, fill=tk.X)

        # Placeholder System
        self.placeholder = "Describe patient profile or ask clinical analysis..."
        self.user_entry.insert("1.0", self.placeholder)
        self.user_entry.config(fg=self.palette['text_muted'])

        self.user_entry.bind("<FocusIn>", self._on_focus_in)
        self.user_entry.bind("<FocusOut>", self._on_focus_out)
        self.user_entry.bind("<Return>", self._intercept_return)
        
        # 2. Controls Area
        controls = tk.Frame(input_dock, bg=self.colors['surface'])
        controls.pack(side=tk.TOP, fill=tk.X, pady=(15, 0))
        
        self.export_btn = tk.Button(controls, text=" 💾 EXPORT RESEARCH NOTE ", bg=self.colors['surface'], 
                                  fg=self.colors['accent'], font=(self.font_family, int(9 * self.font_scale), "bold"), relief="flat",
                                  activebackground=self.colors['border'], activeforeground=self.colors['ai_header'],
                                  padx=15, pady=8, command=self.handle_export, cursor="hand2",
                                  borderwidth=1, highlightthickness=0)
        self.export_btn.pack(side=tk.LEFT)
        self._add_hover(self.export_btn, self.colors['border'], self.colors['surface'])

        self.send_btn = tk.Button(controls, text="SEND", bg=self.colors['accent'], 
                                  fg="white", font=(self.font_family, int(11 * self.font_scale), "bold"), relief="raised",
                                  activebackground=self.colors['ai_header'], activeforeground="white",
                                  padx=40, pady=8, command=self.handle_send, cursor="hand2",
                                  width=12, highlightthickness=0) 
        self.send_btn.pack(side=tk.RIGHT)
        self._add_hover(self.send_btn, self.colors['ai_header'], self.colors['accent'])

        self.stop_btn = tk.Button(controls, text="STOP", bg="#EF4444", 
                                  fg="white", font=(self.font_family, int(10 * self.font_scale), "bold"), relief="flat",
                                  activebackground="#DC2626", activeforeground="white",
                                  padx=20, pady=8, command=self.handle_stop, cursor="hand2",
                                  state="disabled") 
        self.stop_btn.pack(side=tk.RIGHT, padx=10)

    def _on_focus_in(self, event):
        if self.user_entry.get("1.0", tk.END).strip() == self.placeholder:
            self.user_entry.delete("1.0", tk.END)
            self.user_entry.config(fg=self.colors['ai_text'])
        self.underline.config(bg=self.colors['accent'])

    def _on_focus_out(self, event):
        if not self.user_entry.get("1.0", tk.END).strip():
            self.user_entry.insert("1.0", self.placeholder)
            self.user_entry.config(fg=self.palette['text_muted'])
        self.underline.config(bg=self.colors['border'])

    def _intercept_return(self, event):
        """Handle Enter for send, Shift+Enter for new line."""
        # Shift key check (Shift mask is 0x1 or 0x4 on some systems)
        if event.state & (0x1 | 0x4): 
            return None # Let it through for a new line
        
        self.handle_send()
        return "break"

    def _load_saved_keys(self):
        if self.settings_manager:
            keys = self.settings_manager.ai_keys
            provider = self.provider_var.get()
            if provider in keys:
                self.key_entry.delete(0, tk.END)
                self.key_entry.insert(0, keys[provider])

    def _on_provider_change(self, event=None):
        if self.settings_manager:
            provider = self.provider_var.get()
            # Save new provider choice
            self.settings_manager.set_last_ai_provider(provider)
            # Update key entry
            keys = self.settings_manager.ai_keys
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, keys.get(provider, ""))

    def _save_current_key(self, event=None):
        if self.settings_manager:
            provider = self.provider_var.get()
            key = self.key_entry.get().strip()
            self.settings_manager.set_ai_key(provider, key)

    def log_message(self, sender, message, is_ai=True):
        self.chat_display.configure(state='normal')
        
        tag_block = "ai_block" if is_ai else "user_block"
        tag_header = "ai_header" if is_ai else "user_header"
        base_tag = "content_ai" if is_ai else "content_user"
        
        # Header (Researcher/Provider)
        self.chat_display.insert(tk.END, f"  {sender.upper()}\n", (tag_header, tag_block))
        
        # Body with Markdown Support
        self._render_markdown_logic(message, (base_tag, tag_block))
        
        self.chat_display.insert(tk.END, "\n") # Space after block
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def _start_ai_block(self, provider):
        """Prep the UI for a streaming AI response."""
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"  {provider.upper()}\n", ("ai_header", "ai_block"))
        # Mark the start of the content so we can find it
        self.chat_display.mark_set("stream_start", "insert")
        self.chat_display.mark_gravity("stream_start", tk.LEFT)
        self.chat_display.configure(state='disabled')
        self.current_full_response = ""

    def _append_ai_chunk(self, chunk):
        """Append a chunk during streaming (Real-time)."""
        self.chat_display.configure(state='normal')
        self.current_full_response += chunk
        
        # We simplify live rendering to character-by-character appending
        # Markdown is finalized once the full block arrives for maximum precision
        self.chat_display.insert(tk.END, chunk, ("content_ai", "ai_block"))
        
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def _finalize_stream(self, provider):
        """Clean up and perform a markdown pass on the finished stream."""
        self.chat_display.configure(state='normal')
        
        # Remove the raw stream text to replace with formatted text
        self.chat_display.delete("stream_start", tk.END)
        
        # Render properly with markdown
        self._render_markdown_logic(self.current_full_response, ("content_ai", "ai_block"))
        self.chat_display.insert(tk.END, "\n")
        
        self.send_btn.config(state="normal", text="SEND")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def _render_markdown_logic(self, text, base_tags):
        # 0. Robust line splitting (handles both \r\n and \n)
        lines = text.replace('\r\n', '\n').split('\n')
        
        for i, line in enumerate(lines):
            working_line = line.strip()
            
            # Skip truly empty lines but preserve paragraph spacing
            if not working_line:
                if i < len(lines)-1: # Don't add trailing newline at the very end of block
                    self.chat_display.insert(tk.END, "\n", base_tags)
                continue
            
            # 1. Handle Headings (#, ##, ###)
            if working_line.startswith('#'):
                level = 0
                while level < len(working_line) and working_line[level] == '#':
                    level += 1
                header_text = working_line[level:].strip().rstrip('#').strip()
                self.chat_display.insert(tk.END, "  " + header_text + "\n", base_tags + ("h1",))
            
            # 2. Handle Bullets (- Bullet)
            elif working_line.startswith('- ') or working_line.startswith('* '):
                self.chat_display.insert(tk.END, "    • ", base_tags + ("bullet_symbol",))
                self._render_inline(working_line[2:], base_tags)
                self.chat_display.insert(tk.END, "\n", base_tags)
            
            # 3. Handle Normal Paragraphs & Bold-Only Titles
            else:
                self.chat_display.insert(tk.END, "  ", base_tags)
                self._render_inline(line, base_tags)
                self.chat_display.insert(tk.END, "\n", base_tags)

    def _render_inline(self, text, base_tags):
        """High-precision bolding for clinical reports."""
        cursor = 0
        # Use a more resilient non-greedy pattern that supports both styles
        for match in re.finditer(r'(\*\*|__)(?P<content>.*?)\1', text):
            # Lead text
            self.chat_display.insert(tk.END, text[cursor:match.start()], base_tags)
            # Bold segment
            self.chat_display.insert(tk.END, match.group('content'), base_tags + ("bold",))
            cursor = match.end()
        
        # Remaining tail text (IMPORTANT: ensure newlines and trailing subtext are kept)
        if cursor < len(text):
            self.chat_display.insert(tk.END, text[cursor:], base_tags)

    def handle_stop(self):
        """Halts the current clinical AI stream."""
        self.stop_requested = True
        self.stop_btn.config(state="disabled")

    def handle_send(self):
        user_input = self.user_entry.get("1.0", tk.END).strip()
        if not user_input or user_input == self.placeholder: return
        
        provider = self.provider_var.get()
        api_key = self.key_entry.get().strip()
        
        if not api_key:
            messagebox.showwarning("System Error", "Clinical API Key required.")
            return

        self.stop_requested = False
        self._save_current_key()
        self.user_entry.delete("1.0", tk.END)
        self.log_message("Researcher", user_input, is_ai=False)
        
        self.send_btn.config(state="disabled", text="ANALYZING...")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.fetch_ai_stream, args=(provider, api_key, user_input), daemon=True).start()

    def fetch_ai_stream(self, provider, api_key, prompt):
        """Core clinical research engine - handles API orchestration and streaming."""
        try:
            # 1. Multi-AI Factory Orchestration
            if provider not in self.ai_clients:
                client = MultiAIManager.create_client(provider, api_key)
                if not client: raise ValueError(f"Provider '{provider}' not initialized correctly.")
                self.ai_clients[provider] = client
            else:
                # Update key for existing client
                self.ai_clients[provider].client.api_key = api_key

            # 2. UI Preparation
            self.after(0, lambda: self._start_ai_block(provider))
            
            # 3. Stream Response via Background Engine
            for chunk in self.ai_clients[provider].generate_stream(prompt, system_instruction=self.SYSTEM_PROMPT):
                if self.stop_requested:
                    self.after(0, lambda: self._append_ai_chunk("\n\n[RESEARCH STREAM INTERRUPTED BY USER]"))
                    break
                self.after(0, lambda c=chunk: self._append_ai_chunk(c))
                
            # 4. Final Formatting Pass
            self.after(0, lambda: self._finalize_stream(provider))
            self.after(0, lambda: self.stop_btn.config(state="disabled"))
            
        except Exception as e:
            self.after(0, lambda: self._handle_stream_error(provider, str(e)))

    def handle_export(self):
        """Compiles clinical data and chat log into a professional Markdown report."""
        from tkinter import filedialog
        from datetime import datetime
        
        # 1. Generate filename with timestamp
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_ts = ts.replace(":", "-").replace(" ", "_")
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown Document", "*.md"), ("Professional Text", "*.txt")],
            title="Export Clinical Research Note",
            initialfile=f"Clinical_Research_{safe_ts}.md"
        )
        
        if not filename: return

        # 2. Assemble the Professional Report Header
        report = []
        report.append("# CANCER BIOMARKER XAI: CLINICAL RESEARCH NOTE")
        report.append(f"**Generated**: {ts}")
        report.append(f"**AI Analyst**: {self.provider_var.get()}")
        report.append("\n---")

        # 3. Inject Patient Context if available
        if self.clinical_context:
            report.append("\n## 🔬 ACTIVE PATIENT PROFILE")
            features = self.clinical_context.get('features', {})
            if features:
                report.append("### Biomarkers:")
                for f, v in features.items():
                    report.append(f"- **{f}**: {v}")
            
            stats = self.clinical_context.get('stats', {})
            if stats:
                report.append(f"\n### Model Diagnostics ({stats.get('triage')} Risk Level):")
                report.append(f"- **Average Risk Probability**: {stats.get('avg_risk')}")
                report.append(f"- **Diagnostic Confidence**: {stats.get('confidence')}")
            report.append("\n---")

        # 4. Extract Chat History
        report.append("\n## 💬 RESEARCH CONSULTATION LOG")
        chat_raw = self.chat_display.get("1.0", tk.END).strip()
        report.append(chat_raw)
        
        report.append("\n---")
        report.append("\n*DISCLAIMER: This report is generated by an AI Research Assistant for research purposes. It is NOT a clinical diagnosis and must be reviewed by a licensed medical professional.*")

        # 5. Save to disk
        try:
            with open(filename, "w", encoding='utf-8') as f:
                f.write("\n".join(report))
            messagebox.showinfo("Export Success", f"Professional Research Note saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Critical failure saving report: {str(e)}")

    def _handle_stream_error(self, provider, error_msg):
        self.log_message(f"{provider} (Error)", error_msg)
        self.send_btn.config(state="normal", text="SEND")

if __name__ == "__main__":
    from logic.settings_manager import SettingsManager
    root = tk.Tk()
    sm = SettingsManager()
    btn = tk.Button(root, text="Launch Assistant", command=lambda: AIChatModal(root, settings_manager=sm))
    btn.pack(pady=50)
    root.mainloop()
