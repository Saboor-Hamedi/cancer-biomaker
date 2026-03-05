from tkinter import ttk

def apply_styles():
    style = ttk.Style()
    
    # Premium Medic-Blue Theme Palette
    BG_MAIN = '#f4f7f9'
    ACCENT_BLUE = '#2c3e50'
    MEDIC_CYAN = '#3498db'
    TEXT_MAIN = '#2c3e50'
    CARD_BG = '#ffffff'
    
    style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8)
    style.configure('TLabel', font=('Segoe UI', 10), background=BG_MAIN, foreground=TEXT_MAIN)
    style.configure('TFrame', background=BG_MAIN)
    
    # Card & Widget styles
    style.configure('Card.TFrame', background=CARD_BG, relief='flat', borderwidth=0)
    style.configure('Sidebar.TFrame', background=ACCENT_BLUE, relief='flat')
    style.configure('Sidebar.TLabel', background=ACCENT_BLUE, foreground='white', font=('Segoe UI', 12, 'bold'))
    
    # Notebook customization
    style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
    style.configure("TNotebook.Tab", padding=[15, 8], font=('Segoe UI', 10, 'bold'))
    style.map("TNotebook.Tab", 
              background=[("selected", MEDIC_CYAN)], 
              foreground=[("selected", "white")])
    
    # Treeview customization
    style.configure("Treeview", font=('Segoe UI', 10), rowheight=25)
    style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
