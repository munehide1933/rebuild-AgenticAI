# backend/app/services/conversation_service.py
from __future__ import annotations

from datetime import datetime
import uuid
from typing import Optional, List
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.database import Conversation, Message
from app.utils.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class ConversationService:
    """优化后的会话服务"""

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        title: str,
        user_id: Optional[str] = None,
    ) -> Conversation:
        """创建新会话"""
        if not title or not title.strip():
            raise ValidationError("会话标题不能为空", field="title")

        try:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                title=title.strip()[:100],
                summary=title.strip()[:60] if title.strip() else "新建会话",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_deleted=False,
            )

            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            logger.info("Created conversation %s", conversation.id)
            return conversation

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("Failed to create conversation: %s", e)
            raise DatabaseError(
                "创建会话失败",
                details={"title": title},
                original_error=e,
            )

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        meta_info: Optional[dict] = None,
    ) -> Message:
        """添加消息（带事务保护）"""
        if role not in ["user", "assistant", "system"]:
            raise ValidationError(f"无效的角色: {role}", field="role")

        if not content or not content.strip():
            raise ValidationError("消息内容不能为空", field="content")

        try:
            async with db.begin_nested():
                conversation = await db.get(Conversation, conversation_id)
                if not conversation:
                    raise ValidationError(
                        f"会话不存在: {conversation_id}",
                        field="conversation_id",
                    )

                if conversation.is_deleted:
                    raise ValidationError(
                        "无法向已删除的会话添加消息",
                        field="conversation_id",
                    )

                message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role=role,
                    content=content.strip(),
                    meta_info=meta_info or {},
                    created_at=datetime.utcnow(),
                )
                db.add(message)

                if role == "user":
                    snippet = content.strip().replace("\n", " ")
                    conversation.summary = snippet[:60] if snippet else conversation.summary

                    if conversation.title == "新建会话" or not conversation.title:
                        conversation.title = conversation.summary

                conversation.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(message)

            logger.debug("Added %s message to conversation %s", role, conversation_id)
            return message

        except ValidationError:
            await db.rollback()
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("Failed to add message: %s", e)
            raise DatabaseError(
                "添加消息失败",
                details={"conversation_id": conversation_id, "role": role},
                original_error=e,
            )

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """获取会话历史（支持分页）"""
        try:
            query = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .offset(offset)
            )

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            messages = list(result.scalars())

            logger.debug("Retrieved %s messages for conversation %s", len(messages), conversation_id)
            return messages

        except SQLAlchemyError as e:
            logger.error("Failed to get conversation history: %s", e)
            raise DatabaseError(
                "获取会话历史失败",
                details={"conversation_id": conversation_id},
                original_error=e,
            )

    @staticmethod
    async def list_active_conversations(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Conversation]:
        """列出活跃会话（支持分页）"""
        try:
            query = (
                select(Conversation)
                .where(Conversation.is_deleted == False)
                .order_by(
                    Conversation.updated_at.desc(),
                    Conversation.created_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            )

            result = await db.execute(query)
            conversations = list(result.scalars())

            logger.debug("Retrieved %s active conversations", len(conversations))
            return conversations

        except SQLAlchemyError as e:
            logger.error("Failed to list conversations: %s", e)
            raise DatabaseError(
                "获取会话列表失败",
                original_error=e,
            )

    @staticmethod
    async def get_active_conversation(
        db: AsyncSession,
        conversation_id: str,
    ) -> Optional[Conversation]:
        """获取单个活跃会话"""
        try:
            query = select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.is_deleted == False,
                )
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()

            if conversation:
                logger.debug("Retrieved conversation %s", conversation_id)
            else:
                logger.warning("Conversation %s not found or deleted", conversation_id)

            return conversation

        except SQLAlchemyError as e:
            logger.error("Failed to get conversation: %s", e)
            raise DatabaseError(
                "获取会话失败",
                details={"conversation_id": conversation_id},
                original_error=e,
            )

    @staticmethod
    async def soft_delete_conversation(
        db: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """软删除会话"""
        try:
            conversation = await db.get(Conversation, conversation_id)
            if not conversation:
                logger.warning("Conversation %s not found for deletion", conversation_id)
                return False

            conversation.is_deleted = True
            conversation.updated_at = datetime.utcnow()

            await db.commit()
            logger.info("Soft deleted conversation %s", conversation_id)
            return True

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("Failed to delete conversation: %s", e)
            raise DatabaseError(
                "删除会话失败",
                details={"conversation_id": conversation_id},
                original_error=e,
            )

    @staticmethod
    async def get_conversation_count(
        db: AsyncSession,
        include_deleted: bool = False,
    ) -> int:
        """获取会话总数"""
        try:
            from sqlalchemy import func

            query = select(func.count(Conversation.id))
            if not include_deleted:
                query = query.where(Conversation.is_deleted == False)

            result = await db.execute(query)
            count = result.scalar_one()

            return count

        except SQLAlchemyError as e:
            logger.error("Failed to get conversation count: %s", e)
            raise DatabaseError(
                "获取会话数量失败",
                original_error=e,
            )
