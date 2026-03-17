from tkinter import ttk

def apply_styles():
    style = ttk.Style()
    
    # Premium Modern Theme Palette
    BG_MAIN = '#F8FAFC'      # Very light grey-blue (modern standard)
    ACCENT_DARK = '#1E293B'  # Slate-900 for sidebar/headers
    MEDIC_BRAND = '#3B82F6'  # Modern Blue (Tailwind style)
    TEXT_MAIN = '#334155'    # Slate-700
    CARD_BG = '#FFFFFF'
    BORDER_LIGHT = '#E2E8F0'
    
    # Base widget configurations
    style.configure('TButton', font=('Inter', 9), padding=6)
    style.configure('TLabel', font=('Inter', 10), background=BG_MAIN, foreground=TEXT_MAIN)
    style.configure('TFrame', background=BG_MAIN)
    
    # Card & Sidebar styles
    style.configure('Card.TFrame', background=CARD_BG, relief='flat', borderwidth=0)
    style.configure('Sidebar.TFrame', background=ACCENT_DARK, relief='flat')
    style.configure('Sidebar.TLabel', background=ACCENT_DARK, foreground='white', font=('Inter', 12, 'bold'))
    style.configure('SidebarCaption.TLabel', background=ACCENT_DARK, foreground='#94A3B8', font=('Inter', 8, 'bold'))
    
    # Labelframe styling for Sidebar
    style.configure('Sidebar.TLabelframe', background=ACCENT_DARK, foreground='#CBD5E1', bordercolor='#334155')
    style.configure('Sidebar.TLabelframe.Label', background=ACCENT_DARK, foreground='#64748B', font=('Inter', 8, 'bold'))
    
    # Improved Sidebar Button Style
    style.configure('Sidebar.TButton', font=('Inter', 9), padding=6)
    
    # Notebook (Tabs) customization
    style.configure("TNotebook", background=BG_MAIN, borderwidth=0, tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab", 
                    padding=[20, 10], 
                    font=('Inter', 9, 'bold'), 
                    background=BORDER_LIGHT,
                    borderwidth=0,
                    focuscolor=CARD_BG)
    
    # FIXED TAB STYLING: Black text on white/selected background
    style.map("TNotebook.Tab", 
              background=[("selected", CARD_BG), ("active", "#F1F5F9")], 
              foreground=[("selected", "#0F172A"), ("!selected", "#64748B")],
              expand=[("selected", [1, 1, 1, 0])])
    
    # REMOVE DOTTED BORDER on tabs
    style.layout("TNotebook.Tab", [
        ('Notebook.tab', {
            'sticky': 'nswe',
            'children': [
                ('Notebook.padding', {
                    'side': 'top',
                    'sticky': 'nswe',
                    'children': [
                        ('Notebook.label', {'side': 'top', 'sticky': ''})
                    ]
                })
            ]
        })
    ])

    # Treeview customization
    style.configure("Treeview", 
                    font=('Inter', 9), 
                    rowheight=30, 
                    background=CARD_BG,
                    fieldbackground=CARD_BG,
                    borderwidth=0)
    style.configure("Treeview.Heading", 
                    font=('Inter', 9, 'bold'), 
                    background="#F1F5F9", 
                    foreground=TEXT_MAIN,
                    relief='flat')
    style.map("Treeview", background=[('selected', '#1e202e')], foreground=[('selected', '#FFFFFF')])

    # Custom Header Style
    style.configure('Header.TLabel', font=('Inter', 16, 'bold'), background=CARD_BG, foreground=ACCENT_DARK)
    style.configure('SubHeader.TLabel', font=('Inter', 9), background=CARD_BG, foreground="#94A3B8")
