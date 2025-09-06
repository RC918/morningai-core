"""
Authentication Models for MorningAI Core API
Phase 3 MVP - Auth/Referral API Models
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Request Models
class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="用戶電子郵件")
    password: str = Field(..., min_length=8, description="密碼，至少8個字符，包含大寫字母、數字和特殊字符")
    name: str = Field(..., description="用戶顯示名稱")
    referralCode: Optional[str] = Field(None, description="推薦碼（可選）")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密碼至少需要8個字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼必須包含至少一個數字')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('密碼必須包含至少一個特殊字符')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="用戶電子郵件")
    password: str = Field(..., description="密碼")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")

# Response Models
class TokenData(BaseModel):
    accessToken: str = Field(..., description="訪問令牌")
    tokenType: str = Field(default="Bearer", description="令牌類型")
    expiresIn: int = Field(..., description="過期時間（秒）")

class UserData(BaseModel):
    id: str = Field(..., description="用戶ID")
    email: str = Field(..., description="電子郵件")
    name: str = Field(..., description="用戶名稱")

class UserRegisterResponse(BaseModel):
    user: UserData = Field(..., description="用戶資料")
    token: TokenData = Field(..., description="認證令牌")

class UserLoginResponse(BaseModel):
    user: UserData = Field(..., description="用戶資料")
    token: TokenData = Field(..., description="認證令牌")

# Referral Models
class ReferralStatsResponse(BaseModel):
    totalReferrals: int = Field(default=0, description="總推薦數")
    uniqueReferrers: int = Field(default=0, description="唯一推薦人數")
    recent: List[Dict[str, Any]] = Field(default=[], description="最近推薦記錄")

class ReferralLeaderboard(BaseModel):
    rank: int = Field(..., description="排名")
    user_id: str = Field(..., description="用戶ID")
    name: Optional[str] = Field(None, description="姓名")
    referral_count: int = Field(..., description="推薦數量")
    total_rewards: float = Field(..., description="總獎勵")

class ReferralLeaderboardResponse(BaseModel):
    leaderboard: List[ReferralLeaderboard] = Field(..., description="推薦排行榜")
    total_users: int = Field(..., description="總用戶數")
    current_user_rank: Optional[int] = Field(None, description="當前用戶排名")

# Error Models
class ErrorDetail(BaseModel):
    code: str = Field(..., description="錯誤代碼")
    message: str = Field(..., description="錯誤消息")
    field: Optional[str] = Field(None, description="錯誤字段")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="錯誤類型")
    details: List[ErrorDetail] = Field(default=[], description="錯誤詳情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="錯誤時間")
    request_id: Optional[str] = Field(None, description="請求ID")

# Database Models (for internal use)
class UserInDB(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    role_id: Optional[uuid.UUID]
    email: str
    password_hash: str
    name: Optional[str]
    avatar_url: Optional[str]
    referral_code: Optional[str]
    referred_by_code: Optional[str]
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class TenantInDB(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RoleInDB(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime

# JWT Payload Model
class JWTPayload(BaseModel):
    sub: str = Field(..., description="用戶ID")
    email: str = Field(..., description="用戶郵箱")
    tenant_id: str = Field(..., description="租戶ID")
    role: str = Field(..., description="用戶角色")
    exp: int = Field(..., description="過期時間戳")
    iat: int = Field(..., description="簽發時間戳")
    jti: str = Field(..., description="JWT ID")

# API Response Wrapper
class APIResponse(BaseModel):
    success: bool = Field(default=True, description="請求是否成功")
    data: Optional[Any] = Field(None, description="響應數據")
    message: str = Field(default="操作成功", description="響應消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="響應時間")
    request_id: Optional[str] = Field(None, description="請求ID")

# Health Check Models
class HealthCheckResponse(BaseModel):
    status: str = Field(default="healthy", description="服務狀態")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="檢查時間")
    version: str = Field(default="1.0.0", description="API版本")
    database: Optional[str] = Field(None, description="資料庫狀態")
    dependencies: Dict[str, str] = Field(default={}, description="依賴服務狀態")

