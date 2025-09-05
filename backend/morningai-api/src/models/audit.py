"""
審計日誌模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class AuditLog(Base):
    """審計日誌模型"""
    
    __tablename__ = "audit_logs"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 租戶關聯
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE")
    )
    
    # 用戶關聯
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    # 操作信息
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # create, update, delete, login, etc.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, cms_content, etc.
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))  # 資源 ID
    
    # 詳細信息
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 變更記錄
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)  # 變更前的值
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)  # 變更後的值
    
    # 請求信息
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(100))  # 請求追蹤 ID
    
    # 結果
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # 元數據
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # 時間戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # 關聯
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant"
    )
    
    user: Mapped[Optional["User"]] = relationship(
        "User"
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource_type='{self.resource_type}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def create_log(
        cls,
        action: str,
        resource_type: str,
        tenant_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "AuditLog":
        """創建審計日誌記錄"""
        return cls(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message,
            metadata=metadata,
        )

