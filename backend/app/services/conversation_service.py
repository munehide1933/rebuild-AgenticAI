from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Conversation, Message


class ConversationService:
    """会话服务：负责创建会话、添加消息、查询历史记录"""

    @staticmethod
    async def create_conversation(db: AsyncSession, title: str) -> Conversation:
        """创建新对话（不再需要 project_id）"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            created_at=datetime.utcnow(),
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        meta_info: dict | None = None,
    ) -> Message:
        """添加用户消息或 AI 回复"""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_info=meta_info or {},
            created_at=datetime.utcnow(),
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession,
        conversation_id: str,
    ) -> list[Message]:
        """获取对话全部消息（按时间顺序）"""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await db.execute(query)
        return list(result.scalars())