from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.agent import Agent
from app.services.llm_service import LLMService


@dataclass
class ReasoningResult:
    answer: str
    strategy: str
    model: str
    confidence: float
    reasoning_trace: list[str] | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ReasoningState(TypedDict, total=False):
    question: str
    conversation_history: list[Any]
    mcp_context: dict[str, Any]
    model: str
    strategy: Literal["cot", "react"]
    is_complex: bool
    answer: str
    reasoning_trace: list[str]
    steps: list[dict[str, Any]]
    confidence: float
    metadata: dict[str, Any]


class ReasoningOrchestrator:
    """基于 LangGraph 的推理编排器。"""

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service
        self._agent = Agent()
        self._workflow = self._build_workflow()

    async def reason(
        self,
        question: str,
        conversation_history: Iterable[Any],
        mcp_context: dict[str, Any] | None = None,
    ) -> ReasoningResult:
        initial_state: ReasoningState = {
            "question": question,
            "conversation_history": list(conversation_history),
            "mcp_context": mcp_context or {},
            "metadata": {},
        }
        result_state = await self._workflow.ainvoke(initial_state)

        return ReasoningResult(
            answer=result_state.get("answer", ""),
            strategy=result_state.get("strategy", "cot"),
            model=result_state.get("model", self._llm.get_recommended_model(question)),
            confidence=result_state.get("confidence", 0.7),
            reasoning_trace=result_state.get("reasoning_trace"),
            steps=result_state.get("steps", []),
            metadata=result_state.get("metadata", {}),
        )

    def _build_workflow(self):
        workflow = StateGraph(ReasoningState)
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("cot", self._cot_node)
        workflow.add_node("react", self._react_node)
        workflow.add_node("finalize", self._finalize_node)

        workflow.add_edge(START, "classify")
        workflow.add_conditional_edges(
            "classify",
            self._route_node,
            {
                "cot": "cot",
                "react": "react",
            },
        )
        workflow.add_edge("cot", "finalize")
        workflow.add_edge("react", "finalize")
        workflow.add_edge("finalize", END)
        return workflow.compile()

    async def _classify_node(self, state: ReasoningState) -> ReasoningState:
        question = state["question"]
        mcp_context = state.get("mcp_context", {})
        is_complex = await self._agent._is_complex_question(question, mcp_context)
        model = self._llm.get_recommended_model(question)
        strategy: Literal["cot", "react"] = "react" if is_complex else "cot"

        return {
            **state,
            "is_complex": is_complex,
            "model": model,
            "strategy": strategy,
        }

    @staticmethod
    def _route_node(state: ReasoningState) -> Literal["cot", "react"]:
        return state.get("strategy", "cot")

    async def _cot_node(self, state: ReasoningState) -> ReasoningState:
        answer, reasoning_trace = await self._agent._cot_reasoning(
            state["question"],
            state.get("conversation_history", []),
            state.get("mcp_context", {}),
        )
        has_reasoning = len(reasoning_trace) >= 2
        confidence = 0.85 if has_reasoning else 0.70
        return {
            **state,
            "answer": answer,
            "reasoning_trace": reasoning_trace,
            "steps": [],
            "confidence": confidence,
            "metadata": {
                "cot_step_count": len(reasoning_trace),
                "mcp": state.get("mcp_context", {}),
            },
        }

    async def _react_node(self, state: ReasoningState) -> ReasoningState:
        answer, steps = await self._agent._react_reasoning(
            state["question"],
            state.get("conversation_history", []),
            state.get("mcp_context", {}),
        )
        has_tool_usage = len(steps) > 0
        confidence = 0.90 if has_tool_usage else 0.75
        return {
            **state,
            "answer": answer,
            "reasoning_trace": None,
            "steps": steps,
            "confidence": confidence,
            "metadata": {
                "react_step_count": len(steps),
                "used_tools": has_tool_usage,
                "mcp": state.get("mcp_context", {}),
            },
        }

    @staticmethod
    async def _finalize_node(state: ReasoningState) -> ReasoningState:
        return state
