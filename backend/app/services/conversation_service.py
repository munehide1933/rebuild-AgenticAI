from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Conversation, Message


class ConversationService:
    """会话服务：负责创建会话、添加消息、查询历史记录"""

    @staticmethod
    async def create_conversation(db: AsyncSession, title: str) -> Conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            summary=title[:60] if title else "新建会话",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_deleted=False,
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
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_info=meta_info or {},
            created_at=datetime.utcnow(),
        )
        db.add(message)

        conversation = await db.get(Conversation, conversation_id)
        if conversation:
            if role == "user":
                snippet = content.strip().replace("\n", " ")
                conversation.summary = snippet[:60] if snippet else conversation.summary
                if not conversation.title or conversation.title == "新建会话":
                    conversation.title = conversation.summary
            conversation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_conversation_history(db: AsyncSession, conversation_id: str) -> list[Message]:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await db.execute(query)
        return list(result.scalars())

    @staticmethod
    async def list_active_conversations(db: AsyncSession) -> list[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.is_deleted.is_(False))
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars())

    @staticmethod
    async def get_active_conversation(db: AsyncSession, conversation_id: str) -> Conversation | None:
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_deleted.is_(False),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def soft_delete_conversation(db: AsyncSession, conversation_id: str) -> bool:
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            return False
        conversation.is_deleted = True
        conversation.updated_at = datetime.utcnow()
        await db.commit()
        return True
