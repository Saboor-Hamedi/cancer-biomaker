# Clinical AI Cancer Audit System: Documentation

## Professional Deployment & Publication
To ensure the system is correctly packaged for clinical environments, follow this standard release workflow:

### 1. Production Build
Transforms the Python script into a standalone Windows executable.
```bash
python build_exe.py
```
- **Target**: `dist/CancerDetectionDashboard.exe`
- **Components**: Bundles all UI logic, model engines, and visual assets (`background.png`).
- **Optimization**: Uses `--onedir` for faster load times of AI libraries.

### 2. Version Management (Semantic Versioning)
Always update the version in `main.py` before a new release:
1. Open `main.py`.
2. Locate the `VERSION` global variable.
3. Update the string (e.g., `"1.0.3"`).
4. Save the file.

### 3. GitHub Publish
Automatically syncs code to GitHub, creates a Release tag, and uploads the `.exe` zip bundle.
```bash
python publish.py
```
*Note: This Requires GitHub CLI (gh) to be installed and authenticated.*

---

## System Architecture & Logic
The system is built on a modular "Active Committee" framework to ensure diagnostic redundancy:

| Module | Responsibility |
| :--- | :--- |
| **DataManager** | Handles medical data cleaning, outlier removal (Robust Scaling), and biological peak detection. |
| **ModelManager** | The AI core. Manages ensembles including Random Forest, SVM, GNN, and XGBoost. |
| **LayoutManager** | Controls the premium themed workspace, handling tab transitions and status reporting. |
| **Visualizer** | Generates SHAP explainability plots and t-SNE topological mapping. |
| **UI Components** | Individual tab logic for Input, Data View, Consensus, and Performance Analysis. |

---

## Troubleshooting & Technical FAQ

### AttributeError at unexpected lines
If the system crashes with line numbers that don't match the source code, Python may be using stale cached files.
**Resolution**:
1. Close the application.
2. Delete the `__pycache__` directories.
3. Restart via `python main.py`.

### Data Filtering logic
The dashboard specifically targets high-impact biomarkers. For a column to appear in the active diagnostic view, it should ideally be labeled with standard clinical prefixes or contain "peak" in its header.

### Performance Interpretation
- **Accuracy**: Overall population correctness.
- **Sensitivity/Recall**: Critical for not missing at-risk patients.
- **Precision**: Minimizing false positives to avoid unnecessary clinical anxiety.
- **F1-Score**: The primary balance metric for imbalanced medical data.

---
*CONFIDENTIAL CLINICAL DOCUMENTATION | BIO-RECON ANALYTICS*
