import PyInstaller.__main__
import os
import sys
import shutil

def build():
    print("--- Starting Production Build for Cancer Detection Dashboard ---")
    
    # Define the entry point
    entry_point = "main.py"
    
    if not os.path.exists(entry_point):
        print(f"Error: {entry_point} not found!")
        return

    # Assets and modules to include
    # Format: "source;destination" (Windows uses semicolon)
    sep = ";" if sys.platform == "win32" else ":"
    
    added_data = [
        f"background.png{sep}.",
        f"styles.py{sep}.",
        f"controllers{sep}controllers",
        f"handlers{sep}handlers",
        f"logic{sep}logic",
        f"ui{sep}ui",
        f"utils{sep}utils",
        f"views{sep}views",
    ]

    # PyInstaller arguments
    args = [
        entry_point,
        '--onefile',                      # Single executable
        '--windowed',                     # No console window
        '--name=CancerDetectionDashboard', # Name of the exe
        '--clean',                        # Clean cache before build
        '--noconfirm',                    # Overwrite existing dist
    ]

    # Add all data folders
    for data in added_data:
        args.extend(['--add-data', data])

    # Add hidden imports that PyInstaller might miss for AI libraries
    hidden_imports = [
        'sklearn.utils._typedefs',
        'sklearn.neighbors._partition_nodes',
        'sklearn.neighbors._quad_tree',
        'sklearn.tree._utils',
        'torch',
        'xgboost',
    ]
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])

    print(f"Running PyInstaller with args: {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print(f"Your executable is located in: {os.path.abspath('dist/CancerDetectionDashboard.exe')}")
        print("="*50)
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
