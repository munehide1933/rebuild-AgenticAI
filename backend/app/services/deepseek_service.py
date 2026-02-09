from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings
from app.utils.exceptions import LLMError

logger = logging.getLogger(__name__)


class DeepSeekService:
    """DeepSeek-R1 客户端（OpenAI 兼容接口）。"""

    def __init__(self) -> None:
        self._endpoint = settings.DEEPSEEK_API_BASE.rstrip("/")
        self._api_key = settings.DEEPSEEK_API_KEY
        self._model = settings.DEEPSEEK_MODEL
        self._configured = bool(self._endpoint and self._api_key and self._model)

    async def generate_patch(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if not self._configured:
            return {
                "content": "DeepSeek 未配置，无法生成真实补丁。",
                "model": "local-fallback",
            }

        url = f"{self._endpoint}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            choice = data["choices"][0]["message"]
            return {
                "content": choice.get("content", ""),
                "model": data.get("model", self._model),
                "usage": data.get("usage", {}),
            }
        except httpx.HTTPError as exc:
            logger.error("DeepSeek request failed: %s", exc)
            raise LLMError(
                "DeepSeek 请求失败",
                details={"endpoint": self._endpoint, "model": self._model},
                original_error=exc,
            )
