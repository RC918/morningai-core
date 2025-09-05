"""
MorningAI Core API - FastAPI 主應用程序
"""
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 導入配置和數據庫
from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.redis import init_redis, close_redis

# 導入路由
from src.api.v1.auth import router as auth_router
from src.api.v1.users import router as users_router
from src.api.v1.chat import router as chat_router
from src.api.v1.cms import router as cms_router
from src.api.v1.referral import router as referral_router
from src.api.v1.notifications import router as notifications_router

# 導入中間件
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.logging import LoggingMiddleware
from src.middleware.error_handler import ErrorHandlerMiddleware

# 導入監控
from src.core.monitoring import setup_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """應用程序生命週期管理"""
    # 啟動時初始化
    await init_db()
    await init_redis()
    setup_monitoring(app)
    
    yield
    
    # 關閉時清理
    await close_db()
    await close_redis()


# 創建 FastAPI 應用程序
app = FastAPI(
    title="MorningAI Core API",
    description="Phase 3 核心模組 API",
    version="1.0.0",
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    lifespan=lifespan
)

# 添加中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 自定義中間件
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# 註冊 API 路由
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["認證"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["用戶管理"]
)

app.include_router(
    chat_router,
    prefix="/api/v1/chat",
    tags=["聊天系統"]
)

app.include_router(
    cms_router,
    prefix="/api/v1/cms",
    tags=["內容管理"]
)

app.include_router(
    referral_router,
    prefix="/api/v1/referral",
    tags=["推薦系統"]
)

app.include_router(
    notifications_router,
    prefix="/api/v1/notifications",
    tags=["通知系統"]
)

# 健康檢查端點
@app.get("/health", tags=["健康檢查"])
async def health_check():
    """基本健康檢查"""
    return {"status": "healthy", "service": "morningai-core"}


@app.get("/health/ready", tags=["健康檢查"])
async def readiness_check():
    """就緒檢查 - 檢查依賴服務"""
    from src.core.database import check_db_connection
    from src.core.redis import check_redis_connection
    
    checks = {
        "database": await check_db_connection(),
        "redis": await check_redis_connection(),
    }
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        content={
            "status": "ready" if all_ready else "not_ready",
            "checks": checks
        },
        status_code=status_code
    )


@app.get("/health/live", tags=["健康檢查"])
async def liveness_check():
    """存活檢查"""
    return {"status": "alive", "service": "morningai-core"}


# 指標端點
@app.get("/metrics", tags=["監控"])
async def metrics():
    """Prometheus 指標端點"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# 靜態文件服務 (用於前端)
if os.path.exists("src/static"):
    app.mount("/static", StaticFiles(directory="src/static"), name="static")


# 全局異常處理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局異常處理器"""
    import traceback
    import structlog
    
    logger = structlog.get_logger()
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

