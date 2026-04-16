from __future__ import annotations

import sys

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[4]

if str(ROOT_DIR) not in sys.path :
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.src.scripts.cli_utils import add_date_range_arguments, add_llm_arguments, build_parser, setup_environment

setup_environment(__file__, parent_levels=4)

from src.backend.src.processor import backfill_missing_views


def main () -> None :
    """
    Backfill views for emails already stored in the database.
    """
    parser = build_parser("Backfill missing market views from emails already stored in the database.")
    add_date_range_arguments(parser)
    add_llm_arguments(parser)
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
