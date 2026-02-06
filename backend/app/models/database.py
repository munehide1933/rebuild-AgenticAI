from datetime import datetime
from pathlib import Path
import sqlite3

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False, default="新建会话")
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")




class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, index=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    meta_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    _ensure_clean_sqlite_schema()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_conversation_table)


def _migrate_conversation_table(sync_conn) -> None:
    if sync_conn.dialect.name != "sqlite":
        return

    columns = {
        row[1]
        for row in sync_conn.exec_driver_sql("PRAGMA table_info(conversations)").fetchall()
    }

    if "summary" not in columns:
        sync_conn.exec_driver_sql(
            "ALTER TABLE conversations ADD COLUMN summary VARCHAR DEFAULT '新建会话'"
        )
    if "is_deleted" not in columns:
        sync_conn.exec_driver_sql(
            "ALTER TABLE conversations ADD COLUMN is_deleted BOOLEAN DEFAULT 0"
        )
    if "updated_at" not in columns:
        sync_conn.exec_driver_sql("ALTER TABLE conversations ADD COLUMN updated_at DATETIME")
        sync_conn.exec_driver_sql("UPDATE conversations SET updated_at = created_at")


def _ensure_clean_sqlite_schema() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    db_path = _sqlite_path_from_url(DATABASE_URL)
    if not db_path or not db_path.exists():
        return
    tables = _get_sqlite_tables(db_path)
    if "projects" not in tables:
        return
    backup_path = db_path.with_name(
        f"{db_path.stem}.legacy-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{db_path.suffix}"
    )
    db_path.rename(backup_path)


def _sqlite_path_from_url(url: str) -> Path | None:
    if url.startswith("sqlite+aiosqlite:///"):
        return Path(url.replace("sqlite+aiosqlite:///", ""))
    if url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", ""))
    return None


def _get_sqlite_tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()
