"""
重构后的聊天 API：使用推理编排器

支持：
1. 自动路由（简单/复杂/代码问题）
2. Direct / CoT / ReAct 三种推理模式
3. GPT-4o / DeepSeek-R1 双模型
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import ChatRequest, ChatResponse
from app.models.database import get_db
from app.services.conversation_service import ConversationService
from app.services.reasoning_orchestrator import ReasoningOrchestrator
from app.services.llm_service import LLMService


router = APIRouter(prefix="/api/chat", tags=["chat"])

# 初始化服务
llm_service = LLMService()
reasoning_orchestrator = ReasoningOrchestrator(llm_service)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息（智能推理版）
    
    流程：
    1. 创建/获取对话
    2. 保存用户消息
    3. 路由决策 → 选择推理模式
    4. 执行推理（Direct/CoT/ReAct）
    5. 保存助手响应
    """
    
    try:
        # 1. 获取或创建对话
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation = await ConversationService.create_conversation(
                db,
                title=request.message[:50],
            )
            conversation_id = conversation.id

        # 2. 保存用户消息
        await ConversationService.add_message(
            db,
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )

        # 3. 获取对话历史
        history = await ConversationService.get_conversation_history(
            db,
            conversation_id
        )

        # 4. 执行智能推理
        print(f"🤖 处理问题: {request.message[:100]}...")
        
        reasoning_result = await reasoning_orchestrator.reason(
            question=request.message,
            conversation_history=history[-10:],  # 最近 10 条
        )
        
        print(f"✅ 推理完成: {reasoning_result.strategy} ({reasoning_result.model})")

        # 5. 构建 meta_info
        meta_info = {
            "strategy": reasoning_result.strategy,
            "model": reasoning_result.model,
            "confidence": reasoning_result.confidence,
        }
        
        # 添加推理轨迹（如果有）
        if reasoning_result.reasoning_trace:
            meta_info["reasoning_trace"] = reasoning_result.reasoning_trace
        
        # 添加 ReAct 步骤（如果有）
        if reasoning_result.steps:
            meta_info["react_steps"] = reasoning_result.steps
        
        # 添加其他元数据
        meta_info.update(reasoning_result.metadata)

        # 6. 保存助手响应
        assistant_message = await ConversationService.add_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=reasoning_result.answer,
            meta_info=meta_info,
        )
        await db.refresh(assistant_message)

        # 7. 返回响应
        return ChatResponse(
            message_id=assistant_message.id,
            content=reasoning_result.answer,
            conversation_id=conversation_id,
            workflow_state={
                "current_phase": reasoning_result.strategy,
                "active_personas": [reasoning_result.model],
                "phase_outputs": meta_info,
            },
            code_modifications=None,
            suggestions=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reasoning-stats")
async def get_reasoning_stats():
    """获取推理统计信息（调试用）"""
    return {
        "supported_strategies": ["direct", "cot", "react"],
        "supported_models": ["gpt-4o", "deepseek-r1"],
        "routing_rules": "自动路由",
    }
