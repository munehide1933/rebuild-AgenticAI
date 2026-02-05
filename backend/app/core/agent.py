import json
import re
from app.services.llm_service import LLMService
from app.tools.tavily_search import tavily_search
from app.config import settings


class Agent:
    """
    智能体：支持 CoT（简单问题）和 ReAct（复杂问题）
    """

    def __init__(self, max_react_steps: int = 5):
        self.llm = LLMService()
        self.max_react_steps = max_react_steps

    async def run(self, user_message: str, conversation_history: list):
        """
        主入口：自动选择 CoT / ReAct
        """
        is_complex = await self._is_complex_question(user_message)

        if is_complex:
            return await self._react_reasoning(user_message, conversation_history)
        else:
            return await self._cot_reasoning(user_message, conversation_history)

    # ----------------------------------------------------------
    # 复杂度判断：使用默认模型判断
    # ----------------------------------------------------------
    async def _is_complex_question(self, user_message: str) -> bool:
        """
        判断问题是否复杂（需要 ReAct 推理）
        
        使用默认模型进行判断
        """
        prompt = f"""
You are a classifier. Determine whether the user question requires multi-step reasoning,
external knowledge, or tool use.

User question:
{user_message}

Is this a complex question? Answer with "yes" or "no" only.
"""
        # 使用默认模型进行判断
        result = await self.llm.generate_simple(prompt, model=settings.DEFAULT_MODEL)
        return "yes" in result.lower()

    # ----------------------------------------------------------
    # 简单问题：CoT 推理（带显式思考过程）
    # ----------------------------------------------------------
    async def _cot_reasoning(self, user_message: str, history: list):
        """
        CoT (Chain of Thought) 推理
        
        使用推荐的模型（可能是默认模型或 CS 专家模型）
        返回：(思考步骤列表, 最终答案)
        """
        # 根据问题选择模型
        model = self.llm.get_recommended_model(user_message)
        
        system_prompt = """
You are a helpful AI assistant. Please think step by step and output your reasoning process.

Format your response as:
**思考过程：**
1. [Step 1 analysis]
2. [Step 2 analysis]
...

**最终答案：**
[Your concise answer here]
"""

        result = await self.llm.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=history,
            model=model,
        )
        
        # 解析思考过程和最终答案
        content = result["content"]
        
        # 提取思考步骤
        thinking_match = re.search(
            r'\*\*思考过程：?\*\*\s*(.*?)\s*\*\*最终答案：?\*\*',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        reasoning_trace = []
        final_answer = content
        
        if thinking_match:
            thinking_section = thinking_match.group(1).strip()
            # 提取编号步骤
            steps = re.findall(r'^\d+\.\s*(.+?)(?=\n\d+\.|$)', thinking_section, re.MULTILINE | re.DOTALL)
            reasoning_trace = [s.strip() for s in steps if s.strip()]
            
            # 提取最终答案
            answer_match = re.search(
                r'\*\*最终答案：?\*\*\s*(.*)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            if answer_match:
                final_answer = answer_match.group(1).strip()
        
        return final_answer, reasoning_trace

    # ----------------------------------------------------------
    # 复杂问题：ReAct 推理链 + Tavily Web Search
    # ----------------------------------------------------------
    async def _react_reasoning(self, user_message: str, history: list):
        """
        ReAct (Reason + Act) 推理
        
        使用推荐的模型（可能是默认模型或 CS 专家模型）
        返回：(最终答案, 执行步骤列表)
        """
        # 根据问题选择模型
        model = self.llm.get_recommended_model(user_message)
        
        prompt = self._build_react_prompt(user_message)
        steps = []  # 记录所有步骤

        for step_num in range(self.max_react_steps):
            result = await self.llm.generate_simple(prompt, model=model)
            result = result.strip()

            # ---------- Final Answer ----------
            if "Final Answer:" in result:
                final_answer = result.split("Final Answer:", 1)[1].strip()
                return final_answer, steps

            # ---------- Action ----------
            if "Action:" in result:
                action_data = self._extract_action(result)
                
                if action_data is None:
                    # 解析失败，引导 LLM 重新输出
                    prompt += f"\n{result}\n\n[ERROR] Invalid action format. Please use exact JSON format:\nAction: {{\n    \"tool\": \"search\",\n    \"query\": \"your query\"\n}}\n\nThought: "
                    continue
                
                # 执行工具调用
                if action_data["tool"] == "search":
                    query = action_data["query"]
                    search_result = tavily_search(query)
                    
                    # 记录步骤
                    steps.append({
                        "step": step_num + 1,
                        "action": "search",
                        "input": query,
                        "output": search_result[:500],  # 限制长度
                    })
                    
                    prompt += f"\nObservation: {search_result}\n\nThought: "
                    continue

            # ---------- Regular Thought ----------
            prompt += f"\n{result}\n"

        # 超出步数限制
        return "抱歉，该问题过于复杂，我无法在限定步数内完成推理。", steps

    # ----------------------------------------------------------
    # 辅助方法：提取 Action JSON
    # ----------------------------------------------------------
    def _extract_action(self, text: str) -> dict | None:
        """
        从 LLM 输出中提取 Action JSON
        
        支持多种格式：
        1. 纯 JSON 块
        2. 带前后文字的 JSON
        3. 手动解析字段
        """
        # 策略 1: 提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 策略 2: 提取纯 JSON（无代码块）
        json_match = re.search(r'Action:\s*(\{[^}]+\})', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 策略 3: 手动解析字段
        tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', text)
        query_match = re.search(r'"query"\s*:\s*"([^"]+)"', text)
        
        if tool_match and query_match:
            return {
                "tool": tool_match.group(1),
                "query": query_match.group(1),
            }
        
        return None

    # ----------------------------------------------------------
    # 构造 ReAct Prompt
    # ----------------------------------------------------------
    def _build_react_prompt(self, user_input: str):
        return f"""
You are an AI agent using ReAct (Reason + Act) framework.
You can think step by step, call tools, observe results, and continue reasoning.

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
