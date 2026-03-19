"""
UI Layout Manager - Assembles and manages the main application layout.
"""

import tkinter as tk
import numpy as np

from ui.components.dashboard import Dashboard
from ui.components.sidebar import Sidebar
from ui.components.model_explorer import ModelExplorer
from views.dialogs import PreprocessingDialog, SettingsDialog
from ui.components.tabs import AnalysisTab, DataTab, InputTab, ValidationTab, LeaderboardTab
from ui.components.velocity_tab import VelocityTab
from ui.components.console import ConsoleTab
from logic.model_manager import HAS_XGB


class LayoutManager:
    """Manages the assembly and layout of UI components."""

    def __init__(self, root, model_manager, data_manager, callbacks, settings_manager=None, version="1.0.0"):
        self.root = root
        self.model_manager = model_manager
        self.data_manager = data_manager
        self.settings_manager = settings_manager
        self.callbacks = callbacks
        self.version = version

        # UI Components
        self.sidebar = None
        self.dashboard = None
        self.tab_input = None
        self.tab_data = None
        self.tab_analysis = None
        self.tab_validation = None
        self.tab_leaderboard = None
        self.tab_velocity = None
        self.tab_console = None
        self.model_explorer = None

    def setup_layout(self):
        """Set up the main application layout."""
        # Create Sidebar (Right side)
        model_list = ["Random Forest", "Logistic Regression", "SVM", "MLP"]
        if HAS_XGB:
            model_list.append("XGBoost")
        
        from logic.model_manager import HAS_TORCH
        if HAS_TORCH:
            model_list.append("Graph Neural Network")
        
        # Add Ensemble Mode
        model_list.append("AI Ensemble")

        # Update callbacks
        self.callbacks['models'] = model_list
        self.callbacks['show_settings'] = self.show_settings_modal

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

        self.tab_analysis = AnalysisTab(self.dashboard.analysis_tab, version=self.version)
        self.tab_analysis.pack(fill=tk.BOTH, expand=True)

        self.tab_validation = ValidationTab(self.dashboard.validation_tab)
        self.tab_validation.pack(fill=tk.BOTH, expand=True)

        self.tab_leaderboard = LeaderboardTab(self.dashboard.leaderboard_tab)
        self.tab_leaderboard.pack(fill=tk.BOTH, expand=True)

        self.tab_velocity = VelocityTab(self.dashboard.velocity_tab, self.callbacks)
        self.tab_velocity.pack(fill=tk.BOTH, expand=True)

        self.tab_console = ConsoleTab(self.dashboard.log_tab_frame)
        self.tab_console.pack(fill=tk.BOTH, expand=True)
        
        # Link console back to dashboard for easy logging
        self.dashboard.console = self.tab_console

    def show_settings_modal(self):
        """Launch the modal settings window."""
        SettingsDialog(
            self.root, 
            self.settings_manager, 
            self.callbacks.get('refresh_styles')
        )

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
            'tab_velocity': self.tab_velocity,
            'tab_console': self.tab_console,
            'model_explorer': self.model_explorer
        }

    def refresh_input_features(self, features, first_row=None):
        """Refresh the input features in the input tab."""
        if self.tab_input:
            self.tab_input.refresh_features(features, first_row=first_row)

    def refresh_data_tree(self):
        """Refresh the data display tree - showing all relevant clinical columns."""
        if self.tab_data and self.data_manager.uploaded_df is not None:
            tree = self.tab_data.tree
            df = self.data_manager.uploaded_df
            
            # Use all columns by default, but prioritize ID/Class at start if they exist
            all_cols = list(df.columns)
            
            # Priority: ensure sample_id and results are visible first
            priority = ['sample_id', 'cancer_risk_class', 'prediction', 'risk']
            display_cols = []
            for p in priority:
                match = [c for c in all_cols if p in str(c).lower()]
                if match: display_cols.append(match[0])
            
            # Add remaining columns
            remaining = [c for c in all_cols if c not in display_cols]
            display_cols.extend(remaining)

            # Limit to 30 columns to prevent UI freeze (User can scroll)
            display_cols = display_cols[:30]

            # Clear existing columns and rows
            tree.delete(*tree.get_children())
            
            # Reconfigure columns
            tree["columns"] = display_cols
            tree["show"] = "headings"
            
            for col in display_cols:
                # Clean name for display if it's too long
                clean_name = str(col).replace('_', ' ').title()
                tree.heading(col, text=clean_name, anchor='w')
                
                # Auto-width: wide for feature names, medium for numbers
                if 'id' in str(col).lower():
                    tree.column(col, width=120, anchor='w')
                else:
                    tree.column(col, width=140, anchor='center')

            # Chunker for background insertion
            rows = list(df.iterrows())
            total_rows = len(rows)
            chunk_size = 50

            def _insert_chunk(start_idx):
                end_idx = min(start_idx + chunk_size, total_rows)
                for i in range(start_idx, end_idx):
                    _, row = rows[i]
                    vals = [row[c] for c in display_cols]
                    formatted_vals = []
                    for v in vals:
                        if isinstance(v, (float, np.float64, np.float32)):
                            formatted_vals.append(f"{v:.4f}")
                        else:
                            formatted_vals.append(str(v))
                    tree.insert("", tk.END, values=formatted_vals)
                
                if end_idx < total_rows:
                    self.root.after(10, lambda: _insert_chunk(end_idx))

            # Start chunked insertion
            _insert_chunk(0)

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
        if self.tab_velocity: self.tab_velocity.clear()
        if self.tab_console: self.tab_console.clear()
        if self.model_explorer: self.model_explorer.refresh()
        
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
    
    def refresh_all_tabs_theme(self, theme_name):
        """Broadcast theme signal to all dashboard tabs."""
        tabs = [
            self.tab_input, self.tab_data, self.tab_analysis,
            self.tab_validation, self.tab_leaderboard, self.tab_velocity,
            self.tab_console
        ]
        for t in tabs:
            if t and hasattr(t, 'refresh_theme'):
                t.refresh_theme(theme_name)

    # Alias for convenience and backward compatibility
    log = log_message
