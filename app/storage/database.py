"""Database session and async SQLite engine initialization."""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config.settings import settings
from app.core.logging import logger
from app.storage.models import Base

# Ensure directory for SQLite database exists
db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", ""))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db() -> None:
    """Initialize database tables asynchronously and ensure schema columns exist."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            def _migrate_columns(connection):
                try:
                    cursor = connection.connection.cursor()
                    cursor.execute("PRAGMA table_info(analysis_runs)")
                    cols = [col[1] for col in cursor.fetchall()]
                    if cols:
                        if "final_market_verdict" not in cols:
                            cursor.execute("ALTER TABLE analysis_runs ADD COLUMN final_market_verdict VARCHAR(32) DEFAULT 'NEUTRAL'")
                        if "executive_verdict_summary" not in cols:
                            cursor.execute("ALTER TABLE analysis_runs ADD COLUMN executive_verdict_summary TEXT DEFAULT ''")
                except Exception as ex:
                    pass

            await conn.run_sync(_migrate_columns)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async database session context."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
