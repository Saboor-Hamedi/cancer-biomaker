"""
UI Layout Manager - Assembles and manages the main application layout.
"""

import tkinter as tk

from ui.components.dashboard import Dashboard
from ui.components.sidebar import Sidebar
from ui.components.tabs import AnalysisTab, DataTab, InputTab
from logic.model_manager import HAS_XGB


class LayoutManager:
    """Manages the assembly and layout of UI components."""

    def __init__(self, root, model_manager, data_manager, callbacks):
        self.root = root
        self.model_manager = model_manager
        self.data_manager = data_manager
        self.callbacks = callbacks

        # UI Components
        self.sidebar = None
        self.dashboard = None
        self.tab_input = None
        self.tab_data = None
        self.tab_analysis = None

    def setup_layout(self):
        """Set up the main application layout."""
        # Create Sidebar (Right side)
        model_list = ["Random Forest", "Logistic Regression", "SVM"]
        if HAS_XGB:
            model_list.append("XGBoost")

        # Update callbacks with model list
        self.callbacks['models'] = model_list

        self.sidebar = Sidebar(self.root, self.callbacks)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create Dashboard (Main area left)
        self.dashboard = Dashboard(self.root)
        self.dashboard.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate Tabs
        self.tab_input = InputTab(self.dashboard.input_tab, features=self.model_manager.feature_names, data_manager=self.data_manager)
        self.tab_input.pack(fill=tk.BOTH, expand=True)

        self.tab_data = DataTab(self.dashboard.data_tab)
        self.tab_data.pack(fill=tk.BOTH, expand=True)

        self.tab_analysis = AnalysisTab(self.dashboard.analysis_tab)
        self.tab_analysis.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.tab_input.tree.bind("<Double-1>", self.callbacks.get('edit_input_value', lambda e: None))

    def get_components(self):
        """Get references to all UI components."""
        return {
            'sidebar': self.sidebar,
            'dashboard': self.dashboard,
            'notebook': self.dashboard.notebook,
            'tab_input': self.tab_input,
            'tab_data': self.tab_data,
            'tab_analysis': self.tab_analysis
        }

    def refresh_input_features(self, features, first_row=None):
        """Refresh the input features in the input tab."""
        if self.tab_input:
            self.tab_input.refresh_features(features, first_row=first_row)

    def refresh_data_tree(self):
        """Refresh the data display tree."""
        if self.tab_data and self.data_manager.uploaded_df is not None:
            tree = self.tab_data.tree
            df = self.data_manager.uploaded_df

            # Clear existing rows
            tree.delete(*tree.get_children())

            # Rebuild columns
            columns = list(df.columns)
            tree["columns"] = columns

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)

            # Add data
            for _, row in df.iterrows():
                tree.insert("", tk.END, values=list(row))

    def update_data_info(self, rows, cols, samples):
        """Update the data information display."""
        if self.dashboard:
            self.dashboard.update_data_info(rows=rows, cols=cols, samples=samples)

    def update_metrics(self, accuracy, precision, status, triage="Pending", consensus="N/A"):
        """Update the metrics display."""
        if self.dashboard:
            # Map accuracy to confidence and precision to risk
            self.dashboard.update_metrics(
                risk=precision,
                confidence=accuracy,
                insight=status,
                triage=triage,
                consensus=consensus
            )

    def update_status(self, message, color="#64748B"):
        """Update the status bar."""
        if self.dashboard:
            self.dashboard.update_status(message, color)
