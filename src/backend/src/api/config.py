from __future__ import annotations

import os
from typing import List


def env_bool (name : str, default : bool) -> bool :
    """
    Read a boolean environment variable with a fallback.
    """
    value = os.getenv(name)

    if value is None :
        return default
    
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int (name : str, default : int) -> int :
    """
    Read an integer environment variable with a fallback.
    """
    value = os.getenv(name)

    if value is None :
        return default
    
    try :
        return int(value)
    
    except ValueError :
        return default


def env_csv (name : str) -> List[str] :
    """
    Read a comma-separated environment variable.
    """
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_allowed_origins () -> List[str] :
    """
    Resolve CORS origins from environment variables.
    """
    allow_all_origins = env_bool("ALLOW_ALL_ORIGINS", True)
    cors_allowed_origins = env_csv("CORS_ALLOWED_ORIGINS")
    
    if allow_all_origins :
        return ["*"]
    
    return cors_allowed_origins or ["http://localhost:5173"]
