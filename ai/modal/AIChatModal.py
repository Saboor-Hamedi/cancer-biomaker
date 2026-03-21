import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import sys
import os
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
except (ImportError, ValueError):
    try:
        from ChatGPTClient import ChatGPTClient
        from ClaudeClient import ClaudeClient
        from DeepSeekClient import DeepSeekClient
        from GeminiClient import GeminiClient
    except ImportError:
        sys.path.append(parent_dir)
        from ChatGPTClient import ChatGPTClient
        from ClaudeClient import ClaudeClient
        from DeepSeekClient import DeepSeekClient
        from GeminiClient import GeminiClient

class AIChatModal(tk.Toplevel):
    """
    State-of-the-Art AI Clinical Research Assistant.
    Remembers user preferences, manages language consistency, and features a premium chat layout.
    """
    
    SYSTEM_PROMPT = (
        "You are the 'Clinical Research Copilot', an expert assistant in medical data science and Oncology. "
        "CRITICAL: Always respond in English unless the user specifically speaks to you in another language. "
        "Match the language of the user's input. For DeepSeek specifically, ensure the output is purely clinical and professional."
    )

    def __init__(self, parent, settings_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        
        self.title("AI Clinical Research Assistant")
        self.geometry("800x900")
        
        # Theme Integration
        self.theme = settings_manager.theme if settings_manager else 'pure_dark'
        self.is_dark = (self.theme == 'pure_dark')
        
        # Advanced Professional Palette
        if self.is_dark:
            self.colors = {
                'bg': '#020617',         # Slate-950
                'surface': '#0F172A',    # Slate-900
                'border': '#1E293B',     # Slate-800
                'user_header': '#3B82F6', # blue-500
                'ai_header': '#10B981',   # emerald-500
                'user_text': '#F8FAFC',
                'ai_text': '#E2E8F0',
                'accent': '#6366F1',     # Indigo-500
                'input_area': '#0F172A',
                'user_bubble': '#1E293B'
            }
        else:
            self.colors = {
                'bg': '#F8FAFC',         # Slate-50
                'surface': '#FFFFFF',    # White
                'border': '#E2E8F0',     # Slate-200
                'user_header': '#2563EB', # blue-600
                'ai_header': '#059669',   # emerald-600
                'user_text': '#1E293B',
                'ai_text': '#334155',
                'accent': '#4F46E5',
                'input_area': '#FFFFFF',
                'user_bubble': '#F1F5F9'
            }

        self.configure(bg=self.colors['bg'])
        self.transient(parent)
        self.grab_set()

        self.ai_clients = {}
        
        # Load Last Provider State
        self.initial_provider = settings_manager.last_ai_provider if settings_manager else "ChatGPT"

        self._center_modal()
        self._setup_window_icon()
        self._setup_ui()
        self._load_saved_keys()

    def _center_modal(self):
        self.update_idletasks()
        w, h = 800, 900
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

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

        tk.Label(header, text=" CLINICAL RESEARCH COPILOT", font=("Inter", 13, "bold"), 
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

        self.key_entry = tk.Entry(config_dock, show="*", width=25, font=("Consolas", 10), 
                                  bg=self.colors['bg'], fg=self.colors['ai_text'], 
                                  borderwidth=0, highlightthickness=1)
        self.key_entry.config(highlightbackground=self.colors['border'], highlightcolor=self.colors['accent'])
        self.key_entry.pack(side=tk.LEFT)
        self.key_entry.bind("<FocusOut>", self._save_current_key)

        # Chat Area - Main Content
        chat_container = tk.Frame(self, bg=self.colors['bg'], padx=20, pady=10)
        chat_container.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(chat_container, wrap=tk.WORD, state='disabled', 
                                                       font=("Inter", 11), bg=self.colors['bg'], 
                                                       fg=self.colors['ai_text'], borderwidth=0, 
                                                       padx=20, pady=20, highlightthickness=0)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Define Premium Tags for Message Blocks
        self.chat_display.tag_configure("user_block", spacing1=20, spacing3=10, 
                                        background=self.colors['user_bubble'] if not self.is_dark else "#111827",
                                        lmargin1=20, rmargin=20)
        self.chat_display.tag_configure("ai_block", spacing1=20, spacing3=20, lmargin1=20, rmargin=20)
        
        self.chat_display.tag_configure("user_header", font=("Inter", 11, "bold"), foreground=self.colors['user_header'])
        self.chat_display.tag_configure("ai_header", font=("Inter", 11, "bold"), foreground=self.colors['ai_header'])
        
        self.chat_display.tag_configure("content_user", font=("Inter", 11), spacing1=5)
        self.chat_display.tag_configure("content_ai", font=("Inter", 11), spacing1=5)
        self.chat_display.tag_configure("error", foreground="#EF4444", font=("Inter", 10, "italic"))

        # Footer Input
        input_dock = tk.Frame(self, bg=self.colors['surface'], pady=20, padx=30, borderwidth=1, relief="flat")
        input_dock.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 1. Textarea takes FULL WIDTH at the top
        self.user_entry = tk.Text(input_dock, height=4, font=("Inter", 11), 
                                  bg=self.colors['bg'], fg=self.colors['ai_text'], 
                                  borderwidth=1, padx=15, pady=10, insertbackground=self.colors['ai_text'],
                                  highlightthickness=1, highlightbackground=self.colors['border'])
        self.user_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.user_entry.bind("<Return>", self._intercept_return)
        
        # 2. Button stays below it on the RIGHT for a clean layout
        self.send_btn = tk.Button(input_dock, text="SEND", bg=self.colors['accent'], 
                                  fg="white", font=("Inter", 11, "bold"), relief="raised",
                                  activebackground=self.colors['ai_header'], activeforeground="white",
                                  padx=40, pady=8, command=self.handle_send, cursor="hand2",
                                  width=12, highlightthickness=0) 
        self.send_btn.pack(side=tk.TOP, anchor=tk.E, pady=(15, 0)) 

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
        tag_content = "content_ai" if is_ai else "content_user"
        
        # Start Block
        self.chat_display.insert(tk.END, f"  {sender.upper()}\n", (tag_header, tag_block))
        self.chat_display.insert(tk.END, f"  {message}\n", (tag_content, tag_block))
        
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def handle_send(self):
        user_input = self.user_entry.get("1.0", tk.END).strip()
        if not user_input: return
        
        provider = self.provider_var.get()
        api_key = self.key_entry.get().strip()
        
        if not api_key:
            messagebox.showwarning("System Error", "Clinical API Key required.")
            return

        self._save_current_key()
        self.user_entry.delete("1.0", tk.END)
        self.log_message("Researcher", user_input, is_ai=False)
        
        self.send_btn.config(state="disabled", text="ANALYZING...")
        threading.Thread(target=self.fetch_ai_response, args=(provider, api_key, user_input), daemon=True).start()

    def fetch_ai_response(self, provider, api_key, prompt):
        try:
            if provider not in self.ai_clients:
                if provider == "DeepSeek": self.ai_clients[provider] = DeepSeekClient(api_key)
                elif provider == "ChatGPT": self.ai_clients[provider] = ChatGPTClient(api_key)
                elif provider == "Gemini": self.ai_clients[provider] = GeminiClient(api_key)
                elif provider == "Claude": self.ai_clients[provider] = ClaudeClient(api_key)
            else:
                self.ai_clients[provider].client.api_key = api_key

            # Force English and language matching via System Prompt
            response = self.ai_clients[provider].generate_response(prompt, system_instruction=self.SYSTEM_PROMPT)
            self.after(0, lambda: self._finalize_response(provider, response))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self._finalize_response("AI Error", err_msg, is_error=True))

    def _finalize_response(self, provider, response, is_error=False):
        self.send_btn.config(state="normal", text="SEND")
        if is_error:
            self.log_message(provider, response, is_ai=True)
        else:
            self.log_message(provider, response, is_ai=True)

if __name__ == "__main__":
    from logic.settings_manager import SettingsManager
    root = tk.Tk()
    sm = SettingsManager()
    btn = tk.Button(root, text="Launch Assistant", command=lambda: AIChatModal(root, settings_manager=sm))
    btn.pack(pady=50)
    root.mainloop()
