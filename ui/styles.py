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
    'danger_dark': '#B91C1C', 
    'bg': '#F8FAFC',         # Slate 50
    'card': '#FFFFFF',       # White
    'border': '#E2E8F0',     # Slate 200
    'text': '#1E293B',       # Slate 800
    'text_light': '#94A3B8', # Slate 400
    'sidebar_bg': '#0F172A', # Slate 900
    'sidebar_hover': '#1E293B' # Slate 800 (used for items, not full background)
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
        
        style.configure('TFrame', background=PALETTE['bg'])
        style.configure('Card.TFrame', background=PALETTE['card'], 
                        relief='flat', borderwidth=0)
        
        # --- Label Styles ---
        style.configure('TLabel', background=PALETTE['bg'], 
                        foreground=PALETTE['text'], font=FONT_PRIMARY)
        
        style.configure('Header.TLabel', font=FONT_TITLE, 
                        foreground=PALETTE['text'], padding=(0, 5))
        
        style.configure('SubHeader.TLabel', font=("Inter", 11), 
                        foreground=PALETTE['text_light'])
        
        style.configure('CardHeader.TLabel', font=FONT_BOLD, 
                        foreground=PALETTE['text_light'], background=PALETTE['card'])

        # --- Base Focus Style Removal ---
        style.configure('.', focuscolor='', highlightthickness=0)
        style.map('.', focuscolor=[('active', ''), ('focus', '')])

        # --- Sidebar Specific Styles ---
        style.configure('Sidebar.TFrame', background=PALETTE['sidebar_bg'])
        style.configure('Sidebar.TLabel', background=PALETTE['sidebar_bg'], 
                        foreground='#F8FAFC', font=FONT_PRIMARY)
        style.configure('SidebarCaption.TLabel', background=PALETTE['sidebar_bg'], 
                        foreground=PALETTE['text_light'], font=("Inter", 8, "bold"))
        
        style.configure('Sidebar.TLabelframe', background=PALETTE['sidebar_bg'], 
                        foreground='#F8FAFC', borderwidth=0)
        style.configure('Sidebar.TLabelframe.Label', background=PALETTE['sidebar_bg'], 
                        foreground=PALETTE['primary'], font=("Inter", 9, "bold"))

        # --- Button Styles ---
        style.configure('TButton', font=FONT_BOLD, padding=(15, 8), borderwidth=0, relief='flat')
        style.map('TButton',
                  focuscolor=[('active', ''), ('focus', '')],
                  highlightcolor=[('active', ''), ('focus', '')])
        
        # Primary Action Button
        style.configure('Primary.TButton', 
                        background=PALETTE['primary'], 
                        foreground='#FFFFFF')
        style.map('Primary.TButton',
                  background=[('active', PALETTE['primary_dark']), 
                             ('pressed', PALETTE['primary_dark'])],
                  foreground=[('active', '#FFFFFF')])
        
        style.configure('Secondary.TButton', 
                        background=PALETTE['card'], 
                        foreground=PALETTE['secondary'])
        
        # Danger/Reset Button
        style.configure('Danger.TButton', 
                        background='#F1F5F9', # Light gray base
                        foreground=PALETTE['danger'])
        style.map('Danger.TButton',
                  background=[('active', PALETTE['danger']), 
                             ('pressed', PALETTE['danger_dark'] if 'danger_dark' in PALETTE else '#B91C1C')],
                  foreground=[('active', '#FFFFFF')])
        
        # --- Modern Premium Tabs ---
        style.configure('TNotebook', background=PALETTE['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                        padding=(25, 12), 
                        font=FONT_BOLD, 
                        background=PALETTE['border'], 
                        foreground=PALETTE['secondary'],
                        borderwidth=0)
        
        # Ensure the content area (client) matches the card background
        style.configure('TNotebook.client', background=PALETTE['card'], borderwidth=0)
        
        style.map('TNotebook.Tab',
                  background=[('selected', PALETTE['primary']), ('!selected', PALETTE['border'])],
                  foreground=[('selected', '#FFFFFF'), ('!selected', PALETTE['secondary'])],
                  padding=[('selected', (25, 12))], # Consistent height to avoid jumping
                  lightcolor=[('selected', PALETTE['primary']), ('!selected', PALETTE['border'])],
                  bordercolor=[('selected', PALETTE['primary']), ('!selected', PALETTE['border'])],
                  focuscolor=[('selected', ''), ('!selected', '')])

        # --- Scrollbar Styling (Unified with Sidebars) ---
        style.configure('Vertical.TScrollbar', 
                        troughcolor=PALETTE['sidebar_bg'], 
                        background=PALETTE['sidebar_hover'], # Using hover as a subtle thumb
                        borderwidth=0, 
                        arrowsize=12)
        style.configure('Horizontal.TScrollbar', 
                        troughcolor=PALETTE['sidebar_bg'], 
                        background=PALETTE['sidebar_hover'],
                        borderwidth=0,
                        arrowsize=12)

        style.configure('Treeview', 
                        font=FONT_PRIMARY, 
                        rowheight=38,
                        background=PALETTE['card'],
                        fieldbackground=PALETTE['card'],
                        borderwidth=0,
                        highlightthickness=0)
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

        # --- Spinbox Styles ---
        # Configure the general TSpinbox style
        style.configure('TSpinbox',
                        fieldbackground=PALETTE['card'],
                        background=PALETTE['card'], # Background of the spinbox itself
                        foreground=PALETTE['text'],
                        insertbackground=PALETTE['text'],
                        selectbackground=PALETTE['primary'],
                        selectforeground='#FFFFFF',
                        bordercolor=PALETTE['border'],
                        lightcolor=PALETTE['border'],
                        darkcolor=PALETTE['border'],
                        arrowsize=12,
                        padding=8,
                        relief='flat')
        # Configure the Spinbox buttons
        style.map('TSpinbox',
                  background=[('active', PALETTE['border']), ('!active', PALETTE['card'])],
                  foreground=[('active', PALETTE['text']), ('!active', PALETTE['text'])])
        style.map('TSpinbox.button',
                  background=[('active', PALETTE['primary']), ('!active', PALETTE['border'])],
                  foreground=[('active', '#FFFFFF'), ('!active', PALETTE['text'])])


    @staticmethod
    def get_color(name):
        return PALETTE.get(name, '#000000')
