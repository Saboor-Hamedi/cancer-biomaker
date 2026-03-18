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

class UpdateManager:
    """Manages application updates via GitHub Releases with auto-download and install."""
    
    GITHUB_REPO = "Saboor-Hamedi/cancer-biomaker"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self, root, status_callback=None, current_version="1.0.0"):
        self.root = root
        self.status_callback = status_callback
        self.current_version = current_version
        self.latest_release = None
        self.download_url = None
        
        # Consistent folder path for updates
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.update_dir = os.path.join(self.base_dir, "updates")
        
        # Cleanup any stale updates from previous sessions on init
        threading.Thread(target=self.clear_old_updates, daemon=True).start()

    def check_for_updates(self, silent=True):
        """Checks GitHub for a newer version."""
        def _check():
            try:
                log.info("Checking for updates at %s", self.API_URL)
                # Removed initial status_callback for silent checks as per new logic
                # if self.status_callback and not silent:
                #     self.root.after(0, lambda: self.status_callback("Checking for updates...", "blue"))

                req = urllib.request.Request(self.API_URL, headers={'User-Agent': 'Cancer-Detection-App'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    
                    tag_name = data.get('tag_name', '0.0').replace('v', '')
                    self.latest_release = data
                    
                    # Look for a .exe in the assets
                    assets = data.get('assets', [])
                    for asset in assets:
                        if asset.get('name', '').endswith('.exe'):
                            self.download_url = asset.get('browser_download_url')
                            break

                    if self._is_newer(tag_name, self.current_version):
                        msg = f"New version available: v{tag_name}!"
                        log.info(msg)
                        if self.status_callback:
                            self.root.after(0, lambda: self.status_callback(msg, "#3B82F6"))
                        
                        # Always prompt if a new version is found, silent only affects initial check
                        self.root.after(0, lambda: self._prompt_update(tag_name))
                    elif not silent: # Only show "up to date" message if not silent
                        self.root.after(0, lambda: messagebox.showinfo("System Check", 
                            f"Your clinical dashboard is up to date!\n\nCurrent Version: v{self.current_version}\nLatest Version: v{tag_name}"))
                        log.info("Application is up to date.")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    log.info("No releases found on GitHub (404).")
                else:
                    log.error("Update check HTTP error: %s", e)
            except Exception as e:
                log.error("Update check failed: %s", e)
                if not silent:
                    self.root.after(0, lambda: messagebox.showerror("Update Error", f"Could not check for updates:\n{str(e)}"))

        threading.Thread(target=_check, daemon=True).start()

    def _is_newer(self, latest, current):
        """Simple version comparison (semantic-ish)."""
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            return l_parts > c_parts
        except:
            return latest != current

    def _prompt_update(self, version):
        """Shows a custom dialog to update."""
        if messagebox.askyesno("Update Available", f"A new version (v{version}) is available!\n\nWould you like to download and install it now?"):
            self._start_download()

    def _start_download(self):
        """Handles the download with a progress bar."""
        if not self.download_url:
            messagebox.showwarning("Update Error", "No executable found in the release assets. Opening release page instead.")
            import webbrowser 
            url = f"https://github.com/{self.GITHUB_REPO}/releases/latest"
            if self.latest_release:
                url = self.latest_release.get('html_url', url)
            webbrowser.open(url)
            return

        # Create progress window
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Downloading Update")
        progress_win.geometry("400x150")
        progress_win.transient(self.root)
        progress_win.grab_set()
        
        ttk.Label(progress_win, text="Downloading new version...", font=("Segoe UI", 10)).pack(pady=20)
        progress = ttk.Progressbar(progress_win, length=300, mode='determinate')
        progress.pack(pady=10)
        
        def _download_thread():
            try:
                if not self.latest_release:
                    raise ValueError("Release data not initialized")
                
                tag_name = self.latest_release.get('tag_name', 'latest')
                temp_file = os.path.join(self.update_dir, f"CancerDetection_Update_{tag_name}.exe")
                
                if not self.download_url:
                    raise ValueError("Download URL is missing")

                log.info("Starting download: %s", self.download_url)
                req = urllib.request.Request(str(self.download_url), headers={'User-Agent': 'Cancer-Detection-App'})
                with urllib.request.urlopen(req) as response:
                    total_size = int(response.info().get('Content-Length', 0))
                    downloaded = 0
                    
                    with open(temp_file, 'wb') as f:
                        while True:
                            chunk = response.read(16384) # Larger chunk for faster speed
                            if not chunk: break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = (downloaded / total_size) * 100
                                self.root.after(0, lambda p=percent: progress.configure(value=p))
                
                progress_win.destroy()
                log.info("Download completed: %s", temp_file)
                if messagebox.askyesno("Download Complete", "The update has been downloaded. The application will now restart to finish the installation."):
                    self._install_and_restart(temp_file)
            except Exception as e:
                log.error("Download failed: %s", e)
                self.root.after(0, lambda: messagebox.showerror("Download Error", f"Failed to download update: {e}"))
                progress_win.destroy()

        threading.Thread(target=_download_thread, daemon=True).start()

    def _install_and_restart(self, temp_file):
        """Launches the new installer and exits the current app."""
        try:
            log.info("Launching installer: %s", temp_file)
            if getattr(sys, 'frozen', False):
                # We are running as an EXE
                # /SILENT for Inno Setup avoids repeated questions
                subprocess.Popen([temp_file, "/SILENT", "/SP-"], shell=True) 
            else:
                subprocess.Popen([temp_file], shell=True)
                
            self.root.quit()
            sys.exit(0)
        except Exception as e:
            log.error("Installation launch failed: %s", e)
            messagebox.showerror("Installation Error", f"Could not launch installer: {e}")

    def clear_old_updates(self):
        """Deletes any .exe files in the updates folder to save space."""
        try:
            if not os.path.exists(self.update_dir):
                return
            
            for f in os.listdir(self.update_dir):
                if f.endswith(".exe"):
                    try:
                        os.remove(os.path.join(self.update_dir, f))
                    except:
                        pass
            log.info("Update cache cleared.")
        except Exception as e:
            log.warning("Could not clear update cache: %s", e)
