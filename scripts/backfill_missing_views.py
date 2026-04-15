import os
import sys
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import argparse

from src.processor import backfill_missing_views


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill missing market views from emails already stored in the database.")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider (openai or ollama)")
    parser.add_argument("--model", type=str, default=None, help="LLM model name. Inferred by provider if omitted.")
    args = parser.parse_args()

    result = backfill_missing_views(
        start_date=args.start_date,
        end_date=args.end_date,
        provider=args.provider,
        model=args.model,
    )

    print(
        f"[*] Backfill completed: {result['emails_reprocessed']} emails reprocessed, "
        f"{result['views_created']} views created."
    )


if __name__ == "__main__":
    main()
