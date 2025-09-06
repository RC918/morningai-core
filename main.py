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
    """API 健康檢查 - 包含實際連接測試"""
    import psycopg2
    import openai
    from datetime import datetime
    
    health_status = {
        "api_status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment_variables": {},
        "connection_tests": {}
    }
    
    # 檢查環境變數
    database_url = os.getenv("DATABASE_URL")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    health_status["environment_variables"] = {
        "database": "configured" if database_url else "not_configured",
        "openai": "configured" if openai_key else "not_configured",
        "supabase": "configured" if os.getenv("SUPABASE_URL") else "not_configured"
    }
    
    # 測試資料庫連接
    if database_url:
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            health_status["connection_tests"]["database"] = {
                "status": "connected",
                "test_query": "SELECT 1",
                "result": result
            }
        except Exception as e:
            health_status["connection_tests"]["database"] = {
                "status": "failed",
                "error": str(e)
            }
    else:
        health_status["connection_tests"]["database"] = {
            "status": "not_configured"
        }
    
    # 測試 OpenAI API 連接
    if openai_key:
        try:
            client = openai.OpenAI(api_key=openai_key)
            models = client.models.list()
            model_count = len(models.data) if models.data else 0
            health_status["connection_tests"]["openai"] = {
                "status": "connected",
                "available_models": model_count,
                "test": "models.list()"
            }
        except Exception as e:
            health_status["connection_tests"]["openai"] = {
                "status": "failed",
                "error": str(e)
            }
    else:
        health_status["connection_tests"]["openai"] = {
            "status": "not_configured"
        }
    
    # 設定整體健康狀態
    db_healthy = health_status["connection_tests"].get("database", {}).get("status") == "connected"
    openai_healthy = health_status["connection_tests"].get("openai", {}).get("status") == "connected"
    
    if db_healthy and openai_healthy:
        health_status["api_status"] = "healthy"
    elif db_healthy or openai_healthy:
        health_status["api_status"] = "degraded"
    else:
        health_status["api_status"] = "unhealthy"
    
    return health_status

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

