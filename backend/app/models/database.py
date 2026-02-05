from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from app.config import settings
from datetime import datetime
from pathlib import Path
import sqlite3

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()


# -------------------------------
# Conversation 表（不再依赖 project）
# -------------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


# -------------------------------
# Message 表（用于存储对话历史）
# -------------------------------
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    meta_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# -------------------------------
# 获取数据库会话
# -------------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# -------------------------------
# 初始化数据库（建表）
# -------------------------------
async def init_db():
    _ensure_clean_sqlite_schema()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
