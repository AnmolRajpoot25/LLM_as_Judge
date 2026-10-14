"""Database connection and session factory."""

import logging
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config.settings import settings, clean_database_url

logger = logging.getLogger(__name__)


def init_engine(url_str: str):
    sanitized = clean_database_url(url_str)
    try:
        # Validate URL format
        make_url(sanitized)
        is_sqlite = "sqlite" in sanitized
        eng = create_engine(
            sanitized,
            connect_args={"check_same_thread": False} if is_sqlite else {},
            pool_pre_ping=True,
            echo=False
        )
        return eng, sanitized
    except Exception as exc:
        logger.error(
            f"Failed to initialize database engine with URL '{url_str}': {exc}. "
            "Falling back to local SQLite database."
        )
        fallback_url = "sqlite:///./llm_judge.db"
        eng = create_engine(
            fallback_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=False
        )
        return eng, fallback_url


engine, effective_db_url = init_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and run lightweight migrations."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

    # Ensure user_id column exists on existing SQLite databases
    if "sqlite" in effective_db_url:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(sessions)")).fetchall()
                col_names = [r[1] for r in res]
                if "user_id" not in col_names:
                    conn.execute(text("ALTER TABLE sessions ADD COLUMN user_id VARCHAR(64)"))
                    conn.commit()

                res_users = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                user_cols = [r[1] for r in res_users]
                if user_cols:
                    if "is_active" not in user_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                    if "is_superuser" not in user_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT 0"))
                    if "updated_at" not in user_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
                    if "last_login" not in user_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
                    conn.commit()
        except Exception:
            pass

