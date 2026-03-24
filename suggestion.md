# AI Research Assistant: Clinical Roadmap

This document tracks the incremental improvements to the Clinical AI Assistant for the Cancer Biomarker XAI Dashboard.

## Phase 1: Context-Aware Diagnostics (COMPLETE) ✅

- [x] Implement context collection from DataManager.
- [x] Pass patient raw values (PSA, AFP, etc.) to AI providers.
- [x] Include model probability scores and triage classes in the system prompt.
- [x] Session Persistence (Chat history no longer deletes on close).
- [x] Non-Modal UI (Can use dashboard while chatting).

## Phase 3: Automated Clinical Reporting (COMPLETE) ✅

- [x] "Export Research Note" feature in AIChatModal.
- [x] Professional Markdown (.md) report generation.
- [x] Diagnostic context injection (Biomarkers + Model stats).

## Phase 2: Clinical Batch Intelligence (Active Task) 📊

**Objective**: AI analyzes the entire dataset for hidden patterns.

- [ ] AI-driven anomaly detection across columns.
- [ ] Summary of high-risk clusters in the current batch.

## Phase 4: Robustness & System Stability (Audit Results) 🛡️

**Objective**: Hardening the clinical environment against edge cases and platform instability.

- [x] **Thread-Safety**: Fix UI access (`cget`, `get_values`) from background threads in `AIChatModal`.
- [x] **Logic Sequence**: Ensure `Risk_Score` is injected into dataframes before `DiagnosticEngine` batch analysis.
- [x] **Mathematical Robustness**: Add `ZeroDivisionError` guards for Z-score and Velocity calculations.
- [x] **Resource Management**: Implement background task cancellation/cleanup during `System Reset`.
- [x] **Data Integrity**: Add `IQR > 0` guard for biomarker Winsorization in `DataManager`.
- [x] **Performance**: Move individual stability perturbation check to a background thread to prevent UI lag.
- [x] **Clinical Branding**: Clean up residual typos (e.g., "Rish" ➡️ "Risk") across registry and codebase.

### Phase 5: Advanced Forensic Analysis (Strategy) 🧬

- [x] **Cohort Fingerprinting**: Categorize batches into clinical archetypes (e.g., Inflammatory vs. Aggressive).
- [x] **Counterfactual Resilience**: Identify the "Delta" required to move a patient to a lower triage level.
- [x] **Diagnostic Entropy**: Measure batch "Signal Clarity" using information theory.
- [x] **Predictive Trajectories**: Estimate "Time-to-Threshold" based on biomarker velocity.
- [x] **Reasoning Injection**: Generate "Forensic Tags" for atypical presentations (e.g., "High Risk / Low PSA").

---

_Roadmap updated by Antigravity AI — March 2026_
