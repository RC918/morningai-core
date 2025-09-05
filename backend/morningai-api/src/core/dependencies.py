"""
FastAPI 依賴注入模組
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.core.database import get_db
from src.core.security import verify_token, extract_user_id_from_token
from src.core.redis import rate_limiter, get_redis
from src.models.user import User
from src.models.tenant import Tenant
from src.services.user_service import UserService

logger = structlog.get_logger()

# HTTP Bearer 認證方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """獲取當前用戶"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """獲取當前活躍用戶（必須登入）"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """獲取當前超級用戶"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


def require_permission(permission: str):
    """權限檢查裝飾器"""
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        # 檢查用戶是否有指定權限
        has_permission = await current_user.has_permission(permission)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return current_user
    
    return permission_checker


def require_role(role_name: str):
    """角色檢查裝飾器"""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        # 檢查用戶是否有指定角色
        has_role = await current_user.has_role(role_name)
        
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        
        return current_user
    
    return role_checker


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """獲取當前用戶的租戶"""
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no associated tenant"
        )
    
    if not current_user.tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active"
        )
    
    return current_user.tenant


def rate_limit(
    key_func: callable = None,
    limit: int = 100,
    window: int = 3600,
    per_user: bool = True
):
    """速率限制裝飾器"""
    async def rate_limit_checker(
        request: Request,
        current_user: Annotated[Optional[User], Depends(get_current_user)] = None
    ):
        # 生成限制鍵
        if key_func:
            key = key_func(request, current_user)
        elif per_user and current_user:
            key = f"rate_limit:user:{current_user.id}"
        else:
            # 使用 IP 地址
            client_ip = request.client.host
            key = f"rate_limit:ip:{client_ip}"
        
        # 檢查速率限制
        allowed, rate_info = await rate_limiter.is_allowed(key, limit, window)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset_time"]),
                    "Retry-After": str(rate_info["reset_time"])
                }
            )
        
        # 添加速率限制標頭到響應
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset_time"])
        }
        
        return True
    
    return rate_limit_checker


def tenant_isolation():
    """租戶隔離檢查"""
    async def tenant_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        # 超級用戶可以訪問所有租戶
        if current_user.is_superuser:
            return current_user
        
        # 檢查租戶是否活躍
        if not current_user.tenant or not current_user.tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant access denied"
            )
        
        return current_user
    
    return tenant_checker


async def get_client_ip(request: Request) -> str:
    """獲取客戶端IP地址"""
    # 檢查代理標頭
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一個IP（原始客戶端IP）
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 回退到直接連接IP
    return request.client.host


async def get_user_agent(request: Request) -> str:
    """獲取用戶代理字符串"""
    return request.headers.get("User-Agent", "Unknown")


async def get_request_id(request: Request) -> str:
    """獲取請求ID"""
    return request.headers.get("X-Request-ID", "unknown")


class PaginationParams:
    """分頁參數"""
    
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max(1, size), max_size)
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """獲取分頁參數"""
    return PaginationParams(page=page, size=size)


class SortParams:
    """排序參數"""
    
    def __init__(
        self,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"


def get_sort_params(
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> SortParams:
    """獲取排序參數"""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


# 常用的依賴組合
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentTenant = Annotated[Tenant, Depends(get_current_tenant)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
SortDep = Annotated[SortParams, Depends(get_sort_params)]
ClientIP = Annotated[str, Depends(get_client_ip)]
UserAgent = Annotated[str, Depends(get_user_agent)]
RequestID = Annotated[str, Depends(get_request_id)]

