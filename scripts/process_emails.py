import os
import sys
from dotenv import load_dotenv
load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import argparse
from src.processor import process_email_range

def main() -> None :

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
        strict=args.strict
    )

    print(f"[*] Process completed: {result['new_emails']} new emails, {result['views_created']} views created.")
    if args.refresh:
        print("[*] Refresh was applied for the selected date range.")

    return result

if __name__ == "__main__":
    main()