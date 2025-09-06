"""
Auth Router - 認證相關路由
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 簡化的請求模型
class RegisterRequest(BaseModel):
    email: str
    password: str
    referral_code: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(request: RegisterRequest):
    """用戶註冊"""
    return {
        "success": True,
        "message": "用戶註冊成功",
        "data": {
            "email": request.email,
            "referral_code": request.referral_code,
            "user_id": "demo_user_123"
        },
        "status": "registered",
        "endpoint": "/auth/register"
    }

@router.post("/login")
async def login(request: LoginRequest):
    """用戶登入"""
    # 簡化的登入邏輯
    if request.email == "demo@example.com" and request.password == "password":
        return {
            "access_token": "demo_token_123",
            "token_type": "bearer",
            "expires_in": 3600,
            "user_id": "demo_user_123",
            "email": request.email
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.get("/profile")
async def get_profile():
    """獲取用戶資料"""
    return {
        "user_id": "demo_user_123",
        "email": "demo@example.com",
        "username": "demo_user",
        "created_at": "2025-09-06T00:00:00Z",
        "is_active": True
    }

