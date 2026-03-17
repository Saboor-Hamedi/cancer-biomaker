
# publish.py
#  script for you. This is your Python-equivalent of npm run dist:publish.
# python publish.py

import os
import sys
import subprocess
import re

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

    # 2. Check for Executable
    exe_path = os.path.join("dist", "CancerDetectionDashboard.exe")
    # Also check for Inno Setup output if you used it
    installer_path = None
    for file in os.listdir("."):
        if file.endswith(".exe") and ("setup" in file.lower() or "installer" in file.lower()):
            installer_path = file
            break
            
    asset_to_upload = str(installer_path if installer_path else exe_path)

    if not asset_to_upload or not os.path.exists(asset_to_upload):
        print(f"❌ Error: Required asset not found at {asset_to_upload}")
        print("💡 Hint: Run 'python build_exe.py' first!")
        return
    
    print(f"✅ Found asset to upload: {asset_to_upload}")

    # 3. Git Operations
    print("🔄 Syncing with GitHub...")
    run_cmd("git add .")
    run_cmd(f'git commit -m "Release {tag}"')
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
