"""
推薦系統 API 路由
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.core.dependencies import (
    CurrentUser,
    DatabaseSession,
    PaginationDep,
    require_permission,
    rate_limit
)
from src.services.referral_service import ReferralService
from src.schemas.referral import (
    ReferralCodeCreate,
    ReferralCodeUpdate,
    ReferralCodeUse,
    ReferralCodeInfo,
    ReferralStats,
    ReferralLeaderboard,
    ReferralCodeValidation,
    ReferralResponse,
    PaginatedReferralCodes,
    PaginatedReferralRelations
)

logger = structlog.get_logger()

router = APIRouter(prefix="/referral", tags=["推薦系統"])


@router.post(
    "/codes",
    response_model=ReferralResponse,
    summary="創建推薦碼",
    description="創建新的推薦碼"
)
async def create_referral_code(
    code_data: ReferralCodeCreate,
    current_user: Annotated[CurrentUser, Depends(require_permission("referral.create"))],
    db: DatabaseSession,
    _: Annotated[bool, Depends(rate_limit(limit=10, window=3600, per_user=True))]
):
    """
    創建推薦碼
    
    - 支援自定義推薦碼
    - 可設置使用次數限制
    - 可設置過期時間
    """
    try:
        referral_service = ReferralService(db)
        
        referral_code = await referral_service.create_referral_code(
            owner_id=current_user.id,
            max_uses=code_data.max_uses,
            expires_at=code_data.expires_at,
            custom_code=code_data.custom_code
        )
        
        if not referral_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="推薦碼創建失敗，可能是自定義推薦碼已存在"
            )
        
        logger.info("Referral code created successfully", 
                   user_id=str(current_user.id), code=referral_code.code)
        
        return ReferralResponse(
            success=True,
            message="推薦碼創建成功",
            data={
                "referral_code_id": str(referral_code.id),
                "code": referral_code.code
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create referral code", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="推薦碼創建失敗"
        )


@router.post(
    "/use",
    response_model=ReferralResponse,
    summary="使用推薦碼",
    description="使用推薦碼建立推薦關係"
)
async def use_referral_code(
    use_data: ReferralCodeUse,
    current_user: CurrentUser,
    db: DatabaseSession,
    _: Annotated[bool, Depends(rate_limit(limit=5, window=3600, per_user=True))]
):
    """
    使用推薦碼
    
    - 驗證推薦碼有效性
    - 建立推薦關係
    - 防止重複使用和自我推薦
    """
    try:
        referral_service = ReferralService(db)
        
        success, message = await referral_service.use_referral_code(
            code=use_data.code,
            referred_user_id=current_user.id,
            reward_amount=100  # 預設獎勵金額
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        logger.info("Referral code used successfully", 
                   user_id=str(current_user.id), code=use_data.code)
        
        return ReferralResponse(
            success=True,
            message=message,
            data={
                "user_id": str(current_user.id),
                "code": use_data.code
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to use referral code", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="推薦碼使用失敗"
        )


@router.get(
    "/validate/{code}",
    response_model=ReferralCodeValidation,
    summary="驗證推薦碼",
    description="驗證推薦碼是否有效"
)
async def validate_referral_code(
    code: str,
    db: DatabaseSession
):
    """
    驗證推薦碼
    
    - 檢查推薦碼是否存在
    - 檢查推薦碼是否可用
    - 返回推薦碼詳細信息
    """
    try:
        referral_service = ReferralService(db)
        
        referral_code = await referral_service.get_referral_code_by_code(code)
        
        if not referral_code:
            return ReferralCodeValidation(
                valid=False,
                code=code,
                message="推薦碼不存在"
            )
        
        if not referral_code.can_be_used:
            if not referral_code.is_active:
                message = "推薦碼已停用"
            elif referral_code.is_expired:
                message = "推薦碼已過期"
            elif referral_code.is_exhausted:
                message = "推薦碼使用次數已達上限"
            else:
                message = "推薦碼不可用"
            
            return ReferralCodeValidation(
                valid=False,
                code=code,
                owner_name=referral_code.owner.display_name,
                remaining_uses=(
                    referral_code.max_uses - referral_code.current_uses 
                    if referral_code.max_uses else None
                ),
                expires_at=referral_code.expires_at,
                message=message
            )
        
        return ReferralCodeValidation(
            valid=True,
            code=code,
            owner_name=referral_code.owner.display_name,
            remaining_uses=(
                referral_code.max_uses - referral_code.current_uses 
                if referral_code.max_uses else None
            ),
            expires_at=referral_code.expires_at,
            message="推薦碼有效"
        )
        
    except Exception as e:
        logger.error("Failed to validate referral code", code=code, error=str(e))
        return ReferralCodeValidation(
            valid=False,
            code=code,
            message="推薦碼驗證失敗"
        )


@router.get(
    "/stats",
    response_model=ReferralStats,
    summary="獲取推薦統計",
    description="獲取當前用戶的推薦統計信息"
)
async def get_referral_stats(
    current_user: Annotated[CurrentUser, Depends(require_permission("referral.read"))],
    db: DatabaseSession
):
    """
    獲取推薦統計
    
    - 用戶的推薦碼列表
    - 推薦統計數據
    - 最近推薦記錄
    """
    try:
        referral_service = ReferralService(db)
        
        stats = await referral_service.get_user_referral_stats(current_user.id)
        
        return ReferralStats(**stats)
        
    except Exception as e:
        logger.error("Failed to get referral stats", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取推薦統計失敗"
        )


@router.get(
    "/leaderboard",
    response_model=list[ReferralLeaderboard],
    summary="獲取推薦排行榜",
    description="獲取推薦排行榜"
)
async def get_referral_leaderboard(
    current_user: Annotated[CurrentUser, Depends(require_permission("referral.read"))],
    db: DatabaseSession,
    limit: int = Query(10, ge=1, le=100, description="排行榜數量限制")
):
    """
    獲取推薦排行榜
    
    - 按推薦數量排序
    - 支援租戶隔離
    """
    try:
        referral_service = ReferralService(db)
        
        # 如果不是超級用戶，只顯示同租戶的排行榜
        tenant_id = None if current_user.is_superuser else current_user.tenant_id
        
        leaderboard = await referral_service.get_referral_leaderboard(
            tenant_id=tenant_id,
            limit=limit
        )
        
        return [ReferralLeaderboard(**item) for item in leaderboard]
        
    except Exception as e:
        logger.error("Failed to get referral leaderboard", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取推薦排行榜失敗"
        )


@router.get(
    "/codes",
    response_model=PaginatedReferralCodes,
    summary="獲取推薦碼列表",
    description="獲取當前用戶的推薦碼列表"
)
async def get_referral_codes(
    current_user: Annotated[CurrentUser, Depends(require_permission("referral.read"))],
    db: DatabaseSession,
    pagination: PaginationDep
):
    """
    獲取推薦碼列表
    
    - 分頁顯示用戶的推薦碼
    - 包含使用統計
    """
    try:
        referral_service = ReferralService(db)
        
        # 獲取用戶統計（包含推薦碼）
        stats = await referral_service.get_user_referral_stats(current_user.id)
        referral_codes = stats.get("referral_codes", [])
        
        # 手動分頁
        total = len(referral_codes)
        start = pagination.offset
        end = start + pagination.size
        paginated_codes = referral_codes[start:end]
        
        # 轉換為 ReferralCodeInfo 對象
        code_infos = []
        for code_data in paginated_codes:
            code_infos.append(ReferralCodeInfo(
                id=code_data["id"],
                code=code_data["code"],
                owner_id=code_data["owner_id"],
                owner_name=current_user.display_name,
                max_uses=code_data["max_uses"],
                current_uses=code_data["current_uses"],
                is_active=code_data["is_active"],
                expires_at=code_data["expires_at"],
                created_at=code_data["created_at"],
                updated_at=code_data["updated_at"]
            ))
        
        pages = (total + pagination.size - 1) // pagination.size
        
        return PaginatedReferralCodes(
            items=code_infos,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )
        
    except Exception as e:
        logger.error("Failed to get referral codes", 
                    user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取推薦碼列表失敗"
        )


@router.put(
    "/codes/{referral_code_id}",
    response_model=ReferralResponse,
    summary="更新推薦碼",
    description="更新推薦碼設置"
)
async def update_referral_code(
    referral_code_id: str,
    update_data: ReferralCodeUpdate,
    current_user: Annotated[CurrentUser, Depends(require_permission("referral.create"))],
    db: DatabaseSession
):
    """
    更新推薦碼
    
    - 更新推薦碼設置
    - 只能更新自己的推薦碼
    """
    try:
        referral_service = ReferralService(db)
        
        # 檢查推薦碼是否存在且屬於當前用戶
        referral_code = await referral_service.get_referral_code_by_id(referral_code_id)
        
        if not referral_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="推薦碼不存在"
            )
        
        if referral_code.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權限修改此推薦碼"
            )
        
        # 準備更新數據
        update_fields = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields[field] = value
        
        if not update_fields:
            return ReferralResponse(
                success=True,
                message="沒有需要更新的數據",
                data={}
            )
        
        # 更新推薦碼
        updated_code = await referral_service.update_referral_code(
            referral_code_id=referral_code.id,
            **update_fields
        )
        
        if not updated_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="推薦碼更新失敗"
            )
        
        logger.info("Referral code updated successfully", 
                   user_id=str(current_user.id), 
                   referral_code_id=str(referral_code.id))
        
        return ReferralResponse(
            success=True,
            message="推薦碼更新成功",
            data={
                "referral_code_id": str(updated_code.id),
                "updated_fields": list(update_fields.keys())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update referral code", 
                    user_id=str(current_user.id), 
                    referral_code_id=referral_code_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="推薦碼更新失敗"
        )


@router.delete(
    "/codes/{referral_code_id}",
    response_model=ReferralResponse,
    summary="停用推薦碼",
    description="停用指定的推薦碼"
)
async def deactivate_referral_code(
    referral_code_id: str,
    current_user: Annotated[CurrentUser, Depends(require_permission("referral.create"))],
    db: DatabaseSession
):
    """
    停用推薦碼
    
    - 停用指定的推薦碼
    - 只能停用自己的推薦碼
    """
    try:
        referral_service = ReferralService(db)
        
        # 檢查推薦碼是否存在且屬於當前用戶
        referral_code = await referral_service.get_referral_code_by_id(referral_code_id)
        
        if not referral_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="推薦碼不存在"
            )
        
        if referral_code.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權限停用此推薦碼"
            )
        
        # 停用推薦碼
        success = await referral_service.deactivate_referral_code(
            referral_code_id=referral_code.id,
            deactivated_by=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="推薦碼停用失敗"
            )
        
        logger.info("Referral code deactivated successfully", 
                   user_id=str(current_user.id), 
                   referral_code_id=str(referral_code.id))
        
        return ReferralResponse(
            success=True,
            message="推薦碼已停用",
            data={
                "referral_code_id": str(referral_code.id),
                "code": referral_code.code
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to deactivate referral code", 
                    user_id=str(current_user.id), 
                    referral_code_id=referral_code_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="推薦碼停用失敗"
        )

