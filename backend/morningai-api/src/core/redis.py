"""
Redis 連接和快取管理
"""
import asyncio
from typing import Optional, Any, Union
import redis.asyncio as redis
import json
import structlog
from datetime import timedelta

from src.core.config import settings

logger = structlog.get_logger()

# Redis 連接池
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """初始化 Redis 連接"""
    global redis_pool, redis_client
    
    try:
        # 創建連接池
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # 創建 Redis 客戶端
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # 測試連接
        await redis_client.ping()
        
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize Redis connection", error=str(e))
        raise


async def close_redis() -> None:
    """關閉 Redis 連接"""
    global redis_pool, redis_client
    
    if redis_client:
        await redis_client.close()
    
    if redis_pool:
        await redis_pool.disconnect()
    
    logger.info("Redis connection closed")


async def get_redis() -> redis.Redis:
    """獲取 Redis 客戶端"""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client


async def check_redis_connection() -> bool:
    """檢查 Redis 連接狀態"""
    try:
        if not redis_client:
            return False
        
        await redis_client.ping()
        return True
        
    except Exception as e:
        logger.error("Redis connection check failed", error=str(e))
        return False


class RedisCache:
    """Redis 快取管理器"""
    
    def __init__(self):
        self.client = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Failed to get cache", key=key, error=str(e))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """設置快取值"""
        try:
            serialized_value = json.dumps(value, default=str)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                await self.client.setex(key, expire, serialized_value)
            else:
                await self.client.set(key, serialized_value)
            
            return True
        except Exception as e:
            logger.error("Failed to set cache", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """刪除快取值"""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Failed to delete cache", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在"""
        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.error("Failed to check cache existence", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """設置快取過期時間"""
        try:
            result = await self.client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error("Failed to set cache expiration", key=key, error=str(e))
            return False
    
    async def ttl(self, key: str) -> int:
        """獲取快取剩餘時間"""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error("Failed to get cache TTL", key=key, error=str(e))
            return -1
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """增加計數器"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error("Failed to increment counter", key=key, error=str(e))
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """減少計數器"""
        try:
            return await self.client.decrby(key, amount)
        except Exception as e:
            logger.error("Failed to decrement counter", key=key, error=str(e))
            return None


class RateLimiter:
    """基於 Redis 的速率限制器"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> tuple[bool, dict]:
        """
        檢查是否允許請求
        
        Args:
            key: 限制鍵（通常是用戶ID或IP）
            limit: 限制次數
            window: 時間窗口（秒）
        
        Returns:
            (是否允許, 限制信息)
        """
        try:
            current_count = await self.cache.incr(key)
            
            if current_count == 1:
                # 第一次請求，設置過期時間
                await self.cache.expire(key, window)
                ttl = window
            else:
                # 獲取剩餘時間
                ttl = await self.cache.ttl(key)
            
            allowed = current_count <= limit
            
            rate_limit_info = {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset_time": ttl,
                "current": current_count
            }
            
            return allowed, rate_limit_info
            
        except Exception as e:
            logger.error("Rate limiter error", key=key, error=str(e))
            # 發生錯誤時允許請求，避免阻塞服務
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset_time": window,
                "current": 0
            }
    
    async def reset(self, key: str) -> bool:
        """重置速率限制"""
        return await self.cache.delete(key)


class SessionManager:
    """會話管理器"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
    
    async def create_session(
        self, 
        session_id: str, 
        user_id: str, 
        data: dict,
        expire: int = 3600
    ) -> bool:
        """創建會話"""
        session_key = f"{self.session_prefix}{session_id}"
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        
        # 保存會話數據
        session_data = {
            "user_id": user_id,
            "created_at": str(asyncio.get_event_loop().time()),
            **data
        }
        
        success = await self.cache.set(session_key, session_data, expire)
        
        if success:
            # 添加到用戶會話列表
            await self.cache.client.sadd(user_sessions_key, session_id)
            await self.cache.expire(user_sessions_key, expire)
        
        return success
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """獲取會話"""
        session_key = f"{self.session_prefix}{session_id}"
        return await self.cache.get(session_key)
    
    async def update_session(
        self, 
        session_id: str, 
        data: dict,
        expire: Optional[int] = None
    ) -> bool:
        """更新會話"""
        session_key = f"{self.session_prefix}{session_id}"
        current_data = await self.cache.get(session_key)
        
        if current_data:
            current_data.update(data)
            return await self.cache.set(session_key, current_data, expire)
        
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """刪除會話"""
        session_key = f"{self.session_prefix}{session_id}"
        session_data = await self.cache.get(session_key)
        
        if session_data and "user_id" in session_data:
            user_sessions_key = f"{self.user_sessions_prefix}{session_data['user_id']}"
            await self.cache.client.srem(user_sessions_key, session_id)
        
        return await self.cache.delete(session_key)
    
    async def get_user_sessions(self, user_id: str) -> list[str]:
        """獲取用戶的所有會話"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        try:
            sessions = await self.cache.client.smembers(user_sessions_key)
            return [session.decode() for session in sessions]
        except Exception as e:
            logger.error("Failed to get user sessions", user_id=user_id, error=str(e))
            return []
    
    async def delete_user_sessions(self, user_id: str) -> bool:
        """刪除用戶的所有會話"""
        sessions = await self.get_user_sessions(user_id)
        
        for session_id in sessions:
            await self.delete_session(session_id)
        
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        return await self.cache.delete(user_sessions_key)


# 創建全局實例
cache = RedisCache()
rate_limiter = RateLimiter(cache)
session_manager = SessionManager(cache)

