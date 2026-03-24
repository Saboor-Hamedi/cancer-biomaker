import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class VelocityTab(ttk.Frame):
    def __init__(self, parent, callbacks, **kwargs):
        super().__init__(parent, **kwargs)
        self.callbacks = callbacks
        self.pack(fill=tk.BOTH, expand=True)
        
        # Data
        self.current_patient_id = None
        self.velocity_data = None
        self.fig = None
        self.canvas = None
        
        self._create_widgets()

    def _create_widgets(self):
        self.header = ttk.Frame(self, padding=(12, 8, 12, 4))
        self.header.pack(fill=tk.X)
        self.title_label = ttk.Label(self.header, text="LONGITUDINAL BIOMARKER VELOCITY TRACKING — Predictive Patient Trajectory",
                                     font=('Inter', 11, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        # Content split
        self.content_frame = ttk.Frame(self, padding=(15, 0, 15, 10)) # Standardized Padding
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Plot frame
        self.plot_frame = ttk.Frame(self.content_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Metrics frame
        self.metrics_container = ttk.Frame(self.content_frame, padding=(0, 20, 0, 0))
        self.metrics_container.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.metrics_title = ttk.Label(self.metrics_container, text="TRAJECTORY ANALYSIS", 
                                       font=('Inter', 10, 'bold'))
        self.metrics_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.metrics_grid = ttk.Frame(self.metrics_container)
        self.metrics_grid.pack(fill=tk.X)
        
        # Initialize persistent plotting structures
        self.fig, self.ax = plt.subplots(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial display
        self._render_empty_placeholder("Awaiting Patient History Data...")

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        is_dark = theme_name == 'pure_dark'
        
        self.configure(style='TFrame')
        self.header.configure(style='TFrame')
        self.content_frame.configure(style='TFrame')
        self.plot_frame.configure(style='TFrame')
        self.metrics_container.configure(style='TFrame')
        self.metrics_grid.configure(style='TFrame')
        
        self.title_label.config(foreground=palette['medic_brand'])
        self.metrics_title.config(foreground=palette['medic_brand'])
        
        # Update Matplotlib
        text_color = palette['text_main']
        bg_color = palette['bg_main']
        
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        self.ax.set_xlabel("Time (Months from Present)", color=text_color)
        self.ax.set_ylabel("Biomarker Concentration", color=text_color)
        self.ax.tick_params(axis='x', colors=text_color)
        self.ax.tick_params(axis='y', colors=text_color)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(palette['border_light'])
            
        # Re-render if there's data
        if self.velocity_data:
            self._render_plot()
            self._render_metrics()
        else:
            self._render_empty_placeholder("Awaiting Patient History Data...")

    def _render_empty_placeholder(self, message):
        """Internal helper to show a consistent centered message on the plot."""
        for widget in self.metrics_grid.winfo_children():
            widget.destroy()
            
        self.ax.clear()
        # Use a neutral grey that works on both Absolute Black and White
        placeholder_color = "#94A3B8"
        
        # Match ax background to figure background
        self.ax.set_facecolor(self.fig.get_facecolor())
        
        self.ax.text(0.5, 0.5, message, 
                    ha='center', va='center', color=placeholder_color, fontdict={'size': 14})
        self.ax.axis('off')
        
        # Clean potential residual second axis from _render_plot
        for other_ax in self.fig.axes:
            if other_ax != self.ax:
                other_ax.remove()
                
        self.canvas.draw()

    def update_velocity_data(self, patient_id, velocity_data):
        self.current_patient_id = patient_id
        self.velocity_data = velocity_data
        
        if not velocity_data:
            self._render_empty_placeholder("No historical data available for this patient.")
            return
            
        self._render_plot()
        self._render_metrics()

    def _render_plot(self):
        history = self.velocity_data['history']
        forecast = self.velocity_data.get('forecast')
        
        months = [h['month'] for h in history]
        psa = [h['psa'] for h in history]
        afp = [h['afp'] for h in history]
        ca125 = [h['ca125'] for h in history]
        risk = [h['risk'] for h in history]
        
        self.ax.clear()
        self.ax.axis('on')
        
        # Clear potential residual twin axes before creating a new one
        for other_ax in self.fig.axes:
            if other_ax != self.ax:
                other_ax.remove()

        # ── 1. BACKGROUND CLINICAL ZONES ──
        # We shade based on the standardized Risk axis (0.0 - 1.0)
        ax2 = self.ax.twinx()
        ax2.axhspan(0.0, 0.3, color='#10B981', alpha=0.04, label='Healthy Zone')
        ax2.axhspan(0.3, 0.7, color='#F59E0B', alpha=0.04, label='Monitoring Zone')
        ax2.axhspan(0.7, 1.0, color='#EF4444', alpha=0.04, label='Critical Zone')

        # ── 2. HISTORICAL DATA ──
        line1, = self.ax.plot(months, psa, marker='o', color='#3B82F6', label='PSA (Historical)', linewidth=2)
        line2, = self.ax.plot(months, afp, marker='s', color='#10B981', label='AFP (Historical)', linewidth=2)
        line3, = self.ax.plot(months, ca125, marker='^', color='#F59E0B', label='CA125 (Historical)', linewidth=2)
        line4, = ax2.plot(months, risk, marker='D', color='#EF4444', label='AI Risk (Historical)', linewidth=2.5)

        # ── 3. PREDICTIVE FORECASTING ──
        if forecast:
            f_months = [months[-1], forecast['month']]
            # Plot dotted extensions
            self.ax.plot(f_months, [psa[-1], forecast['psa']], '--', color='#3B82F6', alpha=0.5, label='PSA Forecast')
            self.ax.plot(f_months, [afp[-1], forecast['afp']], '--', color='#10B981', alpha=0.5)
            self.ax.plot(f_months, [ca125[-1], forecast['ca125']], '--', color='#F59E0B', alpha=0.5)
            ax2.plot(f_months, [risk[-1], forecast['risk']], ':', color='#EF4444', alpha=0.6, linewidth=2, label='Risk Forecast')
            
            # Add "FORECAST" text label on X-axis
            from ui.styles import StyleManager
            is_dark = sum(self.fig.patch.get_facecolor()[:3]) < 1.0 
            text_mute = "#94A3B8" if is_dark else "#64748B"
            
            self.ax.axvline(x=0, color=text_mute, linestyle='-', alpha=0.3, linewidth=1)
            self.ax.text(forecast['month'], self.ax.get_ylim()[0], ' FORECAST', 
                         color=text_mute, fontsize=8, fontweight='bold', va='bottom')

        # ── 4. INLINE LINE LABELS ──
        # helper to add a small label at the end of the line
        def add_line_label(axis, x, y, text, color):
            axis.text(x + 0.2, y, text, color=color, fontsize=8, fontweight='bold', va='center')

        # Plot labels either at forecast or historical end
        end_m = forecast['month'] if forecast else months[-1]
        if forecast:
            add_line_label(self.ax, end_m, forecast['psa'], "PSA", '#3B82F6')
            add_line_label(self.ax, end_m, forecast['afp'], "AFP", '#10B981')
            add_line_label(self.ax, end_m, forecast['ca125'], "CA125", '#F59E0B')
            add_line_label(ax2, end_m, forecast['risk'], " RISK", '#EF4444')
        else:
            add_line_label(self.ax, end_m, psa[-1], "PSA", '#3B82F6')
            add_line_label(self.ax, end_m, afp[-1], "AFP", '#10B981')
            add_line_label(self.ax, end_m, ca125[-1], "CA125", '#F59E0B')
            add_line_label(ax2, end_m, risk[-1], " RISK", '#EF4444')

        # Styling
        is_dark = sum(self.fig.patch.get_facecolor()[:3]) < 1.0 
        label_color = "#F8FAFC" if is_dark else "#475569"

        
        self.ax.set_xlabel("Time (Months from Present)", fontsize=10, color=label_color)
        self.ax.set_ylabel("Biomarker Concentration", fontsize=10, color=label_color)
        self.ax.grid(True, linestyle='--', alpha=0.1 if is_dark else 0.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.tick_params(colors=label_color)
        
        ax2.set_ylabel("Clinical Risk Score (0.0 - 1.0)", fontsize=10, color='#EF4444', fontweight='bold')
        ax2.set_ylim(0, 1.05) # Slight headroom
        ax2.spines['top'].set_visible(False)
        ax2.tick_params(colors='#EF4444')

        # Legend (Selected items only for clarity)
        lines = [line1, line4]
        labels = ["Biomarkers", "AI Risk Score"]
        self.ax.legend(lines, labels, loc='upper left', frameon=True, fontsize=9,
                       facecolor=self.fig.patch.get_facecolor(), 
                       edgecolor="#334155" if is_dark else "#E2E8F0",
                       labelcolor=label_color)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def _render_metrics(self):
        # Clear existing
        for widget in self.metrics_grid.winfo_children():
            widget.destroy()

        metrics = self.velocity_data.get('metrics', {})
        is_dark = sum(self.fig.patch.get_facecolor()[:3]) < 1.0 
        bg = "#18181B" if is_dark else "#F8FAFC"
        border = "#27272A" if is_dark else "#E2E8F0"
        
        # ── 1. TREND VERDICT BOX (NEW) ──
        verdict_frame = tk.Frame(self.metrics_grid, bg=bg, highlightthickness=1, 
                                 highlightbackground=border, padx=15, pady=10)
        verdict_frame.pack(fill=tk.X, pady=(0, 15))
        
        level_colors = {"DANGER": "#EF4444", "WARNING": "#F59E0B", "SUCCESS": "#10B981", "INFO": "#3B82F6"}
        v_color = level_colors.get(metrics.get('verdict_level', 'INFO'), "#3B82F6")
        
        tk.Label(verdict_frame, text="CLINICAL TREND VERDICT", font=('Inter', 8, 'bold'), 
                 bg=bg, fg="#94A3B8" if is_dark else "#64748B").pack(anchor=tk.W)
        tk.Label(verdict_frame, text=metrics.get('verdict', 'Data stable.'), 
                 font=('Inter', 11, 'bold'), bg=bg, fg=v_color, wraplength=800, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))

        # ── 2. METRICS CARDS ──
        cards_container = ttk.Frame(self.metrics_grid, style='TFrame')
        cards_container.pack(fill=tk.X)

        def make_metric(parent, label, value, is_percentage=True, sub_label=None):
            f = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=border, padx=15, pady=12)
            tk.Label(f, text=label, font=('Inter', 9), bg=bg, fg="#94A3B8" if is_dark else "#64748B").pack(anchor=tk.W)
            
            # Numeric value treatment
            try:
                num_val = float(value) if not isinstance(value, str) else 0
                color = "#10B981" if num_val <= 0 else "#EF4444" 
                sign = "+" if num_val > 0 else ""
                fmt = f"{sign}{num_val:.1f}%" if is_percentage else str(value)
            except:
                color = "#3B82F6"
                fmt = str(value)
            
            tk.Label(f, text=fmt, font=('Inter', 14, 'bold'), bg=bg, fg=color).pack(anchor=tk.W)
            if sub_label:
                tk.Label(f, text=sub_label, font=('Inter', 7, 'italic'), bg=bg, fg="#94A3B8").pack(anchor=tk.W)
            return f

        m1 = make_metric(cards_container, "PSA Velocity", metrics.get('psa_velocity', 0), sub_label="Shift in last 3 months")
        m1.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)
        
        m2 = make_metric(cards_container, "PSA Doubling Time", metrics.get('psa_doubling', 'N/A'), is_percentage=False, sub_label="Clinical malignancy proxy")
        m2.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)

        m3 = make_metric(cards_container, "AI Risk Shift", metrics.get('risk_delta', 0), sub_label="Diagnostic momentum")
        m3.pack(side=tk.LEFT, fill=tk.X, expand=True)


    def clear(self):
        """Reset tab to its initial state."""
        self.current_patient_id = None
        self.velocity_data = None
        self._render_empty_placeholder("Awaiting Patient History Data...")
