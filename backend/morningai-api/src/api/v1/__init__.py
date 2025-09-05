"""
API v1 路由初始化
"""
from fastapi import APIRouter

from src.api.v1 import auth, referral

# 創建 v1 API 路由器
api_router = APIRouter(prefix="/v1")

# 註冊子路由
api_router.include_router(auth.router)
api_router.include_router(referral.router)

# 導出路由器
__all__ = ["api_router"]

