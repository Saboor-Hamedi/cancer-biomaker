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
from logic.settings_manager import SettingsManager
from ui.display_formatter import DisplayFormatter
from ui.layout_manager import LayoutManager
from ui.styles import StyleManager
from utils.async_runner import AsyncRunner
from utils.error_handler import ErrorHandler
from utils.update_manager import UpdateManager
from views.dialogs import PreprocessingDialog
from views.visualizations import Visualizer

# Suppress terminal noise
warnings.filterwarnings('ignore', message='.*use_label_encoder.*')
warnings.filterwarnings('ignore', category=UserWarning, module='joblib')
warnings.filterwarnings('ignore', message='.*X has feature names, but SVC was fitted without feature names.*')
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

VERSION = "1.0.1"

def get_resource_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_user_data_path():
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA', os.path.expandvars('%USERPROFILE%'))
    else:
        base = os.path.expanduser('~/.config')
    path = os.path.join(base, "CancerDetectionDashboard")
    os.makedirs(path, exist_ok=True)
    return path

STATIC_HOME = get_resource_path()
USER_DATA_HOME = get_user_data_path()

if STATIC_HOME not in sys.path:
    sys.path.insert(0, STATIC_HOME)

def setup_crash_protection(root, error_handler):
    import traceback
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error("Uncaught Clinical Exception:\n%s", error_msg)
        try:
            if error_handler:
                error_handler.log_and_notify("Critical System Error", exc_value, show_dialog=True)
            else:
                messagebox.showerror("Clinical Protection Error", f"An unexpected error occurred:\n{str(exc_value)}")
        except:
            messagebox.showerror("Fatal Recovery Error", f"A fatal error occurred: {str(exc_value)}")
    sys.excepthook = handle_exception
    if root: root.report_callback_exception = handle_exception

class CancerDetectionApp:
    def __init__(self, root):
        self.root = root
        self.version = VERSION
        self.root.title(f"Cancer Detection XAI Dashboard v{self.version}")
        self.root.geometry("1280x850")
        self.root.minsize(1100, 700)
        self.root.configure(bg="#000000")
        
        self._setup_window_icon()
        self.settings_manager = SettingsManager(user_data_path=USER_DATA_HOME)
        StyleManager.apply_styles(self.root, self.settings_manager.settings)

        self.data_manager = DataManager(user_data_path=USER_DATA_HOME)
        self.model_manager = ModelManager(USER_DATA_HOME)
        self.velocity_manager = VelocityManager()
        self.async_runner = AsyncRunner(self.root)
        self.error_handler = ErrorHandler(self.root)
        
        setup_crash_protection(self.root, self.error_handler)
        self.layout_manager = LayoutManager(self.root, self.model_manager, self.data_manager, {}, settings_manager=self.settings_manager, version=self.version)
        self.update_manager = UpdateManager(self.root, self.layout_manager.update_status, current_version=self.version, user_data_path=USER_DATA_HOME)

        self.error_handler.console_callback = self.layout_manager.log_message
        self.error_handler.status_callback = self.layout_manager.update_status
        self.error_handler.narrative_callback = lambda t, l="INFO": self.layout_manager.dashboard.update_narrative(t, l)

        self.data_controller = DataController(self.data_manager, self.layout_manager, self.error_handler, model_manager=self.model_manager, velocity_manager=self.velocity_manager, version=self.version, async_runner=self.async_runner)
        self.model_controller = ModelController(self.model_manager, self.data_manager, self.layout_manager, self.error_handler, velocity_manager=self.velocity_manager, async_runner=self.async_runner)
        self.visualization_controller = VisualizationController(self.model_manager, self.data_manager, self.layout_manager, self.error_handler, model_controller=self.model_controller)
        self.display_formatter = DisplayFormatter(self.layout_manager)

        self.menu_handler = MenuHandler(self.root, self.data_controller, self.model_controller, self.visualization_controller, self.layout_manager)
        self.event_handler = EventHandler(self.root, self.data_controller, self.model_controller, self.visualization_controller, self.layout_manager)

        callbacks = {
            'sample': lambda: self.data_controller.handle_sample(self.layout_manager.sidebar.sample_qty.get()),
            'predict_single': self.event_handler.handle_predict_single,
            'predict_file': self.event_handler.handle_predict_file,
            'predict_silent': lambda: None,
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
            'search': self.data_controller.handle_search,
            'on_patient_selected': self.data_controller.on_patient_selected,
            'show_ai_chat': self.show_ai_chat,
            'check_updates': lambda: self.update_manager.check_for_updates(silent=False),
            'refresh_styles': self.refresh_global_styles
        }
        self.layout_manager.callbacks.update(callbacks)
        self.layout_manager.setup_layout()
        # Single style application after layout is complete
        self.refresh_global_styles()
        
        # Session restoration moved to background thread inside _check_models_on_startup()
        self.layout_manager.update_status("Initializing clinical environment...")

        self.event_handler.setup_event_bindings()
        self.menu_handler.build_menubar()
        self._check_models_on_startup()
        self.update_manager.check_for_updates(silent=True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_ai_chat(self):
        """Launches the AI Clinical Research Copilot without freezing the UI."""
        self.layout_manager.update_status("Loading Clinical AI Specialists...", "orange")
        
        def _deferred_load_and_open():
            try:
                # Expensive imports happen in this background thread
                from ai.modal.AIChatModal import AIChatModal
                # Return to main thread to open the window
                self.root.after(0, lambda: self._open_ai_modal(AIChatModal))
            except Exception as e:
                self.root.after(0, lambda: self.error_handler.log_and_notify("AI Loading Error", e))

        threading.Thread(target=_deferred_load_and_open, daemon=True).start()

    def _open_ai_modal(self, modal_class):
        """Helper to actually open the modal after imports finish."""
        self.layout_manager.update_status("AI Ready.", "#10B981")
        modal_class(self.root, settings_manager=self.settings_manager)

    def refresh_global_styles(self):
        StyleManager.apply_styles(self.root, self.settings_manager.settings)
        self.layout_manager.dashboard.refresh_theme(self.settings_manager.theme)
        self.layout_manager.sidebar.refresh_theme(self.settings_manager.theme)
        if self.layout_manager.model_explorer:
            self.layout_manager.model_explorer.refresh_theme(self.settings_manager.theme)
        self.layout_manager.refresh_all_tabs_theme(self.settings_manager.theme)
        self.layout_manager.log_message("System visual identity synchronized.", level="SUCCESS")

    def on_close(self):
        try:
            self.layout_manager.update_status("Saving session & cleaning environment...", "orange")
            self.data_manager.save_session()
            Visualizer.close_all_modals()
            self.root.destroy()
        except: pass
        finally: os._exit(0)

    def _setup_window_icon(self):
        try:
            if sys.platform == "win32":
                myappid = f'clinical.xai.dashboard.{self.version}'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            icon_path = os.path.join(STATIC_HOME, "logo.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.icon_photo)
        except: pass

    def _check_models_on_startup(self):
        def check_task():
            # 1. Restore previous session in the background
            if self.data_manager.restore_session():
                path = self.data_manager.data_path
                self.data_controller.data_path = path
                df = self.data_manager.uploaded_df
                if df is not None:
                    self.root.after(0, self.layout_manager.refresh_data_tree)
                    self.root.after(0, lambda: self.layout_manager.dashboard.update_data_info(rows=len(df), cols=len(df.columns), samples=len(df)))
                self.root.after(0, lambda: self.layout_manager.log_message(f"Auto-loaded: {os.path.basename(path)}", level="INFO"))

            # 2. Check clinical model status
            success, msg = self.model_manager.check_and_train_models("", self.layout_manager.update_status, force=False)
            if success:
                self.root.after(0, lambda: self.layout_manager.refresh_input_features(self.model_manager.feature_names))
                self.root.after(0, lambda: self.layout_manager.update_status("System Ready — Models Loaded", "#10B981"))
                self.root.after(0, lambda: self.error_handler.notify("Clinical models loaded and ready.", type='success'))
            else:
                self.root.after(0, lambda: self.layout_manager.update_status("Upload dataset to train models.", "#3B82F6"))
                self.root.after(0, lambda: self.error_handler.notify("No trained models found.", type='info'))
        threading.Thread(target=check_task, daemon=True).start()

class ClinicalLogRedirector:
    def __init__(self, console_callback, root=None, level="INFO"):
        self.console_callback = console_callback
        self.root = root
        self.level = level
    def write(self, message):
        if message.strip():
            try:
                msg = message.strip()
                if self.root: self.root.after(0, lambda: self.console_callback(msg, level=self.level))
                else: self.console_callback(msg, level=self.level)
            except: pass
    def flush(self): pass

if __name__ == "__main__":
    root = tk.Tk()
    app = CancerDetectionApp(root)
    sys.stdout = ClinicalLogRedirector(app.layout_manager.log_message, root=app.root, level="INFO")
    sys.stderr = ClinicalLogRedirector(app.layout_manager.log_message, root=app.root, level="ERROR")
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        root.mainloop()
    except Exception as e:
        if 'app' in locals():
            app.error_handler.log_and_notify("Emergency Shutdown", e, "System Failure")
            app.on_close()
        else: os._exit(1)
