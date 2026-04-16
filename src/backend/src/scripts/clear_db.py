from __future__ import annotations

import sys

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[4]

if str(ROOT_DIR) not in sys.path :
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(__file__, parent_levels=4)

from src.backend.src.db.database import SessionLocal, initialize_database
from src.backend.src.db.models import Email, UnderlyingView


def clear_db () -> None :
    """
    Delete all stored emails and views from the SQLite database.
    """
    initialize_database()

    db = SessionLocal()
    
    try :

        db.query(UnderlyingView).delete()
        db.query(Email).delete()
        db.commit()

        print("Database cleared: 0 rows in emails and underlying_views.")
    
    finally :
        db.close()


if __name__ == "__main__" :
    clear_db()
