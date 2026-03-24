import tkinter as tk
import numpy as np
from tkinter import ttk, messagebox

class PreprocessingDialog:
    """Professional clinical data optimization dialog."""
    def __init__(self, parent, data_status, settings_manager, on_apply):
        self.modal = tk.Toplevel(parent)
        self.modal.withdraw()
        self.modal.title("BIO-OPTIMIZATION REGISTRY")
        self.settings_manager = settings_manager
        self.on_apply = on_apply
        
        from ui.styles import StyleManager
        self.palette = StyleManager.get_palette(settings_manager.theme)
        self.modal.configure(bg=self.palette['bg_main'])
        self.modal.resizable(False, False)
        
        # Geometry: Center relative to Parent
        width, height = 400, 420
        self.modal.update_idletasks()
        
        p_x = parent.winfo_rootx()
        p_y = parent.winfo_rooty()
        p_w = parent.winfo_width()
        p_h = parent.winfo_height()
        
        x = p_x + (p_w // 2) - (width // 2)
        y = p_y + (p_h // 2) - (height // 2)
        self.modal.geometry(f'{width}x{height}+{x}+{y}')
        
        self._setup_ui(data_status)
        self.modal.deiconify()
        self.modal.grab_set()

    def _setup_ui(self, data_status):
        palette = self.palette
        container = tk.Frame(self.modal, bg=palette['bg_main'], padx=30, pady=25)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(container, text="CLINICAL DATA OPTIMIZATION", font=("Inter", 12, "bold"), 
                 bg=palette['bg_main'], fg=palette['medic_brand']).pack(pady=(0, 5))
        
        status_text = f"RECORDS: {data_status['rows']} | MISSING (NaN): {data_status['nan']}"
        tk.Label(container, text=status_text, font=("Inter", 8, "bold"), 
                 bg=palette['bg_main'], fg=palette['text_muted']).pack(pady=(0, 25))

        # Custom Themed Checkbuttons
        self.scale_var = tk.BooleanVar(value=self.settings_manager.get('scaling_enabled', True))
        self.outlier_var = tk.BooleanVar(value=self.settings_manager.get('outlier_removal', True))

        checks = [
            ("Apply Standard Scaling (Z-Score)", self.scale_var),
            ("Auto Outlier IQR Clipping (3.0 \u03c3)", self.outlier_var)
        ]

        for text, var in checks:
            cb = tk.Checkbutton(container, text=text, variable=var,
                               bg=palette['bg_main'], fg=palette['text_main'], selectcolor=palette['card_bg'],
                               activebackground=palette['bg_main'], activeforeground=palette['medic_brand'],
                               highlightthickness=0, borderwidth=0,
                               font=("Inter", 10), pady=10)
            cb.pack(anchor=tk.W)

        # Guidance
        tk.Label(container, text="These settings ensure mathematical stability for the AI Committee across disparate biomarker scales.", 
                 bg=palette['bg_main'], fg=palette['text_muted'], font=("Inter", 8), wraplength=340, justify=tk.LEFT).pack(pady=30)

        # Controls
        tk.Button(container, text="Apply Changes & Sync", command=self._apply, 
                 bg=palette['medic_brand'], fg="white", font=("Inter", 10, "bold"), 
                 relief='flat', padx=20, pady=10).pack(side=tk.BOTTOM, fill=tk.X)

    def _apply(self):
        options = {
            'scale': self.scale_var.get(),
            'outlier': self.outlier_var.get()
        }
        self.on_apply(options)
        self.modal.destroy()

class SettingsDialog:
    """Modal dialog for application customization."""
    def __init__(self, parent, settings_manager, on_change):
        self.modal = tk.Toplevel(parent)
        self.modal.title("UI Customization")
        self.settings_manager = settings_manager
        self.on_change = on_change
        
        from ui.styles import StyleManager
        self.palette = StyleManager.get_palette(settings_manager.theme)
        
        # Geometry
        self.modal.geometry("450x550")
        self.modal.resizable(False, False)
        self.modal.configure(bg=self.palette['bg_main'])
        
        # Center
        self.modal.update_idletasks()
        x = (self.modal.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.modal.winfo_screenheight() // 2) - (550 // 2)
        self.modal.geometry(f"+{x}+{y}")
        
        self._setup_ui()
        self.modal.grab_set() # Modal behavior

    def _setup_ui(self):
        palette = self.palette
        container = tk.Frame(self.modal, bg=palette['bg_main'], padx=30, pady=25)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(container, text="VISUAL PREFERENCES", font=("Inter", 14, "bold"), 
                 bg=palette['bg_main'], fg=palette['medic_brand']).pack(anchor=tk.W, pady=(0, 20))

        # Theme
        tk.Label(container, text="APPLICATION THEME", font=("Inter", 9, "bold"), 
                 bg=palette['bg_main'], fg=palette['text_muted']).pack(anchor=tk.W, pady=(10, 5))
        
        self.theme_var = tk.StringVar(value=self.settings_manager.theme)
        themes = [
            ("Pure Dark (Absolute Black)", "pure_dark"),
            ("Pure Light (Absolute White)", "pure_light")
        ]
        
        for text, mode in themes:
            rb = tk.Radiobutton(container, text=text, variable=self.theme_var, value=mode,
                                bg=palette['bg_main'], fg=palette['text_main'], selectcolor=palette['card_bg'],
                                activebackground=palette['bg_main'], activeforeground=palette['medic_brand'],
                                font=("Inter", 10), command=self._update_settings)
            rb.pack(anchor=tk.W, pady=3)

        # Separator
        tk.Frame(container, height=1, bg=palette['border_light']).pack(fill=tk.X, pady=20)

        # Scaling Dropdown (Replacing Slider)
        tk.Label(container, text="FONT SIZE (BASE)", font=("Inter", 9, "bold"), 
                 bg=palette['bg_main'], fg=palette['text_muted']).pack(anchor=tk.W, pady=(0, 5))
        
        # Calculate current approx px from current scale
        approx_px_current = int(self.settings_manager.font_scale * 12)
        if approx_px_current not in [12, 14, 16, 18, 20]:
            approx_px_current = 14 # Default fallback
            
        self.px_var = tk.StringVar(value=f"{approx_px_current}px")
        
        # Style for Combobox
        style = ttk.Style(self.modal)
        style.configure('Settings.TCombobox', fieldbackground=palette['bg_main'], 
                        background=palette['border_light'], foreground=palette['text_main'])
        
        self.combo_px = ttk.Combobox(
            container, values=["12px", "14px", "16px", "18px", "20px"],
            textvariable=self.px_var, state="readonly"
        )
        self.combo_px.pack(fill=tk.X, pady=10)
        self.combo_px.bind("<<ComboboxSelected>>", lambda e: self._update_settings())
        
        self.scale_label = tk.Label(container, text="Select base font size for best clinical legibility.", 
                                    bg=palette['bg_main'], fg=palette['medic_brand'], font=("Inter", 9))
        self.scale_label.pack(anchor=tk.W)

        # Tips
        tk.Label(container, text="Use scaling to improve legibility in complex clinical views.", 
                 bg=palette['bg_main'], fg=palette['text_muted'], font=("Inter", 8), wraplength=380, justify=tk.LEFT).pack(pady=20)

        # Close Button
        tk.Button(container, text="Save & Done", command=self.modal.destroy, 
                  bg=palette['medic_brand'], fg="white", font=("Inter", 10, "bold"), 
                  relief='flat', padx=20, pady=8).pack(side=tk.BOTTOM, fill=tk.X)

    def _update_settings(self):
        self.settings_manager.set('theme', self.theme_var.get())
        
        # Map px back to scale factor (Base 12px = 1.0)
        px_val = int(self.px_var.get().replace("px", ""))
        new_scale = px_val / 12.0
        
        self.settings_manager.set('font_scale', round(new_scale, 2))
        self.on_change()
