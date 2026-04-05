import json
import logging
import threading
import urllib.request
import urllib.error
import os
import sys
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QMessageBox, QProgressBar, QFrame, QApplication)
from PySide6.QtCore import Qt, QTimer, Signal, QObject

log = logging.getLogger(__name__)

class _UpdateDialog(QDialog):
    """Custom professional alert for new updates."""
    def __init__(self, parent, version, on_install, on_skip):
        super().__init__(parent)
        self.setWindowTitle("✨ Clinical Update Available")
        self.setFixedSize(480, 240)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        self.on_install = on_install
        self.on_skip = on_skip
        self.version = version
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        
        title = QLabel(f"Version v{version} is ready!")
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; color: #0F172A;")
        layout.addWidget(title)
        
        desc = QLabel("A new clinical production build has been released on GitHub.\nUpdating ensures you have the latest AI diagnostic models and security patches.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-family: 'Segoe UI'; font-size: 11px; color: #64748B;")
        layout.addWidget(desc)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        btn_skip = QPushButton("Skip This Version")
        btn_skip.setStyleSheet("color: #94A3B8; font-family: 'Segoe UI'; border: none; text-decoration: underline;")
        btn_skip.setCursor(Qt.PointingHandCursor)
        btn_skip.clicked.connect(self._do_skip)
        btn_layout.addWidget(btn_skip)
        
        btn_layout.addStretch()
        
        btn_remind = QPushButton("Remind Later")
        btn_remind.setStyleSheet("background-color: #F1F5F9; color: #475569; padding: 8px 15px; border-radius: 4px;")
        btn_remind.setCursor(Qt.PointingHandCursor)
        btn_remind.clicked.connect(self.reject)
        btn_layout.addWidget(btn_remind)
        
        btn_install = QPushButton("Install Now")
        btn_install.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 20px; border-radius: 4px;")
        btn_install.setCursor(Qt.PointingHandCursor)
        btn_install.clicked.connect(self._do_install)
        btn_layout.addWidget(btn_install)
        
        layout.addLayout(btn_layout)

    def _do_install(self):
        self.accept()
        self.on_install()
        
    def _do_skip(self):
        self.accept()
        self.on_skip(self.version)

class UpdateManager(QObject):
    """Manages application updates via GitHub Releases with auto-download and install. (PySide6 Edition)."""
    
    GITHUB_REPO = "Saboor-Hamedi/cancer-biomaker"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    SKIP_FILE = ".version_skip"
    
    status_signal = Signal(str, str)
    
    def __init__(self, parent=None, status_callback=None, current_version="1.0.0", user_data_path=None):
        super().__init__(parent)
        self.parent_win = parent
        if status_callback:
            self.status_signal.connect(status_callback)
            
        self.current_version = current_version
        self.latest_release = None
        self.download_url = None
        
        self.user_data_dir = user_data_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.update_dir = os.path.join(self.user_data_dir, "updates")
        
        if not os.path.exists(self.update_dir):
            try: os.makedirs(self.update_dir)
            except: pass
            
        threading.Thread(target=self.clear_old_updates, daemon=True).start()

    def check_for_updates(self, silent=True):
        """Checks GitHub for a newer version."""
        def _check():
            try:
                log.info("Checking for updates at %s", self.API_URL)
                if not silent:
                    self.status_signal.emit("Checking for updates...", "#3B82F6")

                req = urllib.request.Request(self.API_URL, headers={'User-Agent': 'Cancer-Detection-App'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    tag_name = data.get('tag_name', '0.0').replace('v', '')
                    self.latest_release = data
                    
                    assets = data.get('assets', [])
                    # Strategic Multi-Tier Asset Discovery
                    exe_asset = next((a for a in assets if a.get('name', '').endswith('.exe')), None)
                    zip_asset = next((a for a in assets if a.get('name', '').endswith('.zip')), None)

                    if exe_asset:
                        self.download_url = exe_asset.get('browser_download_url')
                    elif zip_asset:
                        self.download_url = zip_asset.get('browser_download_url')
                    else:
                        self.download_url = None

                    if self._is_newer(tag_name, self.current_version):
                        if silent and self._is_skipped(tag_name):
                            return

                        msg = f"New version available: v{tag_name}!"
                        self.status_signal.emit(msg, "#3B82F6")
                        QTimer.singleShot(0, lambda: self._prompt_update(tag_name))
                    elif not silent:
                        self.status_signal.emit("System Up to Date", "#10B981")
                        QTimer.singleShot(0, lambda: QMessageBox.information(self.parent_win, "System Check", 
                            f"Your clinical dashboard is up to date!\n\nCurrent Version: v{self.current_version}\nLatest Version: v{tag_name}"))
                            
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    if not silent: self.status_signal.emit("App is up to date", "#10B981")
                else:
                    if not silent: self.status_signal.emit(f"Updates unavailable ({e.code})", "red")
            except Exception as e:
                log.error("Update check failed: %s", e)
                if not silent: self.status_signal.emit("Update Check Failed", "red")

        threading.Thread(target=_check, daemon=True).start()

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            return l_parts > c_parts
        except: return latest != current

    def _is_skipped(self, version):
        skip_path = os.path.join(self.user_data_dir, self.SKIP_FILE)
        if os.path.exists(skip_path):
            try:
                with open(skip_path, 'r') as f:
                    return f.read().strip() == version
            except: pass
        return False

    def _save_skip(self, version):
        skip_path = os.path.join(self.user_data_dir, self.SKIP_FILE)
        try:
            with open(skip_path, 'w') as f: f.write(version)
        except: pass

    def _prompt_update(self, version):
        dialog = _UpdateDialog(self.parent_win, version, self._start_download, self._save_skip)
        dialog.exec()

    def _start_download(self):
        if not self.download_url:
            QMessageBox.warning(self.parent_win, "Update Error", "No installer found in assets. Opening release page.")
            import webbrowser 
            webbrowser.open(self.latest_release.get('html_url', f"https://github.com/{self.GITHUB_REPO}/releases/latest"))
            return

        self.progress_win = QDialog(self.parent_win)
        self.progress_win.setWindowTitle("Syncing Clinical Update")
        self.progress_win.setFixedSize(420, 180)
        self.progress_win.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self.progress_win)
        
        title = QLabel("Downloading System Update")
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; color: #0F172A;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.lbl_status = QLabel("Initializing...")
        self.lbl_status.setStyleSheet("color: #64748B;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        layout.addWidget(self.progress)
        
        self.progress_win.show()

        def _download_thread():
            try:
                tag_name = self.latest_release.get('tag_name', 'latest')
                # Dynamic Extension Matching
                ext = ".exe" if self.download_url.lower().endswith(".exe") else ".zip"
                temp_file = os.path.join(self.update_dir, f"Update_{tag_name}{ext}")
                
                req = urllib.request.Request(str(self.download_url), headers={'User-Agent': 'Cancer-Detection-App'})
                with urllib.request.urlopen(req) as response:
                    total_size = int(response.info().get('Content-Length', 0))
                    downloaded = 0
                    
                    with open(temp_file, 'wb') as f:
                        while True:
                            chunk = response.read(65536)
                            if not chunk: break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                p = int((downloaded / total_size) * 100)
                                mb = downloaded / (1024 * 1024)
                                tmb = total_size / (1024 * 1024)
                                QTimer.singleShot(0, lambda val=p, txt=f"{mb:.1f}MB / {tmb:.1f}MB ({p}%)": [
                                    self.progress.setValue(val),
                                    self.lbl_status.setText(txt)
                                ])
                
                QTimer.singleShot(0, lambda: self._on_download_complete(temp_file))
            except Exception as e:
                log.error("Download failed: %s", e)
                QTimer.singleShot(0, lambda: [QMessageBox.critical(self.parent_win, "Update Error", f"Sync failed: {e}"), self.progress_win.close()])

        threading.Thread(target=_download_thread, daemon=True).start()

    def _on_download_complete(self, temp_file):
        self.progress_win.close()
        reply = QMessageBox.question(self.parent_win, "Update Downloaded", "The new clinical build is ready.\nThe application will now close to run the installer.\n\nReady?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._install_and_restart(temp_file)

    def _install_and_restart(self, temp_file):
        try:
            if temp_file.lower().endswith(".exe"):
                # Professional Silent Installation
                subprocess.Popen([temp_file, "/SILENT", "/SP-"], shell=True) 
                QApplication.quit()
            else:
                # Portable ZIP Fallback: Reveal in Explorer for manual extraction
                import os
                os.startfile(os.path.dirname(temp_file))
                QMessageBox.information(self.parent_win, "Portable Update Ready", 
                    "This version was released as a Portable ZIP.\n\nThe update folder has been opened. Please extract the contents to your app directory to finish the update.")
        except Exception as e:
            QMessageBox.critical(self.parent_win, "Installation Error", f"Could not launch installer: {e}")

    def clear_old_updates(self):
        try:
            if not os.path.exists(self.update_dir): return
            for f in os.listdir(self.update_dir):
                if f.endswith(".exe"):
                    try: os.remove(os.path.join(self.update_dir, f))
                    except: pass
        except: pass

