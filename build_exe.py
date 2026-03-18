import PyInstaller.__main__
import os
import sys
import shutil
import zipfile

def get_version():
    """Extract version from main.py to keep in sync."""
    try:
        with open("main.py", "r") as f:
            for line in f:
                if 'VERSION =' in line:
                    return line.split('=')[1].strip().replace('"', '').replace("'", "")
    except:
        pass
    return "1.0.0"

def build():
    version = get_version()
    print(f"--- Starting Production Build for Cancer Detection Dashboard v{version} ---")
    
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

    # AI-Specific: Avoid --collect-all as it bloats the size with tests and docs
    # Instead, we use specific hidden imports and excludes
    
    hidden_imports = [
        'openpyxl',                       # Crucial for Excel loading
        'sklearn.utils._typedefs',
        'torch',
        'torch_geometric',
        'networkx',
        'scipy.special.cython_special',
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
        
    # EXCLUDE huge unnecessary frameworks that get dragged in by data science libs
    # Aggressively prune to reduce size from >1GB to <600MB
    excludes = [
        'django', 'IPython', 'notebook', 'jedi', 'sphinx', 'pytest', 
        'PySide6', 'PyQt5', 'PyQt6', 'matplotlib.tests', 'numpy.tests',
        'torch.testing', 'torch.distributions', 'scipy.stats.tests',
        'unittest', 'test'
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

        # NEW: Automated Inno Setup Installer Creation
        print("\n--- Attempting to create Windows Installer (.exe) ---")
        inno_compiler = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        iss_script = "installer.iss"
        
        # Sync version in .iss file before compiling
        if os.path.exists(iss_script):
            with open(iss_script, "r") as f:
                lines = f.readlines()
            with open(iss_script, "w") as f:
                for line in lines:
                    if line.startswith("#define MyAppVersion"):
                        f.write(f'#define MyAppVersion "{version}"\n')
                    else:
                        f.write(line)
            print(f"Synced {iss_script} to v{version}")

        if os.path.exists(inno_compiler) and os.path.exists(iss_script):
            print(f"Compiling installer: {iss_script}...")
            import subprocess
            subprocess.run([inno_compiler, iss_script], check=True)
            print("Installer created successfully in 'dist/' folder.")
        else:
            print("Note: Inno Setup (ISCC.exe) not found. Skipping installer creation.")
            print("Please install Inno Setup 6 to generate the 'Next-Next' installer.")

        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print(f"1. App Folder: {os.path.abspath(dist_path)}")
        print(f"2. Distribution ZIP: {os.path.abspath(zip_name)}")
        if os.path.exists(os.path.join('dist', 'CancerDetectionDashboard_Installer.exe')):
            print(f"3. Installer EXE: {os.path.abspath(os.path.join('dist', 'CancerDetectionDashboard_Installer.exe'))}")
        print("="*50)
        print("💡 Share the Installer or ZIP file. Users just need to run the installer.")
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
