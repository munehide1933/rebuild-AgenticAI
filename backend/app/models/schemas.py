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


# -----------------------------
# Repo 分析 / 补丁生成
# -----------------------------
class AnalyzeRequest(BaseModel):
    repo_path: Optional[str] = None
    github_url: Optional[str] = None
    focus: Optional[str] = None


class AnalyzeResponse(BaseModel):
    repo_summary: dict[str, Any]
    repo_path: str
    source: str


class GeneratePatchRequest(BaseModel):
    repo_path: Optional[str] = None
    github_url: Optional[str] = None
    feature_request: str
    conversation_id: Optional[str] = None


class GeneratePatchResponse(BaseModel):
    conversation_id: str
    patch: str
    intent: dict[str, Any]
    architecture: str
    repo_summary: dict[str, Any]
