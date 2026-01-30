from __future__ import annotations

import polars as pl
from src.outlook import read_emails_from_folder
from src.classifier import score_email

def main () :

    results_by_email = pl.DataFrame()

    emails = read_emails_from_folder(start_date="2026-01-15", end_date="2026-01-30")

    for email in emails :
        
        dataframe = score_email(email)
        results_by_email = pl.concat([results_by_email, dataframe])
    
    
    print(results_by_email)
    results_by_email.write_excel("classifier.xlsx")
    return None



if __name__ == "__main__" :
    main()
