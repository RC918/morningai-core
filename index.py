"""
MorningAI Core API - Modern FastAPI with Database Support
"""
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI

print(f"Python version: {sys.version}")
print("Starting MorningAI Core API...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("=== MorningAI Core API Starting ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("ASGI application ready!")
    yield
    # Shutdown
    print("=== MorningAI Core API Shutting Down ===")

# 創建FastAPI應用 - 使用現代lifespan
app = FastAPI(
    title="MorningAI Core API",
    description="Modern FastAPI with Database Support",
    version="2.0.0-modern",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """根路徑健康檢查"""
    return {
        "status": "healthy",
        "message": "MorningAI Core API - Modern FastAPI Version!",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-modern",
        "platform": "render",
        "python_version": sys.version,
        "app_type": "ASGI",
        "database_url": "configured" if os.getenv("DATABASE_URL") else "not_configured"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "message": "All systems operational - Modern FastAPI",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": {
            "api": "ok",
            "fastapi": "ok",
            "uvicorn": "ok",
            "asgi": "ok",
            "database": "configured" if os.getenv("DATABASE_URL") else "not_configured"
        }
    }

@app.get("/test")
async def test_endpoint():
    """測試端點"""
    return {
        "message": "API test successful - Python 3.13 compatible",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok",
        "test_data": {
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3],
            "object": {"key": "value"}
        },
        "python_info": {
            "version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }
    }

@app.get("/info")
async def app_info():
    """應用信息端點"""
    return {
        "app_name": "MorningAI Core API",
        "version": "1.0.0-fixed",
        "description": "Python 3.13兼容版本",
        "platform": "render",
        "python_version": sys.version,
        "fastapi_features": [
            "async_endpoints",
            "json_responses",
            "automatic_docs",
            "asgi_compatible"
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "app_type": "ASGI Application"
    }

# 確保這是一個ASGI應用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

