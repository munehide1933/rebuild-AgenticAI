from __future__ import annotations

from typing import Any, Iterable

import httpx

from app.config import settings


class LLMService:
    """
    基于 Azure OpenAI 的 LLM 调用封装（支持多模型）
    
    支持模型：
    - 默认模型（通用）: settings.DEFAULT_MODEL
    - CS 专家模型: settings.CS_SPECIALIST_MODEL
    """

    def __init__(self) -> None:
        self._endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        self._api_version = settings.AZURE_OPENAI_API_VERSION
        self._api_key = settings.AZURE_OPENAI_API_KEY
        self._configured = bool(self._endpoint and self._api_key)
        
        # 模型部署名称映射（从配置读取）
        self._model_deployments = {
            settings.DEFAULT_MODEL: settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            settings.CS_SPECIALIST_MODEL: settings.AZURE_DEEPSEEK_DEPLOYMENT_NAME,
        }
        
        # 当前支持的模型列表
        self._supported_models = list(self._model_deployments.keys())

    async def generate_simple(self, prompt: str, model: str | None = None) -> str:
        """
        生成简单回答（仅用户输入）
        
        Args:
            prompt: 用户输入
            model: 模型名称（留空则使用默认模型）
        """
        if model is None:
            model = settings.DEFAULT_MODEL
            
        messages = [{"role": "user", "content": prompt}]
        response = await self._chat(messages, model=model)
        return response["content"]

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Iterable[Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        生成对话式回答
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            conversation_history: 对话历史
            model: 模型名称（留空则使用默认模型）
        """
        if model is None:
            model = settings.DEFAULT_MODEL
            
        messages = [{"role": "system", "content": system_prompt}]
        for item in conversation_history:
            role = getattr(item, "role", None) or "user"
            content = getattr(item, "content", None) or ""
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})
        return await self._chat(messages, model=model)

    def get_recommended_model(self, question: str) -> str:
        """
        根据问题推荐模型
        
        策略：
        - 计算机/软件工程相关 → CS 专家模型
        - 其他问题 → 默认模型
        
        Returns:
            推荐的模型名称
        """
        question_lower = question.lower()
        
        # 计算机科学/软件工程关键词（50+ 个）
        cs_keywords = {
            # 编程语言
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            
            # 开发相关
            'code', 'coding', 'programming', 'debug', 'debugging', 'bug', 'error',
            'exception', 'compile', 'runtime', 'syntax', 'refactor', 'optimize',
            
            # 软件工程
            'api', 'rest', 'graphql', 'websocket', 'http', 'https', 'json', 'xml',
            'database', 'sql', 'nosql', 'orm', 'migration', 'cache', 'redis',
            'architecture', 'design pattern', 'microservice', 'monolith',
            
            # 算法/数据结构
            'algorithm', 'data structure', 'array', 'linked list', 'tree', 'graph',
            'hash', 'sort', 'search', 'recursion', 'dynamic programming',
            
            # 框架/工具
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'spring',
            'docker', 'kubernetes', 'git', 'ci/cd', 'jenkins', 'github', 'gitlab',
            
            # 问题诊断
            'crash', 'memory leak', 'performance', 'latency', 'throughput',
            'concurrency', 'thread', 'async', 'await', 'callback',
            
            # 其他
            'function', 'class', 'method', 'variable', 'interface', 'module',
            'package', 'library', 'framework', 'frontend', 'backend', 'fullstack',
        }
        
        # 检查是否包含 CS 关键词
        if any(kw in question_lower for kw in cs_keywords):
            return settings.CS_SPECIALIST_MODEL
        
        return settings.DEFAULT_MODEL

    async def _chat(self, messages: list[dict[str, str]], model: str) -> dict[str, Any]:
        """
        调用 Azure OpenAI Chat API
        
        Args:
            messages: 消息列表
            model: 模型名称
        """
        if not self._configured:
            return {
                "content": f"LLM 未配置，返回占位回复。请在 .env 中配置 Azure OpenAI 相关参数。\n(请求模型: {model})",
                "model": "local-fallback",
            }
        
        # 获取部署名称
        deployment_name = self._model_deployments.get(model)
        if not deployment_name:
            raise ValueError(
                f"不支持的模型: {model}。支持的模型: {', '.join(self._supported_models)}"
            )
        
        # 构造请求
        url = (
            f"{self._endpoint}/openai/deployments/{deployment_name}/chat/completions"
            f"?api-version={self._api_version}"
        )
        headers = {"api-key": self._api_key, "Content-Type": "application/json"}
        
        # 注意：不包含 temperature 和 max_tokens（GPT-4o 不支持）
        payload = {"messages": messages}

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]
        return {
            "content": choice["content"],
            "model": data.get("model", model)  # 返回实际使用的模型
        }
