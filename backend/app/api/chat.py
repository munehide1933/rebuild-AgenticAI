"""重构后的聊天 API：支持会话持久化、摘要历史、软删除与 MCP 上下文注入。"""

from __future__ import annotations

import asyncio
import json
from typing import Any

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
from app.services.llm_service import LLMService
from app.services.mcp_service import MCPService
from app.services.reasoning_orchestrator import ReasoningOrchestrator
from app.services.user_profile_service import UserProfileService
from app.services.v1_parity_pipeline import V1ParityPipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])

llm_service = LLMService()
reasoning_orchestrator = ReasoningOrchestrator(llm_service)
mcp_service = MCPService()
v1_parity_pipeline = V1ParityPipeline(llm_service)


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

        if reasoning_result.reasoning_trace:
            meta_info["reasoning_trace"] = reasoning_result.reasoning_trace
        if reasoning_result.steps:
            meta_info["react_steps"] = reasoning_result.steps
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


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = await _prepare_chat_result(request, db)
        return ChatResponse(**payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        async def event_generator():
            progress_hints = [
                "正在理解问题...",
                "正在检索上下文与历史偏好...",
                "正在进行推理分析...",
                "正在组织最终回答...",
            ]

            task = asyncio.create_task(_prepare_chat_result(request, db))
            hint_index = 0

            while not task.done():
                hint = progress_hints[hint_index % len(progress_hints)]
                hint_index += 1
                yield f"data: {json.dumps({'type': 'chunk', 'content': hint + '\n'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.8)

            payload = await task
            content = payload["content"]
            chunk_size = 40
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

            yield f"data: {json.dumps({'type': 'done', 'payload': payload}, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/reasoning-stats")
async def get_reasoning_stats():
    return {
        "supported_strategies": ["direct", "cot", "react", "v1-parity-pipeline"],
        "supported_models": ["gpt-5.1-chat", "DeepSeek-R1-0528"],
        "routing_rules": "自动路由 + 可选深度思考/联网检索",
        "mcp_context": "enabled_with_user_profile",
    }
