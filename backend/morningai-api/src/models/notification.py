"""
通知系統模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class Notification(Base):
    """通知模型"""
    
    __tablename__ = "notifications"
    
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
    
    # 接收者
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE")
    )  # None 表示廣播通知
    
    # 發送者
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    # 通知內容
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 通知類型
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # referral, chat, cms, system
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent
    
    # 渠道設置
    channels: Mapped[list] = mapped_column(JSON, default=list)  # telegram, line, email, push
    
    # 狀態
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, failed, cancelled
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 發送設置
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 外部 ID（用於追蹤第三方平台的消息）
    external_ids: Mapped[Optional[dict]] = mapped_column(JSON)  # {"telegram": "msg_id", "line": "msg_id"}
    
    # 錯誤信息
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 元數據
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    
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
        "Tenant"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    sender: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[sender_id]
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.notification_type}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "sender_id": str(self.sender_id) if self.sender_id else None,
            "title": self.title,
            "content": self.content,
            "notification_type": self.notification_type,
            "priority": self.priority,
            "channels": self.channels,
            "status": self.status,
            "is_read": self.is_read,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "external_ids": self.external_ids,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_broadcast(self) -> bool:
        """是否為廣播通知"""
        return self.user_id is None
    
    @property
    def can_retry(self) -> bool:
        """是否可以重試"""
        return self.status == "failed" and self.retry_count < 3


class NotificationSetting(Base):
    """用戶通知設置模型"""
    
    __tablename__ = "notification_settings"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 用戶關聯
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 通知類型設置
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # 渠道設置
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    line_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    line_user_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 頻率限制
    max_per_day: Mapped[int] = mapped_column(Integer, default=10)
    max_per_week: Mapped[int] = mapped_column(Integer, default=3)  # 病毒式推播限制
    
    # 時間限制
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5))  # "22:00"
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5))    # "08:00"
    
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notification_settings"
    )
    
    def __repr__(self) -> str:
        return f"<NotificationSetting(user_id={self.user_id}, type='{self.notification_type}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "notification_type": self.notification_type,
            "telegram_enabled": self.telegram_enabled,
            "telegram_chat_id": self.telegram_chat_id,
            "line_enabled": self.line_enabled,
            "line_user_id": self.line_user_id,
            "email_enabled": self.email_enabled,
            "push_enabled": self.push_enabled,
            "max_per_day": self.max_per_day,
            "max_per_week": self.max_per_week,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

