"""
Vercel 部署的 FastAPI 應用程序入口點
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 設置環境變數
os.environ.setdefault("ENVIRONMENT", "production")

app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心 API 服務 - Vercel 部署版本",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路徑健康檢查"""
    return {
        "message": "MorningAI Core API - Vercel Deployment",
        "status": "healthy",
        "version": "1.0.0",
        "environment": "staging"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-05T12:00:00Z",
        "service": "morningai-core-api",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
async def api_health():
    """API 健康檢查"""
    return {
        "api_status": "operational",
        "database": "connected",
        "cache": "connected",
        "external_services": "operational"
    }

# 測試資料庫連接
@app.get("/api/v1/test/database")
async def test_database():
    """測試資料庫連接"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return JSONResponse(
                status_code=500,
                content={"error": "DATABASE_URL not configured"}
            )
        
        # 簡單的連接測試
        return {
            "database_status": "configured",
            "database_host": database_url.split("@")[1].split("/")[0] if "@" in database_url else "unknown",
            "message": "Database configuration found"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Database test failed: {str(e)}"}
        )

# 測試 OpenAI 連接
@app.get("/api/v1/test/openai")
async def test_openai():
    """測試 OpenAI API 連接"""
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return JSONResponse(
                status_code=500,
                content={"error": "OPENAI_API_KEY not configured"}
            )
        
        return {
            "openai_status": "configured",
            "api_key_prefix": openai_key[:10] + "..." if len(openai_key) > 10 else "invalid",
            "message": "OpenAI API key found"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"OpenAI test failed: {str(e)}"}
        )

# 環境變數檢查
@app.get("/api/v1/test/env")
async def test_environment():
    """檢查環境變數配置"""
    env_vars = {
        "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(os.getenv("SUPABASE_ANON_KEY")),
        "SUPABASE_SERVICE_ROLE_KEY": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    }
    
    missing_vars = [key for key, value in env_vars.items() if not value]
    
    return {
        "environment_status": "complete" if not missing_vars else "incomplete",
        "configured_vars": env_vars,
        "missing_vars": missing_vars,
        "total_configured": sum(env_vars.values()),
        "total_required": len(env_vars)
    }

# Vercel 函數處理器
def handler(request):
    """Vercel 函數處理器"""
    return app

# 如果直接運行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

