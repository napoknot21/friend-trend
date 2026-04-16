from __future__ import annotations

import argparse
import sys

from pathlib import Path
from dotenv import load_dotenv


def setup_environment (current_file : str | Path, parent_levels : int) -> Path :
    """
    Add the project root to `sys.path` and load the repo `.env` file.
    """
    root_dir = Path(current_file).resolve().parents[parent_levels]
    
    if str(root_dir) not in sys.path :
        sys.path.insert(0, str(root_dir))
    
    load_dotenv(root_dir / ".env")
    
    return root_dir


def build_parser (description : str) -> argparse.ArgumentParser :
    """
    Create a CLI parser with a consistent project style.
    """
    return argparse.ArgumentParser(description=description)


def add_date_range_arguments (parser : argparse.ArgumentParser) -> None :
    """
    Add shared date-range arguments to a parser.
    """
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today")


def add_llm_arguments (parser : argparse.ArgumentParser) -> None :
    """
    Add shared LLM provider arguments to a parser.
    """
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider (openai or ollama)")
    parser.add_argument("--model", type=str, default=None, help="LLM model name. Inferred by provider if omitted.")


def add_server_arguments (
    parser : argparse.ArgumentParser,
    *,
    default_host : str,
    default_port : int,
    default_reload : bool,
    default_workers : int,
) -> None :
    """
    Add shared uvicorn server arguments to a parser.
    """
    parser.add_argument("--host", default=default_host, help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=default_port, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", default=default_reload, help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=default_workers, help="Number of worker processes")
