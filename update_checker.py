import requests
import os
import json
from packaging import version
import hashlib
import tempfile
import shutil
import sys
from datetime import datetime

class UpdateChecker:
    def __init__(self):
        self.current_version = "1.0.0"
        self.github_repo = "YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"  # Replace with your GitHub repo
        self.version_file_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/version.json"
        self.update_check_interval = 24 * 60 * 60  # 24 hours
        self.version_file = "version_check.json"

    def check_for_updates(self):
        """Check for available updates"""
        try:
            # Get last check time
            last_check = self.get_last_check_time()
            current_time = datetime.now().timestamp()

            # Check if enough time has passed
            if last_check and (current_time - last_check) < self.update_check_interval:
                return None

            # Get version info from GitHub
            response = requests.get(self.version_file_url, timeout=5)
            if response.status_code == 200:
                update_info = response.json()
                latest_version = update_info.get('version')
                download_url = update_info.get('download_url')
                changelog = update_info.get('changelog', '')
                file_hash = update_info.get('file_hash', '')

                if latest_version and version.parse(latest_version) > version.parse(self.current_version):
                    return {
                        'version': latest_version,
                        'download_url': download_url,
                        'changelog': changelog,
                        'file_hash': file_hash
                    }

                # Update last check time
                self.save_last_check_time(current_time)

        except Exception as e:
            print(f"Error checking for updates: {str(e)}")

        return None

    def download_update(self, download_url, file_hash):
        """Download and verify the update"""
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, "clipboard_manager_update.exe")

            # Download the file with progress tracking
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                downloaded = 0

                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                progress = int(100 * downloaded / total_size)
                                print(f"Download progress: {progress}%")

                # Verify file hash
                if self.verify_file_hash(temp_file, file_hash):
                    return temp_file
                else:
                    print("Update file verification failed")
                    os.remove(temp_file)

        except Exception as e:
            print(f"Error downloading update: {str(e)}")

        return None

    def verify_file_hash(self, file_path, expected_hash):
        """Verify the downloaded file's hash"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest() == expected_hash
        except:
            return False

    def install_update(self, update_file):
        """Install the update"""
        try:
            # Get the current executable path
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
            else:
                current_exe = os.path.abspath(__file__)

            # Create backup
            backup_file = current_exe + ".backup"
            shutil.copy2(current_exe, backup_file)

            # Replace the current executable
            shutil.copy2(update_file, current_exe)

            # Clean up
            os.remove(update_file)
            os.remove(backup_file)

            return True
        except Exception as e:
            print(f"Error installing update: {str(e)}")
            return False

    def get_last_check_time(self):
        """Get the timestamp of the last update check"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('last_check')
        except:
            pass
        return None

    def save_last_check_time(self, timestamp):
        """Save the timestamp of the last update check"""
        try:
            with open(self.version_file, 'w') as f:
                json.dump({'last_check': timestamp}, f)
        except:
            pass 