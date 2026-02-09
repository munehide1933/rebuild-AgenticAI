"""简化的聊天 API：真正的流式输出"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    MessageDTO,
)
from app.services.conversation_service import ConversationService
from app.core.agent import Agent

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

agent = Agent(max_react_steps=5)  # 限制最大步数为5


<<<<<<< HEAD
async def _generate_streaming_response(
    message: str,
    history: list,
    mcp_context: dict | None = None
) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    try:
        # 直接使用Agent进行推理,不显示中间过程
        full_response, _ = await agent.run(message, history, mcp_context)
        
        # 模拟流式输出效果
        chunk_size = 30
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.02)  # 小延迟,模拟打字效果
            
    except asyncio.TimeoutError:
        yield "\n\n抱歉,响应超时。请尝试简化您的问题。"
    except Exception as e:
        logger.error(f"Error in streaming response: {e}", exc_info=True)
        yield f"\n\n处理出错: {str(e)}"
=======
async def _prepare_chat_result(request: ChatRequest, db: AsyncSession) -> dict[str, Any]:
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = await ConversationService.get_active_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await ConversationService.create_conversation(db, title=request.message[:50])
        conversation_id = conversation.id

    await ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )

    history = await ConversationService.get_conversation_history(db, conversation_id)
    profile = await UserProfileService.get_or_create_default_profile(db)
    mcp_context = mcp_service.build_context(
        question=request.message,
        conversation_history=history,
        user_profile=profile.preferences,
    )

    if request.deep_thinking or request.web_search_enabled:
        parity_result = await v1_parity_pipeline.run(
            question=request.message,
            conversation_history=history,
            deep_thinking=request.deep_thinking,
            web_search_enabled=request.web_search_enabled,
        )
        answer = parity_result.answer
        strategy = parity_result.strategy
        model = parity_result.model
        confidence = parity_result.confidence
        meta_info = {
            "strategy": strategy,
            "model": model,
            "confidence": confidence,
            "mcp": mcp_context,
            **parity_result.metadata,
        }
        code_modifications = parity_result.code_modifications
        suggestions = parity_result.suggestions
    else:
        reasoning_result = await reasoning_orchestrator.reason(
            question=request.message,
            conversation_history=history[-10:],
            mcp_context=mcp_context,
        )

        answer = reasoning_result.answer
        strategy = reasoning_result.strategy
        model = reasoning_result.model
        confidence = reasoning_result.confidence

        meta_info = {
            "strategy": strategy,
            "model": model,
            "confidence": confidence,
            "mcp": mcp_context,
        }

        meta_info.update(reasoning_result.metadata)
        code_modifications = []
        suggestions = []

    await UserProfileService.update_from_interaction(
        db,
        deep_thinking=request.deep_thinking,
        web_search_enabled=request.web_search_enabled,
        question=request.message,
        intent_meta=meta_info.get("intent") if isinstance(meta_info.get("intent"), dict) else None,
    )

    assistant_message = await ConversationService.add_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        meta_info=meta_info,
    )

    return {
        "message_id": assistant_message.id,
        "content": answer,
        "conversation_id": conversation_id,
        "workflow_state": {
            "current_phase": strategy,
            "active_personas": [model],
            "phase_outputs": meta_info,
        },
        "code_modifications": code_modifications,
        "suggestions": suggestions,
    }
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """非流式消息接口"""
    try:
        conversation_id = request.conversation_id
        if conversation_id:
            conversation = await ConversationService.get_active_conversation(db, conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = await ConversationService.create_conversation(db, title=request.message[:50])
            conversation_id = conversation.id

        await ConversationService.add_message(
            db,
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )

        history = await ConversationService.get_conversation_history(db, conversation_id, limit=10)
        
        # 设置超时时间为60秒
        try:
            answer, _ = await asyncio.wait_for(
                agent.run(request.message, history[:-1], None),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            answer = "抱歉,响应超时。请尝试简化您的问题或分多次提问。"

        assistant_message = await ConversationService.add_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            meta_info={},
        )

        return ChatResponse(
            message_id=assistant_message.id,
            content=answer,
            conversation_id=conversation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """真正的流式输出接口"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        conversation_id = None
        assistant_message_id = None
        full_content = ""
        
        try:
            # 创建或获取会话
            conversation_id = request.conversation_id
            if conversation_id:
                conversation = await ConversationService.get_active_conversation(db, conversation_id)
                if not conversation:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Conversation not found'}, ensure_ascii=False)}\n\n"
                    return
            else:
                conversation = await ConversationService.create_conversation(db, title=request.message[:50])
                conversation_id = conversation.id

            await ConversationService.add_message(
                db,
                conversation_id=conversation_id,
                role="user",
                content=request.message,
            )

            history = await ConversationService.get_conversation_history(db, conversation_id, limit=10)
            
            # 流式生成回复
            async for chunk in _generate_streaming_response(request.message, history[:-1], None):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 保存助手回复
            if full_content:
                assistant_message = await ConversationService.add_message(
                    db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_content,
                    meta_info={},
                )
                assistant_message_id = assistant_message.id

            # 发送完成事件
            payload = {
                "message_id": assistant_message_id or "temp",
                "content": full_content,
                "conversation_id": conversation_id,
            }
            yield f"data: {json.dumps({'type': 'done', 'payload': payload}, ensure_ascii=False)}\n\n"

<<<<<<< HEAD
        except Exception as e:
            logger.error(f"Error in stream_message: {e}", exc_info=True)
            error_msg = "处理出错,请稍后重试"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
=======
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
>>>>>>> 3a0ffb3f0f5903549c7c3d0d57cb153bddbd4bc2


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    conversations = await ConversationService.list_active_conversations(db)
    return [
        ConversationSummary(
            id=item.id,
            title=item.title,
            summary=item.summary,
            created_at=item.created_at,
            updated_at=item.updated_at or item.created_at,
        )
        for item in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    conversation = await ConversationService.get_active_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = await ConversationService.get_conversation_history(db, conversation_id)
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at or conversation.created_at,
        messages=[
            MessageDTO(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                meta_info=msg.meta_info or {},
                created_at=msg.created_at,
            )
            for msg in history
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await ConversationService.soft_delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}
