"""
推薦系統模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class ReferralCode(Base):
    """推薦碼模型"""
    
    __tablename__ = "referral_codes"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 推薦碼信息
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 使用限制
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)  # None = 無限制
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 有效期
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
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
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id]
    )
    
    referral_relations: Mapped[list["ReferralRelation"]] = relationship(
        "ReferralRelation",
        back_populates="referral_code",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ReferralCode(id={self.id}, code='{self.code}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "code": self.code,
            "owner_id": str(self.owner_id),
            "max_uses": self.max_uses,
            "current_uses": self.current_uses,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_expired(self) -> bool:
        """檢查是否已過期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_exhausted(self) -> bool:
        """檢查是否已用完"""
        if not self.max_uses:
            return False
        return self.current_uses >= self.max_uses
    
    @property
    def can_be_used(self) -> bool:
        """檢查是否可以使用"""
        return self.is_active and not self.is_expired and not self.is_exhausted


class ReferralRelation(Base):
    """推薦關係記錄"""
    
    __tablename__ = "referral_relations"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 推薦關係
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    referred_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    referral_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("referral_codes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 獎勵狀態
    reward_given: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_amount: Mapped[Optional[int]] = mapped_column(Integer)  # 獎勵金額（分）
    
    # 時間戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # 關聯
    referrer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referrer_id]
    )
    
    referred: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referred_id]
    )
    
    referral_code: Mapped["ReferralCode"] = relationship(
        "ReferralCode",
        back_populates="referral_relations"
    )
    
    def __repr__(self) -> str:
        return f"<ReferralRelation(referrer_id={self.referrer_id}, referred_id={self.referred_id})>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "referrer_id": str(self.referrer_id),
            "referred_id": str(self.referred_id),
            "referral_code_id": str(self.referral_code_id),
            "reward_given": self.reward_given,
            "reward_amount": self.reward_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

