import json
import re
from typing import Any

from app.config import settings
from app.services.llm_service import LLMService
from app.tools.tavily_search import tavily_search


class Agent:
    """智能体：支持 CoT（简单问题）和 ReAct（复杂问题）"""

    def __init__(self, max_react_steps: int = 20):
        self.llm = LLMService()
        self.max_react_steps = max_react_steps

    async def run(self, user_message: str, conversation_history: list, mcp_context: dict[str, Any] | None = None):
        is_complex = await self._is_complex_question(user_message, mcp_context)

        if is_complex:
            return await self._react_reasoning(user_message, conversation_history, mcp_context)
        return await self._cot_reasoning(user_message, conversation_history, mcp_context)

    async def _is_complex_question(self, user_message: str, mcp_context: dict[str, Any] | None = None) -> bool:
        prompt = f"""
You are a classifier. Determine whether the user question requires multi-step reasoning,
external knowledge, or tool use.

User question:
{user_message}

MCP context:
{json.dumps(mcp_context or {}, ensure_ascii=False)}

Is this a complex question? Answer with "yes" or "no" only.
"""
        result = await self.llm.generate_simple(prompt, model=settings.DEFAULT_MODEL)
        return "yes" in result.lower()

    async def _cot_reasoning(self, user_message: str, history: list, mcp_context: dict[str, Any] | None = None):
        model = self.llm.get_recommended_model(user_message)

        system_prompt = f"""
You are a helpful AI assistant. Provide a concise, direct answer without revealing your chain-of-thought.

MCP context (JSON):
{json.dumps(mcp_context or {}, ensure_ascii=False)}
"""

        result = await self.llm.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=history,
            model=model,
        )

        content = result["content"].strip()
        content = re.sub(r'\*\*思考过程：?\*\*[\s\S]*?\*\*最终答案：?\*\*', '', content, flags=re.IGNORECASE).strip()
        content = re.sub(r'^(Final Answer:|最终答案：)\s*', '', content, flags=re.IGNORECASE).strip()

        return content, []

    async def _react_reasoning(self, user_message: str, history: list, mcp_context: dict[str, Any] | None = None):
        model = self.llm.get_recommended_model(user_message)

        prompt = self._build_react_prompt(user_message, mcp_context)
        used_tools = False

        for step_num in range(self.max_react_steps):
            result = await self.llm.generate_simple(prompt, model=model)
            result = result.strip()

            if "Final Answer:" in result:
                final_answer = result.split("Final Answer:", 1)[1].strip()
                return final_answer, used_tools

            if "Action:" in result:
                action_data = self._extract_action(result)

                if action_data is None:
                    prompt += (
                        f"\n{result}\n\n[ERROR] Invalid action format. Please use exact JSON format:\n"
                        "Action: {\n    \"tool\": \"search\",\n    \"query\": \"your query\"\n}\n\nThought: "
                    )
                    continue

                if action_data["tool"] == "search":
                    query = action_data["query"]
                    search_result = tavily_search(query)
                    used_tools = True

                    prompt += f"\nObservation: {search_result}\n\nThought: "
                    continue

            prompt += f"\n{result}\n"

        summary_prompt = (
            prompt
            + "\n\n你已经进行了多轮推理。现在请基于已有 Thought/Observation 直接给出最终答案，"
            + "不再调用工具，格式必须是: Final Answer: <answer>"
        )
        summary_result = (await self.llm.generate_simple(summary_prompt, model=model)).strip()
        if "Final Answer:" in summary_result:
            return summary_result.split("Final Answer:", 1)[1].strip(), used_tools

        return summary_result or "抱歉，我暂时无法完成该问题。", used_tools

    def _extract_action(self, text: str) -> dict | None:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass

        json_match = re.search(r'Action:\s*(\{[^}]+\})', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass

        tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', text)
        query_match = re.search(r'"query"\s*:\s*"([^"]+)"', text)

        if tool_match and query_match:
            return {
                "tool": tool_match.group(1),
                "query": query_match.group(1),
            }

        return None

    def _build_react_prompt(self, user_input: str, mcp_context: dict[str, Any] | None = None):
        return f"""
You are an AI agent using ReAct (Reason + Act) framework.
You can think step by step, call tools, observe results, and continue reasoning.

MCP context (JSON):
{json.dumps(mcp_context or {}, ensure_ascii=False)}

Available tool:
1. tavily_search: Search the web for up-to-date information.

Usage:
Action: {{
    "tool": "search",
    "query": "<the query>"
}}

When you have enough information, respond with:
Final Answer: <answer>

User question:
{user_input}

Thought:
"""
