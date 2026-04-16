from __future__ import annotations

import sqlite3
import sys

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[4]

if str(ROOT_DIR) not in sys.path :
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(__file__, parent_levels=4)

from src.backend.src.db.database import DATABASE_PATH, initialize_database


def run_migration () -> None :
    """
    Apply one-off schema updates to an older SQLite database.
    """
    initialize_database()
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    try :
        cursor.execute("ALTER TABLE emails ADD COLUMN md5_hash VARCHAR;")
        cursor.execute("CREATE INDEX ix_emails_md5_hash ON emails (md5_hash);")
        print("Migration successful: Added md5_hash column.")
    
    except sqlite3.OperationalError as e :
        print(f"Migration error (might already exist): {e}")

    try :
        cursor.execute("ALTER TABLE underlying_views ADD COLUMN confidence INTEGER DEFAULT 50;")
        print("Migration successful: Added confidence column to underlying_views.")
    
    except sqlite3.OperationalError as e :
        print(f"Migration error (confidence may already exist): {e}")
    
    finally :
        conn.commit()
        conn.close()


if __name__ == "__main__" :
    run_migration()
