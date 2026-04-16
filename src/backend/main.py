from __future__ import annotations

import os
import argparse
import uvicorn

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(parent_levels=2)

from src.backend.src.api.app import app
from src.backend.src.api.config import env_bool, env_int


def main () -> None :
    """
    Main entry point for running the FastAPI app with uvicorn.
    """
    default_host = os.getenv("API_HOST", "127.0.0.1")
    default_port = env_int("API_PORT", 8000)
    default_reload = env_bool("API_RELOAD", False)
    default_workers = env_int("API_WORKERS", 1)

    parser = argparse.ArgumentParser(description="Run the FastAPI app with optional uvicorn settings.")

    parser.add_argument("--host", default=default_host, help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=default_port, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", default=default_reload, help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=default_workers, help="Number of worker processes")
    
    args = parser.parse_args()

    uvicorn.run(

        "src.backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,

    )


if __name__ == "__main__" :
    main()
