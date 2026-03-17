# 🩺 Clinical AI Cancer Audit System: Documentation

## 🚀 Professional Deployment & Publication
To ensure the system is correctly packaged for clinical environments, follow this standard release workflow:

### 📦 1. Production Build
Transforms the Python script into a standalone Windows executable.
```bash
python build_exe.py
```
*   **Target**: `dist/CancerDetectionDashboard.exe`
*   **Components**: Bundles all UI logic, model engines, and visual assets (`background.png`).

### 🏷️ 2. Version Management (Semantic Versioning)
Always update the version in `main.py` (around line 53) before a new release:
1.  Open `main.py`.
2.  Change `self.version = "1.0.2"` (Patch) or `"1.1.0"` (New Feature).
3.  Save the file.

### 🌐 3. GitHub Publish
Automatically syncs your code to GitHub, creates a Release tag, and uploads the `.exe` binary.
```bash
python publish.py
```
*Users will automatically be notified of the update via the internal UpdateManager.*

---

## 🏗️ System Architecture & Logic
The system is built on a modular "Active Committee" framework:

| Module | Responsibility |
| :--- | :--- |
| **DataManager** | Handles medical data cleaning, outlier removal (Robust Scaling), and biological peak detection. |
| **ModelManager** | The AI core. Manages ensembles including Random Forest, SVM, GNN, and XGBoost. |
| **LayoutManager** | Controls the premium themed workspace, handling tab transitions and status reporting. |
| **Visualizer** | Generates SHAP explainability plots and t-SNE topological mapping. |

---

## 🛠️ Troubleshooting & Technical FAQ

### ❌ Python `AttributeError` at unexpected lines (e.g. Line 427)
If the system crashes with line numbers that don't exist in your code, Python is running a **cached version (.pyc)**.
**Resolution**:
1. Close the application.
2. Run this command to purge the cache:
   ```bash
   rd /s /q __pycache__
   ```
3. Run the app again: `python main.py`.

### 🧪 Data Crowding (too many columns)
The dashboard automatically filters for "High Impact" biomarkers (like PSA, AFP, concentrations). If you want to see a specific column, ensure it contains the word "peak" or "class" in its lab header.

### 📊 Performance Metrics
All models are evaluated using **F1-Score** and **Clinical Sensitivity** to ensure high-risk patients are not missed, balancing diagnostic precision with the need for safety.
