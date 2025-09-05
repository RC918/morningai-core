"""
CMS 內容管理模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class CMSContent(Base):
    """CMS 內容模型"""
    
    __tablename__ = "cms_contents"
    
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
    
    # 作者
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 基本信息
    slug: Mapped[str] = mapped_column(String(255), nullable=False)  # URL 友好的標識符
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # post, page, etc.
    
    # 狀態
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, published, archived
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(Text)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text)
    
    # 排序和分類
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[Optional[list]] = mapped_column(JSON)
    
    # 發布設置
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 統計
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
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
    
    author: Mapped["User"] = relationship(
        "User"
    )
    
    i18n_contents: Mapped[list["CMSContentI18n"]] = relationship(
        "CMSContentI18n",
        back_populates="content",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<CMSContent(id={self.id}, slug='{self.slug}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "author_id": str(self.author_id),
            "slug": self.slug,
            "content_type": self.content_type,
            "status": self.status,
            "is_featured": self.is_featured,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "sort_order": self.sort_order,
            "category": self.category,
            "tags": self.tags,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_published(self) -> bool:
        """是否已發布"""
        return self.status == "published" and (
            not self.published_at or self.published_at <= datetime.utcnow()
        )
    
    @property
    def is_scheduled(self) -> bool:
        """是否為預約發布"""
        return self.status == "published" and (
            self.scheduled_at and self.scheduled_at > datetime.utcnow()
        )


class CMSContentI18n(Base):
    """CMS 內容多語言模型"""
    
    __tablename__ = "cms_content_i18n"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 內容關聯
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cms_contents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 語言
    language: Mapped[str] = mapped_column(String(10), nullable=False)  # zh-TW, zh-CN, en, etc.
    
    # 內容
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 狀態
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否為預設語言
    
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
    content: Mapped["CMSContent"] = relationship(
        "CMSContent",
        back_populates="i18n_contents"
    )
    
    def __repr__(self) -> str:
        return f"<CMSContentI18n(id={self.id}, language='{self.language}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "content_id": str(self.content_id),
            "language": self.language,
            "title": self.title,
            "excerpt": self.excerpt,
            "content": self.content,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

