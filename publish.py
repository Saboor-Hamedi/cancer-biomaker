
# publish.py
#  script for you. This is your Python-equivalent of npm run dist:publish.
# python build_exe.py
# python publish.py
# set PRESERVE_MODELS=true

import os
import sys
import subprocess
import re
import shutil

def run_cmd(cmd):
    """Utility to run shell commands and return output."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"Output: {e.output}")
        print(f"Stderr: {e.stderr}")
        return None

def get_version():
    """Extract version from main.py."""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for global VERSION or self.version assignment
            match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
            if not match:
                match = re.search(r'self\.version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error reading version: {e}")
    return None

def publish():
    print("🚀 Starting Professional Publish Workflow...")

    # 1. Get Version
    version = get_version()
    if not version:
        print("❌ Error: Could not find version in main.py")
        return
    tag = f"v{version}"
    print(f"📦 Target Version: {tag}")

    # 2. Check for Assets
    # Priority: Inno Installer -> ZIP Bundle -> Standalone EXE
    dist_dir = "dist"
    installer_path = os.path.join(dist_dir, "CancerDetectionDashboard_Installer.exe")
    portable_zip = "CancerDetectionDashboard_Portable.zip"
    onedir_exe = os.path.join(dist_dir, "CancerDetectionDashboard", "CancerDetectionDashboard.exe")
    
    asset_to_upload = None
    
    # Try to find the installer first (most professional)
    if os.path.exists(installer_path):
        asset_to_upload = installer_path
    elif os.path.exists(portable_zip):
        asset_to_upload = portable_zip
    elif os.path.exists(onedir_exe):
        asset_to_upload = onedir_exe

    if not asset_to_upload or not os.path.exists(asset_to_upload):
        print(f"❌ Error: Required assets not found.")
        print("💡 Hint: Run 'python build_exe.py' first to generate the Installer and Portable ZIP!")
        return
    
    print(f"✅ Found asset to upload: {asset_to_upload}")

    # 3. Git Operations
    print("🔄 Syncing with GitHub...")
    run_cmd("git config core.autocrlf true")
    run_cmd("git add main.py publish.py build_exe.py DOCUMENTATION.md README.md requirements.txt")
    # Selective add for folders to keep git clean
    run_cmd("git add controllers/ handlers/ logic/ ui/ utils/ views/ styles.py")
    
    run_cmd(f'git commit -m "Release {tag} - Optimized Clinical Build"')
    print("🚀 Pushing to origin/main...")
    run_cmd("git push origin main")

    # 4. Create Tag
    print(f"🏷️ Creating tag {tag}...")
    # Delete local and remote tag if it exists (allows re-publishing)
    subprocess.run(f"git tag -d {tag}", shell=True, capture_output=True)
    subprocess.run(f"git push --delete origin {tag}", shell=True, capture_output=True)
    
    run_cmd(f"git tag {tag}")
    run_cmd(f"git push origin {tag}")

    # 5. GitHub Release using 'gh' CLI
    print(f"✨ Creating GitHub Release {tag}...")
    release_cmd = f'gh release create {tag} "{asset_to_upload}" --title "Release {tag}" --notes "Automated clinical production build."'
    
    # If release already exists, we might need to overwrite it
    check_release = run_cmd(f"gh release view {tag}")
    if check_release:
        print(f"⚠️ Release {tag} already exists. Updating assets...")
        run_cmd(f'gh release upload {tag} "{asset_to_upload}" --clobber')
    else:
        run_cmd(release_cmd)

    print("\n" + "="*50)
    print("SUCCESS! Your update is now live on GitHub.")
    print(f"Users running the app will now see the v{version} update.")
    print("="*50)

if __name__ == "__main__":
    # Ensure gh is authenticated
    auth_check = run_cmd("gh auth status")
    if not auth_check or "Logged in to github.com" not in auth_check:
        print("❌ Error: GitHub CLI (gh) is not authenticated.")
        print("💡 Run 'gh auth login' first.")
        sys.exit(1)
        
    publish()
