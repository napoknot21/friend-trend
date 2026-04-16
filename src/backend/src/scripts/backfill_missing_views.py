from __future__ import annotations

import argparse

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(parent_levels=4)

from src.backend.src.processor import backfill_missing_views


def main () -> None :
    """
    Backfill views for emails already stored in the database.
    """
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


if __name__ == "__main__" :
    main()
