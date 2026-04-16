from __future__ import annotations

import argparse

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(parent_levels=4)

from src.backend.src.processor import process_email_range


def main () -> None :
    """
    Process Outlook emails for a date range and store extracted views.
    """
    parser = argparse.ArgumentParser(description="Extract market views from Outlook emails using an LLM.")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider (openai or ollama)")
    parser.add_argument("--model", type=str, default=None, help="LLM model name. Inferred by provider if omitted.")
    parser.add_argument("--refresh", action="store_true", help="Refresh: delete existing emails/views for the date range before processing")
    parser.add_argument("--strict", action="store_true", help="Apply strict filtering for market commentary emails")
    args = parser.parse_args()

    result = process_email_range(
        start_date=args.start_date,
        end_date=args.end_date,
        provider=args.provider,
        model=args.model,
        refresh=args.refresh,
        strict=args.strict,
    )

    print(f"[*] Process completed: {result['new_emails']} new emails, {result['views_created']} views created.")
    
    if args.refresh :
        print("[*] Refresh was applied for the selected date range.")


if __name__ == "__main__" :
    main()
