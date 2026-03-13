"""
Style Manager - Manages global application themes and component styles.
"""
from tkinter import ttk

# Modern Minimalist Palette
PALETTE = {
    'primary': '#3B82F6',    # Blue 500
    'primary_dark': '#1D4ED8',
    'secondary': '#64748B',  # Slate 500
    'success': '#10B981',    # Emerald 500
    'warning': '#F59E0B',    # Amber 500
    'danger': '#EF4444',     # Red 500
    'bg': '#F8FAFC',         # Slate 50
    'card': '#FFFFFF',       # White
    'border': '#E2E8F0',     # Slate 200
    'text': '#1E293B',       # Slate 800
    'text_light': '#94A3B8'  # Slate 400
}

FONT_PRIMARY = ("Inter", 10)
FONT_BOLD = ("Inter", 10, "bold")
FONT_TITLE = ("Inter", 18, "bold")

class StyleManager:
    """Manages the application's visual theme using ttk.Style."""
    
    @staticmethod
    def apply_styles(root):
        style = ttk.Style(root)
        
        # Use a modern theme as base if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
            
        # Global Background
        root.configure(bg=PALETTE['bg'])
        
        # --- Frame Styles ---
        style.configure('TFrame', background=PALETTE['bg'])
        style.configure('Card.TFrame', background=PALETTE['card'], 
                        relief='flat', borderwidth=1)
        
        # --- Label Styles ---
        style.configure('TLabel', background=PALETTE['bg'], 
                        foreground=PALETTE['text'], font=FONT_PRIMARY)
        
        style.configure('Header.TLabel', font=FONT_TITLE, 
                        foreground=PALETTE['text'], padding=(0, 5))
        
        style.configure('SubHeader.TLabel', font=("Inter", 11), 
                        foreground=PALETTE['text_light'])
        
        style.configure('CardHeader.TLabel', font=FONT_BOLD, 
                        foreground=PALETTE['text_light'], background=PALETTE['card'])

        # --- Button Styles ---
        style.configure('TButton', font=FONT_BOLD, padding=(15, 8))
        
        # Primary Action Button
        style.configure('Primary.TButton', 
                        background=PALETTE['primary'], 
                        foreground='#FFFFFF')
        style.map('Primary.TButton',
                  background=[('active', PALETTE['primary_dark']), 
                             ('pressed', PALETTE['primary_dark'])])
        
        # Secondary/Ghost Button
        style.configure('Secondary.TButton', 
                        background=PALETTE['card'], 
                        foreground=PALETTE['secondary'])
        
        # --- Notebook Styles ---
        style.configure('TNotebook', background=PALETTE['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', padding=(20, 12), font=FONT_BOLD, 
                        background=PALETTE['border'])
        # Ensure the content area (client) matches the card background
        style.configure('TNotebook.client', background=PALETTE['card'], borderwidth=0)
        style.map('TNotebook.Tab',
                  background=[('selected', PALETTE['card'])],
                  foreground=[('selected', PALETTE['primary'])])

        # --- Treeview Styles ---
        style.configure('Treeview', 
                        font=FONT_PRIMARY, 
                        rowheight=35,
                        background=PALETTE['card'],
                        fieldbackground=PALETTE['card'],
                        borderwidth=0)
        style.configure('Treeview.Heading', 
                        font=FONT_BOLD, 
                        background=PALETTE['bg'],
                        foreground=PALETTE['secondary'],
                        relief='flat',
                        padding=10)
        style.map('Treeview',
                  background=[('selected', PALETTE['primary'])],
                  foreground=[('selected', '#FFFFFF')])

        # --- Entry Styles ---
        style.configure('TEntry', padding=8, relief='flat')

    @staticmethod
    def get_color(name):
        return PALETTE.get(name, '#000000')
