from src.db.database import SessionLocal
from src.db.models import Email, UnderlyingView


def clear_db():
    db = SessionLocal()
    try:
        db.query(UnderlyingView).delete()
        db.query(Email).delete()
        db.commit()
        print("Database cleared: 0 rows in emails and underlying_views.")
    finally:
        db.close()


if __name__ == "__main__":
    clear_db()
