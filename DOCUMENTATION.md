# Cancer Detection XAI Dashboard — Clinical Documentation
*Professional Diagnostic Platform for Biomarker Analysis & AI-Driven Forensic Auditing*

---

## 1. Platform Philosophy
The **Cancer Detection XAI Dashboard** is a high-performance clinical workspace designed for life science researchers and medical oncologists. It bridges the gap between complex machine learning and clinical decision-making by prioritizing **transparency** (XAI) over "black-box" predictions.

The core mission is **"Consensus-Driven Diagnosis"**, where no single AI model makes a decision alone. Instead, a committee of specialized algorithms must vote on every patient record.

---

## 2. Core Technology Stack
The platform utilizes a state-of-the-art Python-based engineering stack:
*   **Interface (UI)**: Custom-themed **Tkinter** with a modern "Pure Dark" and "Pure Light" design system using the **Inter** and **Consolas** typography.
*   **AI Ensemble**: 
    *   **Random Forest**: For robust feature interaction detection.
    *   **SVM (Support Vector Machines)**: For high-dimensional boundary separation.
    *   **XGBoost**: For gradient-boosted diagnostic precision.
    *   **MLP (Multi-Layer Perceptron)**: For neural-pattern recognition.
    *   **GNN (Graph Neural Network)**: For modeling complex biomarker-to-biomarker correlations.
*   **XAI (Explainable AI)**: Integrated **SHAP**, **Permutation Importance**, and **Counterfactual Resilience** engines.
*   **Serialization**: **Joblib** for model persistence and **PyTorch** for graph-based neural weights.

---

## 3. System Architecture
The application follows a strict **Controller-Manager-View** (CMV) architecture:

### A. Logic Layer (Managers)
*   **ModelManager**: Handles the training, loading, and pre-warming of the AI committee.
*   **DataManager**: Manages the "Raw-to-Processed" pipeline, including **Outlier Removal** and **Robust Scaling**.
*   **SettingsManager**: Persists user preferences and theme configurations in `settings_config.json`.
*   **VelocityManager**: Analyzes longitudinal patient history to calculate biomarker trajectory and risk momentum.

### B. Orchestration Layer (Controllers)
*   **ModelController**: Triggers ensemble training and manages single/batch predictions.
*   **DataController**: Handles Excel I/O, dataset parsing, and preprocessing dialogs.
*   **VisualizationController**: Orchestrates the rendering of complex Matplotlib plots inside Tkinter modals.

### C. Visual Layer (Components)
*   **Dashboard**: The central hub containing the High-Risk Clinical Registry and Metric Cards.
*   **Sidebar**: Persistent model selection and high-level clinical controls.
*   **Tabs**: Modular workspace for Input, Data View, AI Consensus, Performance Analysis, and System Logs.

---

## 4. Clinical Workflow Guide

### Phase 1: Data Integration
1.  **Upload Dataset**: Use `File → Upload Dataset` (.xlsx).
2.  **Data Optimization**: Open `Data → Data Optimization`. Here you can toggle **Scaling** (Normalizing biomarker ranges) and **Outlier Removal** (Cleaning noise from the biology).
3.  **Validation**: Check the **Data View** tab to ensure all patient records are parsed correctly.

### Phase 2: AI Committee Training
1.  **Re-Train Models**: Use `Data → Re-Train All Models`.
2.  **Stat Audit**: After training, verify the **Algorithm Leaderboard**. Look for high F1-Scores and low CV Stability (Variance).
3.  **Pre-Warming**: The system automatically "warms up" the models into RAM on startup to ensure instant feedback.

### Phase 3: Diagnostic Forensic
1.  **Individual Diagnosis**: Select a patient in the **Data View** or enter values in **Input Features**.
2.  **Consensus Check**: Switch to the **AI Consensus** tab. If models disagree (Red/Green conflict), proceed to forensic audit.
3.  **XAI Audit**: Use the **Analytics** menu to generate **SHAP Profiles** or **What-If Counterfactuals**. This explains *why* the AI flagged a patient as high-risk.

---

## 5. Forensic Diagnostic Modules

### Biomarker Velocity (Longitudinal Tracking)
The **Patient Trajectory** tab tracks a patient's biomarkers (PSA, AFP, etc.) over time. It calculates "Diagnostic Momentum"—if a biomarker is rising faster than the normal physiological rate, the AI flags it even if the current value is technically "within range."

### AI Committee Consensus
Unlike standard dashboards, we show the **Specific Vote** of every model. Clinical disagreement is a feature, not a bug; it flags cases that are too ambiguous for AI and require immediate human intervention.

### Performance Analysis (Audit Log)
Every major diagnostic event is logged in the **Performance Analysis** tab. This provides an ISO-compliant audit trail of every model's statistical reasoning for the current session.

---

## 6. Performance & Speed Optimization

### Clinical Memory Caching
To avoid the slowness of Excel files, we implemented a **Double-Layer Cache**:
1.  **RAM Data Cache**: Once a dataset is loaded, it stays in the RAM. Moving between tabs does not re-read from the disk.
2.  **Model Pre-Warming**: All AI models are loaded into the memory during the "Initializing environment" phase, making the first diagnostic click near-instant.

---

## 7. Security & Privacy
*   **Local Processing**: No patient data ever leaves your machine. All AI inference is performed locally using the onboard engines.
*   **Python 2.6+ Security**: The system explicitly allowlists clinical GNN classes to prevent "Arbitrary Code Execution" during model restoration, ensuring a secure environment for medical data.

---

## 8. Professional Deployment
To build a standalone version for clinical workstations:
1.  Run `python build_exe.py`.
2.  The executable will be generated in `/dist`.
3.  All assets, including the `views/models` and `static/` directories, are automatically bundled.

---

*CONFIDENTIAL CLINICAL DOCUMENTATION v1.0.8 | BIO-RECON ANALYTICS — NO CODES, ONLY LOGIC*
