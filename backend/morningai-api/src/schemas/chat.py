"""
聊天系統相關的 Pydantic 模型
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ChatMessageSend(BaseModel):
    """發送聊天消息請求"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="聊天消息內容"
    )
    session_id: Optional[UUID] = Field(
        None,
        description="聊天會話ID（可選，不提供則創建新會話）"
    )
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('消息內容不能為空')
        return v.strip()


class ChatMessageResponse(BaseModel):
    """聊天消息回應"""
    session_id: UUID = Field(..., description="聊天會話ID")
    message_id: UUID = Field(..., description="回應消息ID")
    response: str = Field(..., description="AI回應內容")
    intent_analysis: Dict[str, Any] = Field(..., description="意圖分析結果")
    knowledge_used: bool = Field(..., description="是否使用了知識庫")
    knowledge_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="使用的知識庫條目"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="回應元數據"
    )
    followup_question: Optional[str] = Field(
        None,
        description="追問問題（如果需要）"
    )
    created_at: str = Field(..., description="創建時間")


class ChatMessageInfo(BaseModel):
    """聊天消息信息"""
    id: UUID = Field(..., description="消息ID")
    role: str = Field(..., description="角色（user/assistant）")
    content: str = Field(..., description="消息內容")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="消息元數據"
    )
    created_at: str = Field(..., description="創建時間")


class ChatSessionInfo(BaseModel):
    """聊天會話信息"""
    id: UUID = Field(..., description="會話ID")
    title: str = Field(..., description="會話標題")
    message_count: int = Field(..., description="消息數量")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")


class ChatHistoryResponse(BaseModel):
    """聊天歷史回應"""
    session_id: UUID = Field(..., description="會話ID")
    messages: List[ChatMessageInfo] = Field(..., description="消息列表")
    pagination: Dict[str, int] = Field(..., description="分頁信息")


class ChatSessionsResponse(BaseModel):
    """聊天會話列表回應"""
    sessions: List[ChatSessionInfo] = Field(..., description="會話列表")
    pagination: Dict[str, int] = Field(..., description="分頁信息")


class ChatSessionCreate(BaseModel):
    """創建聊天會話請求"""
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="會話標題（可選）"
    )


class ChatSessionUpdate(BaseModel):
    """更新聊天會話請求"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="會話標題"
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('會話標題不能為空')
        return v.strip()


class ChatKnowledgeBaseItem(BaseModel):
    """知識庫條目"""
    id: UUID = Field(..., description="條目ID")
    title: str = Field(..., description="標題")
    content: str = Field(..., description="內容")
    category: str = Field(..., description="分類")
    tags: List[str] = Field(default_factory=list, description="標籤")
    relevance_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="相關性分數"
    )
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")


class ChatKnowledgeBaseCreate(BaseModel):
    """創建知識庫條目請求"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="標題"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="內容"
    )
    category: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分類"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="標籤"
    )
    
    @validator('title', 'content', 'category')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('字段不能為空')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('標籤數量不能超過10個')
        return [tag.strip() for tag in v if tag.strip()]


class ChatKnowledgeBaseUpdate(BaseModel):
    """更新知識庫條目請求"""
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="標題"
    )
    content: Optional[str] = Field(
        None,
        min_length=1,
        max_length=10000,
        description="內容"
    )
    category: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="分類"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="標籤"
    )
    is_active: Optional[bool] = Field(
        None,
        description="是否啟用"
    )
    
    @validator('title', 'content', 'category')
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('字段不能為空')
        return v.strip() if v else v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError('標籤數量不能超過10個')
            return [tag.strip() for tag in v if tag.strip()]
        return v


class ChatKnowledgeBaseSearch(BaseModel):
    """知識庫搜索請求"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="搜索查詢"
    )
    category: Optional[str] = Field(
        None,
        description="分類過濾"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="標籤過濾"
    )
    limit: int = Field(
        5,
        ge=1,
        le=20,
        description="返回結果數量限制"
    )
    similarity_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="相似度閾值"
    )
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('搜索查詢不能為空')
        return v.strip()


class ChatKnowledgeBaseSearchResponse(BaseModel):
    """知識庫搜索回應"""
    query: str = Field(..., description="搜索查詢")
    items: List[ChatKnowledgeBaseItem] = Field(..., description="搜索結果")
    total: int = Field(..., description="總結果數")
    search_time: float = Field(..., description="搜索耗時（秒）")


class ChatStatsResponse(BaseModel):
    """聊天統計回應"""
    total_sessions: int = Field(..., description="總會話數")
    total_messages: int = Field(..., description="總消息數")
    avg_messages_per_session: float = Field(..., description="平均每會話消息數")
    knowledge_usage_rate: float = Field(..., description="知識庫使用率")
    response_accuracy: Optional[float] = Field(
        None,
        description="回應準確率"
    )
    avg_response_time: float = Field(..., description="平均回應時間（秒）")
    last_30_days: Dict[str, Any] = Field(..., description="最近30天統計")


class ChatFeedback(BaseModel):
    """聊天反饋"""
    message_id: UUID = Field(..., description="消息ID")
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="評分（1-5）"
    )
    feedback_type: str = Field(
        ...,
        description="反饋類型（helpful/not_helpful/incorrect/other）"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="反饋評論"
    )
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        allowed_types = ['helpful', 'not_helpful', 'incorrect', 'other']
        if v not in allowed_types:
            raise ValueError(f'反饋類型必須是: {", ".join(allowed_types)}')
        return v


class ChatFeedbackResponse(BaseModel):
    """聊天反饋回應"""
    feedback_id: UUID = Field(..., description="反饋ID")
    message: str = Field(..., description="回應消息")
    created_at: str = Field(..., description="創建時間")


# 通用響應模型
class ChatResponse(BaseModel):
    """聊天系統通用響應"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="響應消息")
    data: Optional[Any] = Field(None, description="響應數據")


# 分頁參數
class ChatPaginationParams(BaseModel):
    """聊天系統分頁參數"""
    page: int = Field(1, ge=1, description="頁碼")
    size: int = Field(20, ge=1, le=100, description="每頁大小")


# 排序參數
class ChatSortParams(BaseModel):
    """聊天系統排序參數"""
    sort_by: str = Field(
        "created_at",
        description="排序字段"
    )
    sort_order: str = Field(
        "desc",
        description="排序順序（asc/desc）"
    )
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('排序順序必須是 asc 或 desc')
        return v

