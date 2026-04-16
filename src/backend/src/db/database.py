from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "trend_classifier.db"

DATABASE_PATH = Path(os.getenv("SQLITE_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = ROOT_DIR / DATABASE_PATH

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
