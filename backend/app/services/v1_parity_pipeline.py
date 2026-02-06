from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.llm_service import LLMService
from app.tools.tavily_search import tavily_search


@dataclass
class V1Intent:
    intent: str = "general_help"
    domain: str = "general"
    requires_web_search: bool = False
    requires_code: bool = False
    key_concepts: list[str] = field(default_factory=list)


@dataclass
class V1PipelineResult:
    answer: str
    strategy: str
    model: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)
    code_modifications: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class V1ParityPipeline:
    """模拟 v1 的多阶段能力：理解→检索→分析→反思→详细分析→代码生成→整合。"""

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service

    async def run(
        self,
        question: str,
        conversation_history: list[Any],
        *,
        deep_thinking: bool = False,
        web_search_enabled: bool = False,
    ) -> V1PipelineResult:
        model = self._llm.get_recommended_model(question)
        intent = await self._understanding(question, conversation_history, model)

        should_search = (
            web_search_enabled
            or intent.requires_web_search
            or intent.domain.lower() in {"medical", "legal"}
        )

        search_result = ""
        if should_search:
            search_query = self._build_search_query(question, intent)
            search_result = tavily_search(search_query)

        initial_analysis = await self._initial_analysis(
            question, conversation_history, intent, search_result, model
        )

        refined_answer = initial_analysis
        reflection = None
        if deep_thinking:
            reflection = await self._reflection(question, initial_analysis, model)
            refined_answer = reflection.get("refined_answer", initial_analysis)

        detailed_analysis = None
        code_artifact = None
        code_modifications: list[dict[str, Any]] = []

        if intent.requires_code or intent.domain.lower() in {"arch/dev", "development", "engineering"}:
            detailed_analysis = await self._detailed_analysis(question, refined_answer, model)
            code_artifact = await self._code_generation(question, detailed_analysis)
            if code_artifact.get("code"):
                code_modifications.append(
                    {
                        "file_path": f"generated/{code_artifact.get('title', 'solution').replace(' ', '_')}.txt",
                        "modification_type": "ADD",
                        "content": code_artifact.get("code", ""),
                    }
                )

        final_answer = self._synthesis(
            intent=intent,
            initial_analysis=initial_analysis,
            refined_answer=refined_answer,
            search_result=search_result,
            reflection=reflection,
            detailed_analysis=detailed_analysis,
            code_artifact=code_artifact,
        )

        return V1PipelineResult(
            answer=final_answer,
            strategy="v1-parity-pipeline",
            model=model,
            confidence=0.88 if deep_thinking else 0.8,
            metadata={
                "intent": intent.__dict__,
                "used_web_search": should_search,
                "search_result_preview": search_result[:600],
                "deep_thinking": deep_thinking,
                "detailed_analysis": detailed_analysis,
                "code_artifact": code_artifact,
                "reflection": reflection,
            },
            code_modifications=code_modifications,
            suggestions=[] if should_search else ["如需最新外部信息，可启用 web_search 模式。"],
        )

    async def _understanding(self, question: str, history: list[Any], model: str) -> V1Intent:
        prompt = f"""
你是 Understanding Agent。请分析用户问题并严格返回 JSON：
{{
  "intent": "...",
  "domain": "general|arch/dev|medical|legal",
  "requires_web_search": true/false,
  "requires_code": true/false,
  "key_concepts": ["..."]
}}

用户问题：{question}
最近历史（最多10条）：{self._history_to_text(history[-10:])}
"""
        raw = await self._llm.generate_simple(prompt, model=model)
        data = self._safe_json(raw)
        return V1Intent(
            intent=str(data.get("intent", "general_help")),
            domain=str(data.get("domain", "general")),
            requires_web_search=bool(data.get("requires_web_search", False)),
            requires_code=bool(data.get("requires_code", False)),
            key_concepts=self._to_str_list(data.get("key_concepts", [])),
        )

    async def _initial_analysis(
        self,
        question: str,
        history: list[Any],
        intent: V1Intent,
        search_result: str,
        model: str,
    ) -> str:
        system_prompt = "你是 Initial Analysis Agent。请给出结构化、可执行、面向落地的分析。"
        user_message = (
            f"问题：{question}\n"
            f"理解结果：{json.dumps(intent.__dict__, ensure_ascii=False)}\n"
            f"搜索结果：{search_result[:3000] if search_result else '无'}\n"
            "请输出：问题理解、可执行步骤、关键风险、下一步建议。"
        )
        result = await self._llm.generate_response(system_prompt, user_message, history[-10:], model=model)
        return result["content"]

    async def _reflection(self, question: str, initial_analysis: str, model: str) -> dict[str, Any]:
        prompt = f"""
你是 Reflection Agent。请对初步分析进行批判性反思，并严格输出 JSON：
{{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvements": ["..."],
  "refined_answer": "..."
}}

问题：{question}
初步分析：{initial_analysis}
"""
        return self._safe_json(await self._llm.generate_simple(prompt, model=model))

    async def _detailed_analysis(self, question: str, refined_answer: str, model: str) -> dict[str, Any]:
        prompt = f"""
你是 Detailed Analysis Agent。请严格输出 JSON：
{{
  "requirements": ["..."],
  "architecture": "...",
  "tech_stack": ["..."],
  "clarifications": ["..."]
}}

问题：{question}
已有答案：{refined_answer}
"""
        return self._safe_json(await self._llm.generate_simple(prompt, model=model))

    async def _code_generation(self, question: str, detailed_analysis: dict[str, Any]) -> dict[str, Any]:
        model = self._llm.get_recommended_model("code generation " + question)
        prompt = f"""
你是 Code Generation Agent。请严格输出 JSON：
{{
  "title": "...",
  "language": "...",
  "code": "...",
  "explanation": "...",
  "dependencies": ["..."]
}}

详细分析：{json.dumps(detailed_analysis, ensure_ascii=False)}
"""
        return self._safe_json(await self._llm.generate_simple(prompt, model=model))

    def _synthesis(
        self,
        *,
        intent: V1Intent,
        initial_analysis: str,
        refined_answer: str,
        search_result: str,
        reflection: dict[str, Any] | None,
        detailed_analysis: dict[str, Any] | None,
        code_artifact: dict[str, Any] | None,
    ) -> str:
        sections = [
            "## 需求理解",
            f"- 意图: {intent.intent}",
            f"- 领域: {intent.domain}",
            f"- 关键概念: {', '.join(intent.key_concepts) if intent.key_concepts else '无'}",
            "",
            "## 分析结果",
            refined_answer or initial_analysis,
        ]

        if search_result:
            sections.extend(["", "## 网络搜索摘要", search_result[:1200]])
        if reflection:
            sections.extend(
                [
                    "",
                    "## 反思改进",
                    f"- 优势: {', '.join(self._to_str_list(reflection.get('strengths', [])))}",
                    f"- 不足: {', '.join(self._to_str_list(reflection.get('weaknesses', [])))}",
                    f"- 改进: {', '.join(self._to_str_list(reflection.get('improvements', [])))}",
                ]
            )
        if detailed_analysis:
            sections.extend(
                [
                    "",
                    "## 技术方案",
                    f"- 架构: {detailed_analysis.get('architecture', '未提供')}",
                    f"- 技术栈: {', '.join(self._to_str_list(detailed_analysis.get('tech_stack', [])))}",
                    f"- 澄清项: {', '.join(self._to_str_list(detailed_analysis.get('clarifications', [])))}",
                ]
            )
        if code_artifact and code_artifact.get("code"):
            sections.extend(
                [
                    "",
                    "## 代码实现",
                    f"**{code_artifact.get('title', 'Generated Code')}** ({code_artifact.get('language', 'text')})",
                    f"```{code_artifact.get('language', 'text')}\n{code_artifact.get('code', '')}\n```",
                    code_artifact.get("explanation", ""),
                ]
            )
        return "\n".join(sections).strip()

    @staticmethod
    def _history_to_text(history: list[Any]) -> str:
        return "\n".join(
            f"{getattr(item, 'role', 'user')}: {getattr(item, 'content', '')[:300]}" for item in history
        )

    @staticmethod
    def _build_search_query(question: str, intent: V1Intent) -> str:
        concepts = ", ".join(intent.key_concepts[:5])
        return f"{question}\n关键词: {concepts}" if concepts else question

    @staticmethod
    def _to_str_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if value is None:
            return []
        return [str(value)]

    @staticmethod
    def _safe_json(raw: str) -> dict[str, Any]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            match = re.search(r"\{[\s\S]*\}", raw)
            if not match:
                return {}
            try:
                data = json.loads(match.group(0))
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
