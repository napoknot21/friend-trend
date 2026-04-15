import sqlite3

def run_migration():
    conn = sqlite3.connect("trend_classifier.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE emails ADD COLUMN md5_hash VARCHAR;")
        cursor.execute("CREATE INDEX ix_emails_md5_hash ON emails (md5_hash);")
        print("Migration successful: Added md5_hash column.")
    except sqlite3.OperationalError as e:
        print(f"Migration error (might already exist): {e}")

    try:
        cursor.execute("ALTER TABLE underlying_views ADD COLUMN confidence INTEGER DEFAULT 50;")
        print("Migration successful: Added confidence column to underlying_views.")
    except sqlite3.OperationalError as e:
        print(f"Migration error (confidence may already exist): {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    run_migration()
