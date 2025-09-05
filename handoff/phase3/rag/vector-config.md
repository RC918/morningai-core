# RAG 向量數據庫配置文檔

## 概述

本文檔描述 MorningAI 聊天模組的 RAG (Retrieval-Augmented Generation) 系統中向量數據庫的配置、選型和實施方案。

## 向量數據庫選型

### 推薦方案：pgvector (PostgreSQL 擴展)

**選擇理由：**
- ✅ 與現有 PostgreSQL 數據庫整合
- ✅ 成熟穩定，生產環境驗證
- ✅ 支援多種向量相似度算法
- ✅ 原生 SQL 查詢支援
- ✅ 開源免費，無額外成本
- ✅ 支援混合查詢（向量 + 傳統過濾）

**技術規格：**
- 向量維度：1536 (OpenAI text-embedding-ada-002)
- 相似度算法：cosine, L2, inner product
- 索引類型：IVFFlat, HNSW
- 最大向量數：10M+ (單表)

### 備選方案

#### 1. Pinecone (託管服務)
- ✅ 專業向量數據庫
- ✅ 高性能和可擴展性
- ❌ 額外成本 ($70+/月)
- ❌ 數據外部託管
- ❌ 供應商鎖定風險

#### 2. Weaviate (開源)
- ✅ 功能豐富
- ✅ GraphQL API
- ❌ 額外基礎設施
- ❌ 學習成本較高
- ❌ 資源消耗較大

#### 3. Chroma (輕量級)
- ✅ 簡單易用
- ✅ Python 原生
- ❌ 生產環境成熟度
- ❌ 擴展性限制
- ❌ 企業級功能不足

## 實施架構

### 數據流程

```
文檔輸入 → 文本切片 → 向量化 → 存儲索引 → 檢索查詢 → 上下文生成
```

### 系統組件

1. **文檔處理器** - 文檔解析和預處理
2. **文本切片器** - 智能分段和重疊處理
3. **向量化服務** - OpenAI Embedding API 調用
4. **向量存儲** - pgvector 數據庫
5. **檢索引擎** - 相似度搜索和排序
6. **上下文生成器** - 結果格式化和引用

## 數據庫架構

### 核心表結構

```sql
-- 知識庫文檔表
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    source_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- 文檔切片表 (向量存儲)
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- OpenAI ada-002 維度
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 向量索引
CREATE INDEX ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON knowledge_chunks USING hnsw (embedding vector_l2_ops);

-- 複合索引
CREATE INDEX idx_chunks_tenant_active ON knowledge_chunks(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX idx_chunks_document ON knowledge_chunks(document_id);
```

### 索引策略

```sql
-- HNSW 索引 (推薦用於生產環境)
CREATE INDEX idx_chunks_embedding_hnsw ON knowledge_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- IVFFlat 索引 (適用於較小數據集)
CREATE INDEX idx_chunks_embedding_ivf ON knowledge_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

## 配置參數

### 文本切片配置

```json
{
  "chunking": {
    "strategy": "recursive_character",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "separators": ["\n\n", "\n", "。", ".", " "],
    "min_chunk_size": 100,
    "max_chunk_size": 1500
  }
}
```

### 向量化配置

```json
{
  "embedding": {
    "model": "text-embedding-ada-002",
    "api_base": "https://api.openai.com/v1",
    "batch_size": 100,
    "retry_attempts": 3,
    "timeout_seconds": 30
  }
}
```

### 檢索配置

```json
{
  "retrieval": {
    "similarity_threshold": 0.7,
    "max_results": 5,
    "rerank_enabled": true,
    "hybrid_search": {
      "enabled": true,
      "vector_weight": 0.7,
      "keyword_weight": 0.3
    }
  }
}
```

## 性能優化

### 索引優化

1. **HNSW 參數調優**
   ```sql
   -- 高精度配置 (較慢但更準確)
   WITH (m = 32, ef_construction = 128)
   
   -- 平衡配置 (推薦)
   WITH (m = 16, ef_construction = 64)
   
   -- 高速配置 (較快但精度略低)
   WITH (m = 8, ef_construction = 32)
   ```

2. **查詢優化**
   ```sql
   -- 設置查詢時的 ef 參數
   SET hnsw.ef_search = 100;
   
   -- 混合查詢範例
   SELECT 
       c.content,
       c.embedding <=> %s::vector AS distance,
       d.title,
       d.category
   FROM knowledge_chunks c
   JOIN knowledge_documents d ON c.document_id = d.id
   WHERE c.tenant_id = %s
     AND d.is_active = true
     AND c.embedding <=> %s::vector < 0.3
   ORDER BY c.embedding <=> %s::vector
   LIMIT 5;
   ```

### 緩存策略

1. **查詢結果緩存**
   - Redis 緩存相似查詢結果
   - TTL: 1小時
   - 緩存鍵: `rag:search:{tenant_id}:{query_hash}`

2. **向量緩存**
   - 緩存常用文檔的向量
   - 減少重複計算
   - 內存緩存 + Redis 持久化

## 部署配置

### Docker Compose 配置

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: morningai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    command: >
      postgres
      -c shared_preload_libraries=vector
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
```

### 初始化腳本

```sql
-- init-scripts/01-enable-vector.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 設置向量相關參數
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';

-- 重載配置
SELECT pg_reload_conf();
```

## 監控和維護

### 性能監控

```sql
-- 查看索引使用情況
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'knowledge_chunks';

-- 查看表大小
SELECT 
    pg_size_pretty(pg_total_relation_size('knowledge_chunks')) as total_size,
    pg_size_pretty(pg_relation_size('knowledge_chunks')) as table_size,
    pg_size_pretty(pg_indexes_size('knowledge_chunks')) as indexes_size;
```

### 維護任務

1. **定期重建索引**
   ```sql
   REINDEX INDEX CONCURRENTLY idx_chunks_embedding_hnsw;
   ```

2. **統計信息更新**
   ```sql
   ANALYZE knowledge_chunks;
   ```

3. **清理過期數據**
   ```sql
   DELETE FROM knowledge_chunks 
   WHERE document_id IN (
       SELECT id FROM knowledge_documents 
       WHERE is_active = false 
         AND updated_at < NOW() - INTERVAL '30 days'
   );
   ```

## 安全考量

### 數據隔離

- 所有查詢必須包含 `tenant_id` 過濾
- 行級安全策略 (RLS) 強制租戶隔離
- 向量數據加密存儲

### 訪問控制

```sql
-- 創建 RLS 策略
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_chunks ON knowledge_chunks
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

## 故障排除

### 常見問題

1. **向量維度不匹配**
   ```
   ERROR: vector dimension mismatch
   解決：確保所有向量都是 1536 維度
   ```

2. **索引構建失敗**
   ```
   ERROR: insufficient memory
   解決：增加 work_mem 或分批處理
   ```

3. **查詢性能差**
   ```
   解決：調整 hnsw.ef_search 參數或重建索引
   ```

### 調試查詢

```sql
-- 查看查詢計劃
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM knowledge_chunks 
WHERE embedding <=> %s::vector < 0.3 
ORDER BY embedding <=> %s::vector 
LIMIT 5;

-- 查看索引統計
SELECT * FROM pg_stat_user_indexes 
WHERE indexrelname LIKE '%embedding%';
```

## 遷移和升級

### 版本升級

1. **pgvector 升級**
   ```sql
   ALTER EXTENSION vector UPDATE;
   ```

2. **索引重建**
   ```sql
   DROP INDEX CONCURRENTLY idx_chunks_embedding_hnsw;
   CREATE INDEX CONCURRENTLY idx_chunks_embedding_hnsw_new 
   ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
   ```

### 數據遷移

```python
# 批量向量化現有文檔
async def migrate_existing_documents():
    documents = await get_unprocessed_documents()
    for doc in documents:
        chunks = chunk_document(doc.content)
        for chunk in chunks:
            embedding = await get_embedding(chunk.content)
            await save_chunk(doc.id, chunk, embedding)
```

## 最佳實踐

1. **文檔預處理**
   - 清理 HTML 標籤和特殊字符
   - 統一編碼格式 (UTF-8)
   - 移除重複內容

2. **切片策略**
   - 保持語義完整性
   - 適當的重疊避免信息丟失
   - 考慮文檔結構 (標題、段落)

3. **向量管理**
   - 定期更新過時內容
   - 監控向量質量
   - 批量處理提高效率

4. **查詢優化**
   - 使用適當的相似度閾值
   - 結合關鍵詞過濾
   - 實施結果重排序

---

**配置版本：** v1.0  
**最後更新：** 2025-01-05  
**負責人：** 技術團隊

