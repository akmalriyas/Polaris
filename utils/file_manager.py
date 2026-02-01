import json
import os
import gzip
from typing import Dict, Any

def save_macro(filepath: str, data: Dict[str, Any]) -> None:
    """
    Save macro data to a .polaris (JSON) file, compressed with GZIP.
    
    Args:
        filepath: Absolute or relative path to save the file.
        data: Dictionary containing metadata and flow data.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with gzip.open(filepath, 'wt', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_macro(filepath: str) -> Dict[str, Any]:
    """
    Load macro data from a .polaris (JSON) file, supporting both GZIP and legacy plain JSON.
    
    Args:
        filepath: Path to the .polaris file.
        
    Returns:
        Dictionary containing the macro data.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Macro file not found: {filepath}")
        
    try:
        # Try processing as GZIP first
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            return json.load(f)
    except (gzip.BadGzipFile, OSError):
        # Fallback to plain text JSON (for legacy files)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
