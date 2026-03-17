import PyInstaller.__main__
import os
import sys
import shutil
import zipfile

def build():
    print("--- Starting Production Build for Cancer Detection Dashboard ---")
    
    # Define the entry point
    entry_point = "main.py"
    
    if not os.path.exists(entry_point):
        print(f"Error: {entry_point} not found!")
        return

    # Assets and modules to include
    sep = ";" if sys.platform == "win32" else ":"
    
    added_data = [
        f"background.png{sep}.",
        f"logo.png{sep}.",
        f"styles.py{sep}.",
        f"controllers{sep}controllers",
        f"handlers{sep}handlers",
        f"logic{sep}logic",
        f"ui{sep}ui",
        f"utils{sep}utils",
        f"views{sep}views",
    ]

    # PyInstaller arguments
    # CHANGED TO --onedir: Much more stable for large AI libraries (sklearn/torch)
    args = [
        entry_point,
        '--onedir',                       # More reliable than onefile for heavy AI libs
        '--windowed',                     # No console window
        '--name=CancerDetectionDashboard', # Name of the folder/exe
        '--clean',                        # Clean cache
        '--noconfirm',                    # Overwrite existing
        '--noupx',                        # No UPX (faster startup for AI libs)
    ]

    # Add all data folders
    for data in added_data:
        args.extend(['--add-data', data])

    # AI-Specific: Collect all metadata for these heavy packages
    args.extend(['--collect-all', 'sklearn'])
    args.extend(['--collect-all', 'xgboost'])
    args.extend(['--collect-all', 'shap'])
    
    # Hidden imports missed by hooks
    hidden_imports = [
        'openpyxl',                       # Crucial for Excel loading
        'sklearn.utils._typedefs',
        'torch',
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
        
    # EXCLUDE huge unnecessary frameworks that get dragged in by data science libs
    # This prevents [WinError 32] file locks on things we don't even use (like django)
    excludes = [
        'django', 'IPython', 'notebook', 'jedi', 'sphinx', 'pytest', 
        'PySide6', 'PyQt5', 'PyQt6', 'matplotlib.tests'
    ]
    for exc in excludes:
        args.extend(['--exclude-module', exc])

    print(f"Running PyInstaller with args: {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        
        # Post-build: Create a ZIP for distribution (Portable "Installer")
        dist_path = os.path.join('dist', 'CancerDetectionDashboard')
        zip_name = 'CancerDetectionDashboard_Portable.zip'
        
        print(f"Creating distribution bundle: {zip_name}...")
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dist_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(dist_path))
                    zipf.write(file_path, arcname)

        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print(f"1. App Folder: {os.path.abspath(dist_path)}")
        print(f"2. Distribution ZIP: {os.path.abspath(zip_name)}")
        print("="*50)
        print("💡 Share the ZIP file. Users just need to extract and run the .exe inside.")
    except Exception as e:
        print(f"Build failed: {e}")

if __name__ == "__main__":
    # Check for PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    build()
