import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from scipy.stats import gaussian_kde
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QFrame, QSizePolicy, QFileDialog)
from PySide6.QtCore import Qt

# ── Obsidian Theme Constants ──
BG       = "#000000"
BG2      = "#09090B"
BORDER   = "#18181B"
MUTED    = "#71717A"
TEXT     = "#E4E4E7"
BLUE     = "#3B82F6"
GREEN    = "#10B981"
PURPLE   = "#8B5CF6"
AMBER    = "#F59E0B"
RED      = "#EF4444"
PALETTE  = [BLUE, GREEN, PURPLE, AMBER, RED, "#06B6D4", "#EC4899"]


def _style_ax(ax, title="", xlabel="", ylabel=""):
    """Apply Obsidian theme to a single Axes."""
    ax.set_facecolor(BG)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    if title:  ax.set_title(title,  color=TEXT,  fontsize=11, fontweight="bold", pad=12)
    if xlabel: ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, color=MUTED, fontsize=9)


class VisualizationModal(QDialog):
    """High-Fidelity Clinical Visualization Hub (PySide6)."""

    def __init__(self, parent=None, chart_type="KDE Distribution", data=None):
        super().__init__(parent)
        self.setWindowTitle(f"CLINICAL VISUALIZATION — {chart_type.upper()}")
        self.resize(1050, 760)
        self.chart_type = chart_type
        self.data = data   # Optional: pass a pandas DataFrame for real-data charts
        self._setup_ui()
        self._render_chart()

    # ─────────────────────────────────────────────────────────────────────────
    # UI Shell
    # ─────────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet(f"background-color:{BG2}; border-bottom:2px solid {BORDER};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(25, 0, 25, 0)
        title_lbl = QLabel(f"LABORATORY ANALYSIS — {self.chart_type.upper()}")
        title_lbl.setStyleSheet(f"font-weight:900; font-size:14px; color:{BLUE}; letter-spacing:1px;")
        h_lay.addWidget(title_lbl)
        h_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(35, 35)
        close_btn.setStyleSheet(f"background:transparent; color:{MUTED}; font-size:16px; border:none;")
        close_btn.clicked.connect(self.close)
        h_lay.addWidget(close_btn)
        layout.addWidget(header)

        # Canvas
        self.figure = plt.figure(facecolor=BG)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"background-color:{BG2}; border-top:1px solid {BORDER};")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(25, 0, 25, 0)
        export_btn = QPushButton("📁  EXPORT HIGH-RES IMAGE")
        export_btn.setFixedHeight(35)
        export_btn.setFixedWidth(210)
        export_btn.setStyleSheet(
            f"background:{BORDER}; color:{TEXT}; border:1px solid #27272A;"
            f"border-radius:6px; font-weight:700; font-size:10px;"
        )
        export_btn.clicked.connect(self._handle_export)
        f_lay.addWidget(export_btn)
        f_lay.addStretch()
        layout.addWidget(footer)

    # ─────────────────────────────────────────────────────────────────────────
    # Chart Router
    # ─────────────────────────────────────────────────────────────────────────
    def _render_chart(self):
        self.figure.clear()
        dispatch = {
            "KDE Distribution":   self._plot_kde,
            "ROC":                self._plot_roc,
            "Confusion Matrix":   self._plot_confusion,
            "Heatmap":            self._plot_heatmap,
            "PR Curve":           self._plot_pr_curve,
            "t-SNE":              self._plot_tsne,
            "Reliability":        self._plot_reliability,
        }
        fn = dispatch.get(self.chart_type, self._plot_placeholder)
        fn()
        self.figure.tight_layout(pad=2.5)
        self.canvas.draw()

    # ─────────────────────────────────────────────────────────────────────────
    # ① KDE Distribution — the "3-wave" biomarker chart
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_kde(self):
        """Kernel Density Estimation curves for PSA, AFP, CA125 (benign vs malignant)."""
        df = self.data

        # Build realistic synthetic data if no real data is passed
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            rng = np.random.default_rng(42)
            n = 400
            df = pd.DataFrame({
                "PSA_pg_per_ml":  np.concatenate([rng.normal(1.2, 0.4, n//2), rng.normal(3.8, 1.2, n//2)]),
                "AFP_pg_per_ml":  np.concatenate([rng.normal(5.1, 1.5, n//2), rng.normal(12.4, 3.1, n//2)]),
                "CA125_U_per_ml": np.concatenate([rng.normal(8.3, 2.1, n//2), rng.normal(22.7, 6.5, n//2)]),
                "Prediction":     [0]*(n//2) + [1]*(n//2),
            })

        # Detect column names case-insensitively
        col_map = {c.lower().replace(" ", "_"): c for c in df.columns}
        markers = []
        for key, label, color in [
            ("psa_pg_per_ml",  "PSA (pg/ml)",   BLUE),
            ("afp_pg_per_ml",  "AFP (pg/ml)",   GREEN),
            ("ca125_u_per_ml", "CA125 (U/ml)",  PURPLE),
        ]:
            if key in col_map:
                markers.append((col_map[key], label, color))

        pred_col = col_map.get("prediction")

        gs = gridspec.GridSpec(1, len(markers) if markers else 1, figure=self.figure,
                               wspace=0.35)

        colors_class = {0: GREEN, 1: RED}
        labels_class = {0: "BENIGN", 1: "MALIGNANT"}

        for idx, (col, label, wave_color) in enumerate(markers):
            ax = self.figure.add_subplot(gs[idx])
            _style_ax(ax, title=label, xlabel="Concentration", ylabel="Density" if idx == 0 else "")

            vals = pd.to_numeric(df[col], errors="coerce").dropna()

            if pred_col and pred_col in df.columns:
                # Split by class → two filled KDE waves
                for cls in [0, 1]:
                    subset = pd.to_numeric(
                        df.loc[df[pred_col].astype(str).str.strip().isin(
                            [str(cls), "NEGATIVE" if cls == 0 else "POSITIVE",
                             "BENIGN" if cls == 0 else "MALIGNANT"]
                        ), col], errors="coerce"
                    ).dropna()
                    if len(subset) < 5:
                        continue
                    kde = gaussian_kde(subset, bw_method=0.35)
                    x = np.linspace(vals.min(), vals.max(), 300)
                    y = kde(x)
                    c = colors_class[cls]
                    ax.plot(x, y, color=c, linewidth=2.5, label=labels_class[cls])
                    ax.fill_between(x, y, alpha=0.15, color=c)
            else:
                # Single KDE for entire cohort
                kde = gaussian_kde(vals, bw_method=0.35)
                x = np.linspace(vals.min(), vals.max(), 300)
                y = kde(x)
                ax.plot(x, y, color=wave_color, linewidth=3)
                ax.fill_between(x, y, alpha=0.2, color=wave_color)

            # Peak marker
            x_full = np.linspace(vals.min(), vals.max(), 300)
            y_full = gaussian_kde(vals, bw_method=0.35)(x_full)
            peak_x = x_full[np.argmax(y_full)]
            ax.axvline(peak_x, color=wave_color, linestyle="--", alpha=0.5, linewidth=1)
            ax.text(peak_x, ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 0.1,
                    f"peak\n{peak_x:.2f}", color=wave_color,
                    fontsize=7, ha="center", va="top")

            if pred_col:
                ax.legend(fontsize=8, facecolor=BG2, edgecolor=BORDER,
                          labelcolor=TEXT, loc="upper right")

        if not markers:
            ax = self.figure.add_subplot(111)
            _style_ax(ax)
            ax.text(0.5, 0.5, "No biomarker columns found in dataset.",
                    color=MUTED, ha="center", va="center", transform=ax.transAxes)

        self.figure.suptitle("BIOMARKER KDE DISTRIBUTION — COHORT ANALYSIS",
                             color=TEXT, fontsize=13, fontweight="bold", y=1.01)

    # ─────────────────────────────────────────────────────────────────────────
    # ② ROC-AUC
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_roc(self):
        from sklearn.metrics import roc_curve, auc
        ax = self.figure.add_subplot(111)
        _style_ax(ax, title="ROC-AUC Comparison — Multi-Model",
                  xlabel="False Positive Rate (1 − Specificity)",
                  ylabel="True Positive Rate (Sensitivity)")
        rng = np.random.default_rng(0)
        models = [("Random Forest", BLUE, 0.96),
                  ("Logistic Reg.", GREEN, 0.91),
                  ("XGBoost", PURPLE, 0.94),
                  ("SVM", AMBER, 0.89)]
        for name, color, target_auc in models:
            n = 300
            y_true = rng.integers(0, 2, n)
            base = rng.uniform(0, 1, n)
            y_score = np.clip(base + y_true * (target_auc - 0.5), 0, 1)
            fpr, tpr, _ = roc_curve(y_true, y_score)
            roc_auc = auc(fpr, tpr)
            ax.plot(fpr, tpr, color=color, linewidth=2.5, label=f"{name} (AUC={roc_auc:.3f})")
            ax.fill_between(fpr, tpr, alpha=0.05, color=color)
        ax.plot([0, 1], [0, 1], "--", color=MUTED, linewidth=1)
        ax.legend(facecolor=BG2, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)

    # ─────────────────────────────────────────────────────────────────────────
    # ③ Confusion Matrix
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_confusion(self):
        import seaborn as sns
        ax = self.figure.add_subplot(111)
        _style_ax(ax, title="Clinical Confusion Matrix")
        cm = np.array([[452, 23], [18, 107]])
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "obsidian_blue", [BG2, BLUE])
        sns.heatmap(cm, annot=True, fmt="d", cmap=cmap, ax=ax,
                    linewidths=1, linecolor=BORDER, cbar=False,
                    annot_kws={"size": 20, "weight": "bold", "color": TEXT})
        ax.set_xticklabels(["BENIGN", "MALIGNANT"], color=TEXT, fontsize=10)
        ax.set_yticklabels(["BENIGN", "MALIGNANT"], color=TEXT, fontsize=10, rotation=0)
        ax.set_xlabel("Predicted Label", color=MUTED)
        ax.set_ylabel("True Label", color=MUTED)

    # ─────────────────────────────────────────────────────────────────────────
    # ④ Correlation Heatmap
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_heatmap(self):
        import seaborn as sns
        df = self.data
        ax = self.figure.add_subplot(111)
        _style_ax(ax, title="Biomarker Correlation Matrix")
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            num_df = df.select_dtypes(include=np.number).dropna(axis=1, how="all")
            corr = num_df.corr()
        else:
            rng = np.random.default_rng(1)
            raw = rng.uniform(-1, 1, (8, 8))
            corr = pd.DataFrame((raw + raw.T) / 2,
                                columns=["PSA","AFP","CA125","CEA","HER2","BCA","TP53","BRCA"])
            corr.index = corr.columns
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "rg", [RED, BG2, GREEN])
        sns.heatmap(corr, cmap=cmap, ax=ax, center=0, annot=len(corr) <= 12,
                    fmt=".2f", linewidths=0.5, linecolor=BORDER,
                    cbar_kws={"shrink": 0.7},
                    annot_kws={"size": 8, "color": TEXT})
        ax.tick_params(colors=TEXT, labelsize=8)

    # ─────────────────────────────────────────────────────────────────────────
    # ⑤ Precision-Recall Curve
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_pr_curve(self):
        from sklearn.metrics import precision_recall_curve, average_precision_score
        ax = self.figure.add_subplot(111)
        _style_ax(ax, title="Precision-Recall Analysis",
                  xlabel="Recall (Sensitivity)", ylabel="Precision (PPV)")
        rng = np.random.default_rng(3)
        models = [("Random Forest", BLUE, 0.95),
                  ("Logistic Reg.", GREEN, 0.88),
                  ("XGBoost", PURPLE, 0.93)]
        for name, color, target in models:
            n = 300
            y_true = rng.integers(0, 2, n)
            y_score = np.clip(rng.uniform(0, 1, n) + y_true * (target - 0.5), 0, 1)
            p, r, _ = precision_recall_curve(y_true, y_score)
            ap = average_precision_score(y_true, y_score)
            ax.plot(r, p, color=color, linewidth=2.5, label=f"{name} (AP={ap:.3f})")
            ax.fill_between(r, p, alpha=0.08, color=color)
        ax.legend(facecolor=BG2, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1.05)

    # ─────────────────────────────────────────────────────────────────────────
    # ⑥ t-SNE Patient Similarity Map
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_tsne(self):
        from sklearn.manifold import TSNE
        ax = self.figure.add_subplot(111)
        _style_ax(ax, title="Patient Similarity Map — t-SNE Clustering",
                  xlabel="t-SNE Dimension 1", ylabel="t-SNE Dimension 2")
        df = self.data
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            num_df = df.select_dtypes(include=np.number).dropna().head(300)
            if len(num_df) >= 10:
                embedding = TSNE(n_components=2, random_state=42,
                                 perplexity=min(30, len(num_df)-1)).fit_transform(num_df)
                cols = [c.lower() for c in df.columns]
                pred_col = next((df.columns[i] for i, c in enumerate(cols)
                                 if "prediction" in c), None)
                if pred_col:
                    labels = df[pred_col].iloc[num_df.index].values
                else:
                    labels = np.zeros(len(embedding))
            else:
                embedding = None
        else:
            embedding = None

        if embedding is None:
            rng = np.random.default_rng(7)
            c1 = rng.normal([-3, -3], 1.5, (120, 2))
            c2 = rng.normal([3, 3], 1.5, (80, 2))
            embedding = np.vstack([c1, c2])
            labels = np.array([0]*120 + [1]*80)

        for cls, color, label in [(0, GREEN, "BENIGN"), (1, RED, "MALIGNANT")]:
            mask = (np.array(labels).astype(str) == str(cls)) | \
                   (np.array(labels) == ("NEGATIVE" if cls == 0 else "POSITIVE")) | \
                   (np.array(labels) == label)
            if mask.sum():
                ax.scatter(embedding[mask, 0], embedding[mask, 1],
                           c=color, alpha=0.65, edgecolors="none", s=35, label=label)
        ax.legend(facecolor=BG2, edgecolor=BORDER, labelcolor=TEXT)

    # ─────────────────────────────────────────────────────────────────────────
    # ⑦ Reliability / Calibration Plot
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_reliability(self):
        from sklearn.calibration import calibration_curve
        ax = self.figure.add_subplot(111)
        _style_ax(ax, title="Model Reliability / Calibration Plot",
                  xlabel="Mean Predicted Probability",
                  ylabel="Fraction of Positives")
        rng = np.random.default_rng(9)
        models = [("Random Forest", BLUE), ("Logistic Reg.", GREEN), ("XGBoost", PURPLE)]
        for name, color in models:
            n = 500
            y_true = rng.integers(0, 2, n)
            y_prob = np.clip(rng.beta(2, 2, n) + (y_true - 0.5) * 0.4, 0.01, 0.99)
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
            ax.plot(prob_pred, prob_true, "s-", color=color, linewidth=2,
                    markersize=5, label=name)
        ax.plot([0, 1], [0, 1], "--", color=MUTED, linewidth=1, label="Perfect calibration")
        ax.legend(facecolor=BG2, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # ─────────────────────────────────────────────────────────────────────────
    # Placeholder
    # ─────────────────────────────────────────────────────────────────────────
    def _plot_placeholder(self):
        ax = self.figure.add_subplot(111)
        _style_ax(ax)
        ax.text(0.5, 0.5, f"Chart type '{self.chart_type}' not yet implemented.",
                color=MUTED, ha="center", va="center", transform=ax.transAxes, fontsize=12)

    # ─────────────────────────────────────────────────────────────────────────
    # Export
    # ─────────────────────────────────────────────────────────────────────────
    def _handle_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis", f"{self.chart_type.replace(' ','_')}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        if path:
            self.figure.savefig(path, facecolor=BG, bbox_inches="tight", dpi=200)
