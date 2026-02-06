from __future__ import annotations

import polars as pl
import datetime as dt

from src.utils import date_to_str
from src.outlook import read_emails_from_folder
from src.classifier import score_email

def main () :

    date = date_to_str()
    emails = read_emails_from_folder(start_date="2026-01-30", end_date=None)

    dfs: list[pl.DataFrame] = []

    for email in emails:
        df_one = score_email(email)

        # skip bad outputs
        if df_one is None:
            continue
        if isinstance(df_one, pl.DataFrame) and df_one.is_empty():
            continue

        dfs.append(df_one)

    # concat once (relaxed schema)
    results_by_email = pl.concat(dfs, how="vertical_relaxed") if dfs else pl.DataFrame()

    # de-dup (only if column exists)
    if not results_by_email.is_empty() and "received_time" in results_by_email.columns:
        results_by_email = results_by_email.unique(subset=["received_time"], keep="first")

    print(results_by_email)

    # write excel
    results_by_email.write_excel(f"classifier_{date}.xlsx")

    return None



if __name__ == "__main__" :
    main()
