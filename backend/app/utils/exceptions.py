# backend/app/utils/exceptions.py
"""统一异常处理"""
from typing import Optional, Any
from enum import Enum

class ErrorCode(Enum):
    """错误代码枚举"""
    # 通用错误 (1xxx)
    INTERNAL_ERROR = 1000
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1004
    
    # LLM 相关错误 (2xxx)
    LLM_API_ERROR = 2001
    LLM_TIMEOUT = 2002
    LLM_RATE_LIMIT = 2003
    LLM_INVALID_RESPONSE = 2004
    
    # 数据库错误 (3xxx)
    DB_CONNECTION_ERROR = 3001
    DB_TRANSACTION_ERROR = 3002
    
    # 业务逻辑错误 (4xxx)
    CONVERSATION_NOT_FOUND = 4001
    INVALID_MESSAGE = 4002

class BaseAppException(Exception):
    """基础应用异常"""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.error_code.name,
            "message": self.message,
            "code": self.error_code.value,
            "details": self.details,
        }

class LLMError(BaseAppException):
    """LLM 相关错误"""
    def __init__(self, message: str, details: Optional[dict] = None, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.LLM_API_ERROR,
            details=details,
            original_error=original_error
        )

class DatabaseError(BaseAppException):
    """数据库相关错误"""
    def __init__(self, message: str, details: Optional[dict] = None, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DB_TRANSACTION_ERROR,
            details=details,
            original_error=original_error
        )

class ValidationError(BaseAppException):
    """验证错误"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": field} if field else {}
        )