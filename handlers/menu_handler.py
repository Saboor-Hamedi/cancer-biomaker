"""
Menu Handler - Handles menu bar actions and commands.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import os

class MenuHandler:
    """Handler for menu bar actions and keyboard shortcuts."""

    def __init__(self, root, data_controller, model_controller, visualization_controller, layout_manager):
        self.root = root
        self.data_controller = data_controller
        self.model_controller = model_controller
        self.visualization_controller = visualization_controller
        self.layout_manager = layout_manager

    def build_menubar(self):
        """Build the complete menu bar."""
        menubar = tk.Menu(self.root)

        # File menu
        self._build_file_menu(menubar)

        # Data menu
        self._build_data_menu(menubar)

        # Analytics menu
        self._build_analytics_menu(menubar)

        # Statistics menu
        self._build_statistics_menu(menubar)

        # Features menu
        self._build_features_menu(menubar)

        # Help menu
        self._build_help_menu(menubar)

        self.root.config(menu=menubar)
        self._bind_shortcuts()

    def _build_file_menu(self, menubar):
        """Build the File menu."""
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Upload Dataset...", command=self.data_controller.handle_upload, accelerator="Ctrl+O")
        file_menu.add_command(label="Load Sample Batch", command=self.data_controller.handle_sample)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results to Excel", command=self.data_controller.handle_export, accelerator="Ctrl+S")
        file_menu.add_command(label="Generate Report...", command=self._handle_report)
        file_menu.add_separator()
        file_menu.add_command(label="Clear All Data", command=self._handle_clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._handle_exit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)

    def _build_data_menu(self, menubar):
        """Build the Data menu."""
        data_menu = tk.Menu(menubar, tearoff=0)
        data_menu.add_command(label="Re-Train All Models", command=self.model_controller.handle_train_models)
        data_menu.add_command(label="Data Optimization...", command=self.data_controller.show_preprocessing)
        menubar.add_cascade(label="Data", menu=data_menu)

    def _build_analytics_menu(self, menubar):
        """Build the Analytics menu."""
        analytics_menu = tk.Menu(menubar, tearoff=0)
        analytics_menu.add_command(label="Local Patient Diagnosis", command=self.visualization_controller.show_local_explanation)
        analytics_menu.add_command(label="Patient Radar Profile", command=self.visualization_controller.show_patient_radar)
        analytics_menu.add_command(label="Detailed Clinical Metrics", command=self.visualization_controller.show_detailed_metrics)
        analytics_menu.add_command(label="Cross-Model Comparison", command=self.visualization_controller.show_model_comparison)
        analytics_menu.add_command(label="Accuracy Comparison", command=self.visualization_controller.show_accuracy_comparison)
        analytics_menu.add_command(label="Model Leadership Selection Report", command=self.visualization_controller.show_model_leadership_report)
        analytics_menu.add_separator()
        analytics_menu.add_command(label="Correlation Heatmap", command=self.visualization_controller.show_correlation_heatmap)
        analytics_menu.add_command(label="Reliability Chart", command=self.visualization_controller.show_calibration_curve)
        analytics_menu.add_command(label="Learning Analysis", command=self.visualization_controller.show_learning_curve)
        analytics_menu.add_command(label="Stability Analysis", command=self.visualization_controller.show_stability)
        analytics_menu.add_command(label="Performance Analysis", command=self.visualization_controller.show_performance_analysis)
        analytics_menu.add_command(label="Multi-Model Learning Curves", command=self.visualization_controller.show_multi_learning_curves)
        analytics_menu.add_separator()
        analytics_menu.add_command(label="ROC Curve Analysis", command=self.visualization_controller.show_roc_curve)
        analytics_menu.add_command(label="Clinical Confusion Matrix", command=self.visualization_controller.show_confusion_matrix)
        analytics_menu.add_command(label="Precision-Recall Curve", command=self.visualization_controller.show_precision_recall)
        analytics_menu.add_command(label="PR-Threshold Analysis", command=self.visualization_controller.show_precision_recall_threshold)
        analytics_menu.add_separator()
        analytics_menu.add_command(label="Patient Map (t-SNE)", command=self.visualization_controller.show_tsne_map)
        analytics_menu.add_command(label="Biomarker Impact (PDP)", command=self.visualization_controller.show_pdp)
        menubar.add_cascade(label="Analytics", menu=analytics_menu)

    def _build_statistics_menu(self, menubar):
        """Build the Statistics menu."""
        stats_menu = tk.Menu(menubar, tearoff=0)
        stats_menu.add_command(label="Statistical Model Comparison", command=self.visualization_controller.show_statistical_comparison)
        stats_menu.add_command(label="Permutation Feature Importance", command=self.visualization_controller.show_permutation_importance)
        stats_menu.add_command(label="SHAP Feature Analysis", command=self.visualization_controller.show_shap_analysis)
        stats_menu.add_command(label="Model Robustness Analysis", command=self.visualization_controller.show_model_robustness_benchmark)
        stats_menu.add_command(label="Clinical Leadership Report", command=self.visualization_controller.show_model_leadership_report)
        stats_menu.add_command(label="Sensitivity Analysis", command=self.visualization_controller.show_sensitivity_analysis)
        menubar.add_cascade(label="Statistics", menu=stats_menu)

    def _build_features_menu(self, menubar):
        """Build the Features menu."""
        features_menu = tk.Menu(menubar, tearoff=0)
        biomarkers = [
            'PSA_peak_height', 'min_slope', 'PSA_concentration_pg_per_ml',
            'max_slope', 'current_at_-0.46V', 'min_current',
            'PSA_actual_peak_current', 'mean_current', 'area_under_curve',
            'peak_height_ratio_PSA_CA125'
        ]
        for feature in biomarkers:
            features_menu.add_command(label=feature, command=lambda f=feature: self.visualization_controller.show_feature_analysis(f))
        menubar.add_cascade(label="Features", menu=features_menu)

    def _build_help_menu(self, menubar):
        """Build the Help menu."""
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=lambda: self.layout_manager.callbacks.get('check_updates', lambda: None)())
        help_menu.add_separator()
        help_menu.add_command(label="Help & Documentation", command=self._show_help, accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind_all("<Control-o>", lambda e: self.data_controller.handle_upload())
        self.root.bind_all("<Control-s>", lambda e: self.data_controller.handle_export())
        self.root.bind_all("<F1>", lambda e: self._show_help())

    def _handle_report(self):
        self.data_controller.handle_report()

    def _handle_clear_all(self):
        self.data_controller.handle_clear_data()

    def _handle_exit(self):
        from views.visualizations import Visualizer
        try:
            Visualizer.close_all_modals()
            self.root.destroy()
        except:
            pass
        import os
        os._exit(0)

    def _show_help(self):
        """Show a professional scrollable modal with detailed documentation."""
        help_win = tk.Toplevel(self.root)
        help_win.title("SYSTEM DOCUMENTATION & CLINICAL GUIDE")
        help_win.geometry("850x700")
        help_win.configure(bg="#FFFFFF")
        help_win.transient(self.root)
        help_win.grab_set()

        # Center
        help_win.update_idletasks()
        w, h = help_win.winfo_width(), help_win.winfo_height()
        x = (help_win.winfo_screenwidth() // 2) - (w // 2)
        y = (help_win.winfo_screenheight() // 2) - (h // 2)
        help_win.geometry(f"+{x}+{y}")

        main = ttk.Frame(help_win, style='Card.TFrame', padding=25)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="BIOMARKER AI CLINICAL DOCUMENTATION", font=("Inter", 15, "bold"), foreground="#0F172A").pack(anchor=tk.W, pady=(0, 15))

        txt_frame = ttk.Frame(main)
        txt_frame.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(txt_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(txt_frame, wrap=tk.WORD, font=("Inter", 11), padx=25, pady=25, 
                       bg="#F8FAFC", fg="#1E293B", borderwidth=0, highlightthickness=0,
                       yscrollcommand=sb.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=text.yview)

        # Robust content loading
        content = ""
        paths = [
            os.path.join(os.getcwd(), "DOCUMENTATION.md"),
            os.path.join(os.path.dirname(__file__), "..", "DOCUMENTATION.md")
        ]
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    content = f.read()
                    break
        
        if content:
            text.insert(tk.END, content)
        else:
            text.insert(tk.END, "DETAILED DOCUMENTATION GUIDE\n" + "="*30 + "\n\n")
            text.insert(tk.END, "1. UPLOAD: Use File -> Upload Dataset (.xlsx)\n")
            text.insert(tk.END, "2. TRAINING: Go to Data -> Re-Train All Models\n")
            text.insert(tk.END, "3. DIAGNOSIS: Select Analytics to view SHAP/ROC results.")

        text.config(state=tk.DISABLED)
        
        ttk.Button(main, text="CLOSE GUIDE", style='Primary.TButton', command=help_win.destroy).pack(side=tk.RIGHT, pady=(20, 0))
