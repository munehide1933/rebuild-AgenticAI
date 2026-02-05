from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableLambda, RunnableParallel


class MCPService:
    """基于 LangChain Runnable 组装 MCP 上下文。"""

    def __init__(self) -> None:
        self._pipeline = RunnableParallel(
            intent=RunnableLambda(self._extract_intent),
            history=RunnableLambda(self._extract_history),
            history_count=RunnableLambda(lambda data: len(data.get("conversation_history", []))),
        )

    def build_context(self, question: str, conversation_history: list[Any]) -> dict[str, Any]:
        payload = {
            "question": question,
            "conversation_history": conversation_history,
        }
        result = self._pipeline.invoke(payload)
        result["context_hint"] = "基于最近会话理解用户当前目标，优先延续上下文。"
        return result

    @staticmethod
    def _extract_intent(data: dict[str, Any]) -> str:
        question = str(data.get("question", ""))
        return question.strip().split("\n")[0][:200]

    @staticmethod
    def _extract_history(data: dict[str, Any]) -> list[dict[str, str]]:
        history = data.get("conversation_history", [])
        recent_messages: list[dict[str, str]] = []
        for item in history[-8:]:
            role = getattr(item, "role", "user")
            content = getattr(item, "content", "")
            recent_messages.append({"role": role, "content": content})
        return recent_messages
