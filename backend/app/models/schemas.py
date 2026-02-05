from pydantic import BaseModel
from typing import Any, Optional

# -----------------------------
# Chat 请求
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


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
