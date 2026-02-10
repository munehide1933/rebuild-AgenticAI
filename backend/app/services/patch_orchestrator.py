from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.deepseek_service import DeepSeekService
from app.services.llm_service import LLMService
from app.services.repo_analyzer import RepoAnalyzer


class PatchState(TypedDict, total=False):
    request: str
    repo_path: str
    repo_summary: dict[str, Any]
    intent: dict[str, Any]
    architecture: str
    patch: str
    mcp_context: dict[str, Any]


@dataclass
class PatchResult:
    intent: dict[str, Any]
    repo_summary: dict[str, Any]
    architecture: str
    patch: str
    metadata: dict[str, Any] = field(default_factory=dict)


class PatchOrchestrator:
    """LangGraph 驱动的补丁生成编排器。"""

    def __init__(self, llm_service: LLMService, deepseek_service: DeepSeekService) -> None:
        self._llm = llm_service
        self._deepseek = deepseek_service
        self._analyzer = RepoAnalyzer()
        self._workflow = self._build_workflow()

    async def generate(
        self,
        request: str,
        repo_path: str,
        mcp_context: dict[str, Any] | None = None,
    ) -> PatchResult:
        initial_state: PatchState = {
            "request": request,
            "repo_path": repo_path,
            "mcp_context": mcp_context or {},
        }
        result_state = await self._workflow.ainvoke(initial_state)

        return PatchResult(
            intent=result_state.get("intent", {}),
            repo_summary=result_state.get("repo_summary", {}),
            architecture=result_state.get("architecture", ""),
            patch=result_state.get("patch", ""),
            metadata={
                "mcp_context": result_state.get("mcp_context", {}),
            },
        )

    def _build_workflow(self):
        workflow = StateGraph(PatchState)
        workflow.add_node("intent", self._intent_node)
        workflow.add_node("repo", self._repo_node)
        workflow.add_node("architecture", self._architecture_node)
        workflow.add_node("patch", self._patch_node)

        workflow.add_edge(START, "intent")
        workflow.add_edge("intent", "repo")
        workflow.add_edge("repo", "architecture")
        workflow.add_edge("architecture", "patch")
        workflow.add_edge("patch", END)
        return workflow.compile()

    async def _intent_node(self, state: PatchState) -> PatchState:
        prompt = (
            "你是架构师助手，请提取用户需求的核心意图。\n"
            "请输出 JSON，字段包含: intent, goal, constraints, risks。\n\n"
            f"用户请求:\n{state['request']}\n\n"
            f"MCP 上下文:\n{json.dumps(state.get('mcp_context', {}), ensure_ascii=False)}"
        )
        response = await self._llm.generate_simple(prompt, model=self._llm.get_recommended_model(state["request"]))
        intent = self._safe_json(response)
        return {**state, "intent": intent}

    async def _repo_node(self, state: PatchState) -> PatchState:
        repo_summary = self._analyzer.analyze(state["repo_path"], focus=state.get("request"))
        return {**state, "repo_summary": repo_summary}

    async def _architecture_node(self, state: PatchState) -> PatchState:
        prompt = (
            "你是资深架构师，请基于仓库概览与需求输出架构设计建议，"
            "包含关键模块、需要新增/修改的文件，以及数据流简述。\n\n"
            f"需求:\n{state['request']}\n\n"
            f"意图摘要:\n{json.dumps(state.get('intent', {}), ensure_ascii=False)}\n\n"
            f"仓库摘要:\n{json.dumps(state.get('repo_summary', {}), ensure_ascii=False)}"
        )
        response = await self._llm.generate_simple(prompt, model=self._llm.get_recommended_model(state["request"]))
        return {**state, "architecture": response.strip()}

    async def _patch_node(self, state: PatchState) -> PatchState:
        system_prompt = (
            "你是 DeepSeek-R1 代码补丁生成器。"
            "请根据架构方案输出统一 diff 格式补丁，仅输出 diff 内容。"
        )
        user_prompt = (
            "需求:\n"
            f"{state['request']}\n\n"
            "意图:\n"
            f"{json.dumps(state.get('intent', {}), ensure_ascii=False)}\n\n"
            "架构:\n"
            f"{state.get('architecture', '')}\n\n"
            "仓库摘要:\n"
            f"{json.dumps(state.get('repo_summary', {}), ensure_ascii=False)}"
        )
        deepseek_response = await self._deepseek.generate_patch(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        patch = deepseek_response.get("content", "")
        return {
            **state,
            "patch": patch,
        }

    @staticmethod
    def _safe_json(payload: str) -> dict[str, Any]:
        try:
            return json.loads(payload)
        except Exception:
            return {"intent": payload.strip()[:200]}
