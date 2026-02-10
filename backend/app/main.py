from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.models.database import init_db
from app.api import analysis, chat
from app.utils.startup_check import check_environment
from app.middleware.error_handler import error_handler_middleware
import logging
import sys

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动前检查
    logger.info("Running startup checks...")
    if not check_environment():
        logger.error("Startup checks failed. Please fix the errors above.")
        sys.exit(1)
    
    # 初始化数据库
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # 关闭时清理
    logger.info("Application shutdown")

app = FastAPI(
    title="Meta-Agent",
    description="通用智能体：深度思考、自我反思、互联网搜索；可扩展工具框架",
    version="1.0.0",
    lifespan=lifespan
)

# 添加错误处理中间件
app.add_middleware(BaseHTTPMiddleware, dispatch=error_handler_middleware)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(analysis.router)

@app.get("/")
async def root():
    return {
        "message": "Meta-Agent API (通用智能体)",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    from app.services.llm_service import LLMService
    
    llm_service = LLMService()
    stats = llm_service.get_stats()
    
    return {
        "status": "healthy",
        "llm_configured": llm_service._configured,
        "llm_stats": stats,
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
