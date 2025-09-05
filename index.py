"""
MorningAI Core API - 最簡化版本用於問題隔離
"""
from datetime import datetime
from fastapi import FastAPI

# 創建最簡化的FastAPI應用
app = FastAPI(
    title="MorningAI Core API - Minimal",
    description="最簡化版本用於問題診斷",
    version="1.0.0-minimal"
)

@app.get("/")
async def root():
    """根路徑 - 最簡化健康檢查"""
    return {
        "status": "healthy",
        "message": "MorningAI Core API - Minimal Version Running Successfully!",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-minimal",
        "platform": "render"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點 - 無外部依賴"""
    return {
        "status": "healthy",
        "message": "All systems operational - minimal version",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "api": "ok",
            "fastapi": "ok",
            "uvicorn": "ok"
        }
    }

@app.get("/test")
async def test_endpoint():
    """測試端點 - 最簡化"""
    return {
        "message": "API test successful - minimal version",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok",
        "test_data": {
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3],
            "object": {"key": "value"}
        }
    }

@app.get("/info")
async def app_info():
    """應用信息端點"""
    return {
        "app_name": "MorningAI Core API",
        "version": "1.0.0-minimal",
        "description": "最簡化版本用於問題診斷",
        "platform": "render",
        "python_version": "3.13",
        "fastapi_features": [
            "async_endpoints",
            "json_responses",
            "cors_support",
            "automatic_docs"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

# 應用啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動事件 - 最簡化"""
    print("MorningAI Core API (Minimal) starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    print("MorningAI Core API (Minimal) shutting down...")

