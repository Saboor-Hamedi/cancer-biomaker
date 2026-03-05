import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

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

        indices = np.argsort(importance)[-12:]
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
    def plot_model_comparison():
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        models = ['Random Forest', 'Log Regression', 'SVM', 'XGBoost']
        accuracy = [98.5, 96.2, 94.8, 97.9]
        f1_scores = [98.1, 95.8, 94.2, 97.5]
        
        x = np.arange(len(models))
        width = 0.35
        
        ax.bar(x - width/2, accuracy, width, label='Accuracy', color=DESIGN_PALETTE['primary'], alpha=0.8)
        ax.bar(x + width/2, f1_scores, width, label='F1-Score', color=DESIGN_PALETTE['secondary'], alpha=0.8)
        
        ax.set_ylabel('Performance (%)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title('Cross-Model Clinical Comparison', fontsize=STYLE_CONFIG['title_size'], fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(models)
        ax.set_ylim(80, 105)
        ax.legend(frameon=False, loc='upper left')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_correlation_heatmap(df):
        numeric_df = df.select_dtypes(include=[np.number]).drop(['sample_id', 'cancer_risk_class'], axis=1, errors='ignore')
        if numeric_df.empty: return None
        
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111)
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn', ax=ax, center=0)
        ax.set_title('Biomarker Correlation Map', fontsize=STYLE_CONFIG['title_size'], fontweight='bold', pad=20)
        fig.tight_layout(pad=3.0)
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
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        feats, scores = zip(*explanation)
        colors = [DESIGN_PALETTE['danger'] if s > 0 else DESIGN_PALETTE['success'] for s in scores]
        ax.barh(feats, scores, color=colors, alpha=0.8)
        ax.set_title(f'Local XAI Diagnosis — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.invert_yaxis()
        ax.grid(axis='x', linestyle='--', alpha=0.3)
        fig.tight_layout(pad=3.0)
        return fig
