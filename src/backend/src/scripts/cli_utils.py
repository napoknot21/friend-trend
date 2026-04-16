from __future__ import annotations

import sys

from pathlib import Path
from dotenv import load_dotenv


def setup_environment (parent_levels : int = 4) -> Path :
    """
    Setup Python path and load environment variables.
    
    Args:
        parent_levels: Number of parent directory levels from __file__ to reach ROOT_DIR
        
    Returns:
        Path: The ROOT_DIR
    """
    root_dir = Path(__file__).resolve().parents[parent_levels]
    
    if str(root_dir) not in sys.path :
        sys.path.insert(0, str(root_dir))
    
    load_dotenv(root_dir / ".env")
    
    return root_dir
