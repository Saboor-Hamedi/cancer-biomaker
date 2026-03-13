"""
Event Handler - Handles UI events and user interactions.
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
from logic.model_manager import HAS_XGB


class EventHandler:
    """Handler for UI events and user interactions."""

    def __init__(self, root, data_controller, model_controller, visualization_controller, layout_manager):
        self.root = root
        self.data_controller = data_controller
        self.model_controller = model_controller
        self.visualization_controller = visualization_controller
        self.layout_manager = layout_manager

    def setup_event_bindings(self):
        """Setup all event bindings."""
        # Button events
        self._bind_button_events()

        # Tab events
        self._bind_tab_events()

        # Tree events
        self._bind_tree_events()

        # Model selection events
        self._bind_model_events()

    def _bind_button_events(self):
        """Bind button click events."""
        # Buttons are already configured with commands in their respective components
        pass

    def _bind_tab_events(self):
        """Bind tab change events."""
        def on_tab_change(event):
            tab = event.widget.tab('current')['text']
            if tab == "Input Features":
                self.handle_tab_input_focus()
            elif tab == "Analysis":
                self.handle_tab_analysis_focus()

        self.layout_manager.get_components()['notebook'].bind('<<NotebookTabChanged>>', on_tab_change)

    def _bind_tree_events(self):
        """Bind tree view events."""
        tab_input = self.layout_manager.get_components().get('tab_input')
        tab_data = self.layout_manager.get_components().get('tab_data')
        
        if tab_input:
            # Double-click to edit
            tab_input.tree.bind('<Double-1>', self.handle_tree_double_click)
            # Right-click context menu
            tab_input.tree.bind('<Button-3>', self.handle_tree_right_click)
        
        if tab_data:
            # Data Tab Tree - Double-click to sync row to input predictors
            tab_data.tree.bind('<Double-1>', self.handle_data_tree_double_click)

    def _bind_model_events(self):
        """Bind model selection events."""
        sidebar = self.layout_manager.get_components()['sidebar']
        sidebar.model_var.trace('w', self.handle_model_change)

    # Event handlers
    def handle_predict_single(self):
        """Handle single prediction."""

        model_name = self.layout_manager.sidebar.model_var.get()
        if not self._require_model(model_name):
            return

        # Get input data from table
        input_data = self.layout_manager.tab_input.get_table_data()
        if not input_data:
            messagebox.showwarning("Input Required", "Please enter biomarker values in the Input Features tab.")
            return

        # Run prediction
        self.model_controller.predict_single(input_data)

    def handle_predict_file(self):
        """Handle batch file prediction."""
        if not self._require_data("Batch Prediction"):
            return

        model_name = self.layout_manager.sidebar.model_var.get()
        if not self._require_model(model_name):
            return

        # Run batch prediction
        self.model_controller.predict_batch()

    def handle_clear_input(self):
        """Handle clearing input fields."""
        if messagebox.askyesno("Confirm Clear", "Clear all input fields?"):
            self.layout_manager.sidebar.clear_input_fields()

    def handle_clear_table(self):
        """Handle clearing the feature table."""
        if messagebox.askyesno("Confirm Clear", "Clear all table data?"):
            self.layout_manager.tab_input.clear_table()

    def handle_tab_input_focus(self):
        """Handle when Input Features tab gets focus."""
        # Refresh the table display
        self.layout_manager.tab_input.refresh_display()

    def handle_tab_analysis_focus(self):
        """Handle when Analysis tab gets focus."""
        # Update analysis display if we have results
        if self.layout_manager.get_components().get('current_prediction_data'):
            self._update_analysis_display()

    def handle_tree_double_click(self, event):
        """Handle double-click on tree item for editing."""
        tree = self.layout_manager.get_components()['tab_input'].tree
        region = tree.identify_region(event.x, event.y)

        if region == "cell":
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)

            if item and column:
                col_index = int(column[1:]) - 1  # Remove '#' prefix
                if col_index == 1:  # Value column
                    self._edit_tree_cell(item, col_index)

    def handle_data_tree_double_click(self, event):
        """Handle double-click on data tree to sync patient data to input predictors."""
        tree = self.layout_manager.get_components()['tab_data'].tree
        item = tree.identify_row(event.y)
        
        if item and self.data_controller.data_manager.uploaded_df is not None:
            # Get values from tree
            values = tree.item(item, 'values')
            df = self.data_controller.data_manager.uploaded_df
            
            # Find matching row in dataframe using index
            # This is robust because we populate the tree in order
            idx = tree.index(item)
            if idx < len(df):
                row_data = df.iloc[idx]
                self.data_controller.sync_row_to_input(row_data)
                
                # Switch to input tab
                try:
                    self.layout_manager.dashboard.notebook.select(self.layout_manager.dashboard.input_tab)
                except:
                    pass

    def handle_tree_right_click(self, event):
        """Handle right-click context menu on tree."""
        tree = self.layout_manager.get_components()['tab_input'].tree
        item = tree.identify_row(event.y)

        if item:
            # Create context menu
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit Value", command=lambda: self._edit_tree_cell(item, 1))
            menu.add_command(label="Set to Default", command=lambda: self._set_default_value(item))
            menu.add_separator()
            menu.add_command(label="Copy Value", command=lambda: self._copy_tree_value(item))
            menu.add_command(label="Paste Value", command=lambda: self._paste_tree_value(item))

            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def handle_model_change(self, *args):
        """Handle model selection change."""
        model_name = self.layout_manager.sidebar.model_var.get()

        # Update model info display
        self.layout_manager.sidebar.update_model_info(model_name)

        # Check if model is available
        model = self.model_controller.model_manager.load_model(model_name)
        if model is None:
            self.layout_manager.update_status(f"Model '{model_name}' not available", "red")
        else:
            self.layout_manager.update_status(f"Model '{model_name}' loaded", "#10B981")

    # Helper methods
    def _edit_tree_cell(self, item, col_index):
        """Edit a cell in the tree."""
        tree = self.layout_manager.get_components()['tab_input'].tree

        # Get current value
        current_value = tree.item(item, 'values')[col_index]

        # Create entry widget for editing
        x, y, width, height = tree.bbox(item, column=col_index)
        entry = tk.Entry(tree, width=width//8)  # Approximate character width
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus()

        def save_edit(event=None):
            new_value = entry.get()
            try:
                # Validate numeric input
                float(new_value)
                # Update tree
                values = list(tree.item(item, 'values'))
                values[col_index] = new_value
                tree.item(item, values=values)
                # Update internal data
                feature_name = values[0]
                self.layout_manager.tab_input.update_feature_value(feature_name, new_value)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a numeric value.")
            finally:
                entry.destroy()

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', cancel_edit)

    def _set_default_value(self, item):
        """Set tree cell to default value."""
        tree = self.layout_manager.get_components()['tab_input'].tree
        feature_name = tree.item(item, 'values')[0]

        # Get default value (you might want to define defaults elsewhere)
        defaults = {
            'PSA_peak_height': 0.0,
            'min_slope': 0.0,
            'PSA_concentration_pg_per_ml': 0.0,
            'max_slope': 0.0,
            'current_at_-0.46V': 0.0,
            'min_current': 0.0,
            'PSA_actual_peak_current': 0.0,
            'mean_current': 0.0,
            'area_under_curve': 0.0,
            'peak_height_ratio_PSA_CA125': 0.0
        }

        default_value = defaults.get(feature_name, 0.0)

        # Update tree
        values = list(tree.item(item, 'values'))
        values[1] = str(default_value)
        tree.item(item, values=values)

        # Update internal data
        self.layout_manager.tab_input.update_feature_value(feature_name, str(default_value))

    def _copy_tree_value(self, item):
        """Copy value from tree cell."""
        tree = self.layout_manager.get_components()['tab_input'].tree
        value = tree.item(item, 'values')[1]  # Value column
        self.root.clipboard_clear()
        self.root.clipboard_append(value)

    def _paste_tree_value(self, item):
        """Paste value to tree cell."""
        try:
            value = self.root.clipboard_get()
            float(value)  # Validate numeric

            tree = self.layout_manager.get_components()['tab_input'].tree
            values = list(tree.item(item, 'values'))
            values[1] = value
            tree.item(item, values=values)

            # Update internal data
            feature_name = values[0]
            self.layout_manager.tab_input.update_feature_value(feature_name, value)

        except (tk.TclError, ValueError):
            messagebox.showerror("Invalid Input", "Clipboard does not contain a valid numeric value.")

    def _update_analysis_display(self):
        """Update the analysis tab with current prediction data."""
        prediction_data = self.layout_manager.get_components().get('current_prediction_data')
        if prediction_data:
            self.layout_manager.tab_analysis.display_prediction_results(prediction_data)

    def _require_data(self, context):
        """Check if data is available."""
        return self.data_controller.error_handler.require_data(context, self.data_controller.data_path)

    def _require_model(self, model_name):
        """Check if model is available."""
        model = self.model_controller.model_manager.load_model(model_name)
        return self.data_controller.error_handler.require_model(model, model_name)
