"""
UI Layout Manager - Assembles and manages the main application layout.
"""

import tkinter as tk

from ui.components.dashboard import Dashboard
from ui.components.sidebar import Sidebar
from ui.components.model_explorer import ModelExplorer
from ui.components.tabs import AnalysisTab, DataTab, InputTab, ValidationTab, LeaderboardTab
from ui.components.console import ConsoleTab
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
        self.tab_validation = None
        self.tab_leaderboard = None
        self.tab_console = None
        self.model_explorer = None

    def setup_layout(self):
        """Set up the main application layout."""
        # Create Sidebar (Right side)
        model_list = ["Random Forest", "Logistic Regression", "SVM", "MLP", "GNN"]
        if HAS_XGB:
            model_list.append("XGBoost")
        
        # Add Ensemble Mode
        model_list.append("AI Ensemble")

        # Update callbacks with model list
        self.callbacks['models'] = model_list

        self.sidebar = Sidebar(self.root, self.callbacks)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Create Model Explorer (Forensic view on the Right)
        self.model_explorer = ModelExplorer(self.root, self.model_manager.script_dir, self.callbacks)
        self.model_explorer.pack(side=tk.RIGHT, fill=tk.Y)

        # Create Dashboard (Main area middle)
        self.dashboard = Dashboard(self.root)
        self.dashboard.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate Tabs
        self.tab_input = InputTab(self.dashboard.input_tab, features=self.model_manager.feature_names, data_manager=self.data_manager)
        self.tab_input.pack(fill=tk.BOTH, expand=True)

        self.tab_data = DataTab(self.dashboard.data_tab)
        self.tab_data.pack(fill=tk.BOTH, expand=True)

        self.tab_analysis = AnalysisTab(self.dashboard.analysis_tab)
        self.tab_analysis.pack(fill=tk.BOTH, expand=True)

        self.tab_validation = ValidationTab(self.dashboard.validation_tab)
        self.tab_validation.pack(fill=tk.BOTH, expand=True)

        self.tab_leaderboard = LeaderboardTab(self.dashboard.leaderboard_tab)
        self.tab_leaderboard.pack(fill=tk.BOTH, expand=True)

        self.tab_console = ConsoleTab(self.dashboard.log_tab_frame)
        self.tab_console.pack(fill=tk.BOTH, expand=True)
        
        # Link console back to dashboard for easy logging
        self.dashboard.console = self.tab_console

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
            'tab_validation': self.tab_validation,
            'tab_leaderboard': self.tab_leaderboard,
            'tab_console': self.tab_console,
            'model_explorer': self.model_explorer
        }

    def refresh_input_features(self, features, first_row=None):
        """Refresh the input features in the input tab."""
        if self.tab_input:
            self.tab_input.refresh_features(features, first_row=first_row)

    def refresh_data_tree(self):
        """Refresh the data display tree - showing only the biological biomarker peaks."""
        if self.tab_data and self.data_manager.uploaded_df is not None:
            tree = self.tab_data.tree
            df = self.data_manager.uploaded_df
            
            # Identify the biomarker peaks (features the model actually uses)
            # We filter for high-impact diagnostic columns to avoid 'Data Crowding' (Item #5)
            important_patterns = ['peak', 'concentration', 'sample_id', 'cancer_risk_class']
            display_cols = [str(c) for c in df.columns if any(p in str(c).lower() for p in important_patterns)]
            
            # If we still have too many (e.g. 62), take only the first 15 diagnostic markers
            if len(display_cols) > 15:
                # Keep ID and Class, and take top 13 peaks
                metadata = [str(c) for c in display_cols if 'id' in str(c).lower() or 'class' in str(c).lower()]
                others = [str(c) for c in display_cols if c not in metadata]
                display_cols = list(metadata) + list(others[:13])

            if not display_cols:
                # Fallback if no specific biomarker columns found: show first 10
                display_cols = list(df.columns[:10])

            # Clear existing columns and rows
            tree.delete(*tree.get_children())
            tree["columns"] = list(display_cols)
            tree["show"] = "headings" # Hide the empty first column

            for col in display_cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor=tk.CENTER)

            # Add data for the filtered columns
            for _, row in df[display_cols].iterrows():
                tree.insert("", tk.END, values=list(row))

    def update_data_info(self, rows, cols, samples):
        """Update the data information display."""
        if self.dashboard:
            self.dashboard.update_data_info(rows=rows, cols=cols, samples=samples)

    def clear_all_data(self):
        """Wipes all diagnostic data across all dashboard tabs (User Request)."""
        if self.tab_input: self.tab_input.clear_table()
        if self.tab_data: self.tab_data.clear()
        if self.tab_analysis: self.tab_analysis.clear()
        if self.tab_validation: self.tab_validation.clear()
        if self.tab_leaderboard: self.tab_leaderboard.clear()
        
        # Reset Metric Cards
        self.update_metrics(risk=0.0, confidence=0.0, triage="Pending", consensus="N/A")
        self.update_data_info(rows=0, cols=0, samples=0)

    def update_metrics(self, confidence=0.0, risk=0.0, triage="Pending", consensus="N/A", **kwargs):
        """Update the metrics display using clinical terminology."""
        if self.dashboard:
            self.dashboard.update_metrics(
                risk=risk,
                confidence=confidence,
                triage=triage,
                consensus=consensus
            )

    def update_status(self, message, color="#64748B"):
        """Update the status bar."""
        if self.dashboard:
            self.dashboard.update_status(message, color)

    def log_message(self, message, level="INFO"):
        """Log a message to the persistent system console."""
        if self.dashboard:
            self.dashboard.log_message(message, level)
    
    # Alias for convenience and backward compatibility
    log = log_message
