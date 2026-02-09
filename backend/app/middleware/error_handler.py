# backend/app/middleware/error_handler.py
"""全局错误处理中间件"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.utils.exceptions import BaseAppException, ErrorCode

logger = logging.getLogger(__name__)

async def error_handler_middleware(request: Request, call_next):
    """全局错误处理"""
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await handle_exception(request, exc)

async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """统一异常处理"""
    
    # 自定义应用异常
    if isinstance(exc, BaseAppException):
        logger.warning(
            f"Application error: {exc.error_code.name} - {exc.message}",
            extra={
                "path": request.url.path,
                "details": exc.details,
            }
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=exc.to_dict()
        )
    
    # FastAPI 验证错误
    if isinstance(exc, RequestValidationError):
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"path": request.url.path}
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "请求数据验证失败",
                "code": ErrorCode.VALIDATION_ERROR.value,
                "details": {"errors": exc.errors()}
            }
        )
    
    # 数据库错误
    if isinstance(exc, SQLAlchemyError):
        logger.error(
            f"Database error: {str(exc)}",
            extra={"path": request.url.path},
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "DATABASE_ERROR",
                "message": "数据库操作失败",
                "code": ErrorCode.DB_TRANSACTION_ERROR.value,
            }
        )
    
    # 未知错误
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "code": ErrorCode.INTERNAL_ERROR.value,
        }
    )