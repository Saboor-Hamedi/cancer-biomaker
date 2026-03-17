# 🚨 ATTENTION.MD: MASTER CONTEXT FOR AI AGENTS 🚨

**To any future AI Agent reading this:** 
This document contains the *absolute ground truth* and master context for the **Cancer Detection XAI Dashboard** project. Read this entire document before making any architectural changes, UI modifications, or model adjustments.

---

## 🔬 1. PROJECT ESSENCE & CLINICAL PURPOSE
This is a **Desktop application (Tkinter)** designed for **Explainable AI (XAI) in Oncology**. It takes biosensor data (electrochemical sensor readings) and predicts the presence of cancer using an ensemble of Machine Learning models. 

It is NOT just a toy machine learning app. It is designed to look, feel, and operate like a **premium clinical diagnostic tool** with a massive emphasis on *explainability* (Why did the AI make this decision?) and *medical precision*.

### The Data (`cancer_biomarkers.xlsx`)
- **Total Samples:** 500 patients.
- **Class Imbalance:** 42 cancer-positive cases (8.4%) vs. 458 healthy cases.
- **Critical Rule:** NEVER aggressively drop outliers. In medical data, outliers are often the sickest patients. We use **Winsorization** (clipping to 1st/99th percentiles) instead of dropping rows to preserve positive cases.

### The Biomarkers (Input Features)
The system measures three primary cancer biomarkers:
1. **PSA CONCENTRATION (pg/mL) [Prostate]**
   - **Weight:** ~86.0% (The absolute dominant signal in this dataset).
   - **Healthy Avg:** ~1,742 pg/mL | **Cancer Avg:** ~58,205 pg/mL.
   - **Critical Threshold:** > 28,224 pg/mL (Values above this are mathematically guaranteed to trigger a positive diagnosis).
2. **AFP CONCENTRATION (pg/mL) [Liver]**
   - **Weight:** ~7.4%.
   - **Elevated Threshold:** 100 pg/mL (Secondary co-signal).
3. **CA125 CONCENTRATION (U/mL) [Ovarian/Peritoneal]**
   - **Weight:** ~6.6%.
   - **Elevated Threshold:** 35 U/mL (Secondary co-signal).
4. **Bio-Sensor Metrics:** Multiple secondary features like `PSA Peak Height`, `Current @ -0.46V`, etc.

---

## 🧠 2. ALGORITHMIC ARCHITECTURE
We use a **Committee Consensus** (Ensemble) approach. 
- **Random Forest:** The undisputed champion. Because the data is highly imbalanced and non-linear (PSA leaps from 1k to 60k), Random Forest's 100 decision trees handle it perfectly without bias (often achieving 100% Recall and 98.9% Specificity).
- **Logistic Regression & SVM:** Linear models that struggle with the severe data skew but provide good baseline comparisons.
- **MLP (Neural Network):** Tends to overfit the small positive class.
- **XGBoost:** Included via lazy loading if `xgboost` is installed on the host machine.

### The Leaderboard Metrics
The AI Leaderboard ranks models by **F1-SCORE**, not raw accuracy. In cancer detection (where 91% of data is negative), predicting "Healthy" for everyone gives 91% accuracy, which is useless. **F1-Score, Specificity, and Recall** are the metrics we care about. CV Mean/Std evaluates model stability.

---

## 🖥 3. UI/UX DESIGN SYSTEM (TKINTER)
The app is built in `tkinter` using `ttk` widgets. It must maintain a modern, premium, "glass/medical" aesthetic. 

- **Colors:** We use specific hex codes. 
  - 🔵 Blue (#EFF6FF, #3B82F6) for PSA features / Info.
  - 🟢 Green (#F0FDF4, #10B981) for AFP / Healthy / Success.
  - 🟠 Orange (#FFF7ED, #F59E0B) for CA125 / Warnings.
  - 🔴 Red (#FEE2E2, #EF4444) for Positive Cancer Detections / Critical Errors.
- **Tabs (`ui/components/tabs.py`):**
  - **Input Tab:** 3-column layout (`BIOMARKER NAME` | `UNIT` | `VALUE`). Feature names are UPPERCASE and auto-humanized from raw column names. It pulls default values from the first row of uploaded data.
  - **Data View Tab:** Simple grid of the raw dataset.
  - **Analytics Tab:** Holds the Performance Report. This report is data-backed, explaining the exact PSA thresholds and offering clinical guidance.
  - **Validation Tab:** The "AI Consensus". Shows majority decisions, dissenters (e.g., `✔ MAJORITY (3/4)`), and overall patient risk.
  - **Leaderboard Tab:** 9-column performance table ranking the models.

---

## ⚙️ 4. CORE MECHANICS & QUIRKS TO REMEMBER

1. **Session Persistence:** When the app closes, it normally wipes trained models to give a "fresh start" (Professor's requirement). However, we save the `data_path` to `session_config.json`. On startup, if data path exists but no models exist, the app gracefully waits for data upload or retraining.
2. **PyInstaller:** The app is bundled into an `.exe` via `build_exe.py`. Avoid deep dynamic imports that PyInstaller can't trace. All static assets (icons, logos) must use `resources/` or `assets/` and be handled safely for PyInstaller paths `sys._MEIPASS`.
3. **No Placeholders in Reports:** The Analytics report parses `cancer_biomarkers.xlsx` to generate REAL insights. Don't use dummy text like "Model X is good." We say: "Random Forest outperforms because 86% of its decision rests on PSA, handling the 33x skew perfectly."
4. **Separation of Concerns:** 
   - `main.py`: Entry point, UI layout setup.
   - `logic/model_manager.py`: Scikit-learn training, prediction, metric calculation.
   - `logic/data_manager.py`: Pandas ingestion, validation, outlier Winsorization, and session saving.
   - `controllers/`: Bridges the UI clicks to the `logic` layer.
   - `ui/components/tabs.py`: All major UI views.

---

## 🛠 5. HOW TO ENHANCE THIS APP (FUTURE TASKS)
If the user asks to add a feature, follow these guiding principles:
- **Think Clinically:** If adding a chart, ask yourself "What does this tell the doctor?"
- **Maintain the UI:** Don't throw ugly standard Tkinter buttons in. Use `ttk.Button` with padding. Follow the established color schemes.
- **Protect the Positives:** If tweaking data ingestion, ensure the 42 positive cancer cases are NEVER dropped or scaled to zero.

*End of Attention Document - You are now fully briefed.*
