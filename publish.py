
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

    # Priority: Inno Installer -> ZIP Bundle
    # DO NOT upload just 'dist/App.exe' — it will fail (missing DLLs)
    # The 'onedir' build requires the full folder to be zipped.
    dist_dir = "dist"
    installer_path = os.path.join(dist_dir, "CancerDetectionDashboard_Installer.exe")
    portable_zip = "CancerDetectionDashboard_Portable.zip"
    
    asset_to_upload = None
    
    if os.path.exists(installer_path):
        asset_to_upload = installer_path
        print(f"📦 Ready: Found PROFESSIONAL INSTALLER ({asset_to_upload})")
    elif os.path.exists(portable_zip):
        asset_to_upload = portable_zip
        print(f"📦 Ready: Found PORTABLE ZIP BUNDLE ({asset_to_upload})")

    if not asset_to_upload:
        print(f"❌ Error: Required assets (Installer or ZIP) NOT FOUND.")
        print("💡 Ensure 'python build_exe.py' runs completely to the end.")
        return
    
    print(f"🚀 Publishing asset: {asset_to_upload}")

    # 3. Git Operations
    print("🔄 Syncing with GitHub...")
    # Dynamically find current branch
    branch = run_cmd("git rev-parse --abbrev-ref HEAD") or "main"
    print(f"🌲 Active Branch: {branch}")
    
    run_cmd("git config core.autocrlf true")
    run_cmd(f'git add .') # Add all tracked and new files (within reasons of .gitignore)
    
    run_cmd(f'git commit -m "Release {tag} - Clinical Dashboard Build"')
    print(f"🚀 Pushing to origin/{branch}...")
    run_cmd(f"git push origin {branch}")

    # 4. Create Tag
    print(f"🏷️ Tag Management: {tag}...")
    subprocess.run(f"git tag -d {tag}", shell=True, capture_output=True)
    subprocess.run(f"git push --delete origin {tag}", shell=True, capture_output=True)
    
    run_cmd(f"git tag {tag}")
    run_cmd(f"git push origin {tag}")

    # 5. GitHub Release using 'gh' CLI
    print(f"✨ Orchestrating GitHub Release {tag}...")
    
    # We will upload BOTH the Installer and the Portable ZIP for professional distribution
    assets = [f'"{installer_path}"' if os.path.exists(installer_path) else None,
              f'"{portable_zip}"' if os.path.exists(portable_zip) else None]
    assets_str = " ".join([a for a in assets if a])
    
    if not assets_str:
        print("❌ Error: No release assets found (ZIP/Installer). Build failed?")
        return

    # Check if release exists
    check_release = run_cmd(f"gh release view {tag}")
    if check_release:
        print(f"⚠️ Release {tag} exists. Refreshing assets...")
        run_cmd(f'gh release upload {tag} {assets_str} --clobber')
    else:
        print(f"🏗️ Creating New Release: {tag}")
        run_cmd(f'gh release create {tag} {assets_str} --title "Clinical AI Dashboard {tag}" --notes "Automated clinical production build with multi-model forensic analysis."')

    print("\n" + "="*60)
    print("PROFESSIONAL DEPLOYMENT SUCCESSFUL!")
    print(f"🚀 Branch: {branch} | Tag: {tag}")
    print(f"📦 Assets Deployed: {assets_str}")
    print("="*60)

if __name__ == "__main__":
    # Ensure gh is authenticated
    auth_check = run_cmd("gh auth status")
    if not auth_check or "Logged in to github.com" not in auth_check:
        print("❌ Error: GitHub CLI (gh) is not authenticated.")
        print("💡 Run 'gh auth login' first.")
        sys.exit(1)
        
    publish()
