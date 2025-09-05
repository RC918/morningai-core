"""
租戶模型 - 多租戶架構支援
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class Tenant(Base):
    """租戶模型"""
    
    __tablename__ = "tenants"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 配置
    settings: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # 限制
    max_users: Mapped[int] = mapped_column(default=100)
    max_storage_mb: Mapped[int] = mapped_column(default=1000)
    
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
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "is_active": self.is_active,
            "is_trial": self.is_trial,
            "settings": self.settings,
            "max_users": self.max_users,
            "max_storage_mb": self.max_storage_mb,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def user_count(self) -> int:
        """獲取用戶數量"""
        return len(self.users) if self.users else 0
    
    @property
    def is_over_user_limit(self) -> bool:
        """是否超過用戶限制"""
        return self.user_count >= self.max_users
    
    def can_add_user(self) -> bool:
        """是否可以添加用戶"""
        return self.is_active and not self.is_over_user_limit

