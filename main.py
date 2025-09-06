"""
MorningAI Core API - Render 部署入口點
簡化版本用於快速部署和測試
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

# 創建 FastAPI 應用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端 API - Render 部署版本",
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
    """根路徑"""
    return {
        "message": "MorningAI Core API - Render Deployment",
        "status": "healthy",
        "version": "1.0.0",
        "environment": "staging",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": "render"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "morningai-core-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/healthz")
async def healthz():
    """Kubernetes 風格健康檢查"""
    return {
        "status": "ok",
        "env": "render",
        "rag": "disabled"
    }

@app.get("/api/v1/health")
async def api_health():
    """API 健康檢查"""
    env_status = {
        "database": "configured" if os.getenv("DATABASE_URL") else "not_configured",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
        "supabase": "configured" if os.getenv("SUPABASE_URL") else "not_configured"
    }
    
    return {
        "api_status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment_variables": env_status
    }

@app.get("/version")
async def version():
    """版本信息"""
    return {
        "version": "v1.0.0-render-deployment",
        "commit": "159f8971",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/echo")
async def echo():
    """回聲測試端點"""
    return {
        "message": "Echo successful",
        "timestamp": datetime.utcnow().isoformat(),
        "cors": "enabled"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

