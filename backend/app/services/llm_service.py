# backend/app/services/llm_service.py
from __future__ import annotations

import asyncio
from typing import Any, Iterable
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

from app.config import settings
from app.utils.exceptions import LLMError, ErrorCode

logger = logging.getLogger(__name__)

class LLMService:
    """优化后的 LLM 服务"""
    
    def __init__(self) -> None:
        self._endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        self._api_version = settings.AZURE_OPENAI_API_VERSION
        self._api_key = settings.AZURE_OPENAI_API_KEY
        self._configured = bool(self._endpoint and self._api_key)
        
        self._model_deployments = {
            settings.DEFAULT_MODEL: settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            settings.CS_SPECIALIST_MODEL: settings.AZURE_DEEPSEEK_DEPLOYMENT_NAME,
        }
        
        self._supported_models = list(self._model_deployments.keys())
        
        # 添加熔断器状态
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_open = False
        self._circuit_breaker_reset_time = None
        
        # 性能统计
        self._call_count = 0
        self._total_tokens = 0
        self._failed_calls = 0
    
    async def generate_simple(self, prompt: str, model: str | None = None) -> str:
        """生成简单回答"""
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
        """生成对话式回答"""
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
        """推荐模型（保持原有逻辑）"""
        question_lower = question.lower()
        
        cs_keywords = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'code', 'coding', 'programming', 'debug', 'bug', 'error', 'api',
            'database', 'sql', 'algorithm', 'function', 'class', 'react', 'vue',
        }
        
        if any(kw in question_lower for kw in cs_keywords):
            return settings.CS_SPECIALIST_MODEL
        
        return settings.DEFAULT_MODEL
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def _chat(self, messages: list[dict[str, str]], model: str) -> dict[str, Any]:
        """调用 Azure OpenAI Chat API（带重试）"""
        
        # 检查熔断器
        if self._circuit_breaker_open:
            if self._circuit_breaker_reset_time and asyncio.get_event_loop().time() > self._circuit_breaker_reset_time:
                logger.info("Circuit breaker reset, retrying...")
                self._circuit_breaker_open = False
                self._circuit_breaker_failures = 0
            else:
                raise LLMError(
                    "服务暂时不可用，请稍后重试",
                    details={"reason": "circuit_breaker_open"}
                )
        
        # 未配置时返回占位
        if not self._configured:
            return {
                "content": f"LLM 未配置，返回占位回复。\n请求模型: {model}",
                "model": "local-fallback",
            }
        
        # 验证模型
        deployment_name = self._model_deployments.get(model)
        if not deployment_name:
            raise ValidationError(
                f"不支持的模型: {model}",
                field="model"
            )
        
        # 构造请求
        url = (
            f"{self._endpoint}/openai/deployments/{deployment_name}/chat/completions"
            f"?api-version={self._api_version}"
        )
<<<<<<< HEAD
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
=======
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
>>>>>>> 81cede4 (Initial commit)
        }
        payload = {"messages": messages}
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            
            # 更新统计
            self._call_count += 1
            if "usage" in data:
                self._total_tokens += data["usage"].get("total_tokens", 0)
            
            # 重置熔断器失败计数
            if self._circuit_breaker_failures > 0:
                self._circuit_breaker_failures = 0
            
            choice = data["choices"][0]["message"]
            return {
                "content": choice["content"],
                "model": data.get("model", model),
                "usage": data.get("usage", {})
            }
            
        except httpx.TimeoutException as e:
            self._failed_calls += 1
            self._increment_circuit_breaker()
            raise LLMError(
                "LLM 请求超时",
                details={"model": model, "timeout": 120},
                original_error=e
            )
        
        except httpx.HTTPStatusError as e:
            self._failed_calls += 1
            self._increment_circuit_breaker()
            
            if e.response.status_code == 429:
                raise LLMError(
                    "API 速率限制，请稍后重试",
                    details={"status_code": 429, "model": model},
                    original_error=e
                )
            elif e.response.status_code >= 500:
                raise LLMError(
                    "LLM 服务暂时不可用",
                    details={"status_code": e.response.status_code, "model": model},
                    original_error=e
                )
            else:
                raise LLMError(
                    f"LLM API 错误: {e.response.status_code}",
                    details={"status_code": e.response.status_code, "response": e.response.text[:200]},
                    original_error=e
                )
        
        except Exception as e:
            self._failed_calls += 1
            self._increment_circuit_breaker()
            raise LLMError(
                f"LLM 调用失败: {str(e)}",
                details={"model": model},
                original_error=e
            )
    
    def _increment_circuit_breaker(self):
        """增加熔断器失败计数"""
        self._circuit_breaker_failures += 1
        
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            self._circuit_breaker_open = True
            # 30 秒后尝试重置
            self._circuit_breaker_reset_time = asyncio.get_event_loop().time() + 30
            logger.error(
                f"Circuit breaker opened after {self._circuit_breaker_failures} failures. "
                f"Will reset in 30 seconds."
            )
    
    def get_stats(self) -> dict[str, Any]:
        """获取服务统计信息"""
        return {
            "total_calls": self._call_count,
            "failed_calls": self._failed_calls,
            "total_tokens": self._total_tokens,
            "success_rate": (self._call_count - self._failed_calls) / max(self._call_count, 1),
            "circuit_breaker_open": self._circuit_breaker_open,
            "circuit_breaker_failures": self._circuit_breaker_failures,
        }