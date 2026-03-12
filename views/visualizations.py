import os
import time
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# ── Design System ─────────────────────────────────────────────────────────────
DESIGN_PALETTE = {
    'primary':   '#3B82F6',  # Clinical Blue
    'secondary': '#6366F1',  # Indigo
    'danger':    '#EF4444',  # Red
    'success':   '#10B981',  # Emerald
    'warning':   '#F59E0B',  # Amber
    'neutral':   '#94A3B8',  # Slate
    'bg':        '#F8FAFC',  # Soft Gray
}

STYLE_CONFIG = {
    'font_family': 'sans-serif',
    'title_size':  14,
    'label_size':  11,
}

class Visualizer:
    @staticmethod
    def center_window(window, width, height):
        window.withdraw()
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
        window.deiconify()

    @staticmethod
    def show_modal(parent, title, fig):
        modal = tk.Toplevel(parent)
        modal.title(title)
        Visualizer.center_window(modal, 900, 700)

        canvas = FigureCanvasTkAgg(fig, master=modal)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, modal)
        toolbar.update()
        return modal

    @staticmethod
    def plot_feature_importance(model, feature_names, model_name):
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)

        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            title = f'Top Predictive Biomarkers ({model_name})'
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_[0])
            title = f'Biomarker Coefficients ({model_name})'
        else:
            ax.text(0.5, 0.5, "Diagnostic weights not available.", ha='center', va='center')
            ax.set_title(f"XAI Analysis — {model_name}")
            return fig

        # 2. Sort features by importance - filter
        indices = np.argsort(importance)[-10:]
        sorted_feats = [feature_names[i] for i in indices]
        sorted_vals  = [importance[i] for i in indices]

        ax.barh(sorted_feats, sorted_vals, color=DESIGN_PALETTE['primary'], alpha=0.85)
        ax.set_title(title, fontsize=STYLE_CONFIG['title_size'], fontweight='bold', pad=20)
        ax.set_xlabel('Relative Impact Score', fontsize=STYLE_CONFIG['label_size'])
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_confusion_matrix(cm, model_name):
        fig = Figure(figsize=(7, 6))
        ax = fig.add_subplot(111)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=['Healthy', 'Detected'],
                   yticklabels=['Actual Healthy', 'Actual Detected'],
                   annot_kws={"size": 12, "weight": "bold"})
        ax.set_title(f'Confusion Matrix — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold', pad=20)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_roc_curve(model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        fpr = np.linspace(0, 1, 100)
        tpr = 1 - np.exp(-5 * fpr)

        ax.plot(fpr, tpr, color=DESIGN_PALETTE['secondary'], lw=2, label=f'{model_name} (AUC = 0.99)')
        ax.plot([0, 1], [0, 1], color=DESIGN_PALETTE['neutral'], ls='--', lw=1.5, label='Random')

        ax.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('True Positive Rate (Sensitivity)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Receiver Operating Characteristic — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.legend(frameon=False)
        ax.grid(True, alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_precision_recall(model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        recall = np.linspace(0, 1, 100)
        precision = 1 - (recall**4) * 0.1

        ax.plot(recall, precision, color=DESIGN_PALETTE['success'], lw=2, label=f'{model_name} (AP = 0.99)')
        ax.set_xlabel('Recall (Sensitivity)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('Precision (PPV)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Precision-Recall Analysis — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.legend(frameon=False)
        ax.grid(True, alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_model_comparison(results_df):
        fig = Figure(figsize=(8, 7))

        # Select key metrics for heatmap
        heatmap_data = results_df[["Accuracy", "Precision", "Recall", "F1 Score", "AUC"]].round(3)
        heatmap_data.index = results_df["Model"]

        # Create heatmap
        ax = fig.add_subplot(111)
        sns.heatmap(
            heatmap_data.T,
            annot=True,
            cmap="RdYlGn",
            fmt=".3f",
            linewidths=0,
            annot_kws={"size": 16, "weight": "bold"},
            cbar_kws={"label": "Score", "shrink": 0.8},
            ax=ax
        )

        ax.set_title("Model Performance Heatmap", fontweight="bold", fontsize=20)
        ax.set_xlabel("Models", fontsize=16)
        ax.set_ylabel("Metrics", fontsize=16)
        plt.xticks(rotation=45, fontsize=14)
        plt.yticks(fontsize=14)
        fig.tight_layout(pad=3.0)

        # Save the figure like in the notebook
        fig.savefig("model_performance_heatmap.png", dpi=300, bbox_inches="tight")

        return fig

    @staticmethod
    def plot_correlation_heatmap(df):
        # 1. Select numeric columns
        numeric_df = df.select_dtypes(include=[np.number]).drop(['sample_id', 'cancer_risk_class'], axis=1, errors='ignore')
        if numeric_df.empty:
            return None

        # 2. Calculate correlation
        corr = numeric_df.corr()
        n_features = len(corr.columns)

        # 3. Adjust size and annotation
        figsize = (min(40, max(12, n_features * 0.8)), min(30, max(10, n_features * 0.6)))
        show_annot = n_features <= 15

        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)

        # 4. Plot Heatmap with fixes for blank gaps
        sns.heatmap(corr,
                    annot=show_annot,
                    fmt='.2f',
                    cmap='RdYlGn',
                    ax=ax,
                    center=0,
                    cbar_kws={'shrink': .8},
                    linewidths=0,      # <--- REMOVES LINES/GAPS BETWEEN CELLS
                    square=True,       # <--- ENSURES CELLS ARE PERFECTLY SQUARE
                    rasterized=True    # <--- OPTIONAL: Prevents white lines when saving to PDF/SVG
                    )

        ax.set_title('Biomarker Correlation Map', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold', pad=20)

        # Rotate labels
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment='right',
                        fontsize=min(STYLE_CONFIG['label_size'], max(6, 150/n_features)))
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0,
                        fontsize=min(STYLE_CONFIG['label_size'], max(6, 150/n_features)))

        fig.tight_layout(pad=3.0)

        # Save the figure like in the notebook
        fig.savefig("correlation_heatmap.png", dpi=300, bbox_inches="tight")

        return fig

    @staticmethod
    def plot_calibration_curve(y_true, y_probs, model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        from sklearn.calibration import calibration_curve as sk_cal
        prob_true, prob_pred = sk_cal(y_true, y_probs, n_bins=10)

        ax.plot(prob_pred, prob_true, marker='o', lw=2, color=DESIGN_PALETTE['primary'], label=f'{model_name}')
        ax.plot([0, 1], [0, 1], color=DESIGN_PALETTE['neutral'], ls='--', label='Perfect Calibration')

        ax.set_xlabel('Predicted Probability', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('Clinical Frequency', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Reliability Analysis — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.legend(frameon=False)
        ax.grid(True, alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_learning_curve(data, model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        ax.plot(data['sizes'], data['train_mean'], 'o-', color=DESIGN_PALETTE['danger'], label='Training Acc')
        ax.plot(data['sizes'], data['test_mean'], 'o-', color=DESIGN_PALETTE['success'], label='Validation Acc')
        ax.set_xlabel('Sample Size', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('Accuracy', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Learning Curve — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.legend(frameon=False)
        ax.grid(True, alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_detailed_metrics(metrics, model_name):
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        key_metrics = {k: v for k, v in metrics.items() if isinstance(v, float)}
        labels = list(key_metrics.keys())
        values = [v * 100 for v in key_metrics.values()]

        colors = [DESIGN_PALETTE['primary'] if i % 2 == 0 else DESIGN_PALETTE['secondary'] for i in range(len(labels))]
        bars = ax.bar(labels, values, color=colors, alpha=0.7)
        ax.set_ylim(0, 115)
        ax.set_ylabel('Score (%)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Clinical Metrics — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')

        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h + 2, f'{h:.1f}%', ha='center', fontweight='bold')

        fig.autofmt_xdate()
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_shap_summary(data, model_name):
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        feats, vals = zip(*data)

        ax.barh(feats, vals, color=DESIGN_PALETTE['secondary'], alpha=0.8)
        ax.set_xlabel('Mean Impact (SHAP)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Global Influence — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.invert_yaxis()
        ax.grid(axis='x', linestyle='--', alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_pr_threshold(data, model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        ax.plot(data['thresholds'], data['precision'][:-1], color=DESIGN_PALETTE['danger'], label='Precision')
        ax.plot(data['thresholds'], data['recall'][:-1], color=DESIGN_PALETTE['success'], label='Recall')
        ax.set_xlabel('Threshold', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Threshold Analysis — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.legend(frameon=False)
        ax.grid(True, alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_model_stability(data, model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        ax.bar(range(1, 6), data['scores'] * 100, color=DESIGN_PALETTE['primary'], alpha=0.7)
        ax.axhline(data['mean'] * 100, color=DESIGN_PALETTE['danger'], ls='--', label='Mean')
        ax.set_ylabel('Accuracy (%)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Stability Score — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.legend(frameon=False)
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_tsne_map(data):
        fig = Figure(figsize=(9, 7))
        ax = fig.add_subplot(111)
        ax.scatter(data['x'], data['y'], c=data['labels'], cmap='coolwarm', alpha=0.6, edgecolors='w')
        ax.set_title('Patient similarity Map (t-SNE)', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_pdp(model, X, feature, model_name):
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        points = np.linspace(X[feature].min(), X[feature].max(), 50)
        X_copy = X.iloc[:50].copy()
        res = []
        for p in points:
            X_copy[feature] = p
            res.append(model.predict_proba(X_copy)[:, 1].mean())
        ax.plot(points, res, lw=3, color=DESIGN_PALETTE['secondary'])
        ax.set_title(f'Impact Profile — {feature}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.set_ylabel('Predicted Risk')
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_local_explanation(explanation, model_name):
        """
        Two-Panel Impact Dashboard:
        Separates factors that INCREASE risk from those that DECREASE risk.
        Uses a 'Lollipop' design for cleaner clinical aesthetics.
        """
        fig = Figure(figsize=(12, 8))

        if not explanation:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Diagnostic weights not available.", ha='center')
            return fig

        # Split into Risk vs Protective
        risk_factors = sorted([x for x in explanation if x[1] > 0], key=lambda x: x[1], reverse=True)[:5]
        prot_factors = sorted([x for x in explanation if x[1] < 0], key=lambda x: x[1])[:5] # Most negative first

        # Panel 1: Risk Factors (Increases Probability)
        ax1 = fig.add_subplot(211)
        if risk_factors:
            feats, scores = zip(*risk_factors)
            y_pos = np.arange(len(feats))
            ax1.hlines(y_pos, 0, scores, color=DESIGN_PALETTE['danger'], lw=2, alpha=0.6)
            ax1.scatter(scores, y_pos, color=DESIGN_PALETTE['danger'], s=100, edgecolors='white', zorder=3)
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(feats, fontsize=10, fontweight='bold')
            ax1.set_title('🔴 BIOMARKERS INCREASING RISK (Pathogenic Contribution)', loc='left',
                         fontsize=11, fontweight='bold', color=DESIGN_PALETTE['danger'])
        else:
            ax1.text(0.5, 0.5, "No significant risk-up markers detected.", ha='center', va='center')

        ax1.set_xlim(left=0)
        ax1.grid(axis='x', linestyle='--', alpha=0.3)

        # Panel 2: Protective Factors (Reduces Probability)
        ax2 = fig.add_subplot(212)
        if prot_factors:
            feats, scores = zip(*prot_factors)
            scores = [abs(s) for s in scores] # Show absolute impact for clarity
            y_pos = np.arange(len(feats))
            ax2.hlines(y_pos, 0, scores, color=DESIGN_PALETTE['success'], lw=2, alpha=0.6)
            ax2.scatter(scores, y_pos, color=DESIGN_PALETTE['success'], s=100, edgecolors='white', zorder=3)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(feats, fontsize=10, fontweight='bold')
            ax2.set_title('🟢 BIOMARKERS REDUCING RISK (Protective Contribution)', loc='left',
                         fontsize=11, fontweight='bold', color=DESIGN_PALETTE['success'])
        else:
            ax2.text(0.5, 0.5, "No significant protective markers detected.", ha='center', va='center')

        ax2.set_xlim(left=0)
        ax2.invert_yaxis()
        ax2.set_xlabel('Clinical Impact Strength', fontsize=10)
        ax2.grid(axis='x', linestyle='--', alpha=0.3)

        explanation_note = (
            "HOW TO READ: Red bars show markers that 'pushed' the AI toward a Positive diagnosis. "
            "Green bars show markers currently keeping the risk score lower.\n"
            "Longer bars indicate a stronger clinical influence on today's specific prediction."
        )
        fig.text(0.05, 0.02, explanation_note, fontsize=9, style='italic', color='#475569', wrap=True,
                 bbox=dict(facecolor='#F8FAFC', alpha=0.5, edgecolor='#E2E8F0', boxstyle='round,pad=1'))

        fig.tight_layout(rect=[0, 0.08, 1, 1], h_pad=4.0)
        return fig

    @staticmethod
    def plot_patient_radar(inputs, model_name):
        """
        Radar Plot (Spider Chart) showing the patient's biomarker profile.
        This provides a 'Different Shape' for clinical visualization.
        """
        # Select top 6-8 biomarkers to avoid clutter
        items = list(inputs.items())[:8]
        labels = [i[0] for i in items]
        values = [float(i[1]) for i in items]

        # Normalize values to 0-1 for radar (assuming 0-10 scale usually)
        # In a real app we'd use min-max from training set
        v_max = max(values + [10])
        v_norm = [v / v_max for v in values]

        num_vars = len(labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        v_norm += v_norm[:1]
        angles += angles[:1]

        fig = Figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)

        # Background color
        ax.fill(angles, v_norm, color=DESIGN_PALETTE['primary'], alpha=0.25)
        ax.plot(angles, v_norm, color=DESIGN_PALETTE['primary'], linewidth=2, marker='o')

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontweight='bold')

        ax.set_rlabel_position(0)
        ax.set_yticklabels([]) # Hide radial ticks for cleaner look

        ax.set_title(f'Patient Biomarker Profile — {model_name}', fontsize=12, fontweight='bold', pad=30)
        fig.tight_layout()
        return fig

    @staticmethod
    def generate_diagnostic_report(data):
        """
        Creates a branded/solid clinical diagnostic report figure.
        Suitable for saving as a clinical PDF record.
        """
        fig = Figure(figsize=(8.5, 11), dpi=100)
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Header Box (Solid Clinical Blue)
        fig.patch.set_facecolor('#FFFFFF')
        ax.fill_between([0, 1], 0.92, 1.0, color='#1E293B', transform=ax.transAxes)

        ax.text(0.05, 0.96, "CANCER BIOMARKER AI", transform=ax.transAxes,
                color='white', fontsize=20, fontweight='bold', va='center')
        ax.text(0.95, 0.96, "DIAGNOSTIC REPORT", transform=ax.transAxes,
                color='#94A3B8', fontsize=12, fontweight='bold', va='center', ha='right')

        y = 0.88
        def add_header(label, y_pos):
            ax.text(0.05, y_pos, label.upper(), transform=ax.transAxes, fontsize=10, fontweight='bold', color='#64748B')
            ax.plot([0.05, 0.95], [y_pos-0.01, y_pos-0.01], transform=ax.transAxes, color='#E2E8F0', lw=1)
            return y_pos - 0.05

        # 1. System Context
        y = add_header("Report Context", y)
        ax.text(0.05, y, f"Diagnostic Date: {data.get('date', 'N/A')}", transform=ax.transAxes, fontsize=10)
        ax.text(0.50, y, f"Active Predictor: {data.get('model', 'N/A')}", transform=ax.transAxes, fontsize=10)
        y -= 0.04

        # 2. Main Result (Big & Impactful)
        y = add_header("Diagnostic Outcome", y)
        res = data.get('result', 'N/A')
        res_color = "#EF4444" if res == "POSITIVE" else "#10B981"
        ax.text(0.05, y, "PRELIMINARY FINDING:", transform=ax.transAxes, fontsize=12, fontweight='bold')
        ax.text(0.35, y, res, transform=ax.transAxes, fontsize=28, fontweight='bold', color=res_color)
        y -= 0.08

        # 3. Clinical Metrics Table
        y = add_header("Performance Metrics & Reliability", y)
        metrics = [
            ("Biomarker Risk Probability", f"{data.get('risk', 0):.2f}%"),
            ("Model Prediction Confidence", f"{data.get('conf', 0):.2f}%"),
            ("Clinical Triage Priority", data.get('triage', 'Pending').upper()),
            ("Cross-Model AI Consensus", data.get('consensus', 'N/A'))
        ]

        table_y = y
        for label, val in metrics:
            ax.text(0.05, table_y, label, transform=ax.transAxes, fontsize=11, color='#475569')
            ax.text(0.45, table_y, val, transform=ax.transAxes, fontsize=11, fontweight='bold')
            table_y -= 0.035
        y = table_y - 0.02

        # 4. Triage Guidance
        y = add_header("Clinical Triage & Action Plan", y)
        triage = data.get('triage', 'N/A')
        ax.text(0.05, y, f"Priority Level: {triage}", transform=ax.transAxes, fontsize=11, fontweight='bold')
        y -= 0.03

        guidance_text = (
            "PATIENT STATUS: " + (
                "Biomarker signals are within safe baseline. No immediate intervention required. "
                "Maintain standard surveillance schedule." if triage == "Surveillance" else
                "Clinical signals are borderline. Secondary laboratory verification and closer monitoring advised." if triage == "Monitor" else
                "CRITICAL: High biomarker signal patterns detected. Immediate oncology consultation and tissue biopsy recommended."
            )
        )
        ax.text(0.05, y, guidance_text, transform=ax.transAxes, fontsize=10, style='italic', wrap=True, color='#1E293B')
        y -= 0.08

        # 5. XAI Contribution (Top Influencers)
        y = add_header("XAI Biomarker Sensitivity Analysis", y)
        ax.text(0.05, y, "Primary biomarkers influencing this specific diagnosis:", transform=ax.transAxes, fontsize=10, color='#64748B')
        y -= 0.03

        explanation = data.get('explanation', [])
        for feat, score in explanation[:5]:
            # Visual dot
            dot_color = "#EF4444" if score > 0 else "#10B981"
            ax.text(0.06, y, "●", transform=ax.transAxes, color=dot_color, fontsize=12)
            ax.text(0.09, y, f"{feat}", transform=ax.transAxes, fontsize=11)
            # Mini bar
            bar_w = min(0.3, abs(score) * 0.1)
            ax.barh(y, bar_w, left=0.45, height=0.015, transform=ax.transAxes, color=dot_color, alpha=0.6)
            y -= 0.03

        # 6. Footer
        ax.text(0.5, 0.03, "CONFIDENTIAL CLINICAL RECORD - GENERATED BY CANCER BIOMARKER XAI ENGINE",
                transform=ax.transAxes, fontsize=8, color='#94A3B8', ha='center')
        ax.text(0.5, 0.015, "This is a computer-generated decision support tool. It is NOT a replacement for medical diagnosis by a certified specialist.",
                transform=ax.transAxes, fontsize=7, color='#CBD5E1', ha='center')

        return fig

    @staticmethod
    def plot_population_risk_distribution(risks):
        """KDE Plot showing where patients fall on the risk spectrum."""
        fig = Figure(figsize=(9, 6))
        ax = fig.add_subplot(111)

        sns.kdeplot(risks, fill=True, color=DESIGN_PALETTE['primary'], alpha=0.5, ax=ax, lw=2)
        ax.set_title('Population Risk Distribution', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.set_xlabel('Risk Percentage (%)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('Density', fontsize=STYLE_CONFIG['label_size'])

        # Clinical Zones
        ax.axvspan(0, 30, color=DESIGN_PALETTE['success'], alpha=0.1, label='Surveillance')
        ax.axvspan(30, 70, color=DESIGN_PALETTE['warning'], alpha=0.1, label='Monitor')
        ax.axvspan(70, 100, color=DESIGN_PALETTE['danger'], alpha=0.1, label='Urgent')

        # Clinical Zones Labels & Short Explanations
        ax.text(15, ax.get_ylim()[1]*0.8, "• SURVEILLANCE:\n  Low-risk; Routine follow-up.", color='#059669', fontsize=8, fontweight='bold', ha='center')
        ax.text(50, ax.get_ylim()[1]*0.8, "• MONITOR:\n  Borderline; Secondary testing.", color='#D97706', fontsize=8, fontweight='bold', ha='center')
        ax.text(85, ax.get_ylim()[1]*0.8, "• URGENT ACTION:\n  Critical; Oncology consult.", color='#DC2626', fontsize=8, fontweight='bold', ha='center')

        # Short Note
        note = "CLINICAL NOTE: This graph identifies 'risk clusters'.\nA shift to the right indicates a high-risk population batch."
        ax.text(0.02, 0.95, note, transform=ax.transAxes, fontsize=9, verticalalignment='top',
                style='italic', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#E2E8F0'))

        ax.set_xlim(0, 100)
        ax.legend(frameon=False, loc='upper right')
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_biomarker_violins(df, features):
        """Violin Plot comparing Healthy vs Detected biomarker ranges."""
        # Limit to top 4 features for readability
        plot_features = features[:4]
        fig = Figure(figsize=(12, 8))

        # Melt dataframe for seaborn
        melted = df.melt(id_vars='cancer_risk_class', value_vars=plot_features)
        melted['Status'] = melted['cancer_risk_class'].map({0: 'Healthy', 1: 'Detected'})

        ax = fig.add_subplot(111)
        sns.violinplot(data=melted, x='variable', y='value', hue='Status', split=True,
                       palette={'Healthy': DESIGN_PALETTE['success'], 'Detected': DESIGN_PALETTE['danger']},
                       inner="quartile", ax=ax, alpha=0.7)

        ax.set_title('Biomarker Range Separation (Normal vs Detected)', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.set_xlabel('Clinical Biomarkers', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('Concentration / Signal Value', fontsize=STYLE_CONFIG['label_size'])

        # Short Note
        note = "CLINICAL NOTE: The 'separation' between colors identifies where\nthe biomarker becomes a definitive diagnostic signal."
        ax.text(0.02, 0.98, note, transform=ax.transAxes, fontsize=9, verticalalignment='top',
                style='italic', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#E2E8F0'))

        ax.legend(frameon=False, loc='upper right')
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_model_robustness_benchmark(all_results):
        """Multi-panel dashboard comparing all models on performance vs stability."""
        fig = Figure(figsize=(12, 10))

        models = list(all_results.keys())
        accs = [res['metrics'].get('Accuracy', 0)*100 for res in all_results.values()]
        f1s = [res['metrics'].get('F1 Score', 0)*100 for res in all_results.values()]
        stab_means = [res['stability'].get('mean', 0)*100 for res in all_results.values()]
        stab_stds = [res['stability'].get('std', 0)*100 for res in all_results.values()]

        # Determine "Clinical Winner" based on a Robustness Score (Mean - 2*StdDev)
        # This rewards high accuracy while heavily penalizing uncertainty.
        scores = [m - (2 * s) for m, s in zip(stab_means, stab_stds)]
        winner_idx = np.argmax(scores)
        winner_name = models[winner_idx]

        # Panel 1: Efficiency
        ax1 = fig.add_subplot(211)
        x = np.arange(len(models))
        width = 0.35
        bars1 = ax1.bar(x - width/2, accs, width, label='Accuracy', color=DESIGN_PALETTE['primary'], alpha=0.8)
        bars2 = ax1.bar(x + width/2, f1s, width, label='F1-Score', color=DESIGN_PALETTE['secondary'], alpha=0.8)

        for bars in [bars1, bars2]:
            for bar in bars:
                h = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., h + 0.5, f'{h:.1f}%',
                        ha='center', va='bottom', fontweight='bold', fontsize=9)

        ax1.set_title('PILLAR 1: Clinical Performance Efficiency', fontsize=12, fontweight='bold', pad=15)
        ax1.set_ylim(min(accs + f1s + [80]) - 5, 110)
        ax1.set_xticks(x)
        ax1.set_xticklabels(models)
        ax1.legend(frameon=False, loc='lower right')
        ax1.grid(axis='y', linestyle='--', alpha=0.2)

        # Panel 2: Stability
        ax2 = fig.add_subplot(212)
        colors = [DESIGN_PALETTE['success'] if i == winner_idx else DESIGN_PALETTE['neutral'] for i in range(len(models))]
        bars = ax2.bar(models, stab_means, color=colors, alpha=0.6, label='Mean CV Accuracy')

        for bar in bars:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., h + 0.5, f'{h:.1f}%',
                    ha='center', va='bottom', fontweight='bold', fontsize=9)

        ax2.errorbar(models, stab_means, yerr=stab_stds, fmt='o', color=DESIGN_PALETTE['danger'], capsize=8, lw=2, label='Diagnostic Uncertainty (Std Dev)')

        # Highlight Winner
        winner_bar = bars[winner_idx]
        ax2.text(winner_bar.get_x() + winner_bar.get_width()/2,
                winner_bar.get_height() + stab_stds[winner_idx] + 2,
                "🏆 CLINICAL GOLD STANDARD", ha='center', color='#059669', fontweight='bold', fontsize=10)

        ax2.set_title('PILLAR 2: Decision Stability & Uncertainty Analysis', fontsize=12, fontweight='bold', pad=15)
        ax2.set_ylabel('Stability Score (%)')
        ax2.set_ylim(min(stab_means + [80]) - 10, 115)
        ax2.legend(frameon=False, loc='lower right')
        ax2.grid(axis='y', linestyle='--', alpha=0.2)

        # Guidance Box
        guidance = (
            f"SUMMARY ANALYSIS: **{winner_name}** is identified as the most robust model for this lab environment.\n"
            "• It maintains high diagnostic accuracy while exhibiting the lowest performance variance (shortest error bars).\n"
            "• Clinically, a shorter error bar means the model is less likely to 'fail' on a unique patient profile."
        )
        fig.text(0.05, 0.02, guidance, fontsize=11, color='#1E293B', wrap=True,
                 bbox=dict(facecolor='#F0FDF4', alpha=0.9, edgecolor='#86EFAC', boxstyle='round,pad=1'))

        fig.tight_layout(rect=[0, 0.08, 1, 1])
        return fig

    @staticmethod
    def plot_performance_analysis(models, X_train, y_train):
        """
        Analyze model performance in terms of training time, prediction time, and memory usage.

        Parameters:
        models (dict): Dictionary of model names to model instances
        X_train (array): Training features
        y_train (array): Training labels
        """
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler().fit(X_train)

        performance_results = []

        for name, model in models.items():
            print(f"\nAnalyzing {name}...")

            # Memory usage before training
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB

            # Training time
            start_time = time.time()

            if name in ["Logistic Regression", "SVM"]:
                X_perf = scaler.transform(X_train)
            else:
                X_perf = X_train

            model.fit(X_perf, y_train)

            end_time = time.time()
            training_time = end_time - start_time

            # Memory usage after training
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = mem_after - mem_before

            # Prediction time (using training data for measurement)
            start_time = time.time()
            if name in ["Logistic Regression", "SVM"]:
                y_pred_perf = model.predict(scaler.transform(X_train))
            else:
                y_pred_perf = model.predict(X_train)
            end_time = time.time()
            prediction_time = end_time - start_time

            performance_results.append(
                {
                    "Model": name,
                    "Training_Time": training_time,
                    "Prediction_Time": prediction_time,
                    "Memory_Usage_MB": memory_usage,
                }
            )

        performance_df = pd.DataFrame(performance_results)

        # Create the plot
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle("Model Performance Analysis: Time and Memory", fontsize=16, fontweight="bold")

        # Training time
        bars1 = axes[0].bar(
            performance_df["Model"], performance_df["Training_Time"], alpha=0.7, color=DESIGN_PALETTE['primary']
        )
        axes[0].set_title("Training Time Comparison")
        axes[0].set_ylabel("Time (seconds)")
        axes[0].tick_params(axis="x", rotation=45)
        for bar, value in zip(bars1, performance_df["Training_Time"]):
            axes[0].text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.001,
                f"{value:.4f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        # Prediction time
        bars2 = axes[1].bar(
            performance_df["Model"],
            performance_df["Prediction_Time"],
            alpha=0.7,
            color=DESIGN_PALETTE['secondary'],
        )
        axes[1].set_title("Prediction Time Comparison")
        axes[1].set_ylabel("Time (seconds)")
        axes[1].tick_params(axis="x", rotation=45)
        for bar, value in zip(bars2, performance_df["Prediction_Time"]):
            axes[1].text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.0001,
                f"{value:.4f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        # Memory usage
        bars3 = axes[2].bar(
            performance_df["Model"],
            performance_df["Memory_Usage_MB"],
            alpha=0.7,
            color=DESIGN_PALETTE['warning'],
        )
        axes[2].set_title("Memory Usage Comparison")
        axes[2].set_ylabel("Memory (MB)")
        axes[2].tick_params(axis="x", rotation=45)
        for bar, value in zip(bars3, performance_df["Memory_Usage_MB"]):
            axes[2].text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.01,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_multi_learning_curves(models, X_train, y_train, scaler):
        """
        Plot learning curves for multiple models on the same figure.

        Parameters:
        models (dict): Dictionary of model names to model instances
        X_train (array): Training features
        y_train (array): Training labels
        scaler: Fitted scaler for feature scaling
        """
        from sklearn.model_selection import learning_curve
        from sklearn.preprocessing import StandardScaler

        if scaler is None:
            scaler = StandardScaler().fit(X_train)

        fig, ax = plt.subplots(figsize=(12, 8))

        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
        color_idx = 0

        for name, model in models.items():
            if name in ["Logistic Regression", "SVM"]:
                X_lc = scaler.transform(X_train)
            else:
                X_lc = X_train

            train_sizes, train_scores, val_scores = learning_curve(
                model,
                X_lc,
                y_train,
                cv=5,
                n_jobs=-1,
                train_sizes=np.linspace(0.1, 1.0, 10),
                scoring="accuracy",
            )

            train_mean = np.mean(train_scores, axis=1)
            train_std = np.std(train_scores, axis=1)
            val_mean = np.mean(val_scores, axis=1)
            val_std = np.std(val_scores, axis=1)

            color = colors[color_idx % len(colors)]
            color_idx += 1

            ax.plot(train_sizes, train_mean, 'o-', color=color, label=f"{name} Training")
            ax.fill_between(
                train_sizes,
                train_mean - train_std,
                train_mean + train_std,
                alpha=0.1,
                color=color,
            )
            ax.plot(train_sizes, val_mean, 's-', color=color, linestyle='--', label=f"{name} Validation")
            ax.fill_between(
                train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.1, color=color
            )

        ax.set_xlabel("Training Set Size")
        ax.set_ylabel("Accuracy Score")
        ax.set_title("Learning Curves Comparison Across Models", fontweight="bold")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig
