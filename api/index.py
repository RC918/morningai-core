"""
簡化的 Vercel API 入口點
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="MorningAI Core API - Vercel")

@app.get("/")
def read_root():
    return {
        "message": "MorningAI Core API - Vercel Deployment",
        "status": "healthy",
        "version": "1.0.0",
        "environment": "staging"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "morningai-core-api",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
def api_health():
    return {
        "api_status": "operational",
        "database": "configured" if os.getenv("DATABASE_URL") else "not_configured",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
    }

@app.get("/test/env")
def test_env():
    """測試環境變數"""
    return {
        "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(os.getenv("SUPABASE_ANON_KEY")),
        "SUPABASE_SERVICE_ROLE_KEY": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    }

# Vercel ASGI 處理器
from mangum import Mangum

handler = Mangum(app)

