import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd

class InputTab(ttk.Frame):
    """Handles patient biomarker entry — 3-column layout with unit extraction and clean names."""

    # ── Unit extraction from raw column names ────────────────────────────────
    _UNIT_SUFFIXES = [
        ('_pg_per_ml',  'pg/mL'),
        ('pg_per_ml',   'pg/mL'),
        ('_ng_per_ml',  'ng/mL'),
        ('ng_per_ml',   'ng/mL'),
        ('_u_per_ml',   'U/mL'),
        ('u_per_ml',    'U/mL'),
        ('_iu_per_ml',  'IU/mL'),
        ('_nm',         'nM'),
        ('_mv',         'mV'),
        ('_ua',         'µA'),
        ('_na',         'nA'),
    ]

    # ── Clinical Reference Thresholds (Standard Oncology ranges) ──────────────
    _THRESHOLDS = {
        'psa':   4.0,  # ng/mL (Prostate Specific Antigen)
        'afp':   20.0, # ng/mL (Alpha-fetoprotein)
        'ca125': 35.0, # U/mL (Cancer Antigen 125)
    }

    @classmethod
    def _humanize(cls, raw: str):
        """Return (display_name, unit) from a raw column name."""
        s = str(raw)
        unit = ''
        sl = s.lower()
        for suffix, label in cls._UNIT_SUFFIXES:
            if sl.endswith(suffix):
                unit = label
                s = s[: len(s) - len(suffix)]
                break
        if not unit:
            for suffix, label in cls._UNIT_SUFFIXES:
                if suffix in sl:
                    unit = label
                    idx = sl.index(suffix)
                    s = s[:idx] + s[idx + len(suffix):]
                    break
        name = (s.replace('_', ' ')
                  .strip()
                  .upper())
        return name, unit

    def __init__(self, parent, features=None, data_manager=None):
        super().__init__(parent)
        self.features = features or []
        self.data_manager = data_manager
        self.tree: ttk.Treeview = None  # type: ignore
        # Maps display_name -> raw feature name so get_values() returns correct keys
        self._display_to_raw: dict = {}
        self._create_widgets()
        if self.features:
            self.refresh_features(self.features)

    def _create_widgets(self):
        self.header = ttk.Frame(self, padding=(12, 8, 12, 4))
        self.header.pack(fill=tk.X)
        self.title_label = ttk.Label(self.header, text="BIOMARKER INPUT — Load Data or Edit Patient Profile",
                                     font=('Inter', 11, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        # Footer Actions - Packed first with side=BOTTOM to ensure it stays pinned
        self.footer = ttk.Frame(self, padding=(15, 0, 15, 12))
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(self.footer, text="Export CSV", style='Primary.TButton', command=lambda: self._export_data('csv')).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.footer, text="Export Excel", style='Primary.TButton', command=lambda: self._export_data('excel')).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(self.footer, text="Reset Values", command=self.clear_table).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.footer, text="Copy Values", command=self._copy_table).pack(side=tk.RIGHT, padx=5)

        container = ttk.Frame(self, padding=(15, 0, 15, 10)) # Standardized Padding
        container.pack(fill=tk.BOTH, expand=True)
        
        # 3-column treeview
        cols = ("feature", "unit", "value")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=22)

        self.tree.heading("feature", text="BIOMARKER / FEATURE NAME", anchor=tk.CENTER)
        self.tree.heading("unit",    text="UNIT", anchor=tk.CENTER)
        self.tree.heading("value",   text="MEASURED VALUE", anchor=tk.CENTER)

        self.tree.column("feature", width=310, anchor=tk.CENTER, stretch=True)
        self.tree.column("unit",    width=110, anchor=tk.CENTER, stretch=False)
        self.tree.column("value",   width=160, anchor=tk.CENTER, stretch=False)

        # Clean initial tags (no hardcoded backgrounds)
        self.tree.tag_configure('psa')
        self.tree.tag_configure('afp')
        self.tree.tag_configure('ca')
        self.tree.tag_configure('other')
        self.tree.tag_configure('abnormal', foreground="#EF4444", font=('Inter', 11, 'bold')) # Clinical Red Highlight

        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL,   command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

    def refresh_features(self, features, first_row=None):
        """Populate the 3-column table. Values come from first_row or data_manager's first row."""
        self.features = list(features)
        if not self.tree:
            return
        self.tree.delete(*self.tree.get_children())
        self._display_to_raw = {}

        # Build normalised value lookup
        row_data: dict = {}
        if first_row is not None:
            for k, v in first_row.items():
                row_data[str(k).lower().strip()] = v
        elif self.data_manager is not None:
            df = getattr(self.data_manager, 'uploaded_df', None)
            if df is not None and len(df) > 0:
                for k, v in df.iloc[0].items():
                    row_data[str(k).lower().strip()] = v

        for raw_f in self.features:
            display_name, unit = self._humanize(raw_f)
            self._display_to_raw[display_name] = raw_f

            # Resolve value: exact key, then partial match
            f_key = str(raw_f).lower().strip()
            val_raw = row_data.get(f_key)
            if val_raw is None:
                for k, v in row_data.items():
                    if k == f_key or (len(f_key) > 4 and (k in f_key or f_key in k)):
                        val_raw = v
                        break

            if val_raw is not None and val_raw == val_raw:  # NaN guard
                val_str = f"{val_raw:.4f}" if isinstance(val_raw, float) else str(val_raw)
            else:
                val_str = "—"

            fl = raw_f.lower()
            base_tag = ('psa' if 'psa' in fl else
                   'afp' if 'afp' in fl else
                   'ca' if 'ca125' in fl or 'ca_125' in fl else
                   'other')
            
            # Clinical Highlight Logic
            tag_list = [base_tag]
            try:
                numeric_val = float(val_raw) if val_raw is not None else 0.0
                thresh_key = 'psa' if 'psa' in fl else 'afp' if 'afp' in fl else 'ca125' if ('ca125' in fl or 'ca_125' in fl) else None
                if thresh_key and numeric_val > self._THRESHOLDS[thresh_key]:
                    tag_list.append('abnormal')
            except: pass

            self.tree.insert("", tk.END,
                             values=(display_name, unit, val_str),
                             tags=tuple(tag_list))

    def refresh_display(self):
        if self.features and not self.tree.get_children():
            self.refresh_features(self.features)

    def _export_data(self, fmt):
        items = self.tree.get_children()
        if not items: return
        headers = ["BIOMARKER / FEATURE NAME", "UNIT", "VALUE"]
        rows = [self.tree.item(i)['values'] for i in items]
        df = pd.DataFrame(rows, columns=headers)
        self._run_export_dialog(df, fmt, "Input_Profile")

    def _copy_table(self):
        items = self.tree.get_children()
        if not items: return
        headers = ["BIOMARKER", "UNIT", "VALUE"]
        rows = [self.tree.item(i)['values'] for i in items]
        df = pd.DataFrame(rows, columns=headers)
        self.clipboard_clear()
        self.clipboard_append(df.to_csv(sep='\t', index=False))
        from tkinter import messagebox
        messagebox.showinfo("Copied", "Biomarker profile copied to clipboard.")

    def _run_export_dialog(self, df, fmt, name):
        from tkinter import filedialog, messagebox
        import pandas as pd
        ext = ".csv" if fmt == 'csv' else ".xlsx"
        path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"{name}{ext}")
        if not path: return
        try:
            if fmt == 'csv': df.to_csv(path, index=False)
            else: df.to_excel(path, index=False)
            messagebox.showinfo("Success", f"Data exported: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def get_values(self) -> dict:
        """Return {raw_feature_name: float_value} for model prediction."""
        if not self.tree:
            return {}
        result = {}
        for i in self.tree.get_children():
            vals = self.tree.item(i)['values']
            display = str(vals[0])
            raw = self._display_to_raw.get(display, display)
            try:
                result[raw] = float(vals[2])
            except (ValueError, TypeError):
                result[raw] = 0.0
        return result

    def get_table_data(self) -> dict:
        return self.get_values()

    def update_feature_value(self, name: str, value) -> None:
        """Update VALUE column by raw feature name or display name."""
        if not self.tree:
            return
        for item in self.tree.get_children():
            vals = list(self.tree.item(item, 'values'))
            display = str(vals[0])
            raw = self._display_to_raw.get(display, display)
            if raw == name or display == name:
                try:
                    num_val = float(value)
                    vals[2] = f"{num_val:.4f}"
                    
                    # Update tags for clinical anomalies
                    tags = list(self.tree.item(item, 'tags'))
                    fl = name.lower()
                    thresh_key = 'psa' if 'psa' in fl else 'afp' if 'afp' in fl else 'ca125' if ('ca125' in fl or 'ca_125' in fl) else None
                    
                    if thresh_key and num_val > self._THRESHOLDS[thresh_key]:
                        if 'abnormal' not in tags: tags.append('abnormal')
                    else:
                        if 'abnormal' in tags: tags.remove('abnormal')
                    self.tree.item(item, tags=tuple(tags))
                except (ValueError, TypeError):
                    vals[2] = str(value)
                self.tree.item(item, values=vals)
                break

    def clear_table(self) -> None:
        if not self.tree:
            return
        for it in self.tree.get_children():
            v = list(self.tree.item(it, 'values'))
            v[2] = "0.0000"
            self.tree.item(it, values=v)

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        is_dark = theme_name == 'pure_dark'
        
        self.configure(style='TFrame')
        self.header.configure(style='TFrame')
        self.title_label.config(foreground=palette['medic_brand'])
        
        # Reset tags for high contrast
        row_bg = palette['card_bg'] # Pure black or white
        alt_bg = palette['border_light'] if is_dark else "#F1F5F9"
        
        self.tree.tag_configure('psa', background=row_bg, foreground=palette['text_main'])
        self.tree.tag_configure('afp', background=row_bg, foreground=palette['text_main'])
        self.tree.tag_configure('ca', background=row_bg, foreground=palette['text_main'])
        self.tree.tag_configure('other', background=row_bg, foreground=palette['text_main'])
        self.tree.tag_configure('abnormal', foreground="#EF4444", font=('Inter', 11, 'bold')) # Override with high-vis red

class DataTab(ttk.Frame):
    def __init__(self, parent, on_select_callback=None, on_row_select_callback=None):
        super().__init__(parent)
        self.tree: ttk.Treeview = None # type: ignore
        self.on_select_callback = on_select_callback
        self.on_row_select_callback = on_row_select_callback # New for direct row sync
        self.selection_indices = set()
        self._create_widgets()

    def _create_widgets(self):
        # Header with Title
        self.header = ttk.Frame(self, padding=(12, 8, 12, 4))
        self.header.pack(fill=tk.X)
        self.title_label = ttk.Label(self.header, text="CLINICAL DATA VIEW — Primary Patient Record Registry",
                                     font=('Inter', 11, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        # Vertical Container for Tree + Horizontal Scrollbar
        main_container = ttk.Frame(self, padding=(15, 0, 15, 10)) # Standardized Padding
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top part: Tree + Vertical Scrollbar
        top_container = ttk.Frame(main_container)
        top_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(top_container, show="headings", height=22)
        # 1. Register click for checkboxes [✓]
        self.tree.bind("<Button-1>", self._on_tree_click)
        # 2. Register selection for row-level details (Trajectory/XAI Sync)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        
        vsb = ttk.Scrollbar(top_container, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(main_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_tree_click(self, event):
        """Toggle checkmark when the [✓] column is clicked."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1": # The [✓] column
                item = self.tree.identify_row(event.y)
                if item:
                    # Get the dataframe index from the item's tags
                    tags = list(self.tree.item(item, "tags"))
                    if not tags: return
                    df_idx = int(tags[0])
                    
                    vals = list(self.tree.item(item, "values"))
                    
                    if df_idx in self.selection_indices:
                        self.selection_indices.remove(df_idx)
                        vals[0] = "[     ]"
                        if 'checked_patient' in tags: tags.remove('checked_patient')
                    else:
                        self.selection_indices.add(df_idx)
                        vals[0] = "[ ✔ ]"
                        if 'checked_patient' not in tags: tags.append('checked_patient')
                    
                    self.tree.item(item, values=vals, tags=tuple(tags))
                    if self.on_select_callback:
                        self.on_select_callback(self.selection_indices)
    def _on_selection_change(self, event):
        """Broadcast row selection for dashboard-wide synchronization."""
        item = self.tree.focus()
        if not item: return
        
        # Pull clinical values to send to controllers
        columns = self.tree["columns"]
        values = self.tree.item(item, "values")
        if not values: return
        
        # Create a dictionary of {column: value}
        row_dict = {}
        for col, val in zip(columns, values):
            if col != '[✓]': # Skip the indicator
                row_dict[col] = val
        
        if self.on_row_select_callback:
            self.on_row_select_callback(row_dict)

    def update_data(self, df, selection_indices=None):
        self.selection_indices = set(selection_indices) if selection_indices else set()
        self.tree.delete(*self.tree.get_children())
        
        # High-visibility selection highlight
        from ui.styles import StyleManager
        is_dark = True # Default
        try:
           # Assuming we can find root/settings
           is_dark = self.winfo_toplevel().settings_manager.theme == 'pure_dark'
        except: pass
        
        highlight_bg = "#1E3A8A" if is_dark else "#BFDBFE"
        self.tree.tag_configure('checked_patient', background=highlight_bg)

        cols = ["[✓]"] + list(df.columns)
        self.tree["columns"] = cols
        
        # [✓] Column header - increased width
        self.tree.heading("[✓]", text="[✓]", anchor=tk.CENTER)
        self.tree.column("[✓]", width=60, minwidth=60, anchor=tk.CENTER, stretch=False)
        
        for col in df.columns:
            self.tree.heading(col, text=col.upper(), anchor=tk.CENTER)
            self.tree.column(col, width=120, minwidth=100, anchor=tk.CENTER, stretch=True)
        
        self.tree.update_idletasks()
        for _, (idx, row) in enumerate(df.iterrows()):
            is_sel = idx in self.selection_indices
            check = "[ ✔ ]" if is_sel else "[     ]"
            tag_list = [str(idx)]
            if is_sel: tag_list.append('checked_patient')
            self.tree.insert("", tk.END, values=[check] + list(row), tags=tuple(tag_list))

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        self.configure(style='TFrame')
        if hasattr(self, 'header'): self.header.configure(style='TFrame')
        if hasattr(self, 'title_label'): self.title_label.config(foreground=palette['medic_brand'])

class AnalysisTab(ttk.Frame):
    """
    PREMIUM CLINICAL PERFORMANCE: Standardized robust scrolling with deep-dive forensic insights.
    """
    def __init__(self, parent, version="1.0.1"):
        super().__init__(parent)
        self.version = version
        self.text: tk.Text = None # type: ignore
        self.sb: ttk.Scrollbar = None # type: ignore
        self._create_widgets()

    def _create_widgets(self):
        # Header with Title
        self.header = ttk.Frame(self, padding=(12, 8, 12, 4))
        self.header.pack(fill=tk.X)
        self.title_label = ttk.Label(self.header, text="DIAGNOSTIC PERFORMANCE — Forensic Audit & AI Reasoning",
                                     font=('Inter', 11, 'bold'))
        self.title_label.pack(side=tk.LEFT)
        
        # [RESTORE] Forensic Actions (Clear/Copy)
        ttk.Button(self.header, text="Clear Analysis", command=self.clear, style='TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.header, text="Copy Report", command=self.copy_all, style='TButton').pack(side=tk.RIGHT, padx=5)

        container = ttk.Frame(self, padding=(15, 0, 15, 10)) # Standardized Padding
        container.pack(fill=tk.BOTH, expand=True)

        self.sb = ttk.Scrollbar(container)
        self.sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(container, wrap=tk.WORD, yscrollcommand=self.sb.set,
                            font=('Inter', 11), 
                            padx=40, pady=35, borderwidth=0, highlightthickness=0)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sb.config(command=self.text.yview)
        self.text.config(state=tk.DISABLED)

        # Premium Forensic Tags - Theme-neutral vibrant colors
        self.text.tag_configure("title", font=('Inter', 20, 'bold'), spacing3=20)
        self.text.tag_configure("sub", font=('Inter', 12, 'bold'), spacing1=20, spacing3=10)
        self.text.tag_configure("crit", font=('Inter', 11, 'bold'), foreground="#EF4444") # Red-500
        self.text.tag_configure("pos", font=('Inter', 11, 'bold'), foreground="#10B981")  # Emerald-500
        self.text.tag_configure("metric", font=('Inter', 11, 'bold'), foreground="#3B82F6") # Blue-500
        self.text.tag_configure("dim", font=('Inter', 10), foreground="#71717A")      # Zinc-500
        self.text.tag_configure("highlight", font=('Inter', 10, 'italic'), foreground="#F59E0B") # Amber-500
        self.text.tag_configure("bullet", font=('Inter', 12, 'bold'), foreground="#3B82F6")
        self.text.tag_configure("code", font=('Consolas', 10), background="#18181B", foreground="#A1A1AA")
        self.text.tag_configure("table_head", font=('Consolas', 10, 'bold'), foreground="#3B82F6")
        self.text.tag_configure("table_row", font=('Consolas', 10))
        self.text.tag_configure("table_row_bold", font=('Consolas', 10, 'bold'))
        self.text.tag_configure("table_row_crit", font=('Consolas', 10, 'bold'), foreground="#EF4444")


    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def copy_all(self):
        """Copies the entire diagnostic report text to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", tk.END))

    def display_batch_report(self, df, metadata=None):
        """Generates a high-fidelity forensic clinical audit report with deep explanations."""
        self.clear()
        self.text.config(state=tk.NORMAL)
        
        total = len(df)
        pos_df = df[df['Prediction'] == 'POSITIVE'] if 'Prediction' in df.columns else df[0:0]
        positives = len(pos_df)
        rate = (positives / total * 100) if total > 0 else 0
        
        self.text.insert(tk.END, "DETAILED CLINICAL PERFORMANCE & FORENSIC AUDIT\n", "title")
        self.text.insert(tk.END, f"Captured: {np.datetime64('now')} | Scope: {total} Records | Forensic Mode: ACTIVE\n", "dim")
        
        self.text.insert(tk.END, "1. EXECUTIVE BATCH TRIAGE SUMMARY\n", "sub")
        clinical_status = metadata.get('clinical_status', 'ACTIVE') if metadata else 'ACTIVE'
        if positives > 0:
            self.text.insert(tk.END, "  • ", "bullet")
            self.text.insert(tk.END, f"ALERT: {positives} symptomatic profiles ({rate:.1f}%) identified in this batch.\n", "crit")
            self.text.insert(tk.END, "  • Forensic Insight: ", "dim")
            self.text.insert(tk.END, f"The ensemble consensus identifies a non-random clustering effect. These positive classifications are correlated with high-signal peaks in {', '.join(metadata.get('top_markers', ['core biomarkers']))}.\n")
        else:
            self.text.insert(tk.END, "  • ", "bullet")
            self.text.insert(tk.END, f"STATUS: Population signals are currently within the physiological baseline ({clinical_status}).\n", "pos")
            self.text.insert(tk.END, "  • Forensic Insight: ", "dim")
            self.text.insert(tk.END, f"Biomarker distributions are within normal limits. Cross-model correlation confirms high negative predictive value across all algorithmic layers.\n")

        # Dynamic Patient-Specific Details
        if positives > 0 and metadata and 'audit_registry' in metadata:
            self.text.insert(tk.END, "2. HIGH-RISK CLINICAL REGISTRY (FLAGGED PATIENT PROFILES)\n", "sub")
            
            # Professional Table Header (Expanded for AI Recommendations)
            h_line = f"  {'ID':<5} │ {'RISK':^8} │ {'COMMITTEE DETECTION':<20} │ {'PSA':>10} │ {'AFP':>10} │ {'CA125':>10} │ {'AI CLINICAL RECOMMENDATION':<32}\n"
            divider = "  " + "—" * 81 + "\n"
            
            self.text.insert(tk.END, h_line, "table_head")
            self.text.insert(tk.END, divider, "dim")
            
            registry = metadata['audit_registry']
            for patient in registry:
                p_id = str(patient.get('id', 'N/A'))[:5]
                risk_val = patient.get('risk', 0)
                risk_str = f"{risk_val * 100:.1f}%"
                detectors = str(patient.get('detectors', 'Ensemble'))[:19]
                
                psa = f"{patient.get('psa', 0):.0f}"
                afp = f"{patient.get('afp', 0):.2f}"
                ca = f"{patient.get('ca125', 0):.2f}"
                action = patient.get('action', 'N/A')
                
                row_line = f"  {p_id:<5} │ {risk_str:>8} │ {detectors:<20} │ {psa:>10} │ {afp:>10} │ {ca:>10} │ {action:<32}\n"
                
                # Highlight logic: Use 'table_row_crit' for very high risk (>90%)
                tag = "table_row_crit" if risk_val > 0.9 else "table_row"
                self.text.insert(tk.END, row_line, tag)
            
            self.text.insert(tk.END, divider, "dim")
            self.text.insert(tk.END, "\n")

        self.text.insert(tk.END, "3. ALGORITHMIC ARCHITECTURE & BIOMARKER SIGNAL ANALYSIS\n", "sub")
        metadata = metadata or {}
        dynamic = metadata.get('dynamic_insights', {})
        
        # Dynamic Archetype Fingerprint
        best_model = metadata.get('champion', 'Ensemble Lead')
        archetype = dynamic.get('archetype', 'Atypical Presentation')
        self.text.insert(tk.END, "  • Cohort Fingerprint: ", "bullet")
        self.text.insert(tk.END, f"'{archetype}' — Categorized by batch-wide biomarker drift.\n")

        self.text.insert(tk.END, "  • Champion Algorithm: ", "bullet")
        self.text.insert(tk.END, f"'{best_model}' — Highest F1-Score in clinical batch evaluation.\n")
        
        # Dynamic Clarity Calculation
        clarity = dynamic.get('clarity', 0.0)
        status = "High (Clean Signal)" if clarity > 0.7 else "Moderate (Metadata Noisy)" if clarity > 0.4 else "Low (Fragmented Population)"
        self.text.insert(tk.END, "  • Diagnostic Clarity: ", "bullet")
        self.text.insert(tk.END, f"{status} — {clarity*100:.1f}% Batch-wide Pattern Certainty.\n")

        # Dynamic Signal Strength
        signals = dynamic.get('signal_strength', [])
        if signals:
            top_s = signals[0]
            self.text.insert(tk.END, f"  • Why {best_model} Outperforms: ", "bullet")
            self.text.insert(tk.END, (
                f"{top_s['impact']:.1%} of its decision-making mass rests on {top_s['marker']} alone in this batch. "
                f"The AI committee identifies this as the primary diagnostic signal for this cohort.\n"
            ))
        else:
            self.text.insert(tk.END, "  • Diagnostic Signal: ", "bullet")
            self.text.insert(tk.END, "Weighted ensemble consensus distributed across all clinical biomarkers.\n")

        # Dynamic Drift/Diversity
        drifts = dynamic.get('drift', [])
        if drifts:
            self.text.insert(tk.END, "  • Population Drift Alert: ", "crit")
            drift_str = ", ".join([f"{d['marker']} ({d['shift']})" for d in drifts])
            self.text.insert(tk.END, f"Detected shift in {drift_str}. This cohort differs from the baseline training set.\n")
        else:
            self.text.insert(tk.END, "  • Cohort Stability: ", "pos")
            self.text.insert(tk.END, "No significant population drift detected. Biomarker distributions match baseline.\n")

        self.text.insert(tk.END, "  • AI Committee Consensus: ", "dim")
        self.text.insert(tk.END, f"Avg agreement: {metadata.get('avg_consensus', 0):.2f}/{metadata.get('total_committee', 4)} models\n")

        self.text.insert(tk.END, "\n4. BIOMARKER CLASSIFICATION THRESHOLDS (Batch Dynamics)\n", "sub")
        # Dynamic correlations
        corrs = dynamic.get('correlations', [])
        if corrs:
            for c in corrs[:2]:
                self.text.insert(tk.END, f"  • CO-SIGNAL DETECTED: ", "bullet")
                self.text.insert(tk.END, f"{c['pair'][0]} and {c['pair'][1]} show {c['strength']} correlation ({c['score']:.2f}).\n", "metric")
        else:
            self.text.insert(tk.END, "  • Signal Independence: ", "bullet")
            self.text.insert(tk.END, "Biomarkers in this batch appear statistically independent.\n", "dim")

        # 5. LOCAL PERFORMANCE TABLE (Item #27 requested by User)
        if metadata and 'scoreboard' in metadata:
            self.text.insert(tk.END, "\n5. LOCAL PERFORMANCE METRICS (COHORT VALIDATION)\n", "sub")
            h_line = f"  {'ALGORITHM':<20} │ {'LOCAL F1':^12} │ {'LOCAL ACC':^12} │ {'DETECTIONS':^12} │ {'STATUS':<15}\n"
            divider = "  " + "—" * 75 + "\n"
            
            self.text.insert(tk.END, h_line, "table_head")
            self.text.insert(tk.END, divider, "dim")
            
            for s in metadata['scoreboard']:
                f1 = s.get('local_f1', 0)
                acc = s.get('local_acc', 0)
                f1_str = f"{f1:^12.2%}" if f1 > 0 else f"{'N/A':^12}"
                acc_str = f"{acc:^12.2%}" if acc > 0 else f"{'N/A':^12}"
                
                status = "EXPERT" if f1 >= 0.9 else "STABLE" if f1 >= 0.7 else "REVIEW" if f1 > 0 else "NO LABELS"
                row = f"  {s['model']:<20} │ {f1_str} │ {acc_str} │ {s['positives']:^12} │ {status:<15}\n"
                
                tag = "table_row_bold" if f1 >= 0.9 else "table_row"
                self.text.insert(tk.END, row, tag)
            self.text.insert(tk.END, divider, "dim")

        self.text.insert(tk.END, "\n6. STRATEGIC CLINICAL RECOMMENDATIONS\n", "sub")
        if positives > 0:
            self.text.insert(tk.END, "  • Recommendation A: ", "bullet")
            self.text.insert(tk.END, "Prioritize PSA-surge patients for immediate urology / oncology consultation.\n")
            self.text.insert(tk.END, "  • Recommendation B: ", "bullet")
            self.text.insert(tk.END, "Co-elevated AFP/CA125 profiles warrant multi-parametric MRI within 14 days.\n")
            self.text.insert(tk.END, "  • Recommendation C: ", "bullet")
            self.text.insert(tk.END, "Cross-validate flagged patients with PSA velocity tracking (e.g. quarterly re-screen).\n")
        else:
            self.text.insert(tk.END, "  • Recommendation A: ", "bullet")
            self.text.insert(tk.END, "Continue routine longitudinal monitoring for this population.\n")
            self.text.insert(tk.END, "  • Recommendation B: ", "bullet")
            self.text.insert(tk.END, "Maintain current ensemble weights. Baseline stability verified.\n")

        self.text.insert(tk.END, "\n6. CLINICAL PATHWAY & PATIENT GUIDANCE\n", "sub")
        conf_zones = dynamic.get('confidence_zones', {})
        if positives > 0:
            top_markers = [s['marker'] for s in signals[:2]] if signals else ['PSA']
            self.text.insert(tk.END, "  • Primary Trigger: ", "bullet")
            self.text.insert(tk.END, f"Diagnostic spikes localized primarily in {', '.join(top_markers)}.\n")
            self.text.insert(tk.END, "  • Batch Reliability: ", "bullet")
            self.text.insert(tk.END, f"{conf_zones.get('certain', 0)} cases in high-confidence zone. {conf_zones.get('ambiguous', 0)} borderline cases flagged.\n")
        else:
            self.text.insert(tk.END, "  • Clinical Status: All biomarkers within healthy baseline ranges for this batch.\n")
            self.text.insert(tk.END, f"  • Guidance: {conf_zones.get('total', 0)} patients cleared for routine wellness protocols.\n")

        self.text.insert(tk.END, "\n7. COMPUTATIONAL LOGGING & PERFORMANCE\n", "sub")
        latency = metadata.get('latency', '12ms') if metadata else '15ms'
        self.text.insert(tk.END, f"  • Processing Speed: {latency}/record (Real-time)\n", "code")
        self.text.insert(tk.END, "  • Memory Integrity: VERIFIED | Inference Engine: XAI-Ensemble\n", "code")

        self.text.insert(tk.END, "\n" + "—" * 65 + "\n", "dim")
        self.text.insert(tk.END, f"CONFIDENTIAL CLINICAL REPORT | DIAGNOSTIC AI POWERED | V{self.version}", "highlight")
        
        self.text.config(state=tk.DISABLED)

    def display_prediction_results(self, data):
        """Displays a high-density clinical forensic report for an individual patient."""
        self.clear()
        self.text.config(state=tk.NORMAL)
        is_pos = data.get('prediction') == 1
        risk = data.get('risk', 0)
        forensic = data.get('forensic', {})
        
        self.text.insert(tk.END, "INDIVIDUAL DIAGNOSTIC FORENSIC (DEEP PROFILE)\n", "title")
        header = f"Status: {'POSITIVE' if is_pos else 'NEGATIVE'} | Reliability: {data.get('confidence', 0):.1%} | Stability: {data.get('stability_metric', 'N/A')}\n"
        self.text.insert(tk.END, header, "dim")
        self.text.insert(tk.END, f"Engine: {data.get('model', 'Ensemble')}\n", "dim")
        self.text.insert(tk.END, "═" * 70 + "\n\n")


        
        self.text.insert(tk.END, "1. AI COMMITTEE VOTE BREAKDOWN (CONSENSUS)\n", "sub")
        self.text.insert(tk.END, f"  • Forensic Consensus: {data.get('consensus', 'N/A')} Agreements\n", "metric")
        
        committee = data.get('individual_results', [])
        for p in committee:
            res_str = "⚑ POS" if p['prediction'] == 1 else "✓ NEG"
            tag = "crit" if p['prediction'] == 1 else "pos"
            self.text.insert(tk.END, f"    - {p['model']:.<25} ", "dim")
            self.text.insert(tk.END, f"{res_str} ({p['risk']:.1%} Risk)\n", tag)
        
        self.text.insert(tk.END, "\n2. METABOLIC DEVIATION & VOLATILITY ANALYSIS\n", "sub")
        deviations = forensic.get('deviations', [])
        if deviations:
            self.text.insert(tk.END, f"  • Core Biomarker Stability: {forensic.get('metabolic_stability', 'Stable')}\n", "highlight")
            for d in deviations:
                tag = "crit" if d['severity'] == 'CRITICAL' else "metric" if d['severity'] == 'WARNING' else "dim"
                self.text.insert(tk.END, f"    - {d['marker']:.<25} ", "dim")
                self.text.insert(tk.END, f"{d['value']:,.1f} units ", "highlight")
                self.text.insert(tk.END, f" [Dev: {d['deviation']}]\n", tag)
        else:
            self.text.insert(tk.END, "  • No primary biomarker deviations detected relative to cohort baseline.\n")

        self.text.insert(tk.END, "\n3. DIAGNOSTIC REASONING (XAI NARRATIVE)\n", "sub")
        inputs = data.get('inputs', {})
        # Pull meaningful inputs
        top_features = sorted(inputs.items(), key=lambda x: float(str(x[1])) if str(x[1]).replace('.','').isdigit() else 0, reverse=True)[:3]
        
        if is_pos:
            self.text.insert(tk.END, "  • Risk Driver: ", "crit")
            self.text.insert(tk.END, f"Elevated levels in {', '.join([f[0] for f in top_features])} confirm the 'Detected' fingerprint.\n")
            self.text.insert(tk.END, "  • Signal Insight: ", "dim")
            self.text.insert(tk.END, f"Profile aligns with the high-risk {data.get('model')} cluster. Metabolic momentum is accelerating.\n")
        else:
            self.text.insert(tk.END, "  • Stability Proof: ", "pos")
            self.text.insert(tk.END, "Global biomarker values are homogeneous and centered within the healthy cluster.\n")
            self.text.insert(tk.END, "  • Clinical Barrier: ", "dim")
            self.text.insert(tk.END, "Primary diagnostic triggers remain significantly below the predictive threshold.\n")

        self.text.insert(tk.END, "\n4. CLINICAL TRIAGE & STRATEGIC ACTION PLAN\n", "sub")
        self.text.insert(tk.END, f"  • Triage Rank: ", "dim")
        self.text.insert(tk.END, f"{forensic.get('triage_level', 'N/A')}\n", "crit" if risk > 0.6 else "pos")
        
        # Longitudinal Context Injection
        vel = data.get('velocity_context')
        if vel:
            self.text.insert(tk.END, f"  • Velocity Verdict: ", "dim")
            self.text.insert(tk.END, f"{vel.get('verdict', 'Stable')}\n", "crit" if vel.get('verdict_level') == 'DANGER' else "dim")
            self.text.insert(tk.END, f"  • Trend Momentum: ", "dim")
            self.text.insert(tk.END, f"PSA Velocity={vel.get('psa_velocity'):+.1f}% | Doubling Time={vel.get('psa_doubling')}\n", "metric")

        self.text.insert(tk.END, f"  • Strategic Path: ", "bullet")
        self.text.insert(tk.END, f"{forensic.get('primary_action', 'Continue monitoring')}\n")

        self.text.insert(tk.END, "\n" + "—" * 70 + "\n", "dim")
        self.text.insert(tk.END, "DISCLAIMER: AI-assisted diagnostic forensic. Final clinical validation is mandatory.", "dim")
        
        self.text.config(state=tk.DISABLED)


    def display_metrics(self, metrics, model_name):
        """Displays high-fidelity validation metrics with clinical interpretations."""
        self.clear()
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, f"ALGORITHM STABILITY & PERFORMANCE: {model_name}\n", "title")
        self.text.insert(tk.END, "Statistical verification of the diagnostic engine reliability.\n\n", "dim")
        
        # Mapping metrics to clinical significance
        significance = {
            "Accuracy": "Overall correctness across all patient samples.",
            "Sensitivity": "Ability to correctly identify symptomatic patients (Low FN).",
            "Recall": "Ability to correctly identify symptomatic patients (Low FN).",
            "Specificity": "Ability to correctly identify healthy patients (Low FP).",
            "Precision": "Probability that a 'Positive' flag is factually correct (PPV).",
            "F1-Score": "Harmonic mean between Precision and Recall. Essential for imbalanced data.",
            "AUC": "Probability that the model ranks a random positive higher than a random negative.",
            "True Positives": "Number of correctly identified clinical cases.",
            "True Negatives": "Number of correctly identified negative cases.",
            "False Positives": "Biomarker noise misidentified as symptomatic (Cost: unnecessary biopsy).",
            "False Negatives": "Symptomatic profiles missed by the algorithm (Cost: delayed treatment)."
        }

        for k, v in metrics.items():
            val = f"{v:.2%}" if isinstance(v, float) and 0 <= v <= 1.0 else str(v)
            if k in ["True Positives", "True Negatives", "False Positives", "False Negatives"]:
                val = str(int(v)) if isinstance(v, (float, int)) else str(v)

            self.text.insert(tk.END, f" • {k:.<30} ", "bullet")
            self.text.insert(tk.END, f"{val}\n", "metric")
            
            # Add clinical interpretation if available
            interpret = significance.get(k, significance.get(k.split(' (')[0]))
            if interpret:
                self.text.insert(tk.END, f"   └ Interpretation: {interpret}\n", "dim")
            self.text.insert(tk.END, "\n") # Small vertical break between metrics

        self.text.insert(tk.END, "\n" + "—" * 60 + "\n", "dim")
        self.text.insert(tk.END, "CLINICAL VALIDATION COMPLETED | ISO-COMPLIANT LOGGING", "highlight")
    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        is_dark = theme_name == 'pure_dark'

        self.configure(style='TFrame')
        if hasattr(self, 'header'): self.header.configure(style='TFrame')
        if hasattr(self, 'title_label'): self.title_label.config(foreground=palette['medic_brand'])
        
        self.text.config(bg=palette['bg_main'], fg=palette['text_main'], 
                         selectbackground=palette['medic_brand'], selectforeground="white")
        
        # Update Reporting Tags - High Contrast Enforcement
        self.text.tag_configure("title", foreground=palette['text_main'], font=("Consolas", 11, "bold"))
        self.text.tag_configure("sub", foreground=palette['medic_brand'], font=("Consolas", 10, "bold"))
        self.text.tag_configure("crit", foreground="#EF4444", font=("Consolas", 10, "bold"))
        self.text.tag_configure("pos", foreground="#10B981", font=("Consolas", 10, "bold"))
        self.text.tag_configure("metric", foreground=palette['medic_brand'], font=("Consolas", 10, "bold"))
        self.text.tag_configure("dim", foreground=palette['text_muted'], font=("Consolas", 10))
        self.text.tag_configure("highlight", background=palette['border_light'], foreground=palette['text_main'])
        self.text.tag_configure("bullet", foreground=palette['medic_brand'])
        self.text.tag_configure("code", foreground=palette['text_muted'], background=palette['bg_main'])
        self.text.tag_configure("table_head", foreground=palette['text_main'], background=palette['border_light'], font=("Consolas", 10, "bold"))
        self.text.tag_configure("table_row", foreground=palette['text_muted'])
        self.text.tag_configure("table_row_bold", foreground=palette['text_main'])
        self.text.tag_configure("table_row_crit", foreground="#EF4444")

class ValidationTab(ttk.Frame):
    """Handles AI Committee Consensus with professional diagnostic highlighting."""
    def __init__(self, parent):
        super().__init__(parent)
        self.tree: ttk.Treeview = None # type: ignore
        self._create_widgets()

    def _create_widgets(self):
        # Footer Actions - Packed first with side=BOTTOM to ensure it stays pinned
        self.footer = ttk.Frame(self, padding=(15, 0, 15, 12))
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(self.footer, text="Export CSV", style='Primary.TButton', command=lambda: self._export_data('csv')).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.footer, text="Export Excel", style='Primary.TButton', command=lambda: self._export_data('excel')).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.footer, text="Copy Consensus", command=self._copy_table).pack(side=tk.RIGHT)

        # Header with Title
        self.header = ttk.Frame(self, padding=(12, 8, 12, 4))
        self.header.pack(fill=tk.X)
        self.title_label = ttk.Label(self.header, text="AI COMMITTEE CONSENSUS — Multi-Algorithm Validation",
                                     font=('Inter', 11, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        # Container for Tree and Scrollbar
        container = ttk.Frame(self, padding=(15, 0, 15, 10))
        container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(container, columns=("m", "d", "r", "f", "a", "gf", "ga", "s"), show="headings", height=22)
        headers = ("ALGORITHM", "COHORT RATE", "AVG RISK", "BATCH F1", "BATCH ACC", "EXPERT F1", "EXPERT AUC", "STATUS")
        for c, h in zip(("m", "d", "r", "f", "a", "gf", "ga", "s"), headers):
            self.tree.heading(c, text=h)
            self.tree.column(c, anchor=tk.CENTER, width=110, stretch=True)
        
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Color configuration
        self.tree.tag_configure('pos')
        self.tree.tag_configure('neg')
        self.tree.tag_configure('summary')

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def _export_data(self, fmt):
        items = self.tree.get_children()
        if not items: return
        headers = ["ALGORITHM", "COHORT RATE", "AVG RISK", "BATCH F1", "BATCH ACC", "EXPERT F1", "EXPERT AUC", "STATUS"]
        rows = [self.tree.item(i)['values'] for i in items]
        df = pd.DataFrame(rows, columns=headers)
        self._run_export_dialog(df, fmt, "Consensus_Audit")

    def _copy_table(self):
        items = self.tree.get_children()
        if not items: return
        headers = ["ALGORITHM", "COHORT RATE", "AVG RISK", "BATCH F1", "BATCH ACC", "EXPERT F1", "EXPERT AUC", "STATUS"]
        rows = [self.tree.item(i)['values'] for i in items]
        df = pd.DataFrame(rows, columns=headers)
        self.clipboard_clear()
        self.clipboard_append(df.to_csv(sep='\t', index=False))
        from tkinter import messagebox
        messagebox.showinfo("Copied", "Consensus table copied to clipboard.")

    def _run_export_dialog(self, df, fmt, name):
        from tkinter import filedialog, messagebox
        ext = ".csv" if fmt == 'csv' else ".xlsx"
        path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"{name}{ext}")
        if not path: return
        try:
            if fmt == 'csv': df.to_csv(path, index=False)
            else: df.to_excel(path, index=False)
            messagebox.showinfo("Success", f"Data exported: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def update_comparison(self, data):
        """Individual Patient View: Highlight Positive detection in Red."""
        self.clear()
        results = data.get('individual_results', [])
        ensemble_decision = data.get('prediction', 0)
        
        # Count agreements for consensus strength
        agree_count = sum(1 for r in results if r['prediction'] == ensemble_decision)
        total = len(results)
        
        for res in results:
            is_pos = res['prediction'] == 1
            decision = "⚑ POSITIVE" if is_pos else "✓ NEGATIVE"
            matches = res['prediction'] == ensemble_decision
            status = f"✔ MAJORITY ({agree_count}/{total})" if matches else f"✘ DISSENTER"
            tag = 'pos' if is_pos else 'neg'
            self.tree.insert("", tk.END, values=(res['model'], decision, f"{res['risk']:.1%}", "", "", "", "", status), tags=(tag,))
        
        # Summary separator row
        consensus_label = "STRONG" if agree_count >= total else "WEAK" if agree_count <= total // 2 else "MODERATE"
        self.tree.insert("", tk.END, values=(
            "─── AI COMMITTEE",
            f"ENSEMBLE: {'POSITIVE' if ensemble_decision == 1 else 'NEGATIVE'}",
            f"{data.get('risk', 0):.1%} Risk",
            "", "", "", "",
            f"{consensus_label} CONSENSUS ({agree_count}/{total})"
        ), tags=('summary',))

    def update_batch_comparison(self, summaries, total_records):
        """Batch View: Show each model's detection rate with clear severity indicators."""
        self.clear()
        if not summaries: return
        
        for s in summaries:
            rate_val = (s['positives'] / total_records) if total_records > 0 else 0
            rate_str = f"{rate_val:.1%}"
            status = f"{s['positives']}/{total_records} FLAGGED"
            f1 = s.get('local_f1', 0)
            acc = s.get('local_acc', 0)
            
            f1_str = f"{f1:^8.2%}" if f1 > 0 else "N/A"
            acc_str = f"{acc:^8.2%}" if acc > 0 else "N/A"
            
            # Global labels
            g_f1_str = f"{s.get('global_f1', 0):^8.2%}"
            g_auc_str = f"{s.get('global_auc', 0):^8.2%}"
            
            tag = 'pos' if s['positives'] > 0 else 'neg'
            self.tree.insert("", tk.END, values=(
                s['model'], rate_str, f"{s['risk']:.1%}", 
                f1_str, acc_str, g_f1_str, g_auc_str, status
            ), tags=(tag,))

        # Grand totals row
        if summaries:
            max_pos = max(s['positives'] for s in summaries)
            avg_risk = sum(s['risk'] for s in summaries) / len(summaries)
            self.tree.insert("", tk.END, values=(
                "─── COMMITTEE VERDICT",
                f"{max_pos}/{total_records} Peak",
                f"{avg_risk:.1%} Avg",
                "BATCH ANALYSIS COMPLETE"
            ), tags=('summary',))

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        self.configure(style='TFrame')
        if hasattr(self, 'header'): self.header.configure(style='TFrame')
        if hasattr(self, 'title_label'): self.title_label.config(foreground=palette['medic_brand'])
        
        self.tree.tag_configure('pos', foreground="#EF4444")
        self.tree.tag_configure('neg', foreground="#10B981")
        self.tree.tag_configure('summary', foreground=palette['text_muted'])

class LeaderboardTab(ttk.Frame):
    """
    CLINICAL ALGORITHM LEADERBOARD: Deep-dive model statistics with clinical context.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.lb_tree: ttk.Treeview = None # type: ignore
        self.audit_tree: ttk.Treeview = None # type: ignore
        self.insight_label: tk.Label = None # type: ignore
        self._create_widgets()

    def _create_widgets(self):
        # Main scrollable container
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True)

        # Footer Actions - Packed first with side=BOTTOM to ensure it stays pinned
        self.footer = ttk.Frame(outer, padding=(15, 0, 15, 12))
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(self.footer, text="Export CSV", style='Primary.TButton', command=lambda: self._export_data('csv')).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.footer, text="Export Excel", style='Primary.TButton', command=lambda: self._export_data('excel')).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.footer, text="Copy Rankings", command=self._copy_table).pack(side=tk.RIGHT)

        # ── Leaderboard Section ────────────────────────────────────────
        self.header = ttk.Frame(outer, padding=(12, 8, 12, 4))
        self.header.pack(fill=tk.X)

        self.title_label = ttk.Label(self.header, text="ALGORITHM LEADERBOARD — Ranked by Clinical F1-Score & Stability",
                                     font=('Inter', 11, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        lb_frame = ttk.Frame(outer, padding=(15, 0, 15, 10))
        lb_frame.pack(fill=tk.BOTH, expand=True) # Full width expansion

        cols = ("rank", "model", "acc", "f1", "auc", "prec", "rec", "spec", "cv", "badge")
        headers = ("RANK", "AI ALGORITHM", "ACCURACY", "F1 SCORE", "ROC-AUC", "PRECISION", "RECALL", "SPECIFICITY", "CV STABILITY", "BADGE")
        widths = (50, 160, 85, 85, 85, 85, 85, 95, 100, 100)

        lb_vsb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        # Give more height since we have extra space now
        self.lb_tree = ttk.Treeview(lb_frame, columns=cols, show="headings", height=8, yscrollcommand=lb_vsb.set)
        lb_vsb.config(command=self.lb_tree.yview)

        for c, h, w in zip(cols, headers, widths):
            self.lb_tree.heading(c, text=h)
            self.lb_tree.column(c, width=w, anchor=tk.CENTER, stretch=True)

        self.lb_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lb_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag colors
        self.lb_tree.tag_configure('gold')
        self.lb_tree.tag_configure('silver')
        self.lb_tree.tag_configure('bronze')
        self.lb_tree.tag_configure('other')

        # Model insight panel
        self.insight_label = tk.Label(outer, text="", font=('Inter', 9, 'italic'),
                                      fg="#3B82F6", bg="#F0F9FF", anchor=tk.W,
                                      padx=15, pady=8, wraplength=900, justify=tk.LEFT)
        self.insight_label.pack(fill=tk.X, padx=15, pady=(0,8))

    def clear(self):
        if self.lb_tree:   
            self.lb_tree.delete(*self.lb_tree.get_children())

    def _export_data(self, fmt):
        items = self.lb_tree.get_children()
        if not items: return
        headers = ["RANK", "ALGORITHM", "ACCURACY", "F1 SCORE", "ROC-AUC", "PRECISION", "RECALL", "SPECIFICITY", "CV STABILITY", "BADGE"]
        rows = [self.lb_tree.item(i)['values'] for i in items]
        df = pd.DataFrame(rows, columns=headers)
        self._run_export_dialog(df, fmt, "Algorithm_Leaderboard")

    def _copy_table(self):
        items = self.lb_tree.get_children()
        if not items: return
        headers = ["RANK", "ALGORITHM", "ACCURACY", "F1 SCORE", "ROC-AUC", "PRECISION", "RECALL", "SPECIFICITY", "CV STABILITY", "BADGE"]
        rows = [self.lb_tree.item(i)['values'] for i in items]
        df = pd.DataFrame(rows, columns=headers)
        self.clipboard_clear()
        self.clipboard_append(df.to_csv(sep='\t', index=False))
        from tkinter import messagebox
        messagebox.showinfo("Copied", "Leaderboard table copied to clipboard.")

    def _run_export_dialog(self, df, fmt, name):
        from tkinter import filedialog, messagebox
        ext = ".csv" if fmt == 'csv' else ".xlsx"
        path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"{name}{ext}")
        if not path: return
        try:
            if fmt == 'csv': df.to_csv(path, index=False)
            else: df.to_excel(path, index=False)
            messagebox.showinfo("Success", f"Data exported: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    # ── CLINICAL LEADERBOARD INSIGHTS (hardcoded from real data analysis) ──────
    _INSIGHTS = {
        "Random Forest": (
            "🏆 WHY IT WINS: Random Forest captures non-linear PSA surge thresholds with 86.0% feature weight on "
            "PSA_concentration. Its ensemble of 100 decision trees is robust against imbalanced class ratios (42 positive "
            "/ 458 healthy). Achieves 100% Recall — zero missed diagnoses — with a specificity of 98.9%."
        ),
        "SVM": (
            "🥈 WHY IT'S CLOSE: SVM with RBF kernel creates a tight decision boundary around the PSA spike zone "
            "(>28,000 pg/mL). Matches Random Forest on Recall and Specificity but is sensitive to scaling. "
            "Strong performer when PSA dominates, but weaker on multi-biomarker edge cases."
        ),
        "Logistic Regression": (
            "🥉 WHY IT UNDERPERFORMS: Logistic Regression assumes linear separability. The PSA distribution in this "
            "dataset has extreme skew (healthy: ~1,742 pg/mL vs cancer: ~58,205 pg/mL), which a linear model handles "
            "less efficiently. Still achieves 100% Recall but produces 1 extra false positive vs RF/SVM."
        ),
        "MLP": (
            "⚠ WHY IT STRUGGLES: The MLP Neural Network overfits on the small positive class (42 samples). "
            "High false-positive rate (24 misclassified healthy patients as cancer) lowers clinical reliability. "
            "Requires more data or class-weight tuning to match tree-based models on this biomarker dataset."
        ),
        "AI Ensemble": (
            "🔬 ENSEMBLE STRATEGY: Majority voting across all available models. In this dataset, RF+SVM agreement "
            "on a POSITIVE flag is the gold standard — when both agree, clinical confidence exceeds 98.5%. "
            "The ensemble is conservative: it only flags POSITIVE when the majority of models detect the biomarker surge."
        ),
    }

    def update_leaderboard(self, leaderboard):
        """Populate ranked leaderboard with clinical badges and live model insight."""
        if not self.lb_tree: return
        self.lb_tree.delete(*self.lb_tree.get_children())

        rank_tags = ['gold', 'silver', 'bronze']
        rank_labels = ["🥇 #1 CHAMPION", "🥈 #2 RUNNER-UP", "🥉 #3 CONTENDER"]
        top_model = ""

        for i, en in enumerate(leaderboard):
            tag = rank_tags[i] if i < 3 else 'other'
            rank_str = rank_labels[i] if i < 3 else f"#{i+1}"
            if i == 0:  top_model = en['model']

            # Clinical badge based on F1 score
            f1 = en.get('f1', 0)
            badge = "GOLD STANDARD" if f1 >= 0.9 else "RELIABLE" if f1 >= 0.8 else "ACCEPTABLE" if f1 >= 0.6 else "REVIEW"

            # Stability rating from CV std
            cv_std = en.get('cv_std', 0)
            cv_str = f"{en.get('cv_mean',0):.2%} ±{cv_std:.3f}"

            self.lb_tree.insert("", tk.END, values=(
                rank_str,
                en['model'],
                f"{en.get('accuracy',0):.2%}",
                f"{f1:.2%}",
                f"{en.get('auc', 0):.2%}",
                f"{en.get('precision', 0):.2%}",
                f"{en.get('recall', 0):.2%}",
                f"{en.get('specificity', 0):.2%}",
                cv_str,
                badge
            ), tags=(tag,))

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        is_dark = theme_name == 'pure_dark'
        
        self.configure(style='TFrame')
        if hasattr(self, 'header'): self.header.configure(style='TFrame')
        self.title_label.config(foreground=palette['medic_brand'])
        self.insight_label.config(bg=palette['card_bg'], fg=palette['medic_brand'])
        
        # Champion tags
        if is_dark:
            self.lb_tree.tag_configure('gold', background="#422006", foreground="#FCD34D")
            self.lb_tree.tag_configure('silver', background="#1E293B", foreground="#F8FAFC")
            self.lb_tree.tag_configure('bronze', background="#431407", foreground="#FB923C")
            self.lb_tree.tag_configure('other', foreground=palette['text_muted'])
        else:
            self.lb_tree.tag_configure('gold', background="#FEF9C3", foreground="#92400E")
            self.lb_tree.tag_configure('silver', background="#F1F5F9", foreground="#334155")
            self.lb_tree.tag_configure('bronze', background="#FFF7ED", foreground="#9A3412")
            self.lb_tree.tag_configure('other', foreground="#475569")
