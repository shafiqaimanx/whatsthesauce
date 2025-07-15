import requests
import logging
import urllib3
from urllib.parse import urljoin
from typing import Optional

"""
Utilities For Downloading Files From URLs
"""

from src.utils.file_utils import sanitize_filename, save_content_to_file, save_binary_to_file

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self, download_dir: str, verify_ssl: bool = False, timeout: int =10, user_agent: str = "Mozilla/5.0"):
        self.download_dir = download_dir
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.user_agent = user_agent

        # Create a session
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        self.session.headers.update({"User-Agent": self.user_agent})

    def download_file(self, url: str) -> Optional[str]:
        """
        Download a file from a URL
        """
        try:
            logger.info(f"Downloading {url}")
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                filename = sanitize_filename(url)
                filepath = save_binary_to_file(self.download_dir, filename, response.content)
                logger.info(f"✅ Downloaded: {url}")
                return filepath
            else:
                logger.warning(f"⚠️ Skipped (status {response.status_code}): {url}")
        except Exception as e:
            logger.error(f"❌ Error downloading {url}: {e}")

        return None
    
    def download_file_directly(self, base_url: str, relative_path: str) -> bool:
        """
        Attempt to download a file from its relative path
        """
        relative_path = relative_path.replace("webpack://", "").lstrip("/")
        full_url = urljoin(base_url, relative_path)

        try:
            logger.info(f"Attempting direct download of {relative_path}")
            response = self.session.get(full_url, timeout=self.timeout)

            if response.status_code == 200:
                save_content_to_file(self.download_dir, relative_path, response.text)
                return True
            else:
                logger.warning(f"⚠️ Could not download fallback: {full_url} (status {response.status_code})")
        except Exception as e:
            logger.error(f"❌ Error downloading fallback {full_url}: {e}")

        return False
    
    