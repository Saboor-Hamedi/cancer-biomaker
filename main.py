import logging
import os
import sys
import threading
import tkinter as tk
import warnings
from datetime import datetime
from tkinter import filedialog, messagebox

import pandas as pd

# Local imports
from ui.components.dashboard import Dashboard
from ui.components.sidebar import Sidebar
from ui.components.tabs import AnalysisTab, DataTab, InputTab

# New modular imports
from controllers.data_controller import DataController
from controllers.model_controller import ModelController
from controllers.visualization_controller import VisualizationController
from handlers.event_handler import EventHandler
from handlers.menu_handler import MenuHandler
from logic.data_manager import DataManager
from logic.model_manager import ModelManager
# Local imports removed: from styles import apply_styles
from ui.display_formatter import DisplayFormatter
from ui.layout_manager import LayoutManager
from ui.styles import StyleManager
from utils.async_runner import AsyncRunner
from utils.error_handler import ErrorHandler
from utils.update_manager import UpdateManager
from views.dialogs import PreprocessingDialog
from views.visualizations import Visualizer
import numpy as np
warnings.filterwarnings('ignore', message='.*use_label_encoder.*')
# Suppress terminal noise from background resource trackers and sklearn feature names
warnings.filterwarnings('ignore', category=UserWarning, module='joblib')
warnings.filterwarnings('ignore', message='.*X has feature names, but SVC was fitted without feature names.*')

# ── Logging: writes to app.log in the script folder ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'app.log'), encoding='utf-8')
    ]
)


class CancerDetectionApp:
    def __init__(self, root):
        self.root = root
        self.version = "1.0.1"
        self.root.title(f"Cancer Detection XAI Dashboard v{self.version}")
        self.root.geometry("1280x850")
        self.root.minsize(1100, 700)
        self.root.configure(bg="#F8FAFC")

        # Apply Global Styles
        StyleManager.apply_styles(self.root)

        # Initialize Core Managers
        self.data_manager = DataManager()
        self.model_manager = ModelManager(os.path.dirname(__file__))

        # Core utilities
        self.async_runner = AsyncRunner(self.root)
        self.error_handler = ErrorHandler(self.root)
        # UI Management (initialized with empty callbacks first)
        self.layout_manager = LayoutManager(self.root, self.model_manager, self.data_manager, {})
        self.update_manager = UpdateManager(self.root, self.layout_manager.update_status, current_version=self.version)

        # Link ErrorHandler to UI for internal notifications (Item #2: "not come out of app")
        self.error_handler.console_callback = self.layout_manager.log_message
        self.error_handler.status_callback = self.layout_manager.update_status
        self.error_handler.narrative_callback = lambda t, l="INFO": self.layout_manager.dashboard.update_narrative(t, l)

        # Controllers
        self.data_controller = DataController(
            self.data_manager,
            self.layout_manager,
            self.error_handler,
            model_manager=self.model_manager
        )

        self.model_controller = ModelController(
            self.model_manager,
            self.data_manager,
            self.layout_manager,
            self.error_handler
        )

        self.visualization_controller = VisualizationController(
            self.model_manager,
            self.data_manager,
            self.layout_manager,
            self.error_handler,
            model_controller=self.model_controller
        )

        self.display_formatter = DisplayFormatter(self.layout_manager)

        # Handlers
        self.menu_handler = MenuHandler(
            self.root,
            self.data_controller,
            self.model_controller,
            self.visualization_controller,
            self.layout_manager
        )

        self.event_handler = EventHandler(
            self.root,
            self.data_controller,
            self.model_controller,
            self.visualization_controller,
            self.layout_manager
        )

        # Connect console to error handler
        self.error_handler.console_callback = self.layout_manager.log_message
        
        # Initial welcome log
        self.layout_manager.log_message("System initialization complete. Monitoring clinical diagnostics.", level="SUCCESS")

        # Legacy Apply Styles removed

        # Define callbacks for LayoutManager
        callbacks = {
            'sample': lambda: self.data_controller.handle_sample(self.layout_manager.sidebar.sample_qty.get()),
            'predict_single': self.event_handler.handle_predict_single,
            'predict_file': self.event_handler.handle_predict_file,
            'predict_silent': lambda: None, # Placeholder for silent updates
            'viz_local': self.visualization_controller.show_local_explanation,
            'viz_radar': self.visualization_controller.show_patient_radar,
            'viz_feat': self.visualization_controller.show_feature_importance,
            'viz_shap': self.visualization_controller.show_shap_summary,
            'viz_dist': self.visualization_controller.show_population_distribution,
            'viz_violin': self.visualization_controller.show_biomarker_violins,
            'viz_robust': self.visualization_controller.show_model_robustness_benchmark,
            'viz_leadership': self.visualization_controller.show_model_leadership_report,
            'viz_pr_thresh': self.visualization_controller.show_pr_threshold,
            'edit_input_value': self.event_handler.handle_tree_double_click,
            'upload': self.data_controller.handle_upload,
            'train_all': self.model_controller.handle_train_models,
            'system_reset': self.model_controller.handle_system_reset,
            'check_updates': lambda: self.update_manager.check_for_updates(silent=False)
        }
        self.layout_manager.callbacks.update(callbacks)

        # Setup Layout
        self.layout_manager.setup_layout()

        # Setup Event Bindings
        self.event_handler.setup_event_bindings()

        # Build Menu Bar
        self.menu_handler.build_menubar()

        # Professor's Requirement: Fresh Start
        # Delete any existing models from previous sessions on startup
        self.model_manager.delete_all_models()

        # Auto-check and train models if missing
        self._check_models_on_startup()

        # Live Update Check (GitHub Releases)
        self.update_manager.check_for_updates(silent=True)

        # Handle proper closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Clean shutdown of the application - deletes models per professor's requirement"""
        try:
            # Inform user
            self.layout_manager.update_status("Cleaning clinical environment...", "orange")
            
            # Delete all model files for a fresh start next time
            self.model_manager.delete_all_models()
            
            # Close all modal windows first
            Visualizer.close_all_modals()
            self.root.destroy()
        except:
            pass
        os._exit(0)  # Force kill all threads and processes

    def _check_models_on_startup(self):
        """Check models on startup and prompt for training."""
        def check_task():
            # Check if models exist (they shouldn't because we delete on start/close)
            success, msg = self.model_manager.check_and_train_models("", self.layout_manager.update_status, force=False)
            
            if success:
                self.root.after(0, lambda: self.layout_manager.refresh_input_features(self.model_manager.feature_names))
                self.root.after(0, lambda: self.layout_manager.update_status("System Ready - Models Verified", "#10B981"))
            else:
                # Prompt user to train
                self.layout_manager.update_status("Action Required: Upload dataset to train AI models", "#EF4444")

        threading.Thread(target=check_task, daemon=True).start()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CancerDetectionApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        # Silent exit on Ctrl+C
        import os
        os._exit(0)
