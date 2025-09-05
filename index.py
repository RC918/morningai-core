"""
MorningAI Core API - 最簡化版本用於Vercel部署測試
"""
from datetime import datetime

# 嘗試導入FastAPI，如果失敗則使用基本HTTP響應
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    # 創建FastAPI應用
    app = FastAPI(
        title="MorningAI Core API",
        description="MorningAI 核心後端服務 - 簡化版",
        version="1.0.0"
    )
    
    # 添加CORS中間件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """根路徑健康檢查"""
        return {
            "status": "healthy",
            "message": "MorningAI Core API is running successfully on Vercel!",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "staging",
            "version": "1.0.0",
            "platform": "vercel"
        }
    
    @app.get("/health")
    async def health_check():
        """健康檢查端點"""
        return {
            "status": "healthy",
            "message": "All systems operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.get("/test")
    async def test_endpoint():
        """測試端點"""
        return {
            "message": "API test successful",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ok"
        }

except ImportError:
    # 如果FastAPI不可用，創建一個基本的WSGI應用
    def app(environ, start_response):
        """基本WSGI應用作為後備"""
        status = '200 OK'
        headers = [
            ('Content-type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ]
        start_response(status, headers)
        
        response = {
            "status": "healthy",
            "message": "MorningAI Core API is running (basic mode)",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "FastAPI not available, using basic WSGI"
        }
        
        import json
        return [json.dumps(response).encode('utf-8')]

# Vercel 處理器
def handler(request):
    """Vercel serverless 函數處理器"""
    return app

# 確保兼容性
__all__ = ['app', 'handler']

