import os
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin

from src.utils.import_utils import find_imports_in_ts_file, extract_sourcemap_url_from_js, resolve_import_with_extensions
from src.browser import BrowserNavigator
from src.downloader import Downloader
from src.sourcemap import SourceMapProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class SourceCodeExtractor:
    def __init__(self, target_url: str, download_dir: str = "downloaded_sources", custom_config: Dict[str, Any] = None):
        self.config = {
            "download_dir": download_dir,
            "headless": False,
            "timeout": 5000,
            "wait_until": "networkidle",
            "verify_ssl": False,
            "request_timeout": 15,
            "user_agent": "Mozilla/5.0",
            "skip_node_modules": True,
            "target_file_patterns": [
                "src/app",
                "src/environments",
                "main.ts",
                "polyfills.ts",
                "styles.css"
            ],
            "allowed_extensions": [".js", ".css", ".html", ".ts", ".tsx", ".jsx"],
            "max_links_to_follow": 5,
        }

        if custom_config:
            self.config.update(custom_config)

        self.download_dir = self.config["download_dir"]
        os.makedirs(self.download_dir, exist_ok=True)

        self.target_url = target_url
        self.browser = BrowserNavigator(self.config)
        self.downloader = Downloader(
            self.download_dir, 
            self.config["verify_ssl"], 
            self.config["request_timeout"], 
            self.config["user_agent"]
        )
        self.sourcemap_processor = SourceMapProcessor(self.download_dir, self.downloader, self.config)

        # State variables
        self.resource_urls = set()
        self.js_files = []      # List of (url, path) tuples
        self.map_files = []     # List of map URLs
        self.processed_files = set()
        self.all_saved_files = []

    async def extract(self) -> List[str]:
        logger.info(f"Starting extraction from {self.target_url}")
        logger.info(f"Files will be saved to {self.download_dir}")
        
        self.resource_urls = await self.browser.navigate_site(self.target_url)
        await self._process_resources()
        self._follow_imports()
        
        logger.info(f"✅ Extraction complete! Check the {self.download_dir} directory.")
        logger.info(f"Total saved files: {len(self.all_saved_files)}")
        
        return self.all_saved_files
    
    async def _process_resources(self) -> None:
        for url in self.resource_urls:
            if url.endswith(".map"):
                self.map_files.append(url)
                logger.info(f"Found map file: {url}")
            elif any(url.endswith(ext) for ext in self.config["allowed_extensions"]):
                path = self.downloader.download_file(url)
                if url.endswith(".js") and path:
                    self.js_files.append((url, path))

        for map_url in self.map_files:
            saved_files = self.sourcemap_processor.process_map_url(map_url)
            if saved_files:
                self.all_saved_files.extend(saved_files)

        for js_url, js_path in self.js_files:
            map_ref = extract_sourcemap_url_from_js(js_path)
            if map_ref:
                if map_ref.startswith("data:"):
                    saved_files = self.sourcemap_processor.process_inline_sourcemap(
                        map_ref, 
                        os.path.dirname(js_url) + "/"
                    )
                    if saved_files:
                        self.all_saved_files.extend(saved_files)
                else:
                    full_map_url = urljoin(js_url, map_ref)
                    if full_map_url not in self.map_files:  # Avoid processing the same map twice
                        saved_files = self.sourcemap_processor.process_map_url(full_map_url)
                        if saved_files:
                            self.all_saved_files.extend(saved_files)

    def _follow_imports(self) -> None:
        files_to_process = [
            f for f in self.all_saved_files 
            if f and (f.endswith('.ts') or f.endswith('.tsx'))
        ]

        logger.info(f"🔍 Following imports in {len(files_to_process)} TypeScript files...")

        while files_to_process:
            current_file = files_to_process.pop(0)
            
            if current_file in self.processed_files:
                continue
            
            self.processed_files.add(current_file)
            imported_files = find_imports_in_ts_file(current_file)
            
            for imp_file in imported_files:
                resolved_file = resolve_import_with_extensions(
                    imp_file, 
                    extensions=['', '.ts', '.tsx', '.js', '.jsx']
                )
                
                if resolved_file and resolved_file not in self.processed_files:
                    files_to_process.append(resolved_file)

        
