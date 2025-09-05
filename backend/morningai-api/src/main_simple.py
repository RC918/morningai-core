"""
MorningAI Core API - 簡化版主應用程序
用於快速測試和開發
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import time

from src.api.v1 import api_router
from src.core.database import engine

# 配置結構化日誌
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# 創建 FastAPI 應用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端 API - 支援用戶認證、推薦系統、聊天功能等",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "認證",
            "description": "用戶認證和授權相關操作",
        },
        {
            "name": "推薦系統",
            "description": "推薦碼管理和推薦關係操作",
        },
        {
            "name": "聊天",
            "description": "聊天功能和 GPT 集成",
        },
        {
            "name": "CMS",
            "description": "內容管理系統",
        },
        {
            "name": "通知",
            "description": "推播通知系統",
        }
    ]
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 請求處理時間中間件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 添加速率限制標頭（如果存在）
    if hasattr(request.state, 'rate_limit_headers'):
        for key, value in request.state.rate_limit_headers.items():
            response.headers[key] = value
    
    return response


# 全局異常處理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """處理請求驗證錯誤"""
    logger.warning("Request validation error", 
                  url=str(request.url), 
                  errors=exc.errors())
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "請求數據驗證失敗",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局異常處理器"""
    logger.error("Unhandled exception", 
                url=str(request.url), 
                error=str(exc),
                exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服務器內部錯誤",
            "error": "請聯繫系統管理員"
        }
    )


# 註冊 API 路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "MorningAI Core API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api": "/api/v1"
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 檢查數據庫連接
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "morningai-core-api",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "morningai-core-api",
                "version": "1.0.0",
                "database": "disconnected",
                "error": str(e)
            }
        )


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    logger.info("MorningAI Core API starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    logger.info("MorningAI Core API shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

