from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

class Styles:
    """Professional Clinical Style System for PySide6 (Qt6)."""
    
    PALETTES = {
        'pure_dark': {
            'bg_main': "#09090B",       # Zinc-950
            'bg_sidebar': "#111114",
            'accent': "#3B82F6",        # Blue-500
            'accent_glow': "rgba(59, 130, 246, 0.15)",
            'text_main': "#FAFAFA",
            'text_dim': "#A1A1AA",
            'card_bg': "#18181B",       # Zinc-900
            'border': "#27272A",
            'success': "#10B981",
            'danger': "#EF4444",
            'warning': "#F59E0B"
        },
        'pure_light': {
            'bg_main': "#F8FAFC",
            'bg_sidebar': "#FFFFFF",
            'accent': "#2563EB",
            'accent_glow': "rgba(37, 99, 235, 0.1)",
            'text_main': "#0F172A",
            'text_dim': "#64748B",
            'card_bg': "#FFFFFF",
            'border': "#E2E8F0",
            'success': "#059669",
            'danger': "#DC2626",
            'warning': "#D97706"
        }
    }

    @staticmethod
    def get_qss(theme='pure_dark'):
        p = Styles.PALETTES.get(theme, Styles.PALETTES['pure_dark'])
        
        return f"""
        /* ── Global Clinical Theme: {theme} ── */
        
        QMainWindow, QWidget {{
            background-color: {p['bg_main']};
            color: {p['text_main']};
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 13px;
        }}

        /* ── Sidebar & Navigation ── */
        QFrame#Sidebar {{
            background-color: {p['bg_sidebar']};
            border-right: 1px solid {p['border']};
        }}

        QLabel#SidebarTitle {{
            color: {p['accent']};
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }}

        /* ── Cards & Containers ── */
        QFrame#Card {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 12px;
        }}
        
        QFrame#RiskCard_DANGER {{
            background-color: {p['card_bg']};
            border: 1px solid {p['danger']};
            border-radius: 12px;
        }}

        /* ── Buttons (Premium Aesthetic) ── */
        QPushButton {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 8px 16px;
            color: {p['text_main']};
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {p['border']};
            border-color: {p['text_dim']};
        }}

        QPushButton#PrimaryBtn {{
            background-color: {p['accent']};
            color: white;
            border: none;
        }}

        QPushButton#PrimaryBtn:hover {{
            background-color: #2563EB;
        }}

        /* ── Inputs ── */
        QLineEdit, QSpinBox, QComboBox {{
            background-color: {p['bg_main']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 6px;
            color: {p['text_main']};
        }}

        QLineEdit:focus {{
            border: 1px solid {p['accent']};
        }}

        /* ── Tabs (Notebook) ── */
        QTabWidget::pane {{
            border: none;
            background: {p['bg_main']};
        }}

        QTabBar::tab {{
            background: transparent;
            padding: 10px 20px;
            color: {p['text_dim']};
            border-bottom: 2px solid transparent;
        }}

        QTabBar::tab:selected {{
            color: {p['accent']};
            border-bottom: 2px solid {p['accent']};
            font-weight: bold;
        }}

        /* ── Tables (Treeview Upgrade) ── */
        QTableWidget, QTreeView {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            gridline-color: {p['border']};
            outline: none;
        }}

        QHeaderView::section {{
            background-color: {p['bg_sidebar']};
            color: {p['text_dim']};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {p['border']};
            font-weight: bold;
            text-transform: uppercase;
        }}

        QTableWidget::item:selected {{
            background-color: {p['accent_glow']};
            color: {p['accent']};
        }}
        
        /* ── Industrial Menus ── */
        QMenuBar {{
            background-color: {p['bg_sidebar']};
            color: {p['text_dim']};
            border-bottom: 1px solid {p['border']};
            padding: 2px 10px;
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {p['bg_main']};
            color: {p['accent']};
        }}
        QMenu {{
            background-color: {p['bg_sidebar']};
            color: {p['text_main']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 5px 0;
        }}
        QMenu::item {{
            padding: 8px 25px 8px 35px;
        }}
        QMenu::item:selected {{
            background-color: {p['accent']};
            color: white;
        }}
        QMenu::separator {{
            height: 1px;
            background: {p['border']};
            margin: 5px 15px;
        }}
        
        /* ── Progress & Status ── */
        QProgressBar {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 4px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {p['accent']};
            border-radius: 3px;
        }}
        """
