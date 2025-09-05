"""
推薦系統相關的 Pydantic 模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ReferralCodeCreate(BaseModel):
    """創建推薦碼請求"""
    custom_code: Optional[str] = Field(None, max_length=20, description="自定義推薦碼")
    max_uses: Optional[int] = Field(None, ge=1, description="最大使用次數")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    
    @validator('custom_code')
    def validate_custom_code(cls, v):
        if v is not None:
            # 推薦碼只能包含大寫字母和數字
            import re
            if not re.match(r'^[A-Z0-9]+$', v):
                raise ValueError('推薦碼只能包含大寫字母和數字')
            if len(v) < 4:
                raise ValueError('推薦碼長度至少需要4個字符')
        return v
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v is not None and v <= datetime.utcnow():
            raise ValueError('過期時間必須是未來時間')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "custom_code": "FRIEND2025",
                "max_uses": 100,
                "expires_at": "2025-12-31T23:59:59Z"
            }
        }


class ReferralCodeUpdate(BaseModel):
    """更新推薦碼請求"""
    max_uses: Optional[int] = Field(None, ge=1, description="最大使用次數")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    is_active: Optional[bool] = Field(None, description="是否啟用")
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v is not None and v <= datetime.utcnow():
            raise ValueError('過期時間必須是未來時間')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "max_uses": 200,
                "expires_at": "2025-12-31T23:59:59Z",
                "is_active": True
            }
        }


class ReferralCodeUse(BaseModel):
    """使用推薦碼請求"""
    code: str = Field(..., max_length=20, description="推薦碼")
    
    @validator('code')
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError('推薦碼不能為空')
        return v.strip().upper()
    
    class Config:
        schema_extra = {
            "example": {
                "code": "FRIEND2025"
            }
        }


class ReferralCodeInfo(BaseModel):
    """推薦碼信息"""
    id: str = Field(..., description="推薦碼ID")
    code: str = Field(..., description="推薦碼")
    owner_id: str = Field(..., description="擁有者ID")
    owner_name: str = Field(..., description="擁有者名稱")
    max_uses: Optional[int] = Field(None, description="最大使用次數")
    current_uses: int = Field(..., description="當前使用次數")
    is_active: bool = Field(..., description="是否啟用")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "990e8400-e29b-41d4-a716-446655440001",
                "code": "FRIEND2025",
                "owner_id": "880e8400-e29b-41d4-a716-446655440002",
                "owner_name": "John Doe",
                "max_uses": 100,
                "current_uses": 25,
                "is_active": True,
                "expires_at": "2025-12-31T23:59:59Z",
                "created_at": "2025-09-01T08:00:00Z",
                "updated_at": "2025-09-05T10:30:00Z"
            }
        }


class ReferralRelationInfo(BaseModel):
    """推薦關係信息"""
    id: str = Field(..., description="推薦關係ID")
    referrer_id: str = Field(..., description="推薦人ID")
    referrer_name: str = Field(..., description="推薦人名稱")
    referred_id: str = Field(..., description="被推薦人ID")
    referred_name: str = Field(..., description="被推薦人名稱")
    referral_code_id: str = Field(..., description="推薦碼ID")
    referral_code: str = Field(..., description="推薦碼")
    reward_given: bool = Field(..., description="是否已發放獎勵")
    reward_amount: Optional[int] = Field(None, description="獎勵金額")
    created_at: datetime = Field(..., description="創建時間")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "bb0e8400-e29b-41d4-a716-446655440001",
                "referrer_id": "880e8400-e29b-41d4-a716-446655440002",
                "referrer_name": "John Doe",
                "referred_id": "880e8400-e29b-41d4-a716-446655440003",
                "referred_name": "Jane Smith",
                "referral_code_id": "990e8400-e29b-41d4-a716-446655440001",
                "referral_code": "FRIEND2025",
                "reward_given": True,
                "reward_amount": 100,
                "created_at": "2025-09-05T10:30:00Z"
            }
        }


class ReferralStats(BaseModel):
    """推薦統計"""
    referral_codes: List[ReferralCodeInfo] = Field(..., description="推薦碼列表")
    total_referrals: int = Field(..., description="總推薦數")
    rewarded_referrals: int = Field(..., description="已獎勵推薦數")
    total_rewards: int = Field(..., description="總獎勵金額")
    recent_referrals: List[ReferralRelationInfo] = Field(..., description="最近推薦記錄")
    
    class Config:
        schema_extra = {
            "example": {
                "referral_codes": [
                    {
                        "id": "990e8400-e29b-41d4-a716-446655440001",
                        "code": "FRIEND2025",
                        "owner_id": "880e8400-e29b-41d4-a716-446655440002",
                        "owner_name": "John Doe",
                        "max_uses": 100,
                        "current_uses": 25,
                        "is_active": True,
                        "expires_at": "2025-12-31T23:59:59Z",
                        "created_at": "2025-09-01T08:00:00Z",
                        "updated_at": "2025-09-05T10:30:00Z"
                    }
                ],
                "total_referrals": 25,
                "rewarded_referrals": 20,
                "total_rewards": 2000,
                "recent_referrals": []
            }
        }


class ReferralLeaderboard(BaseModel):
    """推薦排行榜"""
    user_id: str = Field(..., description="用戶ID")
    display_name: str = Field(..., description="顯示名稱")
    email: str = Field(..., description="電子郵件")
    referral_count: int = Field(..., description="推薦數量")
    total_rewards: int = Field(..., description="總獎勵金額")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "880e8400-e29b-41d4-a716-446655440002",
                "display_name": "John Doe",
                "email": "john@example.com",
                "referral_count": 25,
                "total_rewards": 2000
            }
        }


class ReferralRewardGive(BaseModel):
    """發放推薦獎勵請求"""
    referral_relation_id: str = Field(..., description="推薦關係ID")
    reward_amount: int = Field(..., ge=1, description="獎勵金額")
    
    class Config:
        schema_extra = {
            "example": {
                "referral_relation_id": "bb0e8400-e29b-41d4-a716-446655440001",
                "reward_amount": 100
            }
        }


class ReferralResponse(BaseModel):
    """推薦系統響應"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="響應消息")
    data: Optional[dict] = Field(None, description="響應數據")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {
                    "referral_code_id": "990e8400-e29b-41d4-a716-446655440001"
                }
            }
        }


class ReferralCodeValidation(BaseModel):
    """推薦碼驗證響應"""
    valid: bool = Field(..., description="推薦碼是否有效")
    code: str = Field(..., description="推薦碼")
    owner_name: Optional[str] = Field(None, description="擁有者名稱")
    remaining_uses: Optional[int] = Field(None, description="剩餘使用次數")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    message: str = Field(..., description="驗證消息")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "code": "FRIEND2025",
                "owner_name": "John Doe",
                "remaining_uses": 75,
                "expires_at": "2025-12-31T23:59:59Z",
                "message": "推薦碼有效"
            }
        }


class PaginatedReferralCodes(BaseModel):
    """分頁推薦碼列表"""
    items: List[ReferralCodeInfo] = Field(..., description="推薦碼列表")
    total: int = Field(..., description="總數")
    page: int = Field(..., description="當前頁")
    size: int = Field(..., description="每頁大小")
    pages: int = Field(..., description="總頁數")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "size": 20,
                "pages": 5
            }
        }


class PaginatedReferralRelations(BaseModel):
    """分頁推薦關係列表"""
    items: List[ReferralRelationInfo] = Field(..., description="推薦關係列表")
    total: int = Field(..., description="總數")
    page: int = Field(..., description="當前頁")
    size: int = Field(..., description="每頁大小")
    pages: int = Field(..., description="總頁數")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "size": 20,
                "pages": 3
            }
        }

