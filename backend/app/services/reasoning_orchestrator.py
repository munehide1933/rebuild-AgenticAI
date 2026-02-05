from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from app.core.agent import Agent
from app.services.llm_service import LLMService


@dataclass
class ReasoningResult:
    """推理结果"""
    answer: str                          # 最终答案
    strategy: str                        # 推理策略（cot/react）
    model: str                           # 使用的模型
    confidence: float                    # 置信度（0-1）
    reasoning_trace: list[str] | None = None  # CoT 思考步骤
    steps: list[dict[str, Any]] = field(default_factory=list)  # ReAct 工具调用步骤
    metadata: dict[str, Any] = field(default_factory=dict)     # 其他元数据


class ReasoningOrchestrator:
    """
    统一推理编排器
    
    功能：
    1. 自动路由（简单/复杂问题）
    2. 选择推理策略（CoT/ReAct）
    3. 选择合适的模型
    4. 记录完整推理轨迹
    """

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service
        self._agent = Agent()

    async def reason(
        self,
        question: str,
        conversation_history: Iterable[Any]
    ) -> ReasoningResult:
        """
        执行推理
        
        Args:
            question: 用户问题
            conversation_history: 对话历史
            
        Returns:
            推理结果（包含答案、策略、模型、置信度等）
        """
        # 1. 判断问题复杂度
        is_complex = await self._agent._is_complex_question(question)
        
        # 2. 选择推理策略
        strategy = "react" if is_complex else "cot"
        
        # 3. 选择模型（基于问题内容）
        model = self._llm.get_recommended_model(question)
        
        # 4. 执行推理
        history_list = list(conversation_history)
        
        if strategy == "react":
            # ReAct 推理
            answer, steps = await self._agent._react_reasoning(question, history_list)
            
            # 计算置信度（有工具调用 → 高置信度）
            has_tool_usage = len(steps) > 0
            confidence = 0.90 if has_tool_usage else 0.75
            
            return ReasoningResult(
                answer=answer,
                strategy=strategy,
                model=model,
                confidence=confidence,
                reasoning_trace=None,
                steps=steps,
                metadata={
                    "react_step_count": len(steps),
                    "used_tools": has_tool_usage,
                }
            )
        else:
            # CoT 推理
            answer, reasoning_trace = await self._agent._cot_reasoning(question, history_list)
            
            # 计算置信度（思考步骤多 → 高置信度）
            has_reasoning = len(reasoning_trace) >= 2
            confidence = 0.85 if has_reasoning else 0.70
            
            return ReasoningResult(
                answer=answer,
                strategy=strategy,
                model=model,
                confidence=confidence,
                reasoning_trace=reasoning_trace,
                steps=[],
                metadata={
                    "cot_step_count": len(reasoning_trace),
                }
            )
