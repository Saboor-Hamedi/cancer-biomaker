import json
import logging
import threading
import urllib.request
import urllib.error
import os
import sys
import subprocess
from tkinter import messagebox, ttk
import tkinter as tk

log = logging.getLogger(__name__)

class _UpdateDialog(tk.Toplevel):
    """Custom professional alert for new updates."""
    def __init__(self, parent, version, on_install, on_skip):
        super().__init__(parent)
        self.title("✨ Clinical Update Available")
        self.geometry("480x240")
        self.resizable(False, False)
        self.configure(bg="#FFFFFF")
        self.transient(parent)
        self.grab_set()
        
        self.result = "remind" # Default
        
        # Center on parent
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 240
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 120
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Content
        content = tk.Frame(self, bg="#FFFFFF", padx=30, pady=25)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content, text=f"Version v{version} is ready!", 
                 font=("Segoe UI", 14, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor=tk.W)
        
        tk.Label(content, text="A new clinical production build has been released on GitHub.\nUpdating ensures you have the latest AI diagnostic models and security patches.",
                 font=("Segoe UI", 10), fg="#64748B", bg="#FFFFFF", justify=tk.LEFT, wraplength=420).pack(anchor=tk.W, pady=(10, 20))

        # Buttons
        btn_frame = tk.Frame(content, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def set_result(r):
            self.result = r
            if r == "install": on_install()
            if r == "skip": on_skip(version)
            self.destroy()

        # Primary Action
        install_btn = tk.Button(btn_frame, text="Install Now", bg="#3B82F6", fg="white", 
                                font=("Segoe UI", 10, "bold"), padx=20, pady=8, 
                                relief=tk.FLAT, cursor="hand2", command=lambda: set_result("install"))
        install_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Remind Later
        tk.Button(btn_frame, text="Remind Later", bg="#F1F5F9", fg="#475569", 
                  font=("Segoe UI", 10), padx=15, pady=8, 
                  relief=tk.FLAT, cursor="hand2", command=lambda: set_result("remind")).pack(side=tk.RIGHT)

        # Skip Version
        tk.Button(btn_frame, text="Skip This Version", bg="#FFFFFF", fg="#94A3B8", 
                  font=("Segoe UI", 9, "underline"), borderwidth=0, activebackground="#FFFFFF",
                  cursor="hand2", command=lambda: set_result("skip")).pack(side=tk.LEFT)

class UpdateManager:
    """Manages application updates via GitHub Releases with auto-download and install. (User Requested Refined Alert System)"""
    
    GITHUB_REPO = "Saboor-Hamedi/cancer-biomaker"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    SKIP_FILE = ".version_skip"
    
    def __init__(self, root, status_callback=None, current_version="1.0.0", user_data_path=None):
        self.root = root
        self.status_callback = status_callback
        self.current_version = current_version
        self.latest_release = None
        self.download_url = None
        
        # User writable path for updates and configs
        self.user_data_dir = user_data_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.update_dir = os.path.join(self.user_data_dir, "updates")
        
        if not os.path.exists(self.update_dir):
            try: os.makedirs(self.update_dir)
            except: pass
            
        # Cleanup any stale updates from previous sessions on init
        threading.Thread(target=self.clear_old_updates, daemon=True).start()

    def check_for_updates(self, silent=True):
        """Checks GitHub for a newer version."""
        def _check():
            try:
                log.info("Checking for updates at %s", self.API_URL)
                if self.status_callback and not silent:
                    self.root.after(0, lambda: self.status_callback("Checking for updates...", "#3B82F6"))

                req = urllib.request.Request(self.API_URL, headers={'User-Agent': 'Cancer-Detection-App'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    tag_name = data.get('tag_name', '0.0').replace('v', '')
                    self.latest_release = data
                    
                    # Store installers for this version
                    assets = data.get('assets', [])
                    for asset in assets:
                        if asset.get('name', '').endswith('.exe'):
                            self.download_url = asset.get('browser_download_url')
                            break

                    if self._is_newer(tag_name, self.current_version):
                        # Check if user opted to skip this specific version
                        if silent and self._is_skipped(tag_name):
                            log.info("Update v%s available but skipped by user.", tag_name)
                            return

                        msg = f"New version available: v{tag_name}!"
                        log.info(msg)
                        if self.status_callback:
                            self.root.after(0, lambda: self.status_callback(msg, "#3B82F6"))
                        
                        self.root.after(0, lambda: self._prompt_update(tag_name))
                    elif not silent:
                        log.info("Application is up to date.")
                        self.root.after(0, lambda: self.status_callback("System Up to Date", "#10B981"))
                        self.root.after(0, lambda: messagebox.showinfo("System Check", 
                            f"Your clinical dashboard is up to date!\n\nCurrent Version: v{self.current_version}\nLatest Version: v{tag_name}"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    log.info("No remote releases found (HTTP 404). This is expected if no releases are published yet.")
                    if not silent:
                        self.root.after(0, lambda: self.status_callback("App is up to date", "#10B981"))
                else:
                    log.error("Update check HTTP error: %s", e)
                    if not silent:
                        self.root.after(0, lambda: self.status_callback(f"Updates unavailable ({e.code})", "red"))
            except Exception as e:
                log.error("Update check failed: %s", e)
                if not silent:
                    self.root.after(0, lambda: self.status_callback("Update Check Failed", "red"))
                    # Don't show redundant error box if it's just a network timeout

        threading.Thread(target=_check, daemon=True).start()

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            return l_parts > c_parts
        except: return latest != current

    def _is_skipped(self, version):
        """Checks if the version matches the locally stored skip mark."""
        skip_path = os.path.join(self.user_data_dir, self.SKIP_FILE)
        if os.path.exists(skip_path):
            try:
                with open(skip_path, 'r') as f:
                    return f.read().strip() == version
            except: pass
        return False

    def _save_skip(self, version):
        """Saves a version tag to be excluded from auto-notifications."""
        skip_path = os.path.join(self.user_data_dir, self.SKIP_FILE)
        try:
            with open(skip_path, 'w') as f:
                f.write(version)
            log.info("Version %s added to skip list.", version)
        except: pass

    def _prompt_update(self, version):
        """Shows the new premium update alert."""
        _UpdateDialog(self.root, version, self._start_download, self._save_skip)

    def _start_download(self):
        """Handles the download with a progress bar."""
        if not self.download_url:
            messagebox.showwarning("Update Error", "No installer found in assets. Opening release page.")
            import webbrowser 
            webbrowser.open(self.latest_release.get('html_url', f"https://github.com/{self.GITHUB_REPO}/releases/latest"))
            return

        # Create progress window
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Syncing Clinical Update")
        progress_win.geometry("420x180")
        progress_win.configure(bg="#FFFFFF")
        progress_win.transient(self.root)
        progress_win.grab_set()

        # Center
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        progress_win.geometry(f"+{max(0, x)}+{max(0, y)}")
        
        tk.Label(progress_win, text="Downloading System Update", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#0F172A").pack(pady=(25, 5))
        lbl_status = tk.Label(progress_win, text="Initializing...", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B")
        lbl_status.pack()
        
        progress = ttk.Progressbar(progress_win, length=320, mode='determinate')
        progress.pack(pady=15)
        
        def _download_thread():
            try:
                tag_name = self.latest_release.get('tag_name', 'latest')
                temp_file = os.path.join(self.update_dir, f"Update_{tag_name}.exe")
                
                req = urllib.request.Request(str(self.download_url), headers={'User-Agent': 'Cancer-Detection-App'})
                with urllib.request.urlopen(req) as response:
                    total_size = int(response.info().get('Content-Length', 0))
                    downloaded = 0
                    
                    with open(temp_file, 'wb') as f:
                        while True:
                            chunk = response.read(65536) # Faster 64KB chunks
                            if not chunk: break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = (downloaded / total_size) * 100
                                mb = downloaded / (1024 * 1024)
                                total_mb = total_size / (1024 * 1024)
                                self.root.after(0, lambda p=percent, m=mb, t=total_mb: [
                                    progress.configure(value=p),
                                    lbl_status.config(text=f"Progress: {m:.1f}MB / {t:.1f}MB ({int(p)}%)")
                                ])
                
                self.root.after(0, progress_win.destroy)
                if messagebox.askyesno("Update Downloaded", "The new clinical build is ready. The application will now close to run the installer.\n\nReady?"):
                    self._install_and_restart(temp_file)
            except Exception as e:
                log.error("Download failed: %s", e)
                self.root.after(0, lambda: [messagebox.showerror("Update Error", f"Sync failed: {e}"), progress_win.destroy()])

        threading.Thread(target=_download_thread, daemon=True).start()

    def _install_and_restart(self, temp_file):
        """Launches the new installer and exits the current app."""
        try:
            log.info("Launching installer: %s", temp_file)
            # Use /SILENT if it's an Inno Setup installer
            subprocess.Popen([temp_file, "/SILENT", "/SP-"], shell=True) 
            self.root.quit()
            sys.exit(0)
        except Exception as e:
            log.error("Installation launch failed: %s", e)
            messagebox.showerror("Installation Error", f"Could not launch installer: {e}")

    def clear_old_updates(self):
        """Deletes any .exe files in the updates folder."""
        try:
            if not os.path.exists(self.update_dir): return
            for f in os.listdir(self.update_dir):
                if f.endswith(".exe"):
                    try: os.remove(os.path.join(self.update_dir, f))
                    except: pass
            log.info("Update cache cleared.")
        except Exception as e:
            log.warning("Could not clear update cache: %s", e)
