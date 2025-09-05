"""
認證相關的 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
import re


class UserRegisterRequest(BaseModel):
    """用戶註冊請求"""
    email: EmailStr = Field(..., description="電子郵件地址")
    password: str = Field(..., min_length=8, max_length=128, description="密碼")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用戶名")
    display_name: Optional[str] = Field(None, max_length=255, description="顯示名稱")
    first_name: Optional[str] = Field(None, max_length=100, description="名字")
    last_name: Optional[str] = Field(None, max_length=100, description="姓氏")
    referral_code: Optional[str] = Field(None, max_length=20, description="推薦碼")
    language: str = Field("zh-TW", description="語言偏好")
    timezone: str = Field("Asia/Taipei", description="時區")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('用戶名只能包含字母、數字、下劃線和連字符')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密碼長度至少需要8個字符')
        
        if not any(c.islower() for c in v):
            raise ValueError('密碼需要包含至少一個小寫字母')
        
        if not any(c.isupper() for c in v):
            raise ValueError('密碼需要包含至少一個大寫字母')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼需要包含至少一個數字')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "username": "john_doe",
                "display_name": "John Doe",
                "first_name": "John",
                "last_name": "Doe",
                "referral_code": "FRIEND2025",
                "language": "zh-TW",
                "timezone": "Asia/Taipei"
            }
        }


class UserLoginRequest(BaseModel):
    """用戶登入請求"""
    email: EmailStr = Field(..., description="電子郵件地址")
    password: str = Field(..., description="密碼")
    remember_me: bool = Field(False, description="記住我")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "remember_me": False
            }
        }


class TokenResponse(BaseModel):
    """令牌響應"""
    access_token: str = Field(..., description="訪問令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌類型")
    expires_in: int = Field(..., description="過期時間（秒）")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class RefreshTokenRequest(BaseModel):
    """刷新令牌請求"""
    refresh_token: str = Field(..., description="刷新令牌")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordChangeRequest(BaseModel):
    """密碼更改請求"""
    old_password: str = Field(..., description="舊密碼")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密碼")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密碼長度至少需要8個字符')
        
        if not any(c.islower() for c in v):
            raise ValueError('密碼需要包含至少一個小寫字母')
        
        if not any(c.isupper() for c in v):
            raise ValueError('密碼需要包含至少一個大寫字母')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼需要包含至少一個數字')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "old_password": "OldPass123",
                "new_password": "NewSecurePass456"
            }
        }


class PasswordResetRequest(BaseModel):
    """密碼重置請求"""
    email: EmailStr = Field(..., description="電子郵件地址")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """密碼重置確認"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密碼")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密碼長度至少需要8個字符')
        
        if not any(c.islower() for c in v):
            raise ValueError('密碼需要包含至少一個小寫字母')
        
        if not any(c.isupper() for c in v):
            raise ValueError('密碼需要包含至少一個大寫字母')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼需要包含至少一個數字')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePass456"
            }
        }


class EmailVerificationRequest(BaseModel):
    """郵箱驗證請求"""
    token: str = Field(..., description="驗證令牌")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "verification_token_here"
            }
        }


class UserProfile(BaseModel):
    """用戶資料"""
    id: str = Field(..., description="用戶ID")
    email: str = Field(..., description="電子郵件地址")
    username: Optional[str] = Field(None, description="用戶名")
    display_name: str = Field(..., description="顯示名稱")
    first_name: Optional[str] = Field(None, description="名字")
    last_name: Optional[str] = Field(None, description="姓氏")
    avatar_url: Optional[str] = Field(None, description="頭像URL")
    bio: Optional[str] = Field(None, description="個人簡介")
    language: str = Field(..., description="語言偏好")
    timezone: str = Field(..., description="時區")
    referral_code: str = Field(..., description="推薦碼")
    is_email_verified: bool = Field(..., description="郵箱是否已驗證")
    is_active: bool = Field(..., description="帳戶是否活躍")
    roles: list[str] = Field(..., description="用戶角色")
    permissions: list[str] = Field(..., description="用戶權限")
    tenant_name: str = Field(..., description="租戶名稱")
    login_count: int = Field(..., description="登入次數")
    last_login_at: Optional[datetime] = Field(None, description="最後登入時間")
    created_at: datetime = Field(..., description="創建時間")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "john_doe",
                "display_name": "John Doe",
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "bio": "Software developer",
                "language": "zh-TW",
                "timezone": "Asia/Taipei",
                "referral_code": "USER2025",
                "is_email_verified": True,
                "is_active": True,
                "roles": ["user"],
                "permissions": ["user.read", "chat.create"],
                "tenant_name": "Demo Company",
                "login_count": 15,
                "last_login_at": "2025-09-05T10:30:00Z",
                "created_at": "2025-09-01T08:00:00Z"
            }
        }


class UserProfileUpdate(BaseModel):
    """用戶資料更新"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用戶名")
    display_name: Optional[str] = Field(None, max_length=255, description="顯示名稱")
    first_name: Optional[str] = Field(None, max_length=100, description="名字")
    last_name: Optional[str] = Field(None, max_length=100, description="姓氏")
    bio: Optional[str] = Field(None, max_length=1000, description="個人簡介")
    avatar_url: Optional[str] = Field(None, max_length=500, description="頭像URL")
    language: Optional[str] = Field(None, description="語言偏好")
    timezone: Optional[str] = Field(None, description="時區")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('用戶名只能包含字母、數字、下劃線和連字符')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe_updated",
                "display_name": "John Doe Jr.",
                "first_name": "John",
                "last_name": "Doe Jr.",
                "bio": "Senior software developer",
                "avatar_url": "https://example.com/new_avatar.jpg",
                "language": "en",
                "timezone": "America/New_York"
            }
        }


class AuthResponse(BaseModel):
    """認證響應"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="響應消息")
    data: Optional[dict] = Field(None, description="響應數據")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            }
        }

