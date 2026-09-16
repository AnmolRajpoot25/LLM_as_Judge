"""Database connection and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config.settings import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import text


def init_db():
    """Initialize database tables and run lightweight migrations."""
    Base.metadata.create_all(bind=engine)
    # Ensure user_id column exists on existing SQLite databases
    if "sqlite" in settings.database_url:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(sessions)")).fetchall()
                col_names = [r[1] for r in res]
                if "user_id" not in col_names:
                    conn.execute(text("ALTER TABLE sessions ADD COLUMN user_id VARCHAR(64)"))
                    conn.commit()
        except Exception:
            pass
