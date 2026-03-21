from tkinter import ttk

class StyleManager:
    """Manages global application styling, including themes and font scaling."""
    
    # Global Pure Themes
    THEMES = {
        'pure_dark': {
            'bg_main': '#000000',      # Absolute Black
            'accent_dark': '#000000',   # No layering separation
            'medic_brand': '#3B82F6',   # Subtle blue for active states
            'text_main': '#FFFFFF',     # Absolute White
            'text_muted': '#A1A1AA',    # Zinc-400
            'card_bg': '#000000',
            'border_light': '#27272A'    # Zinc-800 for borders
        },
        'pure_light': {
            'bg_main': '#FFFFFF',      # Absolute White
            'accent_dark': '#FFFFFF',   # No layering separation
            'medic_brand': '#2563EB',   # Blue-600
            'text_main': '#000000',     # Absolute Black
            'text_muted': '#52525B',    # Zinc-600
            'card_bg': '#FFFFFF',
            'border_light': '#E4E4E7'    # Zinc-200
        }
    }

    @classmethod
    def apply_styles(cls, root, settings=None):
        """Apply global CSS-like styles to the application."""
        style = ttk.Style(root)
        
        # Use a cross-platform theme as base to ensure colors work on Windows
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        # Determine settings
        theme_name = settings.get('theme', 'pure_dark') if settings else 'pure_dark'
        scale = settings.get('font_scale', 1.0) if settings else 1.0
        family = settings.get('font_family', 'Inter') if settings else 'Inter'
        is_dark = theme_name == 'pure_dark'
        
        palette = cls.THEMES.get(theme_name, cls.THEMES['pure_dark'])
        
        # Font definitions with SCALING LIMITS (as per user request: max 18px)
        # We cap the scaled size to ensure labels don't overflow containers
        f_small = (family, min(int(8 * scale), 14))
        f_normal = (family, min(int(9 * scale), 16))
        f_medium = (family, min(int(10 * scale), 17), 'bold')
        f_large = (family, min(int(12 * scale), 18), 'bold')
        f_header = (family, min(int(18 * scale), 20), 'bold')
        
        # Base widget configurations - Focus elimination
        # Pure Resilience: Set fixed wraplength to ensure text wraps BEFORE hitting container edges
        wrap_l = 220 
        style.configure('.', font=f_normal, background=palette['bg_main'], foreground=palette['text_main'], 
                        borderwidth=0, relief='flat', focuscolor='', highlightthickness=0)
        
        style.configure('TFrame', background=palette['bg_main'])
        style.configure('TLabel', font=f_normal, background=palette['bg_main'], foreground=palette['text_main'], 
                        wraplength=wrap_l)
        
        # Button Styles - Fixed mapping for hover
        style.configure('TButton', font=f_medium, padding=6, background=palette['border_light'], 
                        foreground=palette['text_main'], borderwidth=0, wraplength=wrap_l)
        style.map('TButton', 
                  background=[('pressed', palette['medic_brand']), ('active', palette['medic_brand']), ('!disabled', palette['border_light'])],
                  foreground=[('active', 'white')])

        # Primary Button mapping fix
        style.configure('Primary.TButton', background=palette['medic_brand'], foreground='white', font=f_medium, borderwidth=0)
        style.map('Primary.TButton', 
                  background=[('pressed', '#1D4ED8'), ('active', '#1E40AF'), ('!disabled', palette['medic_brand'])],
                  foreground=[('active', 'white')])

        # Danger Button mapping fix
        style.configure('Danger.TButton', background='#EF4444', foreground='white', font=f_medium, borderwidth=0)
        style.map('Danger.TButton', 
                  background=[('pressed', '#991B1B'), ('active', '#B91C1C'), ('!disabled', '#EF4444')],
                  foreground=[('active', 'white')])
        
        # Card & Sidebar styles
        style.configure('Card.TFrame', background=palette['card_bg'], relief='flat', borderwidth=0)
        style.configure('Card.TLabel', background=palette['card_bg'], foreground=palette['text_main'], font=f_normal)
        
        # Fix Sidebar Visibility in Light Mode
        style.configure('Sidebar.TFrame', background=palette['accent_dark'], relief='flat', borderwidth=0)
        style.configure('Sidebar.TLabel', background=palette['accent_dark'], foreground=palette['text_main'], font=f_large)
        style.configure('SidebarCaption.TLabel', background=palette['accent_dark'], foreground=palette['text_muted'], font=f_small)
        
        # Labelframe styling 
        style.configure('Sidebar.TLabelframe', background=palette['accent_dark'], foreground=palette['text_muted'], bordercolor=palette['border_light'], borderwidth=0)
        style.configure('Sidebar.TLabelframe.Label', background=palette['accent_dark'], foreground=palette['text_muted'], font=f_small)
        
        # Notebook (Tabs) customization - Premium padding for height
        style.configure("TNotebook", background=palette['bg_main'], borderwidth=0, tabmargins=[0, 0, 0, 0], highlightthickness=0)
        style.configure("TNotebook.Tab", padding=[25, 12], font=f_medium, background=palette['border_light'], borderwidth=0, focuscolor='')
        
        # Tab Mapping - Fixed background/foreground persistence
        # Active tab must show medic_brand text in light mode for clarity
        sel_bg = palette['card_bg']
        sel_fg = palette['medic_brand'] if not is_dark else 'white'
        
        style.map("TNotebook.Tab", 
                  background=[("selected", sel_bg), ("active", palette['border_light']), ("!selected", palette['border_light'])], 
                  foreground=[("selected", sel_fg), ("active", palette['text_main']), ("!selected", palette['text_muted'])])
        
        # Treeview customization - Minimal layering
        style.configure("Treeview", 
                        font=f_normal, 
                        rowheight=int(34 * (1.0 + (scale-1.0)*0.4)),
                        background=palette['card_bg'],
                        fieldbackground=palette['card_bg'],
                        foreground=palette['text_main'],
                        borderwidth=0,
                        highlightthickness=0)
        
        # Ensure headings and selected rows are high-contrast
        style.configure("Treeview.Heading", font=f_medium, background=palette['border_light'], foreground=palette['text_main'], relief='flat', borderwidth=0)
        style.map("Treeview", 
                  background=[('selected', palette['medic_brand']), ('!disabled', palette['card_bg'])], 
                  foreground=[('selected', 'white'), ('!disabled', palette['text_main'])])

        # Custom Header Style
        style.configure('Header.TLabel', font=f_header, background=palette['card_bg'], foreground=palette['text_main'])
        style.configure('SubHeader.TLabel', font=f_normal, background=palette['card_bg'], foreground=palette['text_muted'])

        # Root background
        root.configure(bg=palette['bg_main'])

        # Global Menu Styling - Standardize to 12px for both Menu bar and dropdown Cascades
        root.option_add('*Menu.font', (family, 12))
        root.option_add('*Menubutton.font', (family, 12))

        # Ensure Combobox dropdown list matches the 12px requirement
        root.option_add('*TCombobox*Listbox.font', (family, 12))
        style.configure('TCombobox', font=(family, 12))

    @classmethod
    def get_palette(cls, theme_name='pure_dark'):
        return cls.THEMES.get(theme_name, cls.THEMES['pure_dark'])
