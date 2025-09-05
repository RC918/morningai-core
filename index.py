"""
MorningAI Core API - 根目錄入口點 (備用)
"""
from api.index import app

# 直接導出app以供Vercel使用
def handler(request):
    """Vercel serverless 函數處理器"""
    return app

# 為了確保兼容性
__all__ = ['app', 'handler']

