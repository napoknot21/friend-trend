from __future__ import annotations

import sys

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[4]

if str(ROOT_DIR) not in sys.path :
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.src.scripts.cli_utils import add_date_range_arguments, add_llm_arguments, build_parser, setup_environment

setup_environment(__file__, parent_levels=4)

from src.backend.src.processor import process_email_range


def main () -> None :
    """
    Process Outlook emails for a date range and store extracted views.
    """
    parser = build_parser("Extract market views from Outlook emails using an LLM.")
    add_date_range_arguments(parser)
    add_llm_arguments(parser)
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
