"""
RBAC 角色權限模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class Role(Base):
    """角色模型"""
    
    __tablename__ = "roles"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # 系統內建角色
    
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
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_permissions(self) -> list[str]:
        """獲取角色的所有權限名稱"""
        return [rp.permission.name for rp in self.role_permissions]


class Permission(Base):
    """權限模型"""
    
    __tablename__ = "permissions"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 分類
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # 如: user, chat, cms, etc.
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserRole(Base):
    """用戶角色關聯表"""
    
    __tablename__ = "user_roles"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 外鍵
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 授權信息
    granted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    granted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # 過期時間（可選）
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 關聯
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_roles",
        foreign_keys=[user_id]
    )
    
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_roles"
    )
    
    granted_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[granted_by_id]
    )
    
    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "role_id": str(self.role_id),
            "granted_by_id": str(self.granted_by_id) if self.granted_by_id else None,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }
    
    @property
    def is_expired(self) -> bool:
        """檢查是否已過期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class RolePermission(Base):
    """角色權限關聯表"""
    
    __tablename__ = "role_permissions"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 外鍵
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 授權信息
    granted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    
    granted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 關聯
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="role_permissions"
    )
    
    permission: Mapped["Permission"] = relationship(
        "Permission",
        back_populates="role_permissions"
    )
    
    granted_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[granted_by_id]
    )
    
    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "role_id": str(self.role_id),
            "permission_id": str(self.permission_id),
            "granted_by_id": str(self.granted_by_id) if self.granted_by_id else None,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "is_active": self.is_active,
        }

