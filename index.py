"""
MorningAI Core API - 修復啟動期副作用的純FastAPI ASGI應用
"""
import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

# 創建FastAPI應用 - 無啟動期副作用
app = FastAPI(
    title="MorningAI Core API",
    description="MorningAI 核心後端服務 - 修復版本",
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

def get_database_url() -> Optional[str]:
    """獲取數據庫URL並添加SSL模式"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # 確保使用SSL連接
        if "sslmode=" not in database_url:
            separator = "&" if "?" in database_url else "?"
            database_url += f"{separator}sslmode=require"
        # 替換postgres://為postgresql://
        database_url = database_url.replace("postgres://", "postgresql://")
    return database_url

def get_db_connection():
    """請求依賴：獲取數據庫連接（延後初始化）"""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
async def root():
    """根路徑健康檢查 - 無數據庫依賴"""
    return {
        "status": "healthy",
        "message": "MorningAI Core API is running successfully!",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "staging",
        "version": "1.0.0",
        "platform": "render",
        "database_configured": bool(get_database_url())
    }

@app.get("/health")
async def health_check():
    """健康檢查端點 - 包含數據庫連接測試"""
    database_url = get_database_url()
    db_status = "not_configured"
    
    if database_url:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "message": "All systems operational",
        "timestamp": datetime.utcnow().isoformat(),
        "database_status": db_status,
        "ssl_mode": "require" if database_url and "sslmode=require" in database_url else "not_set"
    }

@app.get("/test")
async def test_endpoint():
    """測試端點 - 無副作用"""
    return {
        "message": "API test successful",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok"
    }

@app.post("/migrate")
async def run_migration():
    """執行數據庫遷移 - 請求時連接"""
    # 簡化的遷移腳本用於測試
    migration_sql = """
    -- 簡化的遷移腳本用於測試
    CREATE TABLE IF NOT EXISTS migration_test (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        message TEXT DEFAULT 'Migration test successful'
    );
    
    INSERT INTO migration_test (message) VALUES ('Migration executed at ' || CURRENT_TIMESTAMP);
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 執行遷移腳本
        cursor.execute(migration_sql)
        conn.commit()
        
        # 檢查結果
        cursor.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'")
        result = cursor.fetchone()
        table_count = result['table_count']
        
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": "Database migration completed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "tables_created": table_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@app.get("/db-info")
async def get_db_info():
    """獲取數據庫信息 - 請求時連接"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取數據庫版本
        cursor.execute("SELECT version()")
        version_result = cursor.fetchone()
        version = version_result['version']
        
        # 獲取表數量
        cursor.execute("SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = 'public'")
        tables_result = cursor.fetchone()
        table_count = tables_result['count']
        
        # 檢查pgvector擴展
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        pgvector_result = cursor.fetchall()
        pgvector_installed = len(pgvector_result) > 0
        
        cursor.close()
        conn.close()
        
        return {
            "database_version": version,
            "public_tables_count": table_count,
            "pgvector_installed": pgvector_installed,
            "timestamp": datetime.utcnow().isoformat(),
            "ssl_enabled": "sslmode=require" in get_database_url()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

# 應用啟動事件（可選的清理方式）
@app.on_event("startup")
async def startup_event():
    """應用啟動事件 - 無副作用記錄"""
    print("MorningAI Core API starting up...")
    print(f"Database configured: {bool(get_database_url())}")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    print("MorningAI Core API shutting down...")

# 確保只有一個ASGI應用，無WSGI後備

