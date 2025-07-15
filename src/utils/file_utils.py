import os
from urllib.parse import urlparse
import logging

"""
Utilities For File Operations
"""

logger = logging.getLogger(__name__)

def sanitize_filename(url_or_path: str) -> str:
    """ 
    Convert URL or path to a valid filename 
    """
    if url_or_path.startswith("http"):
        parsed = urlparse(url_or_path)
        path = parsed.path.strip("/").replace("/", "_")
    else:
        path = url_or_path.strip("/")

    return path if path else "index"

def process_webpack_path(path: str) -> str:
    """
    Process webpack paths to maintain directory structure
    """
    if "webpack://" in path:
        path = path.replace("webpack://", "")

        # Make sure paths that start with `src/` are preserved exacly
        if not path.startswith("src/") and "src/" in path:
            path = path[path.find("src/"):]

        # Special handling for paths that don't obviously contain `src/`
        if not "src/" in path and (path.endswith('.ts') or path.endswith('.tsx')):
            path = f"src/{path}"

    path = path.lstrip("/").replace("..","").replace(":","")
    return path

def save_content_to_file(downlod_dir: str, path: str, content: str) -> str:
    """
    Save content to a file, creating directories as needed
    """
    processed_path = process_webpack_path(path)
    full_path = os.path.join(downlod_dir, processed_path)

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ Extracted: {processed_path}")
        return full_path
    except Exception as e:
        logger.error(f"❌ Error saving file {processed_path}: {e}")
        return None
    
def save_binary_to_file(downlod_dir: str, path: str, content: bytes) -> str:
    """
    Save binary content to a file, creating directories as needed
    """
    full_path = os.path.join(downlod_dir, path)

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(content)

        logger.info(f"✅ Saved binary file: {path}")
        return full_path
    except Exception as e:
        logger.error(f"❌ Error saving binary file {path}: {e}")
        return None
    
