"""
MorningAI Core API - Vercel 部署入口點
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from datetime import datetime

# 創建 FastAPI 應用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端 API - Vercel 部署版本",
    version="1.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """根路徑健康檢查"""
    return {
        "message": "MorningAI Core API - Vercel Deployment",
        "status": "healthy",
        "version": "1.0.0",
        "environment": "staging",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": "vercel"
    }

@app.get("/health")
async def health_check():
    """基本健康檢查"""
    return {
        "status": "healthy",
        "service": "morningai-core-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version
    }

@app.get("/api/v1/health")
async def api_health():
    """詳細API健康檢查"""
    env_status = {
        "database": "configured" if os.getenv("DATABASE_URL") else "not_configured",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
        "supabase": "configured" if os.getenv("SUPABASE_URL") else "not_configured"
    }
    
    return {
        "api_status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment_variables": env_status,
        "services": {
            "database": env_status["database"],
            "ai_service": env_status["openai"],
            "vector_db": env_status["supabase"]
        }
    }

@app.get("/test/env")
async def test_env():
    """測試環境變數配置"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment_check": {
            "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
            "SUPABASE_ANON_KEY": bool(os.getenv("SUPABASE_ANON_KEY")),
            "SUPABASE_SERVICE_ROLE_KEY": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        },
        "platform_info": {
            "python_version": sys.version,
            "platform": "vercel",
            "working_directory": os.getcwd()
        }
    }

@app.get("/api/v1/status")
async def api_status():
    """API狀態端點"""
    return {
        "api_version": "v1",
        "status": "operational",
        "endpoints": [
            "/",
            "/health", 
            "/api/v1/health",
            "/api/v1/status",
            "/test/env"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

# Vercel 處理器 - 這是 Vercel 需要的入口點
def handler(request):
    """Vercel serverless 函數處理器"""
    return app

