from __future__ import annotations

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(parent_levels=4)

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
