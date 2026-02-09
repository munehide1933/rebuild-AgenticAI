from datetime import datetime

from pydantic import BaseModel, Field
from typing import Any, Optional

# -----------------------------
# Chat 请求
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    deep_thinking: bool = False
    web_search_enabled: bool = False


# -----------------------------
# Chat 响应（最简结构）
# -----------------------------
class ChatResponse(BaseModel):
    message_id: str
    content: str
    conversation_id: str
    workflow_state: Optional[dict[str, Any]] = None
    code_modifications: Optional[Any] = None
    suggestions: Optional[Any] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    summary: str
    created_at: datetime
    updated_at: datetime


class MessageDTO(BaseModel):
    id: str
    role: str
    content: str
    meta_info: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationDetail(BaseModel):
    id: str
    title: str
    summary: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageDTO]
