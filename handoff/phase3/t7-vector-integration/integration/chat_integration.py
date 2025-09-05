"""
聊天系統向量整合模組
將向量服務整合到現有的聊天系統中
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .vector_service import VectorService, RAGService, EmbeddingRequest

logger = logging.getLogger(__name__)

class EnhancedChatService:
    """增強的聊天服務 - 整合向量搜索"""
    
    def __init__(self, vector_service: VectorService, rag_service: RAGService):
        self.vector_service = vector_service
        self.rag_service = rag_service
        
        # 配置參數
        self.similarity_threshold = 0.7
        self.max_search_results = 5
        self.confidence_threshold = 0.8
        
    async def process_chat_message(
        self,
        message: str,
        session_id: str,
        user_id: str,
        tenant_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """處理聊天消息 - 整合向量搜索"""
        start_time = datetime.now()
        
        try:
            # 1. 意圖分析
            intent_analysis = await self._analyze_intent(message, context)
            
            # 2. 根據意圖決定處理策略
            if intent_analysis["requires_knowledge_search"]:
                # 需要知識庫搜索
                response_data = await self._handle_knowledge_query(
                    message, user_id, tenant_id, intent_analysis, context
                )
            else:
                # 一般對話，直接使用 GPT
                response_data = await self._handle_general_chat(
                    message, intent_analysis, context
                )
            
            # 3. 後處理
            response_data = await self._post_process_response(
                response_data, message, session_id, user_id, tenant_id
            )
            
            # 4. 記錄處理時間
            total_time = (datetime.now() - start_time).total_seconds()
            response_data["total_processing_time"] = total_time
            
            logger.info(f"聊天消息處理完成: session={session_id}, time={total_time:.3f}s")
            
            return response_data
            
        except Exception as e:
            logger.error(f"處理聊天消息失敗: {e}")
            return await self._generate_error_response(str(e))
    
    async def _analyze_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析用戶意圖"""
        # 簡化的意圖分析 - 實際應用中可以使用更複雜的 NLP 模型
        knowledge_keywords = [
            "定價", "價格", "方案", "功能", "如何", "什麼是", "介紹", 
            "支援", "幫助", "問題", "教學", "使用", "操作"
        ]
        
        requires_knowledge = any(keyword in message for keyword in knowledge_keywords)
        
        # 分析查詢類型
        query_type = "general"
        if any(word in message for word in ["定價", "價格", "方案"]):
            query_type = "pricing"
        elif any(word in message for word in ["功能", "特色", "能力"]):
            query_type = "features"
        elif any(word in message for word in ["支援", "幫助", "問題"]):
            query_type = "support"
        elif any(word in message for word in ["如何", "教學", "操作"]):
            query_type = "tutorial"
        
        return {
            "requires_knowledge_search": requires_knowledge,
            "query_type": query_type,
            "confidence": 0.8,
            "keywords": [word for word in knowledge_keywords if word in message]
        }
    
    async def _handle_knowledge_query(
        self,
        message: str,
        user_id: str,
        tenant_id: str,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """處理需要知識庫的查詢"""
        try:
            # 使用 RAG 服務生成回應
            rag_response = await self.rag_service.generate_rag_response(
                message, tenant_id, user_id, context,
                top_k=self.max_search_results,
                similarity_threshold=self.similarity_threshold
            )
            
            # 增強回應數據
            rag_response.update({
                "intent_analysis": intent_analysis,
                "search_strategy": "rag_enhanced",
                "knowledge_used": len(rag_response.get("sources", [])) > 0
            })
            
            # 如果信心度不足，添加免責聲明
            if rag_response.get("confidence", 0) < self.confidence_threshold:
                rag_response["response"] += "\n\n如需更詳細的信息，建議您聯繫我們的客服團隊。"
                rag_response["has_disclaimer"] = True
            
            return rag_response
            
        except Exception as e:
            logger.error(f"處理知識查詢失敗: {e}")
            return await self._generate_fallback_response(message, context)
    
    async def _handle_general_chat(
        self,
        message: str,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """處理一般聊天"""
        try:
            # 直接使用 GPT 生成回應
            response_data = await self.rag_service._generate_gpt_fallback(message, context)
            
            response_data.update({
                "response_type": "general_chat",
                "intent_analysis": intent_analysis,
                "search_strategy": "direct_gpt",
                "knowledge_used": False,
                "sources": []
            })
            
            return response_data
            
        except Exception as e:
            logger.error(f"處理一般聊天失敗: {e}")
            return await self._generate_error_response(str(e))
    
    async def _post_process_response(
        self,
        response_data: Dict[str, Any],
        original_message: str,
        session_id: str,
        user_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """後處理回應"""
        try:
            # 生成後續問題建議
            follow_up_questions = await self._generate_follow_up_questions(
                original_message, response_data, response_data.get("intent_analysis", {})
            )
            
            response_data["follow_up_questions"] = follow_up_questions
            
            # 添加會話上下文信息
            response_data["session_context"] = {
                "session_id": session_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 計算回應質量分數
            quality_score = await self._calculate_response_quality(response_data)
            response_data["quality_score"] = quality_score
            
            return response_data
            
        except Exception as e:
            logger.warning(f"後處理回應失敗: {e}")
            return response_data
    
    async def _generate_follow_up_questions(
        self,
        original_message: str,
        response_data: Dict[str, Any],
        intent_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成後續問題建議"""
        query_type = intent_analysis.get("query_type", "general")
        
        # 根據查詢類型生成相關問題
        follow_up_map = {
            "pricing": [
                "有沒有免費試用期？",
                "企業版包含哪些額外功能？",
                "可以隨時升級或降級方案嗎？"
            ],
            "features": [
                "這個功能如何使用？",
                "有沒有相關的教學文檔？",
                "支援哪些整合方式？"
            ],
            "support": [
                "客服的服務時間是什麼？",
                "有沒有線上幫助文檔？",
                "如何提交技術支援請求？"
            ],
            "tutorial": [
                "有沒有詳細的操作指南？",
                "是否提供培訓服務？",
                "有沒有視頻教學？"
            ]
        }
        
        return follow_up_map.get(query_type, [
            "還有其他問題嗎？",
            "需要更多詳細信息嗎？",
            "我還能幫您什麼？"
        ])[:3]  # 最多返回3個問題
    
    async def _calculate_response_quality(self, response_data: Dict[str, Any]) -> float:
        """計算回應質量分數"""
        score = 0.5  # 基礎分數
        
        # 根據回應類型調整
        response_type = response_data.get("response_type", "")
        if response_type == "rag":
            score += 0.3  # RAG 回應通常質量較高
        elif response_type == "gpt_fallback":
            score += 0.1
        
        # 根據信心度調整
        confidence = response_data.get("confidence", 0)
        score += confidence * 0.2
        
        # 根據知識庫使用情況調整
        if response_data.get("knowledge_used", False):
            score += 0.1
        
        # 根據來源數量調整
        sources_count = len(response_data.get("sources", []))
        if sources_count > 0:
            score += min(sources_count * 0.05, 0.15)
        
        return min(score, 1.0)  # 最高1.0
    
    async def _generate_fallback_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成備用回應"""
        return {
            "response": "抱歉，我現在無法處理您的問題。請稍後再試，或聯繫我們的客服團隊獲取幫助。",
            "response_type": "error_fallback",
            "confidence": 0.3,
            "processing_time": 0.1,
            "sources": [],
            "knowledge_used": False,
            "has_disclaimer": True
        }
    
    async def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """生成錯誤回應"""
        return {
            "response": "系統暫時無法處理您的請求，請稍後再試。",
            "response_type": "system_error",
            "confidence": 0.0,
            "processing_time": 0.1,
            "sources": [],
            "knowledge_used": False,
            "error": error_message,
            "has_disclaimer": True
        }
    
    async def add_knowledge_to_vector_db(
        self,
        title: str,
        content: str,
        source: str,
        tenant_id: str,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加知識到向量數據庫"""
        try:
            request = EmbeddingRequest(
                text=content,
                title=title,
                source=source,
                url=url,
                metadata=metadata
            )
            
            vector_id = await self.vector_service.add_knowledge_vector(request, tenant_id)
            
            logger.info(f"成功添加知識到向量數據庫: {vector_id}")
            return vector_id
            
        except Exception as e:
            logger.error(f"添加知識到向量數據庫失敗: {e}")
            raise
    
    async def search_knowledge(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        search_type: str = "semantic",
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """搜索知識庫"""
        try:
            if search_type == "hybrid":
                results = await self.vector_service.hybrid_search(
                    query, tenant_id, user_id, top_k, similarity_threshold
                )
            else:
                results = await self.vector_service.semantic_search(
                    query, tenant_id, user_id, top_k, similarity_threshold
                )
            
            # 轉換為 API 響應格式
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "title": result.title,
                    "content": result.content,
                    "chunk_text": result.chunk_text,
                    "source": result.source,
                    "url": result.url,
                    "similarity_score": result.similarity_score,
                    "chunk_index": result.chunk_index,
                    "created_at": result.created_at.isoformat(),
                    "metadata": result.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索知識庫失敗: {e}")
            raise
    
    async def get_chat_analytics(self, tenant_id: str, days: int = 7) -> Dict[str, Any]:
        """獲取聊天分析數據"""
        try:
            # 獲取向量搜索分析
            search_analytics = await self.vector_service.get_search_analytics(tenant_id, days)
            
            # 獲取向量統計
            vector_stats = await self.vector_service.get_vector_stats(tenant_id)
            
            return {
                "search_analytics": search_analytics,
                "vector_stats": vector_stats,
                "period_days": days,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"獲取聊天分析數據失敗: {e}")
            raise


class KnowledgeManagementService:
    """知識管理服務"""
    
    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
    
    async def bulk_import_knowledge(
        self,
        knowledge_items: List[Dict[str, Any]],
        tenant_id: str
    ) -> Dict[str, Any]:
        """批量導入知識"""
        results = {
            "total": len(knowledge_items),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, item in enumerate(knowledge_items):
            try:
                request = EmbeddingRequest(
                    text=item["content"],
                    title=item["title"],
                    source=item.get("source", "bulk_import"),
                    url=item.get("url"),
                    metadata=item.get("metadata", {})
                )
                
                vector_id = await self.vector_service.add_knowledge_vector(request, tenant_id)
                results["success"] += 1
                
                logger.info(f"批量導入進度: {i+1}/{len(knowledge_items)} - {vector_id}")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "title": item.get("title", "未知"),
                    "error": str(e)
                })
                logger.error(f"批量導入失敗 [{i}]: {e}")
        
        logger.info(f"批量導入完成: 成功 {results['success']}, 失敗 {results['failed']}")
        return results
    
    async def sync_cms_to_vectors(self, tenant_id: str, cms_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """同步 CMS 內容到向量數據庫"""
        results = {
            "processed": 0,
            "added": 0,
            "updated": 0,
            "errors": []
        }
        
        for post in cms_posts:
            try:
                # 檢查是否已存在
                existing_vectors = await self._find_existing_vectors(post["id"], tenant_id)
                
                request = EmbeddingRequest(
                    text=post["content"],
                    title=post["title"],
                    source="cms",
                    url=post.get("url"),
                    metadata={
                        "cms_post_id": post["id"],
                        "language": post.get("language", "zh-TW"),
                        "category": post.get("category"),
                        "tags": post.get("tags", [])
                    }
                )
                
                if existing_vectors:
                    # 更新現有向量
                    for vector_id in existing_vectors:
                        await self.vector_service.update_knowledge_vector(vector_id, request)
                    results["updated"] += 1
                else:
                    # 添加新向量
                    await self.vector_service.add_knowledge_vector(request, tenant_id)
                    results["added"] += 1
                
                results["processed"] += 1
                
            except Exception as e:
                results["errors"].append({
                    "post_id": post.get("id"),
                    "title": post.get("title", "未知"),
                    "error": str(e)
                })
                logger.error(f"同步 CMS 內容失敗: {e}")
        
        return results
    
    async def _find_existing_vectors(self, cms_post_id: str, tenant_id: str) -> List[str]:
        """查找現有的向量 ID"""
        # 這裡需要實現查找邏輯，暫時返回空列表
        return []


# 使用示例和測試
async def test_integration():
    """測試整合功能"""
    # 配置
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/morningai"
    OPENAI_API_KEY = "your-openai-api-key"
    
    # 初始化服務
    vector_service = VectorService(DATABASE_URL, OPENAI_API_KEY)
    await vector_service.initialize()
    
    rag_service = RAGService(vector_service, OPENAI_API_KEY)
    chat_service = EnhancedChatService(vector_service, rag_service)
    
    try:
        # 1. 添加測試知識
        await chat_service.add_knowledge_to_vector_db(
            title="MorningAI 定價方案",
            content="MorningAI 提供三種定價方案：基礎版每月99元，包含基本聊天功能；專業版每月299元，包含高級分析和API訪問；企業版每月999元，包含所有功能和專屬支援。",
            source="pricing_page",
            tenant_id="demo-tenant",
            url="https://morningai.com/pricing"
        )
        
        # 2. 測試聊天處理
        response = await chat_service.process_chat_message(
            message="請介紹你們的定價方案",
            session_id="test-session",
            user_id="test-user",
            tenant_id="demo-tenant"
        )
        
        print("=== 聊天回應 ===")
        print(f"回應: {response['response']}")
        print(f"類型: {response['response_type']}")
        print(f"信心度: {response['confidence']}")
        print(f"處理時間: {response['total_processing_time']:.3f}s")
        print(f"來源數量: {len(response['sources'])}")
        
        # 3. 測試知識搜索
        search_results = await chat_service.search_knowledge(
            query="定價",
            tenant_id="demo-tenant",
            user_id="test-user"
        )
        
        print(f"\n=== 知識搜索 ===")
        print(f"找到 {len(search_results)} 個結果")
        for result in search_results:
            print(f"- {result['title']}: {result['similarity_score']:.3f}")
        
        # 4. 測試分析數據
        analytics = await chat_service.get_chat_analytics("demo-tenant")
        print(f"\n=== 分析數據 ===")
        print(f"向量總數: {analytics['vector_stats']['total_vectors']}")
        print(f"搜索總數: {analytics['search_analytics']['total_searches']}")
        
    finally:
        await vector_service.close()

if __name__ == "__main__":
    asyncio.run(test_integration())

