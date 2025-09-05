"""
MorningAI Core API - Vercel 部署入口點
"""
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

# 創建FastAPI應用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端服務",
    version="1.0.0"
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 響應模型
class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    environment: str
    version: str

class StatusResponse(BaseModel):
    service: str
    status: str
    uptime: str
    environment: Dict[str, Any]

@app.get("/", response_model=HealthResponse)
async def root():
    """根路徑健康檢查"""
    return HealthResponse(
        status="healthy",
        message="MorningAI Core API is running successfully on Vercel!",
        timestamp=datetime.utcnow().isoformat(),
        environment="staging",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    return HealthResponse(
        status="healthy",
        message="All systems operational",
        timestamp=datetime.utcnow().isoformat(),
        environment="staging",
        version="1.0.0"
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """系統狀態端點"""
    return StatusResponse(
        service="morningai-core",
        status="running",
        uptime="active",
        environment={
            "platform": "vercel",
            "python_version": "3.9",
            "deployment_time": datetime.utcnow().isoformat(),
            "environment_variables": {
                "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
                "has_supabase_url": bool(os.getenv("SUPABASE_URL")),
                "has_supabase_key": bool(os.getenv("SUPABASE_ANON_KEY"))
            }
        }
    )

@app.get("/api/v1/test")
async def test_endpoint():
    """測試API端點"""
    return {
        "message": "API test successful",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok"
    }

# Vercel 處理器
def handler(request):
    """Vercel serverless 函數處理器"""
    return app

# 確保兼容性
__all__ = ['app', 'handler']

