"""
MorningAI Core API - 包含完整Auth和Referral API的部署版本
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加backend路徑到sys.path
backend_path = Path(__file__).parent / "backend" / "morningai-api" / "src"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# 定義允許的主機名
ALLOWED_HOSTS = [
    "api.morningai.me",
    "*.morningai.me", 
    "morningai-core.onrender.com",
    "morningai-core-staging.onrender.com",
    "morning-ai-api.onrender.com",
    "*.onrender.com",
    "localhost",
    "127.0.0.1",
    "::1"
]

# 創建 FastAPI 應用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端 API - 包含完整Auth和Referral功能",
    version="1.0.0"
)

# 添加中間件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.morningai.me", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 基本健康檢查端點
@app.get("/")
async def read_root():
    """根路徑"""
    return {
        "message": "MorningAI Core API - 完整版本",
        "status": "healthy",
        "version": "1.0.0",
        "environment": "staging",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": "render",
        "features": ["auth", "referral", "health_checks"]
    }

@app.get("/health")
async def health_check():
    """輕量版健康檢查端點"""
    return {"ok": True, "status": "healthy", "service": "morningai-core-api"}

@app.get("/version.json")
async def version_info():
    """版本信息端點"""
    return {
        "service": "morningai-core-api",
        "version": "1.0.0",
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
        "build_id": os.getenv("RENDER_SERVICE_ID", "srv-d2tgr0p5pdvs739ig030"),
        "build_time": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "staging"),
        "platform": "render",
        "python_version": "3.11.9"
    }

@app.get("/healthz")
async def healthz():
    """全量健康檢查"""
    health_status = {
        "status": "ok",
        "env": "render",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # 檢查環境變數
    database_url = os.getenv("DATABASE_URL")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    health_status["checks"]["env_vars"] = {
        "database": "configured" if database_url else "missing",
        "openai": "configured" if openai_key else "missing"
    }
    
    # 簡化的檢查
    if database_url and database_url.startswith("postgresql://"):
        health_status["checks"]["database"] = {"status": "configured", "format": "valid"}
    else:
        health_status["checks"]["database"] = {"status": "not_configured"}
    
    if openai_key:
        health_status["checks"]["openai"] = {"status": "configured"}
    else:
        health_status["checks"]["openai"] = {"status": "not_configured"}
    
    return health_status

# 嘗試導入和註冊API路由
try:
    # 導入API路由
    from api.v1.auth import router as auth_router
    from api.v1.referral import router as referral_router
    
    # 註冊路由
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(referral_router, prefix="/api/v1")
    
    print("[STARTUP] Auth and Referral routes registered successfully")
    
except ImportError as e:
    print(f"[WARNING] Failed to import API routes: {e}")
    print("[INFO] Running in basic mode without Auth/Referral endpoints")
    
    # 添加佔位端點來說明問題
    @app.get("/api/v1/auth/status")
    async def auth_status():
        return {
            "status": "unavailable",
            "reason": "Auth module import failed",
            "message": "請檢查backend/morningai-api/src目錄結構"
        }
    
    @app.get("/api/v1/referral/status")
    async def referral_status():
        return {
            "status": "unavailable", 
            "reason": "Referral module import failed",
            "message": "請檢查backend/morningai-api/src目錄結構"
        }

except Exception as e:
    print(f"[ERROR] Unexpected error during route registration: {e}")

# 添加診斷端點
@app.get("/api/v1/diagnosis")
async def diagnosis():
    """診斷端點 - 檢查路由註冊狀態"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else []
            })
    
    return {
        "total_routes": len(routes),
        "routes": routes,
        "auth_routes": [r for r in routes if "/auth" in r["path"]],
        "referral_routes": [r for r in routes if "/referral" in r["path"]],
        "backend_path_exists": backend_path.exists(),
        "backend_path": str(backend_path)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=True
    )

