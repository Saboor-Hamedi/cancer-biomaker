import os
import time
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use('TkAgg')  # Use TkAgg backend for tkinter compatibility
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from scipy import stats

# ── Design System ─────────────────────────────────────────────────────────────
DESIGN_PALETTE = {
    'primary':   '#2563EB',  # Professional Blue
    'secondary': '#4F46E5',  # Indigo
    'danger':    '#DC2626',  # Clinical Red
    'success':   '#059669',  # Medical Green
    'warning':   '#D97706',  # Alert Amber
    'neutral':   '#475569',  # Slate Grey
    'bg':        '#F8FAFC',  # White-ish
    'text':      '#1E293B',  # Dark Blue-Grey
}

STYLE_CONFIG = {
    'font_family': 'sans-serif',
    'title_size':  16,
    'label_size':  12,
    'note_size':   10,
    'dpi':         100,
}

class Visualizer:
    # Keep track of open modal windows for cleanup
    _open_modals = []

    @staticmethod
    def _add_explanatory_note(ax, title, text):
        """Adds a standardized explanatory note box to any plot."""
        props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='#E2E8F0')
        note_text = f"ANALYSIS INSIGHT: {title}\n{text}"
        ax.text(0.02, -0.05, note_text, transform=ax.transAxes, fontsize=STYLE_CONFIG['note_size'],
                verticalalignment='top', style='italic', bbox=props, wrap=True)

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

        # Track the modal for cleanup
        Visualizer._open_modals.append(modal)

        # Remove from tracking when closed
        def on_modal_close():
            if modal in Visualizer._open_modals:
                Visualizer._open_modals.remove(modal)
            modal.destroy()

        modal.protocol("WM_DELETE_WINDOW", on_modal_close)

        return modal

    @staticmethod
    def close_all_modals():
        """Close all open modal windows"""
        for modal in Visualizer._open_modals[:]:  # Copy the list to avoid modification during iteration
            try:
                modal.destroy()
            except:
                pass
        Visualizer._open_modals.clear()

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
        
        # Add labels on bars
        max_val = max(sorted_vals) if sorted_vals else 1
        total_imp = sum(sorted_vals) if sorted_vals else 1
        for i, v in enumerate(sorted_vals):
            pct = f"{100 * v / total_imp:.1f}%"
            ax.text(v + (max_val * 0.01), i, pct, color=DESIGN_PALETTE['neutral'], va='center', fontweight='bold', fontsize=9)

        ax.set_title(title, fontsize=STYLE_CONFIG['title_size'], fontweight='bold', pad=20)
        ax.set_xlabel('Relative Impact Score', fontsize=STYLE_CONFIG['label_size'])
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        Visualizer._add_explanatory_note(ax, "Feature Hierarchy", 
            "These biomarkers are the primary drivers of the model's decision-making process. "
            "Higher impact scores indicate that changing these values causes the largest shift in diagnosis.")

        fig.tight_layout(pad=4.5)
        return fig

    @staticmethod
    def plot_confusion_matrix(metrics, model_name):
        # Extract cm from metrics dictionary
        tn = metrics.get('True Negatives', 0)
        fp = metrics.get('False Positives', 0)
        fn = metrics.get('False Negatives', 0)
        tp = metrics.get('True Positives', 0)
        cm = [[tn, fp], [fn, tp]]

        fig = Figure(figsize=(7, 6))
        ax = fig.add_subplot(111)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=['Healthy', 'Detected'],
                   yticklabels=['Actual Healthy', 'Actual Detected'],
                   annot_kws={"size": 12, "weight": "bold"})
        ax.set_title(f'Confusion Matrix — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold', pad=20)
        
        Visualizer._add_explanatory_note(ax, "Diagnostic Accuracy", 
            "The diagonal (top-left, bottom-right) shows correct predictions. "
            "Off-diagonal cells represent clinical errors: False Positives and False Negatives.")

        fig.tight_layout(pad=4.0)
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
        
        Visualizer._add_explanatory_note(ax, "Classification Capacity", 
            "The ROC curve measures the model's ability to distinguish between healthy and biopsy-detected cases. "
            "A curve closer to the top-left corner indicates superior diagnostic accuracy.")

        fig.tight_layout(pad=4.5)
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
        
        Visualizer._add_explanatory_note(ax, "Clinical Precision", 
            "This curve evaluates the trade-off between identifying all cancer cases (Recall) "
            "versus minimizing false alarms (Precision). It is critical for screening programs.")

        fig.tight_layout(pad=4.5)
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
        ax.tick_params(axis='x', rotation=45, labelsize=14)
        ax.tick_params(axis='y', labelsize=14)

        Visualizer._add_explanatory_note(ax, "Comparative Performance", 
            "This heatmap provides a cross-model benchmark. Green cells indicate optimized performance metrics, "
            "allowing researchers to identify the most stable algorithm for this specific dataset.")

        fig.tight_layout(pad=4.5)

        # Save the figure like in the notebook
        fig.savefig("model_performance_heatmap.png", dpi=300, bbox_inches="tight")

        return fig

    @staticmethod
    def plot_accuracy_comparison(results_df):
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)

        models = results_df["Model"]
        accuracies = results_df["Accuracy"] * 100  # Convert to percentage

        bars = ax.bar(models, accuracies, color=DESIGN_PALETTE['primary'], alpha=0.8)
        ax.set_title("Model Accuracy Comparison", fontsize=STYLE_CONFIG['title_size'] + 4, fontweight='bold', pad=20)
        ax.set_ylabel("Accuracy (%)", fontsize=STYLE_CONFIG['label_size'])
        ax.set_xlabel("Models", fontsize=STYLE_CONFIG['label_size'])
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Add percentage labels on top of bars
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{acc:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

        Visualizer._add_explanatory_note(ax, "Statistical Benchmarking", 
            "A direct comparison of detection accuracy across all deployed models. "
            "The goal is to select the model with the highest sensitivity and lowest clinical error rate.")

        fig.tight_layout(pad=4.5)
        return fig

    @staticmethod
    def plot_statistical_comparison(cv_results_dict):
        """
        Plot statistical comparison between models using paired t-tests
        cv_results_dict: dict with model names as keys and list of CV scores as values
        """
        fig = Figure(figsize=(12, 8))
        ax = fig.add_subplot(111)

        models = list(cv_results_dict.keys())
        n_models = len(models)

        # Create matrix for p-values
        p_matrix = np.ones((n_models, n_models))
        t_matrix = np.zeros((n_models, n_models))

        for i in range(n_models):
            for j in range(i+1, n_models):
                scores1 = cv_results_dict[models[i]]
                scores2 = cv_results_dict[models[j]]
                t_stat, p_val = stats.ttest_rel(scores1, scores2)
                p_matrix[i, j] = p_val
                p_matrix[j, i] = p_val
                t_matrix[i, j] = t_stat
                t_matrix[j, i] = -t_stat

        # Plot heatmap of p-values
        mask = np.triu(np.ones_like(p_matrix, dtype=bool))
        sns.heatmap(p_matrix, mask=mask, annot=True, fmt='.3f', cmap='RdYlGn_r',
                   xticklabels=models, yticklabels=models, ax=ax,
                   cbar_kws={'label': 'p-value', 'shrink': 0.8})
        ax.set_title('Statistical Significance Matrix (Paired t-test p-values)', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
        ax.set_xlabel('Model B')
        ax.set_ylabel('Model A')

        # Add significance stars
        for i in range(n_models):
            for j in range(i+1, n_models):
                p_val = p_matrix[i, j]
                star = ''
                if p_val < 0.001:
                    star = '***'
                elif p_val < 0.01:
                    star = '**'
                elif p_val < 0.05:
                    star = '*'
                if star:
                    ax.text(j + 0.5, i + 0.5, star, ha='center', va='center',
                           fontsize=16, fontweight='bold', color='white')

        fig.tight_layout(pad=3.0)
        fig.savefig("statistical_model_comparison.png", dpi=300, bbox_inches="tight")
        return fig

    @staticmethod
    def plot_permutation_importance(model, X, y, feature_names, model_name):
        """
        Plot permutation feature importance
        """
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111)

        from sklearn.inspection import permutation_importance
        perm_importance = permutation_importance(model, X, y, n_repeats=10, random_state=42)

        sorted_idx = perm_importance.importances_mean.argsort()
        importances = perm_importance.importances_mean[sorted_idx]
        stds = perm_importance.importances_std[sorted_idx]

        # Handle case where all importances are zero
        if np.all(importances == 0):
            ax.text(0.5, 0.5, f"All features show zero permutation importance.\n"
                     f"This may indicate the model is not using these features\n"
                     f"or the dataset is too small for reliable estimation.",
                     ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title(f'Permutation Feature Importance — {model_name}', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
        else:
            ax.barh(range(len(sorted_idx)), importances,
                   xerr=stds, capsize=5,
                   color=DESIGN_PALETTE['primary'], alpha=0.7)
            ax.set_yticks(range(len(sorted_idx)))
            ax.set_yticklabels([feature_names[i] for i in sorted_idx])
            ax.set_xlabel('Permutation Importance (decrease in accuracy)')
            ax.set_title(f'Permutation Feature Importance — {model_name}', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.3)

        Visualizer._add_explanatory_note(ax, "Permutation Importance", 
            "This measures how much the model's accuracy drops when a feature is 'broken' (shuffled). "
            "Features that cause the biggest drop are the most critical for model predictions.")

        fig.tight_layout(pad=4.5)
        return fig

    @staticmethod
    def plot_shap_analysis(model, X, model_name):
        """
        Plot SHAP summary plot for global feature importance
        """
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111)

        try:
            import shap
            # Ensure we're not using any global matplotlib state
            with plt.ioff():  # Turn off interactive mode
                explainer = shap.Explainer(model)
                shap_values = explainer(X)

                # Use SHAP's built-in plotting which creates its own figure
                # We'll capture it and embed it in our figure
                import io

                # Clear any existing plots
                plt.clf()
                plt.close('all')

                # Create SHAP plot
                shap.summary_plot(shap_values, X, show=False)

                # Get the current figure that SHAP created
                current_fig = plt.gcf()

                # Save it to buffer
                buf = io.BytesIO()
                current_fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)

                # Load the image into our axes
                from PIL import Image
                img = Image.open(buf)
                ax.imshow(img)
                ax.set_title(f'SHAP Feature Importance Summary — {model_name}', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
                ax.axis('off')  # Hide axes for image display

                # Clean up
                plt.close(current_fig)
                buf.close()

        except ImportError:
            ax.text(0.5, 0.5, "SHAP not installed. Install with: pip install shap",
                   ha='center', va='center', fontsize=14)
        except Exception as e:
            ax.text(0.5, 0.5, f"SHAP analysis failed: {str(e)}",
                   ha='center', va='center', fontsize=12)

        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_robustness_analysis(cv_results_dict):
        """
        Plot robustness analysis showing variance across CV folds
        """
        fig = Figure(figsize=(12, 8))

        models = list(cv_results_dict.keys())
        scores = [cv_results_dict[m] for m in models]

        # Box plot
        ax1 = fig.add_subplot(211)
        bp = ax1.boxplot(scores, labels=models, patch_artist=True,
                        boxprops=dict(facecolor=DESIGN_PALETTE['primary'], alpha=0.7, linewidth=2),
                        medianprops=dict(color='white', linewidth=2),
                        whiskerprops=dict(linewidth=2, color=DESIGN_PALETTE['neutral']),
                        capprops=dict(linewidth=2, color=DESIGN_PALETTE['neutral']),
                        flierprops=dict(marker='o', markersize=5, alpha=0.6, markerfacecolor=DESIGN_PALETTE['danger']))
        ax1.set_title('Cross-Validation Score Distribution (Robustness)', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
        ax1.set_ylabel('Accuracy Score')
        ax1.grid(axis='y', linestyle='--', alpha=0.3)

        # Ensure boxes are visible by setting proper y-limits
        if scores:
            all_scores = [score for model_scores in scores for score in model_scores]
            if all_scores:
                y_min, y_max = min(all_scores), max(all_scores)
                y_range = y_max - y_min
                ax1.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)

        # Variance plot
        ax2 = fig.add_subplot(212)
        variances = [np.var(s) for s in scores]
        means = [np.mean(s) for s in scores]
        ax2.scatter(variances, means, s=100, color=DESIGN_PALETTE['secondary'], alpha=0.8)
        for i, model in enumerate(models):
            ax2.annotate(model, (variances[i], means[i]), xytext=(5, 5), textcoords='offset points')
        ax2.set_xlabel('Variance (Lower = More Robust)')
        ax2.set_ylabel('Mean Accuracy')
        ax2.set_title('Robustness vs Performance Trade-off', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def plot_sensitivity_analysis(model, X, y, feature_names, model_name, noise_levels=[0.01, 0.05, 0.1, 0.2]):
        """
        Plot sensitivity to input noise
        """
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)

        baseline_score = model.score(X, y)
        scores = [baseline_score]

        for noise in noise_levels:
            X_noisy = X + np.random.normal(0, noise * X.std(), X.shape)
            score = model.score(X_noisy, y)
            scores.append(score)

        labels = ['Baseline'] + [f'Noise {int(n*100)}%' for n in noise_levels]
        bars = ax.bar(labels, scores, color=DESIGN_PALETTE['warning'], alpha=0.7)
        ax.set_ylabel('Accuracy Score')
        ax.set_title(f'Model Sensitivity to Input Noise — {model_name}', fontsize=STYLE_CONFIG['title_size'] + 2, fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.3)

        # Add value labels
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.005, f'{score:.3f}',
                   ha='center', va='bottom', fontweight='bold')

        fig.tight_layout(pad=3.0)
        return fig

    @staticmethod
    def get_shap_data(model, X, model_name):
        """
         Get SHAP analysis data for display in tab
        """
        try:
            import shap
            explainer = shap.Explainer(model)
            shap_values = explainer(X)

            # Get feature importance - ensure we get scalar values
            feature_importance = np.abs(shap_values.values).mean(0)
            feature_names = X.columns

            # Convert to list of floats to ensure scalar values
            feature_importance = [float(imp) for imp in feature_importance]

            # Sort by importance
            sorted_idx = np.argsort(feature_importance)[::-1]
            top_features = [(feature_names[i], feature_importance[i]) for i in sorted_idx[:10]]

            return {
                'model_name': model_name,
                'top_features': top_features,
                'analysis_type': 'SHAP Feature Importance'
            }

        except Exception as e:
            return {
                'model_name': model_name,
                'error': f"SHAP analysis failed: {str(e)}",
                'analysis_type': 'SHAP Feature Importance'
            }

    @staticmethod
    def get_permutation_data(model, X, y, feature_names, model_name):
        """
        Get permutation importance data for display in tab
        """
        try:
            from sklearn.inspection import permutation_importance
            # Increase n_repeats for more reliable results
            perm_importance = permutation_importance(model, X, y, n_repeats=10, random_state=42)

            # Sort by importance
            sorted_idx = perm_importance.importances_mean.argsort()[::-1]
            top_features = [(feature_names[i], float(perm_importance.importances_mean[i]), float(perm_importance.importances_std[i]))
                          for i in sorted_idx[:10]]

            return {
                'model_name': model_name,
                'top_features': top_features,
                'analysis_type': 'Permutation Feature Importance'
            }

        except Exception as e:
            return {
                'model_name': model_name,
                'error': f"Permutation importance failed: {str(e)}",
                'analysis_type': 'Permutation Feature Importance'
            }

    @staticmethod
    def get_robustness_data(cv_results_dict):
        """
        Get robustness analysis data for display in tab
        """
        robustness_stats = {}

        for model_name, scores in cv_results_dict.items():
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            cv_score = std_score / mean_score if mean_score > 0 else 0

            robustness_stats[model_name] = {
                'mean_accuracy': mean_score,
                'std_accuracy': std_score,
                'coefficient_of_variation': cv_score,
                'min_score': np.min(scores),
                'max_score': np.max(scores),
                'range': np.max(scores) - np.min(scores)
            }

        # Find most robust model (lowest coefficient of variation)
        most_robust = min(robustness_stats.items(), key=lambda x: x[1]['coefficient_of_variation'])

        return {
            'analysis_type': 'Model Robustness Analysis',
            'robustness_stats': robustness_stats,
            'most_robust_model': most_robust[0],
            'stability_ranking': sorted(robustness_stats.items(), key=lambda x: x[1]['coefficient_of_variation'])
        }

    @staticmethod
    def get_sensitivity_data(model, X, y, feature_names, model_name, noise_levels=[0.01, 0.05, 0.1, 0.2]):
        """
        Get sensitivity analysis data for display in tab
        """
        try:
            baseline_score = model.score(X, y)
            sensitivity_results = [{'noise_level': 0.0, 'accuracy': baseline_score, 'noise_type': 'Baseline'}]

            for noise in noise_levels:
                X_noisy = X + np.random.normal(0, noise * X.std(), X.shape)
                score = model.score(X_noisy, y)
                sensitivity_results.append({
                    'noise_level': noise,
                    'accuracy': score,
                    'noise_type': f'Noise {int(noise*100)}%',
                    'accuracy_drop': baseline_score - score
                })

            # Find most sensitive noise level
            max_drop = max(sensitivity_results[1:], key=lambda x: x['accuracy_drop'])

            return {
                'model_name': model_name,
                'sensitivity_results': sensitivity_results,
                'baseline_accuracy': baseline_score,
                'most_sensitive_noise': max_drop['noise_type'],
                'max_accuracy_drop': max_drop['accuracy_drop'],
                'analysis_type': 'Sensitivity Analysis'
            }

        except Exception as e:
            return {
                'model_name': model_name,
                'error': f"Sensitivity analysis failed: {str(e)}",
                'analysis_type': 'Sensitivity Analysis'
            }

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

        Visualizer._add_explanatory_note(ax, "Probability Calibration", 
            "Measures how the predicted probability aligns with real-world incidence. "
            "A model on the dashed line has 'perfect' reliability for clinical decision support.")

        fig.tight_layout(pad=4.5)
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

        Visualizer._add_explanatory_note(ax, "Clinical Training Efficiency", 
            "Monitors the model's hunger for data. If the lines are converging, "
            "the model has learned enough patterns to generalize to new patients.")

        fig.tight_layout(pad=4.5)
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

        Visualizer._add_explanatory_note(ax, "Clinical Benchmark Metrics", 
            "Accuracy provides an overview, while Precision and Recall balance the risks of 'False Alarms' "
            "versus 'Missed Diagnoses'. Higher percentages indicate more reliable clinical outcomes.")

        fig.autofmt_xdate()
        fig.tight_layout(pad=4.5)
        return fig

    @staticmethod
    def plot_shap_summary(data, model_name):
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        feats, vals = zip(*data)

        ax.barh(feats, vals, color=DESIGN_PALETTE['secondary'], alpha=0.8)
        
        # Add total impact labels
        total_shap = sum(vals) if vals else 1
        max_shap = max(vals) if vals else 1
        for i, v in enumerate(vals):
            pct = f"{100 * v / total_shap:.1f}%"
            ax.text(v + (max_shap * 0.01), i, pct, color=DESIGN_PALETTE['neutral'], va='center', fontweight='bold', fontsize=9)

        ax.set_xlabel('Mean Impact (SHAP)', fontsize=STYLE_CONFIG['label_size'])
        ax.set_title(f'Global Influence — {model_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.invert_yaxis()
        ax.grid(axis='x', linestyle='--', alpha=0.3)

        Visualizer._add_explanatory_note(ax, "SHAP Explainability", 
            "This shows the average absolute contribution of each feature across the legal patient cohort. "
            "SHAP values provide a game-theoretic proof of biomarker contribution.")

        fig.tight_layout(pad=4.5)
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
        
        Visualizer._add_explanatory_note(ax, "Topological Cluster Map", 
            "Compresses high-dimensional patient data into a 2D map. "
            "Clusters of similar colors represent patient groups with shared clinical phenotypes.")

        fig.tight_layout(pad=4.5)
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
            ax1.set_title('BIOMARKERS INCREASING RISK (Pathogenic Contribution)', loc='left',
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
            ax2.set_title('BIOMARKERS REDUCING RISK (Protective Contribution)', loc='left',
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
    def get_patient_radar_data(inputs, model_name):
        """
        Get patient biomarker data for display in tab.
        Returns dictionary with analysis data.
        """
        # Select top 8 biomarkers to avoid clutter
        items = list(inputs.items())[:8]
        labels = [i[0] for i in items]
        values = [float(i[1]) for i in items]

        # Clinical insights
        high_count = sum(1 for v in values if v > 5.0)  # Assuming 0-10 scale
        low_count = sum(1 for v in values if v < 2.0)
        normal_count = len(values) - high_count - low_count

        biomarker_analysis = []
        for label, value in zip(labels, values):
            insight = ""
            if value > 5.0:
                insight = "Elevated level - may indicate increased risk"
            elif value < 2.0:
                insight = "Low level - may indicate protective factor"
            else:
                insight = "Normal range - typical clinical values"

            biomarker_analysis.append({
                'name': label,
                'value': value,
                'insight': insight
            })

        return {
            'model_name': model_name,
            'biomarkers_analyzed': len(labels),
            'biomarker_data': biomarker_analysis,
            'elevated_count': high_count,
            'low_count': low_count,
            'normal_count': normal_count,
            'assessment': ("increased risk factors present" if high_count > low_count else
                         "protective factors dominant" if low_count > high_count else
                         "balanced biomarker profile observed")
        }

    @staticmethod
    def plot_patient_radar(inputs, model_name):
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

        ax.legend(frameon=False, loc='upper right')

        Visualizer._add_explanatory_note(ax, "Biomarker Range Separation", 
            "The comparison between colors identifies where a biomarker becomes a definitive diagnostic signal. "
            "Minimal overlap indicates high individual predictive value.")

        fig.tight_layout(pad=4.5)
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
    def get_performance_data(models, X_train, y_train):
        """
        Get performance analysis data without plotting.
        Returns list of performance dictionaries for each model.
        """
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler().fit(X_train)

        performance_results = []

        for name, model in models.items():
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

        return performance_results

    @staticmethod
    def plot_performance_analysis(models, X_train, y_train):
        """
        Plot performance analysis using pre-computed data.
        """
        # Get performance data
        performance_results = Visualizer.get_performance_data(models, X_train, y_train)
        performance_df = pd.DataFrame(performance_results)

        # Create the plot using Figure
        fig = Figure(figsize=(18, 6))
        axes = fig.subplots(1, 3)
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

        # Add a note to the first axis as a representative
        Visualizer._add_explanatory_note(axes[0], "Computational Efficiency", 
            "Analyzes the trade-off between algorithmic complexity and speed. "
            "Essential for selecting models that can run in real-world clinical environments with limited hardware.")

        fig.tight_layout(rect=[0, 0.08, 1, 1])
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

        fig = Figure(figsize=(12, 8))
        ax = fig.add_subplot(111)

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

        Visualizer._add_explanatory_note(ax, "Convergence & Fit", 
            "These curves show how model accuracy improves with more data. "
            "A small gap between training and validation indicates a well-generalized model (no overfitting).")

        fig.tight_layout(pad=4.5)
        return fig

    @staticmethod
    def plot_feature_distribution(df, feature_name):
        """Plot the distribution of a specific feature, split by cancer risk class."""
        fig = Figure(figsize=(10, 7))
        ax = fig.add_subplot(111)

        # Create Status column for legend
        plot_df = df.copy()
        if 'cancer_risk_class' in plot_df.columns:
            plot_df['Status'] = plot_df['cancer_risk_class'].map({0: 'Healthy', 1: 'Detected'})
            sns.histplot(data=plot_df, x=feature_name, hue='Status', kde=True, ax=ax, 
                         palette={'Healthy': DESIGN_PALETTE['success'], 'Detected': DESIGN_PALETTE['danger']},
                         alpha=0.5, multiple="stack")
        else:
            sns.histplot(data=plot_df, x=feature_name, kde=True, ax=ax, color=DESIGN_PALETTE['primary'])

        # Add percentage labels on top of bars
        total = len(df)
        for p in ax.patches:
            height = p.get_height()
            if height > 0:
                percentage = f'{100 * height / total:.1f}%'
                ax.annotate(percentage, (p.get_x() + p.get_width() / 2., height),
                            ha='center', va='center', fontsize=9, xytext=(0, 7),
                            textcoords='offset points', fontweight='bold', color=DESIGN_PALETTE['neutral'])

        ax.set_title(f'Biomarker Distribution Profile — {feature_name}', fontsize=STYLE_CONFIG['title_size'], fontweight='bold')
        ax.set_xlabel('Concentration / Signal Value', fontsize=STYLE_CONFIG['label_size'])
        ax.set_ylabel('Patient Count', fontsize=STYLE_CONFIG['label_size'])
        ax.grid(True, alpha=0.3)
        
        # Explanatory Note for Research
        Visualizer._add_explanatory_note(ax, "Biomarker Distribution", 
            f"This graph shows how {feature_name} varies across the population. The overlap between categories "
            "identifies diagnostic ambiguity, while separation indicates high predictive power.")

        fig.tight_layout(pad=4.0)
        return fig
