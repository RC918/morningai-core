"""
MorningAI Core API - 修復Python 3.13兼容性問題
"""
import sys
from datetime import datetime
from fastapi import FastAPI

print(f"Python version: {sys.version}")
print("Starting MorningAI Core API...")

# 創建FastAPI應用 - 明確ASGI配置
app = FastAPI(
    title="MorningAI Core API",
    description="修復Python 3.13兼容性的版本",
    version="1.0.0-fixed",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def root():
    """根路徑健康檢查"""
    return {
        "status": "healthy",
        "message": "MorningAI Core API - Python 3.13 Compatible Version!",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-fixed",
        "platform": "render",
        "python_version": sys.version,
        "app_type": "ASGI"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "message": "All systems operational - Python 3.13 compatible",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": {
            "api": "ok",
            "fastapi": "ok",
            "uvicorn": "ok",
            "asgi": "ok"
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

# 應用事件處理
@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    print("=== MorningAI Core API Starting ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("ASGI application ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    print("=== MorningAI Core API Shutting Down ===")

# 確保這是一個ASGI應用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

