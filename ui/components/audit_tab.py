import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np

class AuditTab(ttk.Frame):
    """
    Clinical Audit & Discrepancy Tab.
    Focuses exclusively on identifying and explaining misclassifications between
    the AI ensemble and the Excel ground truth.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=tk.BOTH, expand=True)
        
        self.audit_df = None
        self.tree = None
        
        self._create_widgets()

    def _create_widgets(self):
        # Footer Actions - Packed first with side=BOTTOM to ensure it stays pinned
        self.footer = ttk.Frame(self, padding=(15, 0, 15, 15))
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.btn_csv = ttk.Button(self.footer, text="Export CSV", style='Primary.TButton', command=lambda: self._handle_export('csv'))
        self.btn_csv.pack(side=tk.LEFT, padx=5)
        
        self.btn_excel = ttk.Button(self.footer, text="Export Excel", style='Primary.TButton', command=lambda: self._handle_export('excel'))
        self.btn_excel.pack(side=tk.LEFT, padx=5)
        
        self.btn_copy = ttk.Button(self.footer, text="Copy Data", style='TButton', command=self._handle_copy)
        self.btn_copy.pack(side=tk.RIGHT)

        # Header
        header = ttk.Frame(self, padding=(15, 12, 15, 4))
        header.pack(fill=tk.X)
        self.title_label = ttk.Label(header, text="CLINICAL DISCREPANCY AUDIT — AI vs. Research Baseline", 
                                     font=('Inter', 12, 'bold'))
        self.title_label.pack(side=tk.LEFT)
        
        # Summary Row
        self.summary_frame = ttk.Frame(self, padding=(15, 0, 15, 10))
        self.summary_frame.pack(fill=tk.X)
        
        self.discrepancy_count = ttk.Label(self.summary_frame, text="Mismatches Detected: 0", font=('Inter', 10))
        self.discrepancy_count.pack(side=tk.LEFT, padx=(0, 20))
        
        self.accuracy_label = ttk.Label(self.summary_frame, text="Excel Alignment: 100.0%", font=('Inter', 10))
        self.accuracy_label.pack(side=tk.LEFT)

        # Table Container
        table_container = ttk.Frame(self, padding=15)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Columns: [ID, Biomarkers..., Ground Truth, AI Prediction, Risk, Discrepancy Type]
        columns = ("#1", "ID", "PSA", "AFP", "CA125", "Ground Truth", "AI Prediction", "Diff", "Risk", "Forensic Reasoning")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Audit.Treeview")
        
        self.tree.heading("ID", text="SAMPLE ID")
        self.tree.heading("PSA", text="PSA")
        self.tree.heading("AFP", text="AFP")
        self.tree.heading("CA125", text="CA125")
        self.tree.heading("Ground Truth", text="EXCEL LABEL")
        self.tree.heading("AI Prediction", text="AI VERDICT")
        self.tree.heading("Diff", text="DELTA")
        self.tree.heading("Risk", text="RISK %")
        self.tree.heading("Forensic Reasoning", text="AUDIT REASONING")

        # Column widths - DISABLE STRETCH to FORCE horizontal overflow
        self.tree.column("#1", width=0, stretch=tk.NO)
        self.tree.column("ID", width=120, stretch=tk.NO)
        self.tree.column("PSA", width=90, stretch=tk.NO)
        self.tree.column("AFP", width=90, stretch=tk.NO)
        self.tree.column("CA125", width=90, stretch=tk.NO)
        self.tree.column("Ground Truth", width=130, stretch=tk.NO)
        self.tree.column("AI Prediction", width=130, stretch=tk.NO)
        self.tree.column("Diff", width=80, stretch=tk.NO)
        self.tree.column("Risk", width=90, stretch=tk.NO)
        self.tree.column("Forensic Reasoning", width=600, stretch=tk.NO)

        # Scrollbars
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tag configuration for row highlighting
        self.tree.tag_configure('false_positive', background='#FEF2F2', foreground='#991B1B') # Light Red
        self.tree.tag_configure('false_negative', background='#FEFCE8', foreground='#854D0E') # Light Yellow (Warning)

    def refresh_theme(self, theme_name):
        from ui.styles import StyleManager
        palette = StyleManager.get_palette(theme_name)
        is_dark = theme_name == 'pure_dark'
        
        self.title_label.config(foreground=palette['medic_brand'])
        
        # Treeview styling
        style = ttk.Style()
        bg = palette['card_bg']
        fg = palette['text_main']
        sel_bg = palette['medic_brand']
        
        style.configure("Audit.Treeview", background=bg, foreground=fg, fieldbackground=bg, borderwidth=0)
        style.map("Audit.Treeview", background=[('selected', sel_bg)], foreground=[('selected', 'white')])
        
        if is_dark:
            # Dark mode adjustments for error visibility
            self.tree.tag_configure('false_positive', background='#450A0A', foreground='#FECACA')
            self.tree.tag_configure('false_negative', background='#422006', foreground='#FEF08A')
        else:
            self.tree.tag_configure('false_positive', background='#FEF2F2', foreground='#991B1B')
            self.tree.tag_configure('false_negative', background='#FEFCE8', foreground='#854D0E')

    def update_audit_data(self, df):
        """Filters the dataframe for mismatches and populates the audit table."""
        self.clear()
        
        if df is None or 'Prediction' not in df.columns or 'Prediction' not in df.columns:
            return

        # 1. Identify Ground Truth column
        gt_col = None
        for col in df.columns:
            c_low = str(col).lower()
            if any(k in c_low for k in ['truth', 'label', 'target', 'actual', 'verified', 'status', 'diagnosis', 'class', 'cancer', 'rish']):
                gt_col = col
                break
        
        if not gt_col:
            # Fallback to search for the first column with HEALTHY/DETECTED values that isn't the AI prediction
            for col in df.columns:
                if col in ['Prediction', 'GT_Norm', 'AI_Norm', 'Risk_Score']: continue
                vals = df[col].astype(str).str.upper().unique()
                if any(v in ['POSITIVE', 'NEGATIVE', 'HEALTHY', 'DETECTED', '1', '0'] for v in vals):
                    gt_col = col
                    break
        
        if not gt_col:
            self.accuracy_label.config(text="Excel Alignment: N/A (No Label)")
            return

        # 2. Normalize and compare
        df_copy = df.copy()
        df_copy['GT_Norm'] = df_copy[gt_col].astype(str).str.upper().str.strip()
        # Clean potential numeric labels
        df_copy['GT_Norm'] = df_copy['GT_Norm'].replace({'1': 'POSITIVE', '0': 'NEGATIVE', '1.0': 'POSITIVE', '0.0': 'NEGATIVE', 'TRUE': 'POSITIVE', 'FALSE': 'NEGATIVE'})
        
        df_copy['AI_Norm'] = df_copy['Prediction'].astype(str).str.upper().str.strip()
        
        # Filter for Mismatches
        mismatch_df = df_copy[df_copy['GT_Norm'] != df_copy['AI_Norm']].copy()
        
        # Add reasoning to df for export
        mismatch_df['Reasoning'] = mismatch_df.apply(
            lambda r: self._generate_reasoning(
                "FP" if (r['AI_Norm'] == 'POSITIVE' and r['GT_Norm'] == 'NEGATIVE') else "FN",
                r.get('Risk_Score', 0),
                r.get('PSA', 0), # Fallback to search if these keys aren't exact
                r.get('AFP', 0),
                r.get('CA125', 0)
            ), axis=1
        )
        self.audit_df = mismatch_df
        
        # 3. Update Labels
        count = len(mismatch_df)
        total = len(df)
        accuracy = ((total - count) / total * 100) if total > 0 else 100
        
        self.discrepancy_count.config(text=f"Mismatches Detected: {count}")
        self.accuracy_label.config(text=f"Excel Alignment: {accuracy:.1f}%")
        
        if count == 0:
            # Add a "Perfect Sync" row
            self.tree.insert("", "end", values=("", "SYSTEM STABLE", "---", "---", "---", "PERFECT", "SYNC", "0", "---", "All AI verdicts matches the research baseline exactly."))
            return

        # 4. Populate Table with Forensic Logic
        for idx, row in mismatch_df.iterrows():
            gt = row['GT_Norm']
            ai = row['AI_Norm']
            risk = row.get('Risk_Score', 0)
            
            # Type of error
            error_type = "FP" if (ai == 'POSITIVE' and gt == 'NEGATIVE') else "FN"
            tag = 'false_positive' if error_type == "FP" else 'false_negative'
            
            # Logic Inference
            def get_val(keywords):
                for col in df.columns:
                    if any(k in col.lower() for k in keywords):
                        return row[col]
                return 0.0

            psa = get_val(['psa'])
            afp = get_val(['afp'])
            ca125 = get_val(['ca_125', 'ca125'])
            
            reasoning = self._generate_reasoning(error_type, risk, psa, afp, ca125)
            
            self.tree.insert("", "end", values=(
                idx, idx, f"{psa:.1f}", f"{afp:.1f}", f"{ca125:.1f}", 
                gt, ai, error_type, f"{risk*100:.1f}%", reasoning
            ), tags=(tag,))

    def _generate_reasoning(self, error_type, risk, psa, afp, ca125):
        """Qualitative analysis of the mismatch."""
        if error_type == "FP":
            # False Positive - AI flagged it, but Excel said it's healthy
            if psa > 15000: return "Biomarker peak (PSA) triggered high-risk threshold unnecessarily."
            if risk > 0.8: return "Algorithm committee reached over-confident false consensus."
            return "Metabolic variance misinterpreted as symptomatic pattern."
        else:
            # False Negative - AI missed it, but Excel said it's detected
            if risk < 0.2: return "Silent presentation; normal biomarker range masked the underlying risk."
            if risk < 0.5: return "Weak signal; AI uncertainty favored a lower-risk classification."
            return "Clinical edge-case; ground truth signal inconsistent with training baseline."

    def clear(self):
        self.audit_df = None
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.discrepancy_count.config(text="Mismatches Detected: 0")
        self.accuracy_label.config(text="Excel Alignment: 100.0%")

    def _handle_export(self, fmt):
        if self.audit_df is None or self.audit_df.empty:
            from tkinter import messagebox
            messagebox.showwarning("Export Failed", "No discrepancies detected to export.")
            return
            
        from tkinter import filedialog
        file_ext = ".csv" if fmt == 'csv' else ".xlsx"
        path = filedialog.asksaveasfilename(defaultextension=file_ext, 
                                             filetypes=[("Excel Data", "*.xlsx"), ("CSV Data", "*.csv")] if fmt == 'excel' else [("CSV Data", "*.csv")])
        if not path: return
        
        try:
            # Clean export df (remove internal norm columns)
            export_df = self.audit_df.drop(columns=['GT_Norm', 'AI_Norm'], errors='ignore')
            if fmt == 'csv':
                export_df.to_csv(path, index=True)
            else:
                export_df.to_excel(path, index=True)
            from tkinter import messagebox
            messagebox.showinfo("Export Success", f"Audit report saved: {path}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Export Error", f"Failed to save audit: {e}")

    def _handle_copy(self):
        if self.audit_df is None or self.audit_df.empty: return
        text = self.audit_df.to_csv(sep='\t', index=True)
        self.clipboard_clear()
        self.clipboard_append(text)
        from tkinter import messagebox
        messagebox.showinfo("Copied", "Audit data copied to clipboard (TSV format).")
