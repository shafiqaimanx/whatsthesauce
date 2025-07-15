import os
from typing import Dict, Any

"""
Configuration Settings
"""

DEFAULT_CONFIG: Dict[str, Any] = {
    # Downloads directory name
    "download_dir":"downloaded_sources",

    # Browser settings
    "headless":False,
    "timeout":5000,
    "wait_until":"networkidle",

    # Request settings
    "verify_ssl":False,
    "request_timeout":15,
    "user_agent":"Mozilla/5.0",

    # Processing settings
    "skip_node_modules":True,
    "target_file_patterns":[
        "src/app",
        "src/environments",
        "main.ts",
        "polyfills.ts",
        "style.css"
    ],
    "allowed_extensions":[".js", ".css", ".html", ".ts", ".tsx", ".jsx"],
    "max_links_to_follow":5,
}


class Config:
    def __init__(self, custom_config: Dict[str, Any] = None):
        self.config = DEFAULT_CONFIG.copy()

        if custom_config:
            self.config.update(custom_config)

        os.makedirs(self.config["download_dir"], exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """ Get a configuration values """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """ Set a configuration values """
        self.config[key] = value

        if key == "download_dir":
            os.makedirs(value, exist_ok=True)

