"""
數據庫連接和會話管理
"""
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import structlog

from src.core.config import settings

logger = structlog.get_logger()

# 數據庫引擎和會話
engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    """SQLAlchemy 基礎模型類"""
    pass


async def init_db() -> None:
    """初始化數據庫連接"""
    global engine, async_session_maker
    
    try:
        # 創建異步引擎
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            pool_timeout=settings.DATABASE_TIMEOUT,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )
        
        # 創建會話工廠
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database connection initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database connection", error=str(e))
        raise


async def close_db() -> None:
    """關閉數據庫連接"""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """獲取數據庫會話"""
    if not async_session_maker:
        raise RuntimeError("Database not initialized")
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """檢查數據庫連接狀態"""
    try:
        if not engine:
            return False
            
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
        
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False


async def create_tables() -> None:
    """創建所有表"""
    if not engine:
        raise RuntimeError("Database engine not initialized")
    
    # 導入所有模型以確保它們被註冊
    from src.models import (
        tenant, user, role, permission, 
        chat, cms, referral, notification, audit
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def drop_tables() -> None:
    """刪除所有表（僅用於測試）"""
    if not engine:
        raise RuntimeError("Database engine not initialized")
    
    if not settings.is_testing:
        raise RuntimeError("Can only drop tables in testing environment")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("Database tables dropped successfully")


class DatabaseManager:
    """數據庫管理器"""
    
    def __init__(self):
        self.engine = engine
        self.session_maker = async_session_maker
    
    async def execute_raw_sql(self, sql: str, params: dict = None) -> any:
        """執行原始 SQL"""
        async with self.session_maker() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result
    
    async def get_table_info(self, table_name: str) -> dict:
        """獲取表信息"""
        sql = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
        """
        
        async with self.session_maker() as session:
            result = await session.execute(text(sql), {"table_name": table_name})
            columns = result.fetchall()
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col.column_name,
                        "type": col.data_type,
                        "nullable": col.is_nullable == "YES",
                        "default": col.column_default
                    }
                    for col in columns
                ]
            }
    
    async def get_database_stats(self) -> dict:
        """獲取數據庫統計信息"""
        stats_sql = """
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_tuples,
            n_dead_tup as dead_tuples
        FROM pg_stat_user_tables
        ORDER BY tablename
        """
        
        async with self.session_maker() as session:
            result = await session.execute(text(stats_sql))
            tables = result.fetchall()
            
            return {
                "tables": [
                    {
                        "schema": table.schemaname,
                        "name": table.tablename,
                        "inserts": table.inserts,
                        "updates": table.updates,
                        "deletes": table.deletes,
                        "live_tuples": table.live_tuples,
                        "dead_tuples": table.dead_tuples
                    }
                    for table in tables
                ]
            }


# 創建全局數據庫管理器實例
db_manager = DatabaseManager()

