import PyInstaller.__main__
import os
import sys
import shutil
import zipfile
import warnings
# Suppress Pydantic experimental warnings and other library clutter
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*PydanticExperimentalWarning.*")
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"


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
    import zipfile
    version = get_version()
    print(f"--- Starting Production Build for Cancer Detection Dashboard v{version} ---")
    
    # DEEP CLEAN: Handle Windows PermissionErrors by attempting to clear previous artifacts first
    # This prevents the "Access is denied" error during the PyInstaller build phase
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            try:
                print(f"🧹 Clearing previous {folder} registry...")
                shutil.rmtree(folder)
            except PermissionError:
                print(f"❌ ERROR: Could not clear '{folder}' directory. It is likely being used by another process.")
                print(f"💡 FIX: Please close any open instances of the Dashboard or your file explorer, then try again.")
                return
            except Exception as e:
                print(f"⚠️ Warning during cleanup of {folder}: {e}")

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
        f"controllers{sep}controllers",
        f"handlers{sep}handlers",
        f"logic{sep}logic",
        f"ui{sep}ui",
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
        '--log-level=WARN', # REDUCE CLUTTER: Only show critical build warnings
    ]

    # Add all data folders
    for data in added_data:
        args.extend(['--add-data', data])

    # HIDDEN IMPORTS: These are often missed by PyInstaller's analyzer
    hidden_imports = [
        'PySide6.QtPrintSupport',
        'utils.report_engine',
        'openpyxl',
        'sklearn.utils._typedefs',
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._partition_nodes',
        'sklearn.ensemble._gradient_boosting',
        'sklearn.utils._cython_blas',
        'scipy.special.cython_special',
        'PIL._tkinter_finder',
        'defusedxml',
        'unittest',
        'packaging',
        'pkg_resources',
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
        
    # COLLECT ALL: For complex AI libraries, we must collect everything to avoid runtime "ModuleNotFound"
    # This is critical for XGBoost and PyTorch which have hidden DLLs
    from PyInstaller.utils.hooks import collect_all
    
    packages_to_collect = ['PySide6', 'torch', 'torch_geometric', 'xgboost', 'shap', 'sklearn', 'umap', 'matplotlib', 'numpy']
    for pkg in packages_to_collect:
        datas, binaries, hiddenimports = collect_all(pkg)
        for d in datas:
            args.extend(['--add-data', f"{d[0]}{sep}{d[1]}"])
        for b in binaries:
            args.extend(['--add-binary', f"{b[0]}{sep}{b[1]}"])
        for hi in hiddenimports:
            args.extend(['--hidden-import', hi])

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
    'PyQt5', 'PyQt6', 'nbformat', 'nbconvert',
    'tensorboard', 'torch.distributed', 'torch.nn.modules.export', 'torch.testing',
    'matplotlib.tests', 'numpy.tests', 'expecttest', 'hypothesis',
    'onnxscript', 'onnx', 'opt_einsum', 'triton', 'IPython.kernel', 'cupy',
    'numba.np.ufunc.tbbpool'  # <--- ADD THIS to fix the tbb12.dll error
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

        # Cleanup: Delete the 'build' directory to save space as it can be very large
        build_dir = "build"
        if os.path.exists(build_dir):
            print(f"Cleaning up {build_dir} directory...")
            shutil.rmtree(build_dir)
            
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
