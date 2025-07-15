import json
import base64
import logging
from typing import List, Dict, Any, Optional

"""
Utilities For Processing Source Maps
"""

from src.utils.file_utils import save_content_to_file
from src.downloader import Downloader

logger = logging.getLogger(__name__)

class SourceMapProcessor:
    def __init__(self, download_dir: str, downloader: Downloader, config: Dict[str, Any]):
        self.download_dir = download_dir
        self.downloader = downloader
        self.config = config
        self.skip_node_modules = config.get("skip_node_modules", True)
        self.target_file_patterns = config.get("target_file_patterns", [])

    def process_source_map(self, sourcemap: Dict[str, Any], base_url: str) -> List[str]:
        """
        Process a source map to extract original source files
        """
        sources = sourcemap.get("sources", [])
        sources_content = sourcemap.get("sourcesContent", [])

        saved_files = []

        for i, src in enumerate(sources):
            # Skip `node_modules` file if configured
            if self.skip_node_modules and "node_modules" in src:
                continue

            is_target = False
            for pattern in self.target_file_patterns:
                if pattern in src:
                    is_target = True
                    logger.info(f"🔍 Found target file: {src}")
                    break

            content = sources_content[i] if i < len(sources_content) else None

            if content:
                saved_path = save_content_to_file(self.download_dir, src, content)
                if saved_path:
                    saved_files.append(saved_path)
            else:
                logger.warning(f"⚠️ No inline source for {src}, trying fallback download...")
                self.downloader.download_file_directly(base_url, src)

        return saved_files
    
    def process_map_url(self, map_url: str) -> Optional[List[str]]:
        """
        Fetch and process a source map from URL
        """
        try:
            logger.info(f"📦 Fetching source map: {map_url}")
            response = self.downloader.session.get(
                map_url, 
                verify=self.downloader.verify_ssl, 
                timeout=self.downloader.timeout
            )
            
            if response.status_code == 200:
                sourcemap = response.json()
                return self.process_source_map(sourcemap, f"{map_url.rsplit('/', 1)[0]}/")
            else:
                logger.warning(f"⚠️ Failed to fetch source map: {map_url}")
        except Exception as e:
            logger.error(f"❌ Error fetching source map {map_url}: {e}")
        
        return None
    
    def process_inline_sourcemap(self, data_url: str, base_url: str) -> Optional[List[str]]:
        """
        Process an inline base64 encoded source map
        """
        try:
            if data_url.startswith("data:application/json;base64,"):
                encoded = data_url.split("base64,", 1)[-1]
                decoded = base64.b64decode(encoded).decode('utf-8')

                sourcemap = json.loads(decoded)
                return self.process_source_map(sourcemap, base_url)
            else:
                logger.warning(f"Unsupported data URL format: {data_url[:30]}...")
        except Exception as e:
            logger.error(f"❌ Error decoding inline source map: {e}")

        return None
    
