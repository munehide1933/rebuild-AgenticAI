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
<<<<<<< HEAD
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

=======
    async def create_conversation(
        db: AsyncSession, 
        title: str,
        user_id: Optional[str] = None
    ) -> Conversation:
        """创建新会话"""
        if not title or not title.strip():
            raise ValidationError("会话标题不能为空", field="title")
        
        try:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                title=title.strip()[:100],  # 限制长度
                summary=title.strip()[:60] if title.strip() else "新建会话",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_deleted=False,
            )
            
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            
            logger.info(f"Created conversation {conversation.id}")
            return conversation
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to create conversation: {e}")
            raise DatabaseError(
                "创建会话失败",
                details={"title": title},
                original_error=e
            )
    
>>>>>>> 81cede4 (Initial commit)
    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        meta_info: Optional[dict] = None,
    ) -> Message:
<<<<<<< HEAD
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
=======
        """添加消息（带事务保护）"""
        
        # 验证输入
        if role not in ["user", "assistant", "system"]:
            raise ValidationError(f"无效的角色: {role}", field="role")
        
        if not content or not content.strip():
            raise ValidationError("消息内容不能为空", field="content")
        
        try:
            # 开始事务
            async with db.begin_nested():
                # 验证会话存在
                conversation = await db.get(Conversation, conversation_id)
                if not conversation:
                    raise ValidationError(
                        f"会话不存在: {conversation_id}",
                        field="conversation_id"
                    )
                
                if conversation.is_deleted:
                    raise ValidationError(
                        "无法向已删除的会话添加消息",
                        field="conversation_id"
                    )
                
                # 创建消息
                message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role=role,
                    content=content.strip(),
                    meta_info=meta_info or {},
                    created_at=datetime.utcnow(),
                )
                db.add(message)
                
                # 更新会话摘要和时间
                if role == "user":
                    snippet = content.strip().replace("\n", " ")
                    conversation.summary = snippet[:60] if snippet else conversation.summary
                    
                    # 如果是第一条消息，更新标题
                    if conversation.title == "新建会话" or not conversation.title:
                        conversation.title = conversation.summary
                
                conversation.updated_at = datetime.utcnow()
            
            # 提交主事务
            await db.commit()
            await db.refresh(message)
            
            logger.debug(f"Added {role} message to conversation {conversation_id}")
            return message
            
        except ValidationError:
            await db.rollback()
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to add message: {e}")
            raise DatabaseError(
                "添加消息失败",
                details={"conversation_id": conversation_id, "role": role},
                original_error=e
            )
    
    @staticmethod
    async def get_conversation_history(
        db: AsyncSession, 
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0
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
            
            logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise DatabaseError(
                "获取会话历史失败",
                details={"conversation_id": conversation_id},
                original_error=e
            )
    
    @staticmethod
    async def list_active_conversations(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """列出活跃会话（支持分页）"""
        try:
            query = (
                select(Conversation)
                .where(Conversation.is_deleted == False)
                .order_by(
                    Conversation.updated_at.desc(),
                    Conversation.created_at.desc()
                )
                .offset(offset)
                .limit(limit)
            )
            
            result = await db.execute(query)
            conversations = list(result.scalars())
            
            logger.debug(f"Retrieved {len(conversations)} active conversations")
            return conversations
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to list conversations: {e}")
            raise DatabaseError(
                "获取会话列表失败",
                original_error=e
            )
    
    @staticmethod
    async def get_active_conversation(
        db: AsyncSession, 
        conversation_id: str
    ) -> Optional[Conversation]:
        """获取单个活跃会话"""
        try:
            query = select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.is_deleted == False
                )
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                logger.debug(f"Retrieved conversation {conversation_id}")
            else:
                logger.warning(f"Conversation {conversation_id} not found or deleted")
            
            return conversation
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get conversation: {e}")
            raise DatabaseError(
                "获取会话失败",
                details={"conversation_id": conversation_id},
                original_error=e
            )
    
    @staticmethod
    async def soft_delete_conversation(
        db: AsyncSession, 
        conversation_id: str
    ) -> bool:
        """软删除会话"""
        try:
            conversation = await db.get(Conversation, conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for deletion")
                return False
            
            conversation.is_deleted = True
            conversation.updated_at = datetime.utcnow()
            
            await db.commit()
            logger.info(f"Soft deleted conversation {conversation_id}")
            return True
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to delete conversation: {e}")
            raise DatabaseError(
                "删除会话失败",
                details={"conversation_id": conversation_id},
                original_error=e
            )
    
    @staticmethod
    async def get_conversation_count(
        db: AsyncSession,
        include_deleted: bool = False
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
            logger.error(f"Failed to get conversation count: {e}")
            raise DatabaseError(
                "获取会话数量失败",
                original_error=e
            )
>>>>>>> 81cede4 (Initial commit)
