"""
極簡版本 MorningAI Core API
僅包含核心Auth和Referral端點
"""
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="MorningAI Core API",
    description="極簡版本 - 僅核心端點",
    version="1.0.0-minimal"
)

@app.get("/")
async def read_root():
    """根路徑"""
    return {
        "message": "MorningAI Core API - 極簡版本",
        "status": "healthy",
        "version": "1.0.0-minimal",
        "environment": "staging",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": "render",
        "features": ["auth", "referral", "health_checks"],
        "fix_version": "ultra_minimal"
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"ok": True, "status": "healthy", "service": "morningai-core-api"}

@app.get("/healthz")
async def healthz():
    """全量健康檢查"""
    return {
        "status": "ok",
        "env": "render",
        "timestamp": datetime.utcnow().isoformat(),
        "fix_version": "ultra_minimal"
    }

# Auth端點
@app.post("/auth/register")
async def register():
    """用戶註冊"""
    return {
        "success": True,
        "message": "註冊端點已註冊",
        "status": "endpoint_available",
        "fix_version": "ultra_minimal"
    }

@app.post("/auth/login")
async def login():
    """用戶登入"""
    return {
        "success": True,
        "message": "登入端點已註冊",
        "access_token": "demo_token_123",
        "token_type": "bearer",
        "fix_version": "ultra_minimal"
    }

@app.get("/auth/profile")
async def get_profile():
    """獲取用戶資料"""
    return {
        "user_id": "demo_user_123",
        "email": "demo@example.com",
        "username": "demo_user",
        "fix_version": "ultra_minimal"
    }

# Referral端點
@app.get("/referral/stats")
async def referral_stats():
    """推薦統計"""
    return {
        "success": True,
        "data": {
            "total_referrals": 10,
            "successful_referrals": 8,
            "pending_referrals": 2,
            "total_rewards": 800.0
        },
        "message": "推薦統計獲取成功",
        "fix_version": "ultra_minimal"
    }

@app.post("/referral/use")
async def use_referral_code():
    """使用推薦碼"""
    return {
        "success": True,
        "message": "推薦碼使用成功",
        "fix_version": "ultra_minimal"
    }

@app.get("/referral/codes")
async def get_referral_codes():
    """獲取推薦碼列表"""
    return {
        "success": True,
        "data": {
            "codes": ["ABC123", "DEF456", "GHI789"]
        },
        "message": "推薦碼列表獲取成功",
        "fix_version": "ultra_minimal"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

