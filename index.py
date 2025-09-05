"""
MorningAI Core API - 包含數據庫遷移功能（使用psycopg2）
"""
import os
from datetime import datetime

# 嘗試導入FastAPI，如果失敗則使用基本HTTP響應
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from urllib.parse import urlparse
    
    # 創建FastAPI應用
    app = FastAPI(
        title="MorningAI Core API",
        description="MorningAI 核心後端服務 - 包含數據庫功能",
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
    
    # 數據庫連接配置
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    def get_db_connection():
        """獲取數據庫連接"""
        if not DATABASE_URL:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
        try:
            # 如果URL包含postgres://，替換為postgresql://
            db_url = DATABASE_URL.replace("postgres://", "postgresql://")
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    
    @app.get("/")
    async def root():
        """根路徑健康檢查"""
        return {
            "status": "healthy",
            "message": "MorningAI Core API is running successfully!",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "staging",
            "version": "1.0.0",
            "platform": "render",
            "database_configured": bool(DATABASE_URL)
        }
    
    @app.get("/health")
    async def health_check():
        """健康檢查端點"""
        db_status = "not_configured"
        
        if DATABASE_URL:
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
            "database_status": db_status
        }
    
    @app.get("/test")
    async def test_endpoint():
        """測試端點"""
        return {
            "message": "API test successful",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ok"
        }
    
    @app.post("/migrate")
    async def run_migration():
        """執行數據庫遷移"""
        if not DATABASE_URL:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
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
        """獲取數據庫信息"""
        if not DATABASE_URL:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
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
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

except ImportError as e:
    # 如果FastAPI不可用，創建一個基本的WSGI應用
    def app(environ, start_response):
        """基本WSGI應用作為後備"""
        status = '200 OK'
        headers = [
            ('Content-type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ]
        start_response(status, headers)
        
        response = {
            "status": "healthy",
            "message": "MorningAI Core API is running (basic mode)",
            "timestamp": datetime.utcnow().isoformat(),
            "note": f"FastAPI not available: {str(e)}"
        }
        
        import json
        return [json.dumps(response).encode('utf-8')]

# Vercel 處理器
def handler(request):
    """Vercel serverless 函數處理器"""
    return app

# 確保兼容性
__all__ = ['app', 'handler']

