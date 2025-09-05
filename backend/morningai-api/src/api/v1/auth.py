"""
認證 API 路由
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.core.database import get_db
from src.core.dependencies import (
    get_current_active_user, 
    rate_limit,
    get_client_ip,
    get_user_agent,
    CurrentUser,
    DatabaseSession
)
from src.core.security import create_access_token, create_refresh_token, verify_token
from src.services.user_service import UserService
from src.services.referral_service import ReferralService
from src.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    UserProfile,
    UserProfileUpdate,
    AuthResponse
)
from src.models.tenant import Tenant

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["認證"])
security = HTTPBearer()


@router.post(
    "/register",
    response_model=AuthResponse,
    summary="用戶註冊",
    description="註冊新用戶帳戶，支援推薦碼"
)
async def register(
    request: Request,
    user_data: UserRegisterRequest,
    db: DatabaseSession,
    _: Annotated[bool, Depends(rate_limit(limit=5, window=3600, per_user=False))]
):
    """
    用戶註冊
    
    - 驗證用戶輸入數據
    - 檢查推薦碼（如果提供）
    - 創建用戶帳戶
    - 建立推薦關係（如果使用推薦碼）
    """
    try:
        user_service = UserService(db)
        referral_service = ReferralService(db)
        
        # 獲取預設租戶（Demo 租戶）
        from sqlalchemy import select
        stmt = select(Tenant).where(Tenant.slug == "morningai-demo")
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="系統配置錯誤：找不到預設租戶"
            )
        
        # 處理推薦碼
        referrer_user_id = None
        if user_data.referral_code:
            # 驗證推薦碼
            referral_code = await referral_service.get_referral_code_by_code(
                user_data.referral_code
            )
            
            if not referral_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="推薦碼不存在"
                )
            
            if not referral_code.can_be_used:
                if not referral_code.is_active:
                    detail = "推薦碼已停用"
                elif referral_code.is_expired:
                    detail = "推薦碼已過期"
                elif referral_code.is_exhausted:
                    detail = "推薦碼使用次數已達上限"
                else:
                    detail = "推薦碼不可用"
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )
            
            referrer_user_id = referral_code.owner_id
        
        # 創建用戶
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            tenant_id=tenant.id,
            username=user_data.username,
            display_name=user_data.display_name,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            referred_by_id=referrer_user_id,
            language=user_data.language,
            timezone=user_data.timezone
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用戶創建失敗，郵箱或用戶名可能已存在"
            )
        
        # 使用推薦碼
        if user_data.referral_code and referrer_user_id:
            success, message = await referral_service.use_referral_code(
                code=user_data.referral_code,
                referred_user_id=user.id,
                reward_amount=100  # 預設獎勵金額
            )
            
            if not success:
                logger.warning("Failed to use referral code during registration",
                             code=user_data.referral_code, message=message)
        
        logger.info("User registered successfully", 
                   user_id=str(user.id), email=user.email)
        
        return AuthResponse(
            success=True,
            message="註冊成功",
            data={
                "user_id": str(user.id),
                "email": user.email,
                "referral_code": user.referral_code
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="註冊失敗，請稍後再試"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用戶登入",
    description="用戶登入並獲取訪問令牌"
)
async def login(
    request: Request,
    login_data: UserLoginRequest,
    db: DatabaseSession,
    _: Annotated[bool, Depends(rate_limit(limit=10, window=3600, per_user=False))]
):
    """
    用戶登入
    
    - 驗證用戶憑證
    - 生成訪問令牌和刷新令牌
    - 記錄登入信息
    """
    try:
        user_service = UserService(db)
        
        # 驗證用戶
        user = await user_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="郵箱或密碼錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成令牌
        access_token_expires = 3600  # 1小時
        refresh_token_expires = 7 * 24 * 3600  # 7天
        
        if login_data.remember_me:
            access_token_expires = 24 * 3600  # 24小時
            refresh_token_expires = 30 * 24 * 3600  # 30天
        
        # 創建令牌數據
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "is_superuser": user.is_superuser
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=None  # 使用預設過期時間
        )
        
        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=None  # 使用預設過期時間
        )
        
        logger.info("User logged in successfully", 
                   user_id=str(user.id), email=user.email)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=access_token_expires
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登入失敗，請稍後再試"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新令牌",
    description="使用刷新令牌獲取新的訪問令牌"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: DatabaseSession
):
    """
    刷新令牌
    
    - 驗證刷新令牌
    - 生成新的訪問令牌
    """
    try:
        # 驗證刷新令牌
        payload = verify_token(refresh_data.refresh_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 檢查令牌類型
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌類型錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的令牌數據",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 驗證用戶是否存在且活躍
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用戶不存在或已停用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成新的訪問令牌
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "is_superuser": user.is_superuser
        }
        
        access_token = create_access_token(data=token_data)
        
        logger.info("Token refreshed successfully", user_id=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # 保持原刷新令牌
            token_type="bearer",
            expires_in=3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失敗，請稍後再試"
        )


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="獲取用戶資料",
    description="獲取當前用戶的詳細資料"
)
async def get_profile(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    獲取用戶資料
    
    - 返回當前用戶的詳細信息
    - 包含角色和權限信息
    """
    try:
        # 獲取用戶角色
        roles = []
        permissions = []
        
        for user_role in current_user.user_roles:
            if user_role.is_active:
                roles.append(user_role.role.name)
                
                for role_permission in user_role.role.role_permissions:
                    if role_permission.is_active:
                        permissions.append(role_permission.permission.name)
        
        # 去重權限
        permissions = list(set(permissions))
        
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            display_name=current_user.display_name,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            avatar_url=current_user.avatar_url,
            bio=current_user.bio,
            language=current_user.language,
            timezone=current_user.timezone,
            referral_code=current_user.referral_code,
            is_email_verified=current_user.is_email_verified,
            is_active=current_user.is_active,
            roles=roles,
            permissions=permissions,
            tenant_name=current_user.tenant.name,
            login_count=current_user.login_count or 0,
            last_login_at=current_user.last_login_at,
            created_at=current_user.created_at
        )
        
    except Exception as e:
        logger.error("Failed to get user profile", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶資料失敗"
        )


@router.put(
    "/profile",
    response_model=AuthResponse,
    summary="更新用戶資料",
    description="更新當前用戶的資料"
)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    更新用戶資料
    
    - 更新用戶的基本信息
    - 記錄變更日誌
    """
    try:
        user_service = UserService(db)
        
        # 準備更新數據
        update_data = {}
        for field, value in profile_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            return AuthResponse(
                success=True,
                message="沒有需要更新的數據",
                data={}
            )
        
        # 更新用戶
        updated_user = await user_service.update_user(
            user_id=current_user.id,
            **update_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用戶資料更新失敗"
            )
        
        logger.info("User profile updated successfully", 
                   user_id=str(current_user.id))
        
        return AuthResponse(
            success=True,
            message="用戶資料更新成功",
            data={
                "user_id": str(updated_user.id),
                "updated_fields": list(update_data.keys())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user profile", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶資料更新失敗"
        )


@router.post(
    "/change-password",
    response_model=AuthResponse,
    summary="更改密碼",
    description="更改當前用戶的密碼"
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
    _: Annotated[bool, Depends(rate_limit(limit=5, window=3600, per_user=True))]
):
    """
    更改密碼
    
    - 驗證舊密碼
    - 設置新密碼
    - 記錄安全日誌
    """
    try:
        user_service = UserService(db)
        
        # 更改密碼
        success = await user_service.change_password(
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="舊密碼錯誤或密碼更改失敗"
            )
        
        logger.info("Password changed successfully", 
                   user_id=str(current_user.id))
        
        return AuthResponse(
            success=True,
            message="密碼更改成功",
            data={"user_id": str(current_user.id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to change password", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密碼更改失敗"
        )


@router.post(
    "/logout",
    response_model=AuthResponse,
    summary="用戶登出",
    description="登出當前用戶"
)
async def logout(
    current_user: CurrentUser
):
    """
    用戶登出
    
    - 記錄登出日誌
    - 在實際應用中可以將令牌加入黑名單
    """
    try:
        logger.info("User logged out", user_id=str(current_user.id))
        
        return AuthResponse(
            success=True,
            message="登出成功",
            data={"user_id": str(current_user.id)}
        )
        
    except Exception as e:
        logger.error("Logout failed", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失敗"
        )

