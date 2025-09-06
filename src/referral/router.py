"""
Referral Router - 推薦系統相關路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# 簡化的請求模型
class UseReferralRequest(BaseModel):
    referral_code: str
    user_id: str

class ReferralStats(BaseModel):
    total_referrals: int
    successful_referrals: int
    pending_referrals: int
    total_rewards: float

@router.get("/stats")
async def referral_stats():
    """推薦統計"""
    return {
        "success": True,
        "data": {
            "total_referrals": 10,
            "successful_referrals": 8,
            "pending_referrals": 2,
            "total_rewards": 800.0,
            "referral_codes": ["ABC123", "DEF456", "GHI789"]
        },
        "message": "推薦統計獲取成功",
        "endpoint": "/referral/stats"
    }

@router.post("/use")
async def use_referral_code(request: UseReferralRequest):
    """使用推薦碼"""
    return {
        "success": True,
        "message": "推薦碼使用成功",
        "data": {
            "referral_code": request.referral_code,
            "user_id": request.user_id,
            "reward_amount": 100.0,
            "status": "applied"
        },
        "endpoint": "/referral/use"
    }

@router.get("/codes")
async def get_referral_codes():
    """獲取推薦碼列表"""
    return {
        "success": True,
        "data": {
            "codes": [
                {
                    "code": "ABC123",
                    "created_at": "2025-09-01T00:00:00Z",
                    "uses": 5,
                    "max_uses": 10,
                    "is_active": True
                },
                {
                    "code": "DEF456", 
                    "created_at": "2025-09-02T00:00:00Z",
                    "uses": 3,
                    "max_uses": 5,
                    "is_active": True
                }
            ]
        },
        "message": "推薦碼列表獲取成功",
        "endpoint": "/referral/codes"
    }

@router.get("/validate/{code}")
async def validate_referral_code(code: str):
    """驗證推薦碼"""
    # 簡化的驗證邏輯
    valid_codes = ["ABC123", "DEF456", "GHI789"]
    
    if code in valid_codes:
        return {
            "success": True,
            "valid": True,
            "code": code,
            "message": "推薦碼有效",
            "remaining_uses": 5
        }
    else:
        return {
            "success": True,
            "valid": False,
            "code": code,
            "message": "推薦碼無效或已過期",
            "remaining_uses": 0
        }

