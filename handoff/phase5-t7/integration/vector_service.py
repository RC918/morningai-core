"""
向量服務整合模組
實現 pgvector 與聊天系統的完整整合
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncpg
import openai
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchResult:
    """向量搜索結果"""
    id: str
    title: str
    content: str
    source: str
    url: Optional[str]
    similarity_score: float
    chunk_index: int
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class EmbeddingRequest:
    """嵌入請求"""
    text: str
    source: str
    title: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class VectorService:
    """向量服務 - pgvector 整合"""
    
    def __init__(self, database_url: str, openai_api_key: str):
        self.database_url = database_url
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimension = 1536
        self.pool = None
        
    async def initialize(self):
        """初始化向量服務"""
        logger.info("初始化向量服務...")
        
        # 創建連接池
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        
        # 確保 pgvector 擴展已安裝
        await self._ensure_pgvector_extension()
        
        # 創建向量表
        await self._create_vector_tables()
        
        logger.info("向量服務初始化完成")
    
    async def _ensure_pgvector_extension(self):
        """確保 pgvector 擴展已安裝"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("pgvector 擴展已啟用")
            except Exception as e:
                logger.error(f"啟用 pgvector 擴展失敗: {e}")
                raise
    
    async def _create_vector_tables(self):
        """創建向量相關表"""
        async with self.pool.acquire() as conn:
            # 知識庫向量表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS knowledge_vectors (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    knowledge_id UUID REFERENCES cms_posts(id) ON DELETE CASCADE,
                    tenant_id UUID NOT NULL REFERENCES tenants(id),
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    embedding vector({self.embedding_dimension}),
                    source TEXT,
                    url TEXT,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 創建向量索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_vectors_embedding_idx 
                ON knowledge_vectors USING hnsw (embedding vector_cosine_ops);
            """)
            
            # 創建其他索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_vectors_tenant_idx 
                ON knowledge_vectors(tenant_id);
                
                CREATE INDEX IF NOT EXISTS knowledge_vectors_knowledge_idx 
                ON knowledge_vectors(knowledge_id);
                
                CREATE INDEX IF NOT EXISTS knowledge_vectors_created_idx 
                ON knowledge_vectors(created_at DESC);
            """)
            
            # 搜索歷史表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS vector_search_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    tenant_id UUID NOT NULL REFERENCES tenants(id),
                    query_text TEXT NOT NULL,
                    query_embedding vector({self.embedding_dimension}),
                    results_count INTEGER NOT NULL DEFAULT 0,
                    search_time FLOAT NOT NULL DEFAULT 0,
                    similarity_threshold FLOAT NOT NULL DEFAULT 0.7,
                    search_type VARCHAR(20) NOT NULL DEFAULT 'semantic',
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS vector_search_history_user_idx 
                ON vector_search_history(user_id);
                
                CREATE INDEX IF NOT EXISTS vector_search_history_created_idx 
                ON vector_search_history(created_at DESC);
            """)
            
            logger.info("向量表創建完成")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        try:
            # 清理和預處理文本
            cleaned_text = self._preprocess_text(text)
            
            # 調用 OpenAI Embedding API
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=cleaned_text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # 驗證向量維度
            if len(embedding) != self.embedding_dimension:
                raise ValueError(f"嵌入向量維度不匹配: 期望 {self.embedding_dimension}, 實際 {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入向量失敗: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """預處理文本"""
        # 移除多餘空白
        text = ' '.join(text.split())
        
        # 限制長度 (OpenAI 限制)
        max_length = 8000
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"文本被截斷到 {max_length} 字符")
        
        return text
    
    async def add_knowledge_vector(self, request: EmbeddingRequest, tenant_id: str) -> str:
        """添加知識庫向量"""
        try:
            # 文檔切片
            chunks = self._chunk_text(request.text)
            
            # 生成向量 ID
            vector_ids = []
            
            async with self.pool.acquire() as conn:
                for i, chunk in enumerate(chunks):
                    # 生成嵌入向量
                    embedding = await self.generate_embedding(chunk)
                    
                    # 插入向量數據
                    vector_id = await conn.fetchval("""
                        INSERT INTO knowledge_vectors 
                        (tenant_id, title, content, chunk_text, chunk_index, embedding, source, url, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                    """, 
                    tenant_id, request.title, request.text, chunk, i, 
                    embedding, request.source, request.url, 
                    json.dumps(request.metadata or {}))
                    
                    vector_ids.append(str(vector_id))
                    
                    logger.info(f"添加向量塊 {i+1}/{len(chunks)}: {vector_id}")
            
            logger.info(f"成功添加 {len(chunks)} 個向量塊")
            return vector_ids[0]  # 返回第一個塊的 ID
            
        except Exception as e:
            logger.error(f"添加知識庫向量失敗: {e}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """文檔切片"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 如果不是最後一塊，嘗試在句號處切分
            if end < len(text):
                # 尋找最近的句號
                period_pos = text.rfind('.', start, end)
                if period_pos > start + chunk_size // 2:
                    end = period_pos + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 計算下一塊的起始位置 (考慮重疊)
            start = max(start + chunk_size - overlap, end)
            
            if start >= len(text):
                break
        
        logger.info(f"文檔切分為 {len(chunks)} 塊")
        return chunks
    
    async def semantic_search(
        self, 
        query: str, 
        tenant_id: str,
        user_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        search_type: str = "semantic"
    ) -> List[VectorSearchResult]:
        """語義搜索"""
        start_time = datetime.now()
        
        try:
            # 生成查詢向量
            query_embedding = await self.generate_embedding(query)
            
            # 執行向量搜索
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id,
                        title,
                        content,
                        chunk_text,
                        chunk_index,
                        source,
                        url,
                        metadata,
                        created_at,
                        1 - (embedding <=> $1::vector) as similarity_score
                    FROM knowledge_vectors
                    WHERE tenant_id = $2
                        AND 1 - (embedding <=> $1::vector) >= $3
                    ORDER BY embedding <=> $1::vector
                    LIMIT $4
                """, query_embedding, tenant_id, similarity_threshold, top_k)
                
                # 轉換結果
                results = []
                for row in rows:
                    result = VectorSearchResult(
                        id=str(row['id']),
                        title=row['title'],
                        content=row['content'],
                        source=row['source'] or '',
                        url=row['url'],
                        similarity_score=float(row['similarity_score']),
                        chunk_index=row['chunk_index'],
                        metadata=row['metadata'] or {},
                        created_at=row['created_at']
                    )
                    results.append(result)
                
                # 記錄搜索歷史
                search_time = (datetime.now() - start_time).total_seconds()
                await self._record_search_history(
                    conn, user_id, tenant_id, query, query_embedding,
                    len(results), search_time, similarity_threshold, search_type
                )
                
                logger.info(f"語義搜索完成: 查詢='{query}', 結果數={len(results)}, 耗時={search_time:.3f}s")
                return results
                
        except Exception as e:
            logger.error(f"語義搜索失敗: {e}")
            raise
    
    async def _record_search_history(
        self, conn, user_id: str, tenant_id: str, query: str, 
        query_embedding: List[float], results_count: int, 
        search_time: float, similarity_threshold: float, search_type: str
    ):
        """記錄搜索歷史"""
        try:
            await conn.execute("""
                INSERT INTO vector_search_history 
                (user_id, tenant_id, query_text, query_embedding, results_count, 
                 search_time, similarity_threshold, search_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, user_id, tenant_id, query, query_embedding, results_count,
            search_time, similarity_threshold, search_type)
        except Exception as e:
            logger.warning(f"記錄搜索歷史失敗: {e}")
    
    async def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> List[VectorSearchResult]:
        """混合搜索 (語義 + 關鍵詞)"""
        try:
            # 語義搜索
            semantic_results = await self.semantic_search(
                query, tenant_id, user_id, top_k * 2, similarity_threshold, "hybrid"
            )
            
            # 關鍵詞搜索
            keyword_results = await self._keyword_search(query, tenant_id, top_k * 2)
            
            # 合併和重新排序結果
            combined_results = self._combine_search_results(
                semantic_results, keyword_results, 
                semantic_weight, keyword_weight
            )
            
            # 返回前 top_k 個結果
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"混合搜索失敗: {e}")
            raise
    
    async def _keyword_search(self, query: str, tenant_id: str, top_k: int) -> List[VectorSearchResult]:
        """關鍵詞搜索"""
        async with self.pool.acquire() as conn:
            # 使用 PostgreSQL 全文搜索
            rows = await conn.fetch("""
                SELECT 
                    id, title, content, chunk_text, chunk_index, source, url, metadata, created_at,
                    ts_rank_cd(to_tsvector('english', chunk_text), plainto_tsquery('english', $1)) as rank
                FROM knowledge_vectors
                WHERE tenant_id = $2
                    AND to_tsvector('english', chunk_text) @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $3
            """, query, tenant_id, top_k)
            
            results = []
            for row in rows:
                result = VectorSearchResult(
                    id=str(row['id']),
                    title=row['title'],
                    content=row['content'],
                    source=row['source'] or '',
                    url=row['url'],
                    similarity_score=float(row['rank']),  # 使用 rank 作為相似度
                    chunk_index=row['chunk_index'],
                    metadata=row['metadata'] or {},
                    created_at=row['created_at']
                )
                results.append(result)
            
            return results
    
    def _combine_search_results(
        self, 
        semantic_results: List[VectorSearchResult],
        keyword_results: List[VectorSearchResult],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[VectorSearchResult]:
        """合併搜索結果"""
        # 創建結果字典
        combined = {}
        
        # 添加語義搜索結果
        for result in semantic_results:
            combined[result.id] = result
            # 設置組合分數
            result.similarity_score = result.similarity_score * semantic_weight
        
        # 添加關鍵詞搜索結果
        for result in keyword_results:
            if result.id in combined:
                # 合併分數
                combined[result.id].similarity_score += result.similarity_score * keyword_weight
            else:
                result.similarity_score = result.similarity_score * keyword_weight
                combined[result.id] = result
        
        # 按分數排序
        sorted_results = sorted(combined.values(), key=lambda x: x.similarity_score, reverse=True)
        
        return sorted_results
    
    async def get_search_analytics(self, tenant_id: str, days: int = 7) -> Dict[str, Any]:
        """獲取搜索分析數據"""
        async with self.pool.acquire() as conn:
            # 搜索統計
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_searches,
                    AVG(search_time) as avg_search_time,
                    AVG(results_count) as avg_results_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM vector_search_history
                WHERE tenant_id = $1 
                    AND created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            """ % days, tenant_id)
            
            # 熱門查詢
            popular_queries = await conn.fetch("""
                SELECT query_text, COUNT(*) as count
                FROM vector_search_history
                WHERE tenant_id = $1 
                    AND created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                GROUP BY query_text
                ORDER BY count DESC
                LIMIT 10
            """ % days, tenant_id)
            
            # 搜索類型分布
            search_types = await conn.fetch("""
                SELECT search_type, COUNT(*) as count
                FROM vector_search_history
                WHERE tenant_id = $1 
                    AND created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                GROUP BY search_type
            """ % days, tenant_id)
            
            return {
                "total_searches": stats['total_searches'],
                "avg_search_time": float(stats['avg_search_time'] or 0),
                "avg_results_count": float(stats['avg_results_count'] or 0),
                "unique_users": stats['unique_users'],
                "popular_queries": [
                    {"query": row['query_text'], "count": row['count']} 
                    for row in popular_queries
                ],
                "search_type_distribution": [
                    {"type": row['search_type'], "count": row['count']} 
                    for row in search_types
                ]
            }
    
    async def update_knowledge_vector(self, vector_id: str, request: EmbeddingRequest) -> bool:
        """更新知識庫向量"""
        try:
            # 生成新的嵌入向量
            embedding = await self.generate_embedding(request.text)
            
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE knowledge_vectors 
                    SET title = $2, content = $3, chunk_text = $3, embedding = $4, 
                        source = $5, url = $6, metadata = $7, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, vector_id, request.title, request.text, embedding,
                request.source, request.url, json.dumps(request.metadata or {}))
                
                return result == "UPDATE 1"
                
        except Exception as e:
            logger.error(f"更新知識庫向量失敗: {e}")
            raise
    
    async def delete_knowledge_vector(self, vector_id: str) -> bool:
        """刪除知識庫向量"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM knowledge_vectors WHERE id = $1
                """, vector_id)
                
                return result == "DELETE 1"
                
        except Exception as e:
            logger.error(f"刪除知識庫向量失敗: {e}")
            raise
    
    async def get_vector_stats(self, tenant_id: str) -> Dict[str, Any]:
        """獲取向量統計信息"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_vectors,
                    COUNT(DISTINCT knowledge_id) as unique_documents,
                    AVG(LENGTH(chunk_text)) as avg_chunk_length,
                    MIN(created_at) as oldest_vector,
                    MAX(created_at) as newest_vector
                FROM knowledge_vectors
                WHERE tenant_id = $1
            """, tenant_id)
            
            return {
                "total_vectors": stats['total_vectors'],
                "unique_documents": stats['unique_documents'],
                "avg_chunk_length": float(stats['avg_chunk_length'] or 0),
                "oldest_vector": stats['oldest_vector'],
                "newest_vector": stats['newest_vector']
            }
    
    async def close(self):
        """關閉向量服務"""
        if self.pool:
            await self.pool.close()
            logger.info("向量服務已關閉")


class RAGService:
    """RAG 服務 - 整合向量搜索和 GPT 生成"""
    
    def __init__(self, vector_service: VectorService, openai_api_key: str):
        self.vector_service = vector_service
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.gpt_model = "gpt-4"
    
    async def generate_rag_response(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """生成 RAG 回應"""
        try:
            # 1. 向量搜索
            search_results = await self.vector_service.semantic_search(
                query, tenant_id, user_id, top_k, similarity_threshold
            )
            
            # 2. 構建上下文
            if search_results:
                # 有相關結果，使用 RAG
                response_data = await self._generate_rag_with_context(
                    query, search_results, context
                )
                response_data["response_type"] = "rag"
                response_data["sources"] = [
                    {
                        "title": result.title,
                        "url": result.url,
                        "content": result.chunk_text[:200] + "..." if len(result.chunk_text) > 200 else result.chunk_text,
                        "relevance": result.similarity_score
                    }
                    for result in search_results
                ]
            else:
                # 無相關結果，使用 GPT fallback
                response_data = await self._generate_gpt_fallback(query, context)
                response_data["response_type"] = "gpt_fallback"
                response_data["sources"] = []
            
            return response_data
            
        except Exception as e:
            logger.error(f"生成 RAG 回應失敗: {e}")
            raise
    
    async def _generate_rag_with_context(
        self,
        query: str,
        search_results: List[VectorSearchResult],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """基於搜索結果生成 RAG 回應"""
        # 構建上下文
        context_text = "\n\n".join([
            f"來源: {result.title}\n內容: {result.chunk_text}"
            for result in search_results[:3]  # 只使用前3個最相關的結果
        ])
        
        # 構建提示詞
        system_prompt = f"""
你是 MorningAI 的智能助手。請基於以下知識庫內容回答用戶問題。

知識庫內容：
{context_text}

回答要求：
1. 基於提供的知識庫內容回答
2. 如果知識庫內容不足以完整回答，請說明並提供一般性建議
3. 保持友善和專業的語調
4. 使用繁體中文回答
"""
        
        # 調用 GPT
        start_time = datetime.now()
        
        response = await self.openai_client.chat.completions.create(
            model=self.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "response": response.choices[0].message.content,
            "confidence": 0.9,  # RAG 回應通常有較高信心
            "processing_time": processing_time,
            "token_usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def _generate_gpt_fallback(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """GPT fallback 回應"""
        system_prompt = """
你是 MorningAI 的智能助手。由於知識庫中沒有找到相關信息，請基於你的一般知識回答用戶問題。

回答要求：
1. 承認知識庫中沒有找到相關信息
2. 提供一般性的幫助和建議
3. 建議用戶聯繫客服獲取更詳細信息
4. 保持友善和專業的語調
5. 使用繁體中文回答
"""
        
        start_time = datetime.now()
        
        response = await self.openai_client.chat.completions.create(
            model=self.gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "response": response.choices[0].message.content,
            "confidence": 0.6,  # Fallback 回應信心較低
            "processing_time": processing_time,
            "token_usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }


# 使用示例
async def main():
    """測試向量服務"""
    # 配置
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/morningai"
    OPENAI_API_KEY = "your-openai-api-key"
    
    # 初始化服務
    vector_service = VectorService(DATABASE_URL, OPENAI_API_KEY)
    await vector_service.initialize()
    
    rag_service = RAGService(vector_service, OPENAI_API_KEY)
    
    try:
        # 測試添加知識
        request = EmbeddingRequest(
            text="MorningAI 提供三種定價方案：基礎版每月99元、專業版每月299元、企業版每月999元。",
            title="定價方案",
            source="pricing_page",
            url="https://morningai.com/pricing"
        )
        
        vector_id = await vector_service.add_knowledge_vector(request, "demo-tenant-id")
        print(f"添加向量成功: {vector_id}")
        
        # 測試搜索
        results = await vector_service.semantic_search(
            "定價方案是什麼", "demo-tenant-id", "demo-user-id"
        )
        
        print(f"搜索結果: {len(results)} 個")
        for result in results:
            print(f"- {result.title}: {result.similarity_score:.3f}")
        
        # 測試 RAG 回應
        rag_response = await rag_service.generate_rag_response(
            "請介紹你們的定價方案", "demo-tenant-id", "demo-user-id"
        )
        
        print(f"RAG 回應: {rag_response['response']}")
        print(f"回應類型: {rag_response['response_type']}")
        
    finally:
        await vector_service.close()

if __name__ == "__main__":
    asyncio.run(main())

