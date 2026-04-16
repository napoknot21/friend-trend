from __future__ import annotations

import os
import sys
import uvicorn

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path :
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.src.scripts.cli_utils import add_server_arguments, build_parser, setup_environment

setup_environment(__file__, parent_levels=2)

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

    parser = build_parser("Run the FastAPI app with optional uvicorn settings.")
    add_server_arguments(
        parser,
        default_host=default_host,
        default_port=default_port,
        default_reload=default_reload,
        default_workers=default_workers,
    )
    
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
