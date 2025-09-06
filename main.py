"""
MorningAI Core API - Render 部署入口點
簡化版本用於快速部署和測試
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from datetime import datetime

# 定義允許的主機名
ALLOWED_HOSTS = [
    "api.morningai.me",
    "admin.morningai.me", 
    "morning-ai-api.onrender.com",
    "localhost",
    "127.0.0.1",
    "*.morningai.me",  # 萬用字元支持子域名
    "*"  # 臨時允許所有主機用於測試
]

# 創建 FastAPI 應用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端 API - Render 部署版本",
    version="1.0.0"
)

# 添加 TrustedHost 中間件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.morningai.me", "http://localhost:3000", "*"],
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
def api_health():
    """API 健康檢查 - 環境變數檢查和 OpenAI 連接測試（無資料庫連接）"""
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
    
    # 資料庫連接測試（簡化版 - 僅 URL 格式驗證）
    if database_url:
        if database_url.startswith("postgresql://"):
            health_status["connection_tests"]["database"] = {
                "status": "configured",
                "test": "url_format_valid",
                "note": "actual_connection_test_disabled_due_to_python313_compatibility"
            }
        else:
            health_status["connection_tests"]["database"] = {
                "status": "misconfigured",
                "error": "invalid_postgresql_url_format"
            }
    else:
        health_status["connection_tests"]["database"] = {
            "status": "not_configured"
        }
    
    # 測試 OpenAI API 連接
    if openai_key:
        try:
            # 使用更簡單的客戶端初始化
            client = openai.OpenAI(
                api_key=openai_key,
                timeout=10.0  # 添加超時設置
            )
            # 使用更簡單的測試請求
            response = client.models.list()
            model_count = len(response.data) if hasattr(response, 'data') and response.data else 0
            health_status["connection_tests"]["openai"] = {
                "status": "connected",
                "available_models": model_count,
                "test": "models.list()",
                "client_version": openai.__version__
            }
        except openai.AuthenticationError as e:
            health_status["connection_tests"]["openai"] = {
                "status": "failed",
                "error": f"Authentication failed: {str(e)}",
                "error_type": "authentication"
            }
        except openai.APIError as e:
            health_status["connection_tests"]["openai"] = {
                "status": "failed", 
                "error": f"API error: {str(e)}",
                "error_type": "api_error"
            }
        except Exception as e:
            health_status["connection_tests"]["openai"] = {
                "status": "failed",
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unknown"
            }
    else:
        health_status["connection_tests"]["openai"] = {
            "status": "not_configured"
        }
    
    # 設定整體健康狀態
    db_configured = health_status["connection_tests"].get("database", {}).get("status") in ["configured", "connected"]
    openai_healthy = health_status["connection_tests"].get("openai", {}).get("status") == "connected"
    
    if db_configured and openai_healthy:
        health_status["api_status"] = "healthy"
    elif db_configured or openai_healthy:
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
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )


