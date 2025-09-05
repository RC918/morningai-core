"""
聊天服務層 - 處理 GPT+RAG 整合和對話管理
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta

import openai
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.redis import RedisCache, RateLimiter
from src.models.chat import ChatSession, ChatMessage, ChatKnowledgeBase
from src.models.user import User
from src.models.audit import AuditLog
from src.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval-Augmented Generation) 服務"""
    
    def __init__(self):
        self.cache = RedisCache()
        self.knowledge_cache_ttl = 3600  # 1小時
    
    async def search_knowledge(
        self,
        query: str,
        tenant_id: UUID,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        在知識庫中搜索相關內容
        
        Args:
            query: 搜索查詢
            tenant_id: 租戶ID
            limit: 返回結果數量限制
            similarity_threshold: 相似度閾值
            
        Returns:
            相關知識條目列表
        """
        try:
            # 檢查緩存
            cache_key = f"rag:search:{tenant_id}:{hash(query)}:{limit}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # TODO: 實施向量搜索
            # 這裡應該使用向量數據庫（如 Pinecone, Weaviate, 或 pgvector）
            # 進行語義搜索
            
            # 暫時使用簡單的關鍵詞匹配作為示例
            knowledge_items = await self._simple_keyword_search(
                query, tenant_id, limit
            )
            
            # 緩存結果
            await self.cache.set(
                cache_key,
                json.dumps(knowledge_items, default=str),
                ttl=self.knowledge_cache_ttl
            )
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []
    
    async def _simple_keyword_search(
        self,
        query: str,
        tenant_id: UUID,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        簡單的關鍵詞搜索（示例實現）
        在實際應用中應該替換為向量搜索
        """
        # 這是一個簡化的實現，實際應該使用向量數據庫
        keywords = query.lower().split()
        
        # 模擬知識庫內容
        mock_knowledge = [
            {
                "id": str(uuid4()),
                "title": "產品功能介紹",
                "content": "我們的產品提供聊天、推薦系統、內容管理等功能。",
                "category": "product",
                "relevance_score": 0.9,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": str(uuid4()),
                "title": "使用指南",
                "content": "註冊後可以使用推薦碼邀請朋友，享受聊天功能。",
                "category": "guide",
                "relevance_score": 0.8,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": str(uuid4()),
                "title": "常見問題",
                "content": "如何重置密碼？請聯繫客服或使用忘記密碼功能。",
                "category": "faq",
                "relevance_score": 0.7,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        # 簡單的關鍵詞匹配
        relevant_items = []
        for item in mock_knowledge:
            content_lower = item["content"].lower()
            title_lower = item["title"].lower()
            
            score = 0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 0.3
                if keyword in title_lower:
                    score += 0.5
            
            if score > 0:
                item["relevance_score"] = min(score, 1.0)
                relevant_items.append(item)
        
        # 按相關性排序
        relevant_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return relevant_items[:limit]
    
    async def generate_context(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> str:
        """
        從知識庫條目生成上下文
        
        Args:
            knowledge_items: 知識庫條目列表
            
        Returns:
            格式化的上下文字符串
        """
        if not knowledge_items:
            return ""
        
        context_parts = []
        for item in knowledge_items:
            context_parts.append(
                f"標題: {item['title']}\n"
                f"內容: {item['content']}\n"
                f"相關性: {item['relevance_score']:.2f}\n"
            )
        
        return "\n---\n".join(context_parts)


class GPTService:
    """GPT 服務"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE
        )
        self.cache = RedisCache()
        self.rate_limiter = RateLimiter()
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None,
        user_id: Optional[UUID] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Tuple[str, Dict[str, Any]]:
        """
        生成 GPT 回應
        
        Args:
            messages: 對話歷史
            context: RAG 提供的上下文
            user_id: 用戶ID（用於速率限制）
            temperature: 創造性參數
            max_tokens: 最大令牌數
            
        Returns:
            (回應內容, 元數據)
        """
        try:
            # 速率限制檢查
            if user_id:
                rate_key = f"gpt:rate_limit:{user_id}"
                if not await self.rate_limiter.check_rate_limit(
                    rate_key, limit=20, window=3600  # 每小時20次
                ):
                    raise Exception("GPT API 速率限制超出")
            
            # 構建系統提示
            system_prompt = self._build_system_prompt(context)
            
            # 準備消息
            formatted_messages = [
                {"role": "system", "content": system_prompt}
            ] + messages
            
            # 調用 OpenAI API
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            response_time = time.time() - start_time
            
            # 提取回應內容
            content = response.choices[0].message.content
            
            # 構建元數據
            metadata = {
                "model": settings.OPENAI_MODEL,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_time": response_time,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "has_context": bool(context),
                "context_length": len(context) if context else 0
            }
            
            return content, metadata
            
        except openai.RateLimitError:
            logger.warning("OpenAI API rate limit exceeded")
            raise Exception("API 速率限制超出，請稍後再試")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception("AI 服務暫時不可用，請稍後再試")
        except Exception as e:
            logger.error(f"GPT generation failed: {e}")
            raise
    
    def _build_system_prompt(self, context: Optional[str] = None) -> str:
        """
        構建系統提示
        
        Args:
            context: RAG 提供的上下文
            
        Returns:
            系統提示字符串
        """
        base_prompt = """你是 MorningAI 的智能助手，專門幫助用戶解答問題和提供支援。

請遵循以下原則：
1. 友善、專業、有幫助
2. 回答要準確、簡潔、易懂
3. 如果不確定答案，請誠實說明
4. 優先使用提供的上下文信息
5. 如果需要更多信息才能回答，請主動詢問

回答語言：繁體中文"""
        
        if context:
            base_prompt += f"\n\n相關上下文信息：\n{context}"
        
        return base_prompt
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        分析用戶意圖
        
        Args:
            message: 用戶消息
            
        Returns:
            意圖分析結果
        """
        try:
            # 簡化的意圖分析
            # 在實際應用中可以使用更複雜的 NLP 模型
            
            intent_keywords = {
                "greeting": ["你好", "嗨", "hello", "hi"],
                "question": ["什麼", "如何", "怎麼", "為什麼", "?", "？"],
                "help": ["幫助", "協助", "支援", "help"],
                "complaint": ["問題", "錯誤", "不能", "無法", "故障"],
                "goodbye": ["再見", "拜拜", "bye", "goodbye"]
            }
            
            message_lower = message.lower()
            detected_intents = []
            
            for intent, keywords in intent_keywords.items():
                for keyword in keywords:
                    if keyword in message_lower:
                        detected_intents.append(intent)
                        break
            
            # 如果沒有檢測到特定意圖，默認為問題
            if not detected_intents:
                detected_intents = ["question"]
            
            return {
                "intents": detected_intents,
                "primary_intent": detected_intents[0] if detected_intents else "unknown",
                "confidence": 0.8,  # 簡化的信心分數
                "requires_followup": "question" in detected_intents and len(message.split()) < 3
            }
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                "intents": ["unknown"],
                "primary_intent": "unknown",
                "confidence": 0.0,
                "requires_followup": False
            }


class ChatService:
    """聊天服務主類"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.gpt_service = GPTService()
        self.audit_service = AuditService()
        self.cache = RedisCache()
        self.rate_limiter = RateLimiter()
    
    async def send_message(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        message: str,
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        發送聊天消息並獲取回應
        
        Args:
            db: 數據庫會話
            user_id: 用戶ID
            tenant_id: 租戶ID
            message: 用戶消息
            session_id: 聊天會話ID（可選）
            
        Returns:
            聊天回應結果
        """
        try:
            # 速率限制檢查
            rate_key = f"chat:rate_limit:{user_id}"
            if not await self.rate_limiter.check_rate_limit(
                rate_key, limit=30, window=3600  # 每小時30條消息
            ):
                raise Exception("聊天頻率限制超出，請稍後再試")
            
            # 獲取或創建聊天會話
            session = await self._get_or_create_session(
                db, user_id, tenant_id, session_id
            )
            
            # 保存用戶消息
            user_message = await self._save_message(
                db, session.id, user_id, message, "user"
            )
            
            # 分析用戶意圖
            intent_analysis = await self.gpt_service.analyze_intent(message)
            
            # 獲取對話歷史
            conversation_history = await self._get_conversation_history(
                db, session.id, limit=10
            )
            
            # RAG 知識檢索
            knowledge_items = await self.rag_service.search_knowledge(
                message, tenant_id, limit=3
            )
            
            # 生成上下文
            context = await self.rag_service.generate_context(knowledge_items)
            
            # 準備對話消息
            messages = self._format_conversation_history(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # 生成回應
            response_content, metadata = await self.gpt_service.generate_response(
                messages=messages,
                context=context,
                user_id=user_id
            )
            
            # 保存助手回應
            assistant_message = await self._save_message(
                db, session.id, None, response_content, "assistant", metadata
            )
            
            # 更新會話統計
            await self._update_session_stats(db, session.id)
            
            # 記錄審計日誌
            await self.audit_service.log_action(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                action="chat.send_message",
                resource_type="chat_message",
                resource_id=str(user_message.id),
                details={
                    "session_id": str(session.id),
                    "message_length": len(message),
                    "response_length": len(response_content),
                    "has_rag_context": bool(knowledge_items),
                    "intent": intent_analysis["primary_intent"]
                }
            )
            
            # 構建回應
            result = {
                "session_id": str(session.id),
                "message_id": str(assistant_message.id),
                "response": response_content,
                "intent_analysis": intent_analysis,
                "knowledge_used": len(knowledge_items) > 0,
                "knowledge_items": knowledge_items,
                "metadata": metadata,
                "created_at": assistant_message.created_at.isoformat()
            }
            
            # 檢查是否需要追問
            if intent_analysis.get("requires_followup"):
                followup = await self._generate_followup_question(
                    message, response_content
                )
                if followup:
                    result["followup_question"] = followup
            
            return result
            
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            # 記錄錯誤審計日誌
            await self.audit_service.log_action(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                action="chat.send_message_failed",
                resource_type="chat_message",
                details={
                    "error": str(e),
                    "message_length": len(message)
                }
            )
            raise
    
    async def get_chat_history(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """
        獲取聊天歷史
        
        Args:
            db: 數據庫會話
            user_id: 用戶ID
            session_id: 聊天會話ID
            page: 頁碼
            size: 每頁大小
            
        Returns:
            聊天歷史
        """
        try:
            # 驗證會話所有權
            session = await db.get(ChatSession, session_id)
            if not session or session.user_id != user_id:
                raise Exception("聊天會話不存在或無權限訪問")
            
            # 獲取消息
            offset = (page - 1) * size
            query = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(desc(ChatMessage.created_at))
                .offset(offset)
                .limit(size)
            )
            
            result = await db.execute(query)
            messages = result.scalars().all()
            
            # 獲取總數
            count_query = select(ChatMessage).where(
                ChatMessage.session_id == session_id
            )
            count_result = await db.execute(count_query)
            total = len(count_result.scalars().all())
            
            # 格式化消息
            formatted_messages = []
            for msg in reversed(messages):  # 按時間順序排列
                formatted_messages.append({
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata,
                    "created_at": msg.created_at.isoformat()
                })
            
            return {
                "session_id": str(session_id),
                "messages": formatted_messages,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
            
        except Exception as e:
            logger.error(f"Get chat history failed: {e}")
            raise
    
    async def get_user_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        獲取用戶的聊天會話列表
        
        Args:
            db: 數據庫會話
            user_id: 用戶ID
            page: 頁碼
            size: 每頁大小
            
        Returns:
            會話列表
        """
        try:
            offset = (page - 1) * size
            query = (
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(desc(ChatSession.updated_at))
                .offset(offset)
                .limit(size)
            )
            
            result = await db.execute(query)
            sessions = result.scalars().all()
            
            # 獲取總數
            count_query = select(ChatSession).where(
                ChatSession.user_id == user_id
            )
            count_result = await db.execute(count_query)
            total = len(count_result.scalars().all())
            
            # 格式化會話
            formatted_sessions = []
            for session in sessions:
                formatted_sessions.append({
                    "id": str(session.id),
                    "title": session.title,
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                })
            
            return {
                "sessions": formatted_sessions,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
            
        except Exception as e:
            logger.error(f"Get user sessions failed: {e}")
            raise
    
    async def _get_or_create_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        session_id: Optional[UUID] = None
    ) -> ChatSession:
        """獲取或創建聊天會話"""
        if session_id:
            session = await db.get(ChatSession, session_id)
            if session and session.user_id == user_id:
                return session
        
        # 創建新會話
        session = ChatSession(
            id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            title="新對話",
            message_count=0
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    async def _save_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: Optional[UUID],
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """保存聊天消息"""
        message = ChatMessage(
            id=uuid4(),
            session_id=session_id,
            user_id=user_id,
            content=content,
            role=role,
            metadata=metadata or {}
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        return message
    
    async def _get_conversation_history(
        self,
        db: AsyncSession,
        session_id: UUID,
        limit: int = 10
    ) -> List[ChatMessage]:
        """獲取對話歷史"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return list(reversed(messages))  # 按時間順序排列
    
    def _format_conversation_history(
        self,
        messages: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """格式化對話歷史為 OpenAI 格式"""
        formatted = []
        for msg in messages[:-1]:  # 排除最後一條消息（當前用戶輸入）
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        return formatted
    
    async def _update_session_stats(
        self,
        db: AsyncSession,
        session_id: UUID
    ):
        """更新會話統計"""
        session = await db.get(ChatSession, session_id)
        if session:
            session.message_count += 2  # 用戶消息 + 助手回應
            session.updated_at = datetime.utcnow()
            await db.commit()
    
    async def _generate_followup_question(
        self,
        user_message: str,
        assistant_response: str
    ) -> Optional[str]:
        """生成追問問題"""
        try:
            # 簡化的追問邏輯
            # 在實際應用中可以使用更複雜的 NLP 分析
            
            if len(user_message.split()) < 3:
                followup_templates = [
                    "能否提供更多詳細信息？",
                    "您具體想了解哪個方面？",
                    "有什麼特定的問題需要幫助嗎？"
                ]
                return followup_templates[hash(user_message) % len(followup_templates)]
            
            return None
            
        except Exception as e:
            logger.error(f"Generate followup question failed: {e}")
            return None

