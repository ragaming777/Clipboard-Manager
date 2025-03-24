import os
import json
import hashlib
import requests
import base64
from datetime import datetime
import mimetypes

class GitHubUploader:
    def __init__(self, username, token, repo):
        self.username = username
        self.token = token
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_release(self, version, changelog):
        """Create a new release"""
        url = f"{self.base_url}/releases"
        data = {
            "tag_name": f"v{version}",
            "name": f"Version {version}",
            "body": changelog,
            "draft": False,
            "prerelease": False
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            print(f"Error creating release: {response.text}")
            return None
        return response.json()

    def upload_release_asset(self, release_url, file_path):
        """Upload a file as a release asset"""
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        # Get the upload URL from the release
        response = requests.get(release_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Error getting release info: {response.text}")
            return None
            
        upload_url = response.json()['upload_url'].replace('{?name,label}', f'?name={file_name}')
        
        # Upload the file
        with open(file_path, 'rb') as f:
            headers = {
                "Authorization": f"token {self.token}",
                "Content-Type": content_type
            }
            response = requests.post(upload_url, headers=headers, data=f)
            
            if response.status_code != 201:
                print(f"Error uploading asset: {response.text}")
                return None
                
            return response.json()['browser_download_url']

    def upload_file(self, file_path, version, changelog):
        """Upload a new version using GitHub Releases"""
        try:
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            
            # Create a new release
            release = self.create_release(version, changelog)
            if not release:
                return False

            # Upload the file as a release asset
            download_url = self.upload_release_asset(release['url'], file_path)
            if not download_url:
                return False

            # Create version.json content
            version_info = {
                "version": version,
                "download_url": download_url,
                "changelog": changelog,
                "file_hash": file_hash,
                "release_date": datetime.now().strftime("%Y-%m-%d")
            }

            # Update version.json in the repository
            version_url = f"{self.base_url}/contents/version.json"
            version_data = {
                "message": f"Update version info to {version}",
                "content": base64.b64encode(json.dumps(version_info, indent=4).encode('utf-8')).decode('utf-8')
            }
            
            # Check if version.json exists
            response = requests.get(version_url, headers=self.headers)
            if response.status_code == 200:
                version_data["sha"] = response.json()["sha"]
            
            response = requests.put(version_url, headers=self.headers, json=version_data)
            if response.status_code not in [201, 200]:
                print(f"Error updating version info: {response.text}")
                return False

            print(f"Successfully uploaded version {version}")
            return True

        except Exception as e:
            print(f"Error uploading update: {str(e)}")
            return False

if __name__ == "__main__":
    # Replace these with your GitHub credentials
    GITHUB_USERNAME = "ragaming777"
    GITHUB_TOKEN = "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"  # Make sure this token has repo access
    GITHUB_REPO = "ragaming777/Clipboard-Manager"

    # Create uploader instance
    uploader = GitHubUploader(GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_REPO)

    # Example usage
    if len(sys.argv) < 4:
        print("Usage: python upload_update.py <exe_path> <version> <changelog>")
        print("Example: python upload_update.py dist/clipboard_manager.exe 1.1.0 'Added new features'")
        sys.exit(1)

    exe_path = sys.argv[1]
    version = sys.argv[2]
    changelog = sys.argv[3]

    # Upload the update
    if uploader.upload_file(exe_path, version, changelog):
        print("Update process completed successfully!")
    else:
        print("Update process failed!") 
