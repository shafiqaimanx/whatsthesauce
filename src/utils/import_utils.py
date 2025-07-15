import os
import re
import logging
from typing import List

"""
Utilities For Processing Import Statements In Source Files
"""

logger = logging.getLogger(__name__)

def find_imports_in_ts_file(file_path: str) -> List[str]:
    """
    Find import statements in TS/JS files to discover related files
    """
    imported_files = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find import statements
        import_pattern = r'import\s+(?:.*?)\s+from\s+[\'"]([^\'"]+)[\'"]'
        matches = re.findall(import_pattern, content)

        base_dir = os.path.dirname(file_path)

        for match in matches:
            if match.startswith('./') or match.startswith('../'):
                imported_path = os.path.normpath(os.path.join(base_dir, match))
                imported_files.append(imported_path)
            elif not match.startswith('@') and '/' not in match:
                imported_files.append(os.path.join(base_dir, match))
            # Skip package imports (e.g., @angular/core, react, etc.)

        logger.debug(f"Found {len(imported_files)} imports in {file_path}")
    except Exception as e:
        logger.error(f"Error processing imports in {file_path}")

    return imported_files

def resolve_import_with_extensions(base_path: str, extensions: List[str] = None) -> str:
    """
    Try to resolve an import path with various extensions
    """
    if extensions is None:
        extensions = ['', '.ts', '.tsx', '.js', '.jsx']

    for ext in extensions:
        check_path = f"{base_path}{ext}" if not base_path.endswith(ext) else base_path
        if os.path.exists(check_path):
            return check_path
        
    return None

def extract_sourcemap_url_from_js(js_path: str) -> str:
    """
    Extract sourceMappingURL from a JS file
    """
    try:
        with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

            # Look for sourceMappingURL in the file
            match = re.search(r'sourceMappingURL=([^\s"\']+)', content)
            if match:
                return match.group(1)
    except Exception as e:
        logger.error(f"Could not read JS file {js_path}: {e}")

    return None