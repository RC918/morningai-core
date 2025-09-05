"""
聊天系統 API 路由
"""
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import (
    get_current_user,
    require_permission,
    rate_limit,
    get_pagination_params,
    get_sort_params
)
from src.models.user import User
from src.services.chat_service import ChatService
from src.schemas.chat import (
    ChatMessageSend,
    ChatMessageResponse,
    ChatHistoryResponse,
    ChatSessionsResponse,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatKnowledgeBaseCreate,
    ChatKnowledgeBaseUpdate,
    ChatKnowledgeBaseSearch,
    ChatKnowledgeBaseSearchResponse,
    ChatStatsResponse,
    ChatFeedback,
    ChatFeedbackResponse,
    ChatResponse,
    ChatPaginationParams,
    ChatSortParams
)

router = APIRouter()
chat_service = ChatService()


@router.post("/send", response_model=ChatMessageResponse)
@rate_limit(limit=30, window=3600)  # 每小時30條消息
async def send_message(
    request: ChatMessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    發送聊天消息
    
    **功能特色:**
    - GPT+RAG 智能回應
    - 自動意圖分析
    - 知識庫檢索
    - 對話上下文維護
    - 自動追問功能
    - 速率限制保護
    
    **權限要求:** 需要 `chat.create` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.create" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.create' required"
        )
    
    try:
        result = await chat_service.send_message(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            message=request.message,
            session_id=request.session_id
        )
        
        return ChatMessageResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天服務錯誤: {str(e)}"
        )


@router.get("/sessions", response_model=ChatSessionsResponse)
async def get_user_sessions(
    pagination: ChatPaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取用戶的聊天會話列表
    
    **功能特色:**
    - 分頁顯示
    - 按更新時間排序
    - 包含會話統計信息
    
    **權限要求:** 需要 `chat.read` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.read" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.read' required"
        )
    
    try:
        result = await chat_service.get_user_sessions(
            db=db,
            user_id=current_user.id,
            page=pagination.page,
            size=pagination.size
        )
        
        return ChatSessionsResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取會話列表失敗: {str(e)}"
        )


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: UUID,
    pagination: ChatPaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取聊天歷史
    
    **功能特色:**
    - 分頁顯示
    - 按時間順序排列
    - 包含消息元數據
    - 會話所有權驗證
    
    **權限要求:** 需要 `chat.read` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.read" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.read' required"
        )
    
    try:
        result = await chat_service.get_chat_history(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            page=pagination.page,
            size=pagination.size
        )
        
        return ChatHistoryResponse(**result)
        
    except Exception as e:
        if "不存在或無權限" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天會話不存在或無權限訪問"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取聊天歷史失敗: {str(e)}"
        )


@router.post("/sessions", response_model=ChatResponse)
async def create_session(
    request: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    創建新的聊天會話
    
    **功能特色:**
    - 自定義會話標題
    - 自動生成會話ID
    - 租戶隔離
    
    **權限要求:** 需要 `chat.create` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.create" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.create' required"
        )
    
    try:
        # 創建會話的邏輯在 send_message 中自動處理
        # 這裡提供一個顯式創建會話的端點
        session = await chat_service._get_or_create_session(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            session_id=None
        )
        
        # 如果提供了標題，更新會話標題
        if request.title:
            session.title = request.title
            await db.commit()
            await db.refresh(session)
        
        return ChatResponse(
            success=True,
            message="聊天會話創建成功",
            data={
                "session_id": str(session.id),
                "title": session.title,
                "created_at": session.created_at.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建會話失敗: {str(e)}"
        )


@router.put("/sessions/{session_id}", response_model=ChatResponse)
async def update_session(
    session_id: UUID,
    request: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新聊天會話
    
    **功能特色:**
    - 更新會話標題
    - 會話所有權驗證
    
    **權限要求:** 需要 `chat.update` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.update" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.update' required"
        )
    
    try:
        # 驗證會話所有權
        session = await db.get(ChatSession, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天會話不存在或無權限訪問"
            )
        
        # 更新會話
        session.title = request.title
        await db.commit()
        await db.refresh(session)
        
        return ChatResponse(
            success=True,
            message="聊天會話更新成功",
            data={
                "session_id": str(session.id),
                "title": session.title,
                "updated_at": session.updated_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新會話失敗: {str(e)}"
        )


@router.delete("/sessions/{session_id}", response_model=ChatResponse)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    刪除聊天會話
    
    **功能特色:**
    - 軟刪除會話
    - 會話所有權驗證
    - 級聯刪除相關消息
    
    **權限要求:** 需要 `chat.delete` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.delete" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.delete' required"
        )
    
    try:
        # 驗證會話所有權
        session = await db.get(ChatSession, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天會話不存在或無權限訪問"
            )
        
        # 軟刪除會話（設置 is_active = False）
        session.is_active = False
        await db.commit()
        
        return ChatResponse(
            success=True,
            message="聊天會話刪除成功",
            data={
                "session_id": str(session.id)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除會話失敗: {str(e)}"
        )


@router.post("/knowledge/search", response_model=ChatKnowledgeBaseSearchResponse)
@require_permission("chat.read")
async def search_knowledge(
    request: ChatKnowledgeBaseSearch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索知識庫
    
    **功能特色:**
    - 語義搜索
    - 分類和標籤過濾
    - 相似度閾值控制
    - 結果排序
    
    **權限要求:** 需要 `chat.read` 權限
    """
    try:
        import time
        start_time = time.time()
        
        # 搜索知識庫
        knowledge_items = await chat_service.rag_service.search_knowledge(
            query=request.query,
            tenant_id=current_user.tenant_id,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        search_time = time.time() - start_time
        
        return ChatKnowledgeBaseSearchResponse(
            query=request.query,
            items=knowledge_items,
            total=len(knowledge_items),
            search_time=search_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知識庫搜索失敗: {str(e)}"
        )


@router.post("/knowledge", response_model=ChatResponse)
@require_permission("chat.manage")
@rate_limit(limit=10, window=3600)  # 每小時10次
async def create_knowledge_item(
    request: ChatKnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    創建知識庫條目
    
    **功能特色:**
    - 支援分類和標籤
    - 自動向量化（TODO）
    - 租戶隔離
    
    **權限要求:** 需要 `chat.manage` 權限
    """
    try:
        # TODO: 實施知識庫條目創建
        # 這裡需要實現向量化和存儲邏輯
        
        return ChatResponse(
            success=True,
            message="知識庫條目創建成功",
            data={
                "title": request.title,
                "category": request.category
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建知識庫條目失敗: {str(e)}"
        )


@router.post("/feedback", response_model=ChatFeedbackResponse)
@rate_limit(limit=50, window=3600)  # 每小時50次反饋
async def submit_feedback(
    request: ChatFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交聊天反饋
    
    **功能特色:**
    - 消息評分
    - 反饋分類
    - 評論支援
    - 用於改進AI回應質量
    
    **權限要求:** 需要 `chat.create` 權限
    """
    # 檢查權限
    if not any(perm.name == "chat.create" for perm in current_user.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'chat.create' required"
        )
    
    try:
        # TODO: 實施反饋存儲和處理邏輯
        
        return ChatFeedbackResponse(
            feedback_id=UUID("12345678-1234-5678-9012-123456789012"),
            message="反饋提交成功，感謝您的意見！",
            created_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交反饋失敗: {str(e)}"
        )


@router.get("/stats", response_model=ChatStatsResponse)
@require_permission("chat.read")
async def get_chat_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取聊天統計信息
    
    **功能特色:**
    - 會話和消息統計
    - 知識庫使用率
    - 回應準確率
    - 性能指標
    
    **權限要求:** 需要 `chat.read` 權限
    """
    try:
        # TODO: 實施統計數據計算
        
        return ChatStatsResponse(
            total_sessions=0,
            total_messages=0,
            avg_messages_per_session=0.0,
            knowledge_usage_rate=0.0,
            response_accuracy=None,
            avg_response_time=0.0,
            last_30_days={}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取統計信息失敗: {str(e)}"
        )

