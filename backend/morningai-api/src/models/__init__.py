"""
數據庫模型包
"""

# 導入所有模型以確保它們被 SQLAlchemy 註冊
from .tenant import Tenant
from .user import User
from .role import Role, Permission, UserRole, RolePermission
from .chat import ChatSession, ChatMessage
from .cms import CMSContent, CMSContentI18n
from .referral import ReferralCode, ReferralRelation
from .notification import Notification, NotificationSetting
from .audit import AuditLog

__all__ = [
    "Tenant",
    "User", 
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "ChatSession",
    "ChatMessage",
    "CMSContent",
    "CMSContentI18n",
    "ReferralCode",
    "ReferralRelation",
    "Notification",
    "NotificationSetting",
    "AuditLog",
]

