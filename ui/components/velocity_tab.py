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
        # Header
        header = ttk.Frame(self, padding=(15, 12, 15, 6))
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="LONGITUDINAL BIOMARKER VELOCITY TRACKING",
                  font=('Inter', 12, 'bold'), foreground="#0F172A").pack(anchor=tk.W)
        ttk.Label(header, text="Time-series trajectory of patient metabolic profile over time",
                  font=('Inter', 9), foreground="#94A3B8").pack(anchor=tk.W)

        # Content split
        self.content_frame = ttk.Frame(self, padding=(15, 10))
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Plot frame
        self.plot_frame = ttk.Frame(self.content_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Metrics frame
        self.metrics_frame = ttk.Frame(self.content_frame, padding=(0, 20, 0, 0))
        self.metrics_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Initialize persistent plotting structures
        self.fig, self.ax = plt.subplots(figsize=(10, 4), dpi=100)
        self.fig.patch.set_facecolor('#ffffff')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial display
        self._render_empty_placeholder("Awaiting Patient History Data...")
        
    def _render_empty_placeholder(self, message):
        """Internal helper to show a consistent centered message on the plot."""
        # Clean current state
        for widget in self.metrics_frame.winfo_children():
            widget.destroy()
            
        self.ax.clear()
        self.ax.set_facecolor('#ffffff')
        self.ax.text(0.5, 0.5, message, 
                    ha='center', va='center', color='#94A3B8', fontdict={'size': 14})
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
        
        months = [h['month'] for h in history]
        psa = [h['psa'] for h in history]
        afp = [h['afp'] for h in history]
        ca125 = [h['ca125'] for h in history]
        risk = [h['risk'] for h in history]
        
        self.ax.clear()
        self.ax.axis('on')
        self.ax.set_facecolor('#ffffff')
        
        # Clear potential residual twin axes before creating a new one
        for other_ax in self.fig.axes:
            if other_ax != self.ax:
                other_ax.remove()

        # Plot Biomarkers on left axis
        line1, = self.ax.plot(months, psa, marker='o', color='#3B82F6', label='PSA (pg/mL)', linewidth=2)
        line2, = self.ax.plot(months, afp, marker='s', color='#10B981', label='AFP (pg/mL)', linewidth=2)
        line3, = self.ax.plot(months, ca125, marker='^', color='#F59E0B', label='CA125 (U/mL)', linewidth=2)
        
        self.ax.set_xlabel("Time (Months from Present)", fontsize=10, color="#475569")
        self.ax.set_ylabel("Biomarker Concentration", fontsize=10, color="#475569")
        self.ax.grid(True, linestyle='--', alpha=0.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        # Plot Clinical Risk on right axis
        ax2 = self.ax.twinx()
        line4, = ax2.plot(months, risk, marker='D', color='#EF4444', label='AI Risk Score', linewidth=2, linestyle='--')
        ax2.set_ylabel("Risk Score (0.0 - 1.0)", fontsize=10, color="#EF4444")
        ax2.set_ylim(0, 1)
        ax2.spines['top'].set_visible(False)

        # Combine legends
        lines = [line1, line2, line3, line4]
        labels = [l.get_label() for l in lines]
        self.ax.legend(lines, labels, loc='upper left', frameon=True, fontsize=9)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def _render_metrics(self):
        # Clear existing
        for widget in self.metrics_frame.winfo_children():
            widget.destroy()

        metrics = self.velocity_data.get('metrics', {})
        
        ttk.Label(self.metrics_frame, text="TRAJECTORY ANALYSIS", 
                 font=('Inter', 10, 'bold'), foreground="#334155").pack(anchor=tk.W, pady=(0, 5))
                 
        grid = ttk.Frame(self.metrics_frame)
        grid.pack(fill=tk.X)
        
        def make_metric(parent, label, value, is_percentage=True):
            f = ttk.Frame(parent, padding=10, relief=tk.FLAT, borderwidth=1)
            ttk.Label(f, text=label, font=('Inter', 9), foreground="#64748B").pack(anchor=tk.W)
            
            color = "#10B981" if value <= 0 else "#EF4444" 
            sign = "+" if value > 0 else ""
            fmt = f"{sign}{value:.1f}%" if is_percentage else f"{value}"
            
            ttk.Label(f, text=fmt, font=('Inter', 14, 'bold'), foreground=color).pack(anchor=tk.W)
            return f

        m1 = make_metric(grid, "PSA 3-Month Velocity", metrics.get('psa_velocity', 0))
        m1.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)
        
        m2 = make_metric(grid, "AFP 3-Month Velocity", metrics.get('afp_velocity', 0))
        m2.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)

        m3 = make_metric(grid, "AI Risk Shift", metrics.get('risk_delta', 0))
        m3.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def clear(self):
        """Reset tab to its initial state."""
        self.current_patient_id = None
        self.velocity_data = None
        self._render_empty_placeholder("Awaiting Patient History Data...")
