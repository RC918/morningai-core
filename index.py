"""
MorningAI Core API - Modern FastAPI with Database Support
"""
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import psycopg
from psycopg import sql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"Python version: {sys.version}")
print("Starting MorningAI Core API...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("=== MorningAI Core API Starting ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("ASGI application ready!")
    yield
    # Shutdown
    print("=== MorningAI Core API Shutting Down ===")

# 創建FastAPI應用 - 使用現代lifespan
app = FastAPI(
    title="MorningAI Core API",
    description="Modern FastAPI with Database Support",
    version="2.0.0-modern",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """根路徑健康檢查"""
    return {
        "status": "healthy",
        "message": "MorningAI Core API - Modern FastAPI Version!",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-modern",
        "platform": "render",
        "python_version": sys.version,
        "app_type": "ASGI",
        "database_url": "configured" if os.getenv("DATABASE_URL") else "not_configured"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "message": "All systems operational - Modern FastAPI",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": {
            "api": "ok",
            "fastapi": "ok",
            "uvicorn": "ok",
            "asgi": "ok",
            "database": "configured" if os.getenv("DATABASE_URL") else "not_configured"
        }
    }

@app.get("/test")
async def test_endpoint():
    """測試端點"""
    return {
        "message": "API test successful - Python 3.13 compatible",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok",
        "test_data": {
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3],
            "object": {"key": "value"}
        },
        "python_info": {
            "version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }
    }

@app.get("/info")
async def app_info():
    """應用信息端點"""
    return {
        "app_name": "MorningAI Core API",
        "version": "1.0.0-fixed",
        "description": "Python 3.13兼容版本",
        "platform": "render",
        "python_version": sys.version,
        "fastapi_features": [
            "async_endpoints",
            "json_responses",
            "automatic_docs",
            "asgi_compatible"
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "app_type": "ASGI Application"
    }

def get_database_connection():
    """Get database connection with robust error handling and DNS resolution fix"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    
    try:
        # Parse and fix the DATABASE_URL for better compatibility
        from urllib.parse import urlparse, urlunparse, parse_qs
        
        parsed = urlparse(database_url)
        logger.info(f"Attempting database connection to {parsed.hostname}:{parsed.port}")
        
        # Ensure we have a clean connection string
        # Fix common issues with Render DATABASE_URL
        if parsed.scheme == 'postgres':
            # Convert postgres:// to postgresql:// for better psycopg3 compatibility
            parsed = parsed._replace(scheme='postgresql')
        
        # Ensure SSL is properly configured
        query_params = parse_qs(parsed.query)
        if 'sslmode' not in query_params:
            if parsed.query:
                new_query = parsed.query + '&sslmode=require'
            else:
                new_query = 'sslmode=require'
            parsed = parsed._replace(query=new_query)
        
        # Reconstruct the URL
        fixed_url = urlunparse(parsed)
        
        # Try connection with additional connection parameters for better reliability
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'dbname': parsed.path[1:] if parsed.path else 'postgres',
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require',
            'connect_timeout': 10,
            'application_name': 'morningai-core'
        }
        
        logger.info(f"Connecting with params: host={conn_params['host']}, port={conn_params['port']}, db={conn_params['dbname']}")
        
        # Try direct parameter connection first (more reliable than URL parsing)
        conn = psycopg.connect(**conn_params)
        logger.info("Database connection successful via parameters")
        return conn
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Database URL format: {database_url[:50]}...")
        
        # Try fallback connection with original URL
        try:
            logger.info("Trying fallback connection with original URL...")
            conn = psycopg.connect(database_url)
            logger.info("Fallback connection successful")
            return conn
        except Exception as fallback_e:
            logger.error(f"Fallback connection also failed: {fallback_e}")
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/healthz")
async def comprehensive_health_check():
    """Comprehensive health check including database connectivity"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "api": {"status": "healthy", "message": "API is responding"},
            "database": {"status": "unknown", "message": "Not tested"}
        }
    }
    
    # Test database connection
    try:
        conn = get_database_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                health_status["checks"]["database"] = {
                    "status": "healthy", 
                    "message": "Database connection successful"
                }
            else:
                health_status["checks"]["database"] = {
                    "status": "unhealthy", 
                    "message": "Database query failed"
                }
        conn.close()
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy", 
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/db-info")
async def database_info():
    """Database connection information"""
    try:
        conn = get_database_connection()
        with conn.cursor() as cursor:
            # Get database version
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]
            
        conn.close()
        
        return {
            "status": "connected",
            "database_version": db_version,
            "database_size": db_size,
            "tables_count": len(tables),
            "tables": tables,
            "timestamp": datetime.utcnow().isoformat(),
            "migration_status": "completed" if "tenants" in tables else "pending"
        }
        
    except Exception as e:
        logger.error(f"Database info error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/migrate")
async def run_migration():
    """Run database migration and seed"""
    try:
        conn = get_database_connection()
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Check if migration has already been run
            try:
                cursor.execute("SELECT COUNT(*) FROM tenants")
                count = cursor.fetchone()[0]
                if count > 0:
                    return {
                        "status": "skipped",
                        "message": "Database already contains data. Migration skipped.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
            except psycopg.Error:
                logger.info("Tables don't exist yet. Proceeding with migration.")
            
            # Read and execute migration script
            migration_file = '/opt/render/project/src/handoff/phase3/09-seed-and-migration/migration.sql'
            if not os.path.exists(migration_file):
                raise HTTPException(status_code=404, detail="Migration file not found")
            
            with open(migration_file, 'r', encoding='utf-8') as file:
                migration_sql = file.read()
            
            # Execute migration
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            # Read and execute seed script
            seed_file = '/opt/render/project/src/handoff/phase3/09-seed-and-migration/seed.sql'
            if os.path.exists(seed_file):
                with open(seed_file, 'r', encoding='utf-8') as file:
                    seed_sql = file.read()
                
                statements = [stmt.strip() for stmt in seed_sql.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
            
            # Verify migration success
            cursor.execute("SELECT COUNT(*) FROM tenants")
            tenant_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM roles")
            role_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "success",
            "message": "Database migration and seed completed successfully",
            "results": {
                "tenants_created": tenant_count,
                "users_created": user_count,
                "roles_created": role_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@app.get("/db-test")
async def test_database():
    """Test database connection and basic queries"""
    try:
        conn = get_database_connection()
        with conn.cursor() as cursor:
            # Test basic query
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()[0]
            
            # Test current timestamp
            cursor.execute("SELECT NOW()")
            timestamp = cursor.fetchone()[0]
            
        conn.close()
        
        return {
            "status": "success",
            "test_query_result": result,
            "database_timestamp": timestamp.isoformat(),
            "connection": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database test error: {e}")
        raise HTTPException(status_code=500, detail=f"Database test failed: {str(e)}")

# 確保這是一個ASGI應用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

