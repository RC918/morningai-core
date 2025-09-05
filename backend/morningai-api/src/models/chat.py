"""
聊天系統模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class ChatSession(Base):
    """聊天會話模型"""
    
    __tablename__ = "chat_sessions"
    
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
    
    # 會話信息
    title: Mapped[Optional[str]] = mapped_column(String(255))
    context: Mapped[Optional[dict]] = mapped_column(JSON)  # 會話上下文
    
    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 統計
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    
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
        back_populates="chat_sessions"
    )
    
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, user_id={self.user_id})>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "context": self.context,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatMessage(Base):
    """聊天消息模型"""
    
    __tablename__ = "chat_messages"
    
    # 主鍵
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 會話關聯
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 消息內容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    
    # GPT 相關
    model: Mapped[Optional[str]] = mapped_column(String(50))  # 使用的模型
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)  # 使用的 token 數
    
    # RAG 相關
    rag_sources: Mapped[Optional[list]] = mapped_column(JSON)  # RAG 來源文檔
    confidence_score: Mapped[Optional[float]] = mapped_column()  # 置信度分數
    
    # 處理狀態
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否為 fallback 回應
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)  # 處理時間（毫秒）
    
    # 元數據
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # 時間戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # 關聯
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages"
    )
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role='{self.role}')>"
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "content": self.content,
            "role": self.role,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "rag_sources": self.rag_sources,
            "confidence_score": self.confidence_score,
            "is_fallback": self.is_fallback,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def is_user_message(self) -> bool:
        """是否為用戶消息"""
        return self.role == "user"
    
    @property
    def is_assistant_message(self) -> bool:
        """是否為助手消息"""
        return self.role == "assistant"
    
    @property
    def has_rag_sources(self) -> bool:
        """是否有 RAG 來源"""
        return bool(self.rag_sources)

