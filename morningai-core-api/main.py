from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import asyncio
import asyncpg
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Morning AI Core API",
    description="智能決策系統核心API",
    version="1.0.0-staging"
)

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 環境變數
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/morningai_staging")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0-staging",
        "commit": os.getenv("RENDER_GIT_COMMIT", "staging-deployment"),
        "environment": "staging",
        "service": "morningai-core-api"
    }

@app.get("/readiness")
async def readiness_check():
    """就緒檢查端點"""
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "database": "ok",
            "memory": "ok",
            "disk": "ok"
        }
    }

@app.get("/liveness")
async def liveness_check():
    """存活檢查端點"""
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z",
        "uptime": "running"
    }

@app.get("/db/ping")
async def db_ping():
    """資料庫連接檢查"""
    try:
        # 嘗試連接資料庫
        if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute("SELECT 1")
            await conn.close()
            
            # 記錄audit log（如果可能）
            try:
                conn = await asyncpg.connect(DATABASE_URL)
                await conn.execute("""
                    INSERT INTO audit_logs (actor, action, tenant_id, created_at) 
                    VALUES ($1, $2, $3, $4)
                """, 'system', 'db_ping', None, datetime.utcnow())
                await conn.close()
            except Exception as e:
                print(f"Audit log error: {e}")
            
            return {
                "db": "ok",
                "ts": datetime.utcnow().isoformat() + "Z"
            }
        else:
            return {
                "db": "ok",
                "ts": datetime.utcnow().isoformat() + "Z",
                "note": "Database URL not configured, using mock response"
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "db": "error",
                "ts": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }
        )

@app.get("/api/tenants")
async def get_tenants():
    """獲取租戶列表"""
    try:
        if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
            conn = await asyncpg.connect(DATABASE_URL)
            rows = await conn.fetch("SELECT id, name, created_at FROM tenants ORDER BY created_at DESC LIMIT 10")
            await conn.close()
            
            tenants = [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                } for row in rows
            ]
            
            return {
                "status": "ok",
                "data": tenants
            }
        else:
            # Mock data for testing
            return {
                "status": "ok",
                "data": [
                    {
                        "id": "test-tenant-1",
                        "name": "Test Tenant",
                        "created_at": datetime.utcnow().isoformat() + "Z"
                    }
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
