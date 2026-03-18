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

    # Check for models
    models_path = os.path.join("views", "models")
    model_files = [f for f in os.listdir(models_path) if f.endswith(".pkl")] if os.path.exists(models_path) else []
    if not model_files:
        print("⚠️  WARNING: No pre-trained models (.pkl) found in views/models!")
        print("   If you want models included in the build, train them in the app first.")
        print("   Use 'set PRESERVE_MODELS=true' before running the app to keep models on close.")
    else:
        print(f"✅ Found {len(model_files)} pre-trained models to include in the build.")

    # Assets and modules to include
    sep = ";" if sys.platform == "win32" else ":"
    
    # Ensure views/models directory exists (even if empty)
    models_dir = os.path.join("views", "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir, exist_ok=True)

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
        # Explicitly make sure models are included if they exist
        f"views/models{sep}views/models",
    ]

    # PyInstaller arguments - using --onedir for stability with AI libs
    args = [
        entry_point,
        '--onedir',
        '--windowed',
        '--name=CancerDetectionDashboard',
        '--clean',
        '--noconfirm',
        '--noupx',
    ]

    # Add all data folders
    for data in added_data:
        args.extend(['--add-data', data])

    # HIDDEN IMPORTS: These are often missed by PyInstaller's analyzer
    hidden_imports = [
        'openpyxl',
        'sklearn.utils._typedefs',
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._partition_nodes',
        'sklearn.ensemble._gradient_boosting',
        'sklearn.utils._cython_blas',
        'torch',
        'torch_geometric',
        'networkx',
        'scipy.special.cython_special',
        'PIL._tkinter_finder',
        'defusedxml',
        'unittest',
        'packaging',
        'pkg_resources',
        'umap',
        'shap',
        'xgboost'
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
        
    # COLLECT ALL: For complex AI libraries, we must collect everything to avoid runtime "ModuleNotFound"
    collect_all = ['torch', 'torch_geometric', 'xgboost', 'shap', 'sklearn', 'umap']
    # 1. Create .ICO for professional Windows branding
    try:
        from PIL import Image
        png_path = "logo.png"
        ico_path = "logo.ico"
        if os.path.exists(png_path):
            img = Image.open(png_path)
            # Create a professional multi-size ICO
            img.save(ico_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
            print(f"✅ Generated professional icon: {ico_path}")
            args.extend(['--icon', ico_path])
    except Exception as e:
        print(f"⚠️ Warning: Could not generate .ico file: {e}")

    # EXCLUDE only definitely unused, large third-party frameworks and heavy torch/geometric submodules
    # These often trigger ModuleNotFound errors during the build analysis because they are optional deps.
    # Aggressive collection of optional submodules by the torch/geometric libraries can cause issues.
    excludes = [
        'django', 'IPython', 'notebook', 'jedi', 'sphinx', 'pytest', 
        'PySide6', 'PyQt5', 'PyQt6', 'nbformat', 'nbconvert',
        'tensorboard', 'torch.distributed', 'torch.nn.modules.export', 'torch.testing',
        'matplotlib.tests', 'numpy.tests', 'expecttest', 'hypothesis',
        'onnxscript', 'onnx', 'opt_einsum', 'triton', 'IPython.kernel','cupy'
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

        # Automated Inno Setup Installer Creation
        print("\n--- Attempting to create Windows Installer (.exe) ---")
        
        # Search for ISCC.exe in common locations or local app data
        inno_locations = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Programs\Inno Setup 6\ISCC.exe'),
            "ISCC.exe" # Path search
        ]
        
        inno_compiler = None
        for loc in inno_locations:
            if shutil.which(loc) or os.path.exists(loc):
                inno_compiler = loc
                break

        iss_script = "installer.iss"
        
        # Sync version in .iss file before compiling
        if os.path.exists(iss_script):
            with open(iss_script, "r") as f:
                iss_lines = f.readlines()
            with open(iss_script, "w") as f:
                for line in iss_lines:
                    if line.strip().startswith("#define MyAppVersion"):
                        f.write(f'#define MyAppVersion "{version}"\n')
                    else:
                        f.write(line)
            print(f"Synced {iss_script} to v{version}")

        if inno_compiler and os.path.exists(iss_script):
            print(f"Compiling installer using {inno_compiler}: {iss_script}...")
            import subprocess
            subprocess.run([inno_compiler, iss_script], check=True)
            print("Installer created successfully in 'dist/' folder.")
        else:
            if not inno_compiler:
                print("Note: Inno Setup (ISCC.exe) not found on system PATH or default locations.")
            if not os.path.exists(iss_script):
                print(f"Note: {iss_script} not found in current directory.")
            print("💡 Please install Inno Setup 6 and ensure ISCC.exe is in your PATH to generate the 'Next-Next' installer.")

        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print(f"1. App Folder: {os.path.abspath(dist_path)}")
        print(f"2. Distribution ZIP: {os.path.abspath(zip_name)}")
        installer_exe = os.path.join('dist', 'CancerDetectionDashboard_Installer.exe')
        if os.path.exists(installer_exe):
            print(f"3. Installer EXE: {os.path.abspath(installer_exe)}")
        print("="*50)
        print("💡 Share the Installer or ZIP file. Users just need to run the installer.")
    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check for PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    build()
