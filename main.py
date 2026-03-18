import logging
import os
import sys
import threading
import tkinter as tk
import pandas as pd
import numpy as np
import warnings
import ctypes
from PIL import Image, ImageTk
from datetime import datetime
from tkinter import filedialog, messagebox

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
from logic.velocity_manager import VelocityManager
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

# ── Persistent Path Management ────────────────────────────────────────────────
def get_resource_path():
    """Identify the directory for static assets (icons, etc)."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller Bundle
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_user_data_path():
    """Identify the writable directory for logs, models, and sessions."""
    if os.name == 'nt':
        # Windows: %LOCALAPPDATA%/CancerDetectionDashboard
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    else:
        # Linux/Mac: ~/.config/CancerDetectionDashboard
        base = os.path.expanduser('~/.config')
        
    path = os.path.join(base, "CancerDetectionDashboard")
    if not os.path.exists(path):
        try: os.makedirs(path)
        except: pass
    return path

STATIC_HOME = get_resource_path()
USER_DATA_HOME = get_user_data_path()

# Ensure STATIC_HOME is in sys.path for robust local imports
if STATIC_HOME not in sys.path:
    sys.path.insert(0, STATIC_HOME)

# ── Logging: writes to USER_DATA_HOME ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(USER_DATA_HOME, 'app.log'), encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # Also log to console for debugging
    ]
)

# ── Global Metadata ──────────────────────────────────────────────────────────
# Change the version here to reflect across the entire application interface.
VERSION = "1.0.1"

# ── Global Crash Protection ──────────────────────────────────────────────────
def setup_crash_protection(root, error_handler):
    """
    Hook into sys.excepthook and Tkinter callback exceptions 
    to prevent the 'vanishing app' syndrome in production.
    """
    import traceback
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error("Uncaught Clinical Exception:\n%s", error_msg)
        
        # Try to use the modern error handler if available
        try:
            if error_handler:
                error_handler.log_and_notify("Critical System Error", exc_value, show_dialog=True)
            else:
                messagebox.showerror("Clinical Protection Error", 
                                     f"An unexpected error occurred:\n{str(exc_value)}\n\nPlease check app.log for details.")
        except:
            # Absolute fallback if even the error handler fails (e.g. within TK loop)
            messagebox.showerror("Fatal Recovery Error", f"A fatal error occurred: {str(exc_value)}")

    # Standard python exception hook
    sys.excepthook = handle_exception
    
    # Tkinter specific exception hook (for button callbacks, etc.)
    if root:
        root.report_callback_exception = handle_exception


class CancerDetectionApp:
    def __init__(self, root):
        self.root = root
        self.version = VERSION
        self.root.title(f"Cancer Detection XAI Dashboard v{self.version}")
        self.root.geometry("1280x850")
        self.root.minsize(1100, 700)
        self.root.configure(bg="#F8FAFC")
        
        # Set Window Icon
        self._setup_window_icon()

        # Apply Global Styles
        StyleManager.apply_styles(self.root)

        # Initialize Core Managers
        self.data_manager = DataManager(user_data_path=USER_DATA_HOME)
        self.model_manager = ModelManager(USER_DATA_HOME)
        self.velocity_manager = VelocityManager()

        # Core utilities
        self.async_runner = AsyncRunner(self.root)
        self.error_handler = ErrorHandler(self.root)
        
        # Activate Crash Protection
        setup_crash_protection(self.root, self.error_handler)
        # UI Management (initialized with empty callbacks first)
        self.layout_manager = LayoutManager(self.root, self.model_manager, self.data_manager, {}, version=self.version)
        self.update_manager = UpdateManager(self.root, self.layout_manager.update_status, current_version=self.version, user_data_path=USER_DATA_HOME)

        # Link ErrorHandler to UI for internal notifications (Item #2: "not come out of app")
        self.error_handler.console_callback = self.layout_manager.log_message
        self.error_handler.status_callback = self.layout_manager.update_status
        self.error_handler.narrative_callback = lambda t, l="INFO": self.layout_manager.dashboard.update_narrative(t, l)

        # Controllers
        self.data_controller = DataController(
            self.data_manager,
            self.layout_manager,
            self.error_handler,
            model_manager=self.model_manager,
            velocity_manager=self.velocity_manager,
            version=self.version,
            async_runner=self.async_runner
        )

        self.model_controller = ModelController(
            self.model_manager,
            self.data_manager,
            self.layout_manager,
            self.error_handler,
            velocity_manager=self.velocity_manager
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
            'show_counterfactual': self.visualization_controller.show_counterfactual_analysis,
            'show_biomarker_network': self.visualization_controller.show_biomarker_network,
            'check_updates': lambda: self.update_manager.check_for_updates(silent=False)
        }
        self.layout_manager.callbacks.update(callbacks)

        # Setup Layout
        self.layout_manager.setup_layout()

        # Setup Event Bindings
        self.event_handler.setup_event_bindings()

        # Build Menu Bar
        self.menu_handler.build_menubar()

        # Auto-check and train models if missing
        # NOTE: Models are preserved between sessions and only cleared on application close.
        self._check_models_on_startup()

        # Live Update Check (GitHub Releases)
        self.update_manager.check_for_updates(silent=True)

        # Handle proper closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Clean shutdown of the application - deletes models per professor's requirement,
        unless PRESERVE_MODELS environment variable is set for building purposes."""
        try:
            self.layout_manager.update_status("Saving session & cleaning environment...", "orange")
            # Save the data path so Analytics works on next launch
            self.data_manager.save_session()
            
            # Prof's requirement: Models must be deleted on close
            # But we allow an escape hatch for the dev to build the EXE with models included
            if os.environ.get('PRESERVE_MODELS', '').lower() != 'true':
                self.model_manager.delete_all_models()
                print("Models deleted per policy.")
            else:
                print("PRESERVE_MODELS=true: Keeping models for build.")

            Visualizer.close_all_modals()
            self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            os._exit(0)

    def _setup_window_icon(self):
        """Setup the window and taskbar icon."""
        try:
            # Fix taskbar icon on Windows
            if sys.platform == "win32":
                myappid = f'clinical.xai.dashboard.{self.version}'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

            icon_path = os.path.join(STATIC_HOME, "logo.png")
            if os.path.exists(icon_path):
                # Using PIL for better scaling
                img = Image.open(icon_path)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.icon_photo)
        except Exception as e:
            print(f"Warning: Could not load window icon: {e}")

    def _check_models_on_startup(self):
        """Check models on startup. If models exist, load features. If not, prompt user to upload data."""
        def check_task():
            success, msg = self.model_manager.check_and_train_models("", self.layout_manager.update_status, force=False)
            
            if success:
                # Models exist on disk — restore session & load feature names
                self.data_manager.restore_session()
                self.data_controller.data_path = self.data_manager.data_path
                self.root.after(0, lambda: self.layout_manager.refresh_input_features(self.model_manager.feature_names))
                self.root.after(0, lambda: self.layout_manager.update_status("System Ready — Models Loaded", "#10B981"))
                self.root.after(0, lambda: self.error_handler.notify("Clinical models loaded and ready.", type='success'))
            else:
                # No models found — inform user of the required workflow
                self.root.after(0, lambda: self.layout_manager.update_status(
                    "Welcome! Upload a dataset via the sidebar to train the AI models.", "#3B82F6"
                ))
                self.root.after(0, lambda: self.error_handler.notify(
                    "No trained models found. Upload your Excel dataset and click Train Models to begin.", type='info'
                ))

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
