"""
用戶模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class User(Base):
    """用戶模型"""
    
    __tablename__ = "users"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 租戶關聯
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 基本信息
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 認證信息
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 個人資料
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    
    # 偏好設置
    language: Mapped[str] = mapped_column(String(10), default="zh-TW")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Taipei")
    
    # 推薦信息
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    referred_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    # 登入信息
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    login_count: Mapped[int] = mapped_column(default=0)
    
    # 時間戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # 關聯
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users"
    )
    
    # 自引用關聯 - 推薦關係
    referred_by: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        back_populates="referrals"
    )
    
    referrals: Mapped[list["User"]] = relationship(
        "User",
        back_populates="referred_by"
    )
    
    # 角色關聯
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 聊天會話
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 通知設置
    notification_settings: Mapped[list["NotificationSetting"]] = relationship(
        "NotificationSetting",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """轉換為字典"""
        data = {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "email": self.email,
            "username": self.username,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "language": self.language,
            "timezone": self.timezone,
            "referral_code": self.referral_code,
            "referred_by_id": str(self.referred_by_id) if self.referred_by_id else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "is_email_verified": self.is_email_verified,
                "last_login_ip": self.last_login_ip,
            })
        
        return data
    
    @property
    def full_name(self) -> str:
        """獲取全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username or self.email.split("@")[0]
    
    @property
    def referral_count(self) -> int:
        """獲取推薦用戶數量"""
        return len(self.referrals) if self.referrals else 0
    
    def has_role(self, role_name: str) -> bool:
        """檢查是否有特定角色"""
        if not self.user_roles:
            return False
        return any(ur.role.name == role_name for ur in self.user_roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """檢查是否有特定權限"""
        if self.is_superuser:
            return True
        
        if not self.user_roles:
            return False
        
        for user_role in self.user_roles:
            for role_permission in user_role.role.role_permissions:
                if role_permission.permission.name == permission_name:
                    return True
        
        return False
