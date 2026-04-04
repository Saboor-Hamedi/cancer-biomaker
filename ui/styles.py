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
            border-radius: 0px;
        }}
        
        QFrame#RiskCard_DANGER {{
            background-color: {p['card_bg']};
            border: 1px solid {p['danger']};
            border-radius: 0px;
        }}

        /* ── Buttons (Premium Aesthetic) ── */
        QPushButton {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 0px;
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
            border-radius: 0px;
            padding: 6px;
            color: {p['text_main']};
        }}

        QLineEdit:focus {{
            border: 1px solid {p['accent']};
        }}

        /* ── Tabs ── */
        QTabWidget {{
            border: none;
        }}

        QTabWidget::pane {{
            border: none;
            background-color: {p['bg_main']};
        }}

        QTabBar {{
            background-color: {p['bg_sidebar']};
            border-bottom: 2px solid {p['border']};
        }}

        QTabBar::tab {{
            background: transparent;
            color: {p['text_dim']};
            padding: 12px 24px;
            margin-right: 0px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            border: none;
            border-bottom: 3px solid transparent;
            min-width: 120px;
        }}

        QTabBar::tab:hover {{
            color: {p['text_main']};
            background-color: {p['bg_main']};
        }}

        QTabBar::tab:selected {{
            color: {p['accent']};
            background-color: {p['bg_main']};
            border-bottom: 3px solid {p['accent']};
            font-weight: 900;
        }}

        QTabBar::tab:first {{
            margin-left: 8px;
        }}

        QWidget#MainTabs > QWidget {{
            background-color: {p['bg_main']};
        }}

        /* ── Tables (Treeview Upgrade) ── */
        QTableWidget, QTreeView {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 0px;
            gridline-color: {p['border']};
            outline: none;
            color: {p['text_main']};
        }}

        QTableWidget::item {{
            color: {p['text_main']};
            border: none;
        }}

        QTableWidget::item:alternate {{
            background-color: {p['bg_main']};
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

        /* ── List Widgets (Model List, etc.) ── */
        QListWidget {{
            background-color: transparent;
            border: none;
            color: {p['text_dim']};
            font-size: 12px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 4px 6px;
            border-radius: 0px;
            border: none;
        }}
        QListWidget::item:selected {{
            background-color: {p['accent_glow']};
            color: {p['accent']};
        }}

        /* ── Status HUD Card ── */
        QFrame#StatusHUD {{
            background-color: {p['card_bg']};
            border: 1px solid {p['border']};
            border-radius: 0px;
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
            border-radius: 0px;
        }}
        QMenuBar::item:selected {{
            background-color: {p['bg_main']};
            color: {p['accent']};
        }}
        QMenu {{
            background-color: {p['bg_sidebar']};
            color: {p['text_main']};
            border: 1px solid {p['border']};
            border-radius: 0px;
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
            border-radius: 0px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {p['accent']};
            border-radius: 0px;
        }}
        """
