import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./meeting_ai.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)
    if "sqlite" in DATABASE_URL:
        from sqlalchemy import text
        with engine.connect() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(meetings)"))
                cols = [row[1] for row in res.fetchall()]
                if cols:
                    if "title" not in cols:
                        conn.execute(text("ALTER TABLE meetings ADD COLUMN title TEXT DEFAULT 'Untitled Meeting'"))
                    if "ended_at" not in cols:
                        conn.execute(text("ALTER TABLE meetings ADD COLUMN ended_at DATETIME"))
                    if "duration_seconds" not in cols:
                        conn.execute(text("ALTER TABLE meetings ADD COLUMN duration_seconds INTEGER"))
                    conn.commit()
            except Exception as e:
                print(f"DB migration check note: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()