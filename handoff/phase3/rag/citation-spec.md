# RAG 引用規格文檔

## 概述

本文檔定義 MorningAI 聊天模組中 RAG (Retrieval-Augmented Generation) 系統的引用 (Citation) 格式、實施標準和最佳實踐。引用功能確保 AI 回應的可追溯性和可信度。

## 引用格式標準

### 基本引用格式

```json
{
  "citation_id": "cite_001",
  "source_type": "knowledge_base",
  "title": "推薦碼使用指南",
  "content_snippet": "推薦碼是邀請朋友的專用代碼，每個用戶可以生成唯一推薦碼...",
  "relevance_score": 0.95,
  "chunk_id": "chunk_12345",
  "document_id": "doc_67890",
  "url": "https://help.morningai.com/referral-guide",
  "created_at": "2025-01-01T10:00:00Z",
  "metadata": {
    "category": "guide",
    "tags": ["推薦碼", "邀請", "獎勵"],
    "author": "產品團隊",
    "last_updated": "2024-12-15T09:00:00Z"
  }
}
```

### 引用類型

#### 1. 知識庫引用 (Knowledge Base Citation)

```json
{
  "citation_id": "kb_001",
  "source_type": "knowledge_base",
  "title": "產品功能介紹",
  "content_snippet": "MorningAI 提供智能聊天、推薦系統、內容管理等核心功能...",
  "relevance_score": 0.92,
  "chunk_id": "chunk_kb_001",
  "document_id": "doc_product_intro",
  "category": "product_info",
  "confidence": "high"
}
```

#### 2. 外部連結引用 (External Link Citation)

```json
{
  "citation_id": "ext_001", 
  "source_type": "external_link",
  "title": "官方文檔 - API 使用指南",
  "content_snippet": "API 調用需要包含有效的認證令牌...",
  "url": "https://docs.morningai.com/api-guide",
  "domain": "docs.morningai.com",
  "relevance_score": 0.88,
  "access_date": "2025-01-05T14:30:00Z"
}
```

#### 3. 內部文檔引用 (Internal Document Citation)

```json
{
  "citation_id": "int_001",
  "source_type": "internal_document", 
  "title": "用戶手冊第三章",
  "content_snippet": "註冊流程包含郵箱驗證和推薦碼輸入步驟...",
  "document_path": "/docs/user-manual/chapter-3.md",
  "page_number": 15,
  "section": "3.2 註冊流程",
  "relevance_score": 0.90
}
```

#### 4. FAQ 引用 (FAQ Citation)

```json
{
  "citation_id": "faq_001",
  "source_type": "faq",
  "question": "如何重置密碼？",
  "answer_snippet": "點擊登入頁面的「忘記密碼」連結，輸入註冊郵箱...",
  "faq_id": "faq_password_reset",
  "category": "account_management",
  "relevance_score": 0.96
}
```

## 引用生成流程

### 1. 檢索階段 (Retrieval Phase)

```python
async def retrieve_with_citations(query: str, tenant_id: str, limit: int = 5) -> List[Dict]:
    """
    檢索相關內容並生成引用
    
    Args:
        query: 用戶查詢
        tenant_id: 租戶ID
        limit: 最大結果數
        
    Returns:
        包含引用信息的檢索結果
    """
    # 1. 向量檢索
    vector_results = await vector_search(query, tenant_id, limit * 2)
    
    # 2. 關鍵詞檢索
    keyword_results = await keyword_search(query, tenant_id, limit)
    
    # 3. 混合排序
    combined_results = hybrid_rank(vector_results, keyword_results)
    
    # 4. 生成引用
    citations = []
    for i, result in enumerate(combined_results[:limit]):
        citation = generate_citation(result, i + 1)
        citations.append(citation)
    
    return citations

def generate_citation(search_result: Dict, citation_index: int) -> Dict:
    """生成單個引用"""
    return {
        "citation_id": f"cite_{citation_index:03d}",
        "source_type": determine_source_type(search_result),
        "title": search_result.get("title", "未命名文檔"),
        "content_snippet": extract_snippet(search_result["content"]),
        "relevance_score": search_result["similarity_score"],
        "chunk_id": search_result["chunk_id"],
        "document_id": search_result["document_id"],
        "url": search_result.get("url"),
        "metadata": search_result.get("metadata", {}),
        "created_at": datetime.utcnow().isoformat()
    }
```

### 2. 內容摘要階段 (Content Extraction)

```python
def extract_snippet(content: str, max_length: int = 150) -> str:
    """
    提取內容摘要
    
    Args:
        content: 原始內容
        max_length: 最大長度
        
    Returns:
        內容摘要
    """
    if len(content) <= max_length:
        return content
    
    # 在句子邊界截斷
    sentences = re.split(r'[。.!?！？]', content)
    snippet = ""
    
    for sentence in sentences:
        if len(snippet + sentence) <= max_length - 3:
            snippet += sentence + "。"
        else:
            break
    
    if len(snippet) < max_length - 3:
        snippet = content[:max_length - 3]
    
    return snippet + "..."

def highlight_relevant_text(content: str, query: str) -> str:
    """
    高亮相關文本
    
    Args:
        content: 原始內容
        query: 查詢詞
        
    Returns:
        高亮後的內容
    """
    query_terms = query.split()
    highlighted_content = content
    
    for term in query_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted_content = pattern.sub(f"**{term}**", highlighted_content)
    
    return highlighted_content
```

### 3. 引用整合階段 (Citation Integration)

```python
async def generate_response_with_citations(query: str, citations: List[Dict]) -> Dict:
    """
    生成帶引用的回應
    
    Args:
        query: 用戶查詢
        citations: 引用列表
        
    Returns:
        包含引用的回應
    """
    # 1. 構建上下文
    context = build_context_from_citations(citations)
    
    # 2. 生成回應
    prompt = build_prompt_with_context(query, context, citations)
    response = await call_gpt_api(prompt)
    
    # 3. 插入引用標記
    response_with_citations = insert_citation_markers(response, citations)
    
    # 4. 驗證引用使用
    used_citations = extract_used_citations(response_with_citations)
    
    return {
        "response": response_with_citations,
        "citations": citations,
        "used_citations": used_citations,
        "citation_count": len(used_citations)
    }

def build_context_from_citations(citations: List[Dict]) -> str:
    """從引用構建上下文"""
    context_parts = []
    
    for i, citation in enumerate(citations, 1):
        context_part = f"[{i}] {citation['title']}: {citation['content_snippet']}"
        context_parts.append(context_part)
    
    return "\n\n".join(context_parts)

def insert_citation_markers(response: str, citations: List[Dict]) -> str:
    """在回應中插入引用標記"""
    # 簡化實現：在相關內容後添加引用標記
    for i, citation in enumerate(citations, 1):
        # 查找相關內容
        snippet_words = citation["content_snippet"].split()[:5]
        for word in snippet_words:
            if word in response:
                # 在相關內容後添加引用標記
                response = response.replace(
                    word, 
                    f"{word}[{i}]", 
                    1  # 只替換第一個匹配
                )
                break
    
    return response
```

## 引用顯示格式

### 1. 內聯引用 (Inline Citations)

**格式：** `內容[1]`

**範例：**
```
推薦碼是邀請朋友的專用代碼[1]，每個用戶都可以生成唯一推薦碼邀請朋友[2]。
```

### 2. 引用列表 (Citation List)

**格式：**
```
參考資料：
[1] 推薦碼使用指南 - 推薦碼是邀請朋友的專用代碼...
[2] 用戶手冊 - 每個用戶都可以生成唯一推薦碼...
```

### 3. 卡片式引用 (Citation Cards)

```json
{
  "citation_card": {
    "id": "cite_001",
    "title": "推薦碼使用指南",
    "snippet": "推薦碼是邀請朋友的專用代碼...",
    "source": "知識庫",
    "confidence": "高",
    "url": "https://help.morningai.com/referral-guide",
    "actions": ["查看完整內容", "相關問題"]
  }
}
```

## 前端顯示規範

### HTML 結構

```html
<div class="chat-response">
  <div class="response-content">
    推薦碼是邀請朋友的專用代碼<sup class="citation-marker" data-citation="cite_001">[1]</sup>，
    每個用戶都可以生成唯一推薦碼邀請朋友<sup class="citation-marker" data-citation="cite_002">[2]</sup>。
  </div>
  
  <div class="citations-section">
    <h4>參考資料：</h4>
    <div class="citation-list">
      <div class="citation-item" id="cite_001">
        <span class="citation-number">[1]</span>
        <div class="citation-content">
          <h5 class="citation-title">推薦碼使用指南</h5>
          <p class="citation-snippet">推薦碼是邀請朋友的專用代碼...</p>
          <div class="citation-meta">
            <span class="citation-source">知識庫</span>
            <span class="citation-confidence">信心度: 95%</span>
            <a href="#" class="citation-link">查看完整內容</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### CSS 樣式

```css
.citation-marker {
  color: #007bff;
  cursor: pointer;
  font-size: 0.8em;
  text-decoration: none;
}

.citation-marker:hover {
  background-color: #e7f3ff;
  border-radius: 2px;
}

.citations-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.citation-item {
  display: flex;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.citation-number {
  font-weight: bold;
  color: #007bff;
  margin-right: 0.5rem;
  min-width: 2rem;
}

.citation-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.citation-snippet {
  font-size: 0.8rem;
  color: #666;
  margin: 0 0 0.25rem 0;
  line-height: 1.4;
}

.citation-meta {
  font-size: 0.7rem;
  color: #888;
}

.citation-link {
  color: #007bff;
  text-decoration: none;
  margin-left: 0.5rem;
}
```

### JavaScript 互動

```javascript
class CitationManager {
    constructor() {
        this.initializeCitationEvents();
    }
    
    initializeCitationEvents() {
        // 引用標記點擊事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('citation-marker')) {
                const citationId = e.target.dataset.citation;
                this.highlightCitation(citationId);
                this.scrollToCitation(citationId);
            }
        });
        
        // 引用懸停事件
        document.addEventListener('mouseover', (e) => {
            if (e.target.classList.contains('citation-marker')) {
                const citationId = e.target.dataset.citation;
                this.showCitationPreview(e.target, citationId);
            }
        });
    }
    
    highlightCitation(citationId) {
        // 移除之前的高亮
        document.querySelectorAll('.citation-item.highlighted')
            .forEach(item => item.classList.remove('highlighted'));
        
        // 高亮目標引用
        const citationElement = document.getElementById(citationId);
        if (citationElement) {
            citationElement.classList.add('highlighted');
        }
    }
    
    scrollToCitation(citationId) {
        const citationElement = document.getElementById(citationId);
        if (citationElement) {
            citationElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }
    }
    
    showCitationPreview(trigger, citationId) {
        // 創建預覽彈窗
        const preview = this.createCitationPreview(citationId);
        document.body.appendChild(preview);
        
        // 定位彈窗
        this.positionPreview(preview, trigger);
        
        // 自動隱藏
        setTimeout(() => {
            if (preview.parentNode) {
                preview.parentNode.removeChild(preview);
            }
        }, 3000);
    }
    
    createCitationPreview(citationId) {
        const citationData = this.getCitationData(citationId);
        
        const preview = document.createElement('div');
        preview.className = 'citation-preview';
        preview.innerHTML = `
            <div class="preview-title">${citationData.title}</div>
            <div class="preview-snippet">${citationData.snippet}</div>
            <div class="preview-meta">
                來源: ${citationData.source} | 
                信心度: ${Math.round(citationData.confidence * 100)}%
            </div>
        `;
        
        return preview;
    }
    
    getCitationData(citationId) {
        // 從頁面中提取引用數據
        const citationElement = document.getElementById(citationId);
        if (!citationElement) return null;
        
        return {
            title: citationElement.querySelector('.citation-title').textContent,
            snippet: citationElement.querySelector('.citation-snippet').textContent,
            source: citationElement.querySelector('.citation-source').textContent,
            confidence: 0.95 // 從數據屬性獲取
        };
    }
}

// 初始化引用管理器
document.addEventListener('DOMContentLoaded', () => {
    new CitationManager();
});
```

## 質量控制

### 引用驗證

```python
class CitationValidator:
    """引用驗證器"""
    
    def validate_citation(self, citation: Dict) -> Dict[str, Any]:
        """驗證單個引用"""
        errors = []
        warnings = []
        
        # 必需字段檢查
        required_fields = ["citation_id", "source_type", "title", "content_snippet"]
        for field in required_fields:
            if not citation.get(field):
                errors.append(f"缺少必需字段: {field}")
        
        # 內容質量檢查
        snippet = citation.get("content_snippet", "")
        if len(snippet) < 20:
            warnings.append("內容摘要過短")
        elif len(snippet) > 200:
            warnings.append("內容摘要過長")
        
        # 相關性檢查
        relevance_score = citation.get("relevance_score", 0)
        if relevance_score < 0.5:
            warnings.append(f"相關性分數較低: {relevance_score}")
        
        # URL 有效性檢查
        url = citation.get("url")
        if url and not self.is_valid_url(url):
            errors.append(f"無效的URL: {url}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality_score": self.calculate_quality_score(citation, errors, warnings)
        }
    
    def is_valid_url(self, url: str) -> bool:
        """檢查URL有效性"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def calculate_quality_score(self, citation: Dict, errors: List, warnings: List) -> float:
        """計算引用質量分數"""
        base_score = 1.0
        
        # 錯誤扣分
        base_score -= len(errors) * 0.3
        
        # 警告扣分
        base_score -= len(warnings) * 0.1
        
        # 相關性加分
        relevance_score = citation.get("relevance_score", 0)
        base_score += (relevance_score - 0.5) * 0.2
        
        return max(0.0, min(1.0, base_score))
```

### 引用去重

```python
def deduplicate_citations(citations: List[Dict]) -> List[Dict]:
    """去除重複引用"""
    seen_content = set()
    unique_citations = []
    
    for citation in citations:
        # 使用內容摘要的哈希作為去重鍵
        content_hash = hashlib.md5(
            citation["content_snippet"].encode()
        ).hexdigest()
        
        if content_hash not in seen_content:
            seen_content.add(content_hash)
            unique_citations.append(citation)
    
    return unique_citations

def merge_similar_citations(citations: List[Dict], similarity_threshold: float = 0.8) -> List[Dict]:
    """合併相似引用"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    if len(citations) <= 1:
        return citations
    
    # 計算內容相似度
    contents = [c["content_snippet"] for c in citations]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(contents)
    similarity_matrix = cosine_similarity(tfidf_matrix)
    
    # 找出相似引用對
    merged_indices = set()
    merged_citations = []
    
    for i in range(len(citations)):
        if i in merged_indices:
            continue
        
        similar_indices = [i]
        for j in range(i + 1, len(citations)):
            if j not in merged_indices and similarity_matrix[i][j] > similarity_threshold:
                similar_indices.append(j)
                merged_indices.add(j)
        
        # 合併相似引用
        if len(similar_indices) > 1:
            merged_citation = merge_citation_group([citations[idx] for idx in similar_indices])
            merged_citations.append(merged_citation)
        else:
            merged_citations.append(citations[i])
        
        merged_indices.add(i)
    
    return merged_citations
```

## 性能優化

### 引用緩存

```python
class CitationCache:
    """引用緩存管理器"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1小時
    
    async def get_cached_citations(self, query_hash: str, tenant_id: str) -> List[Dict]:
        """獲取緩存的引用"""
        cache_key = f"citations:{tenant_id}:{query_hash}"
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def cache_citations(self, query_hash: str, tenant_id: str, citations: List[Dict]):
        """緩存引用結果"""
        cache_key = f"citations:{tenant_id}:{query_hash}"
        await self.redis.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(citations, ensure_ascii=False)
        )
```

## 監控和分析

### 引用使用統計

```python
async def track_citation_usage(citation_id: str, action: str, user_id: str):
    """追蹤引用使用情況"""
    event = {
        "citation_id": citation_id,
        "action": action,  # "viewed", "clicked", "copied"
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 記錄到分析系統
    await analytics_client.track("citation_interaction", event)

async def generate_citation_report(tenant_id: str, date_range: tuple) -> Dict:
    """生成引用使用報告"""
    return {
        "total_citations": await count_citations(tenant_id, date_range),
        "most_cited_documents": await get_top_cited_documents(tenant_id, date_range),
        "citation_click_rate": await calculate_citation_ctr(tenant_id, date_range),
        "user_engagement": await analyze_citation_engagement(tenant_id, date_range)
    }
```

## 最佳實踐

### 1. 引用選擇原則

- **相關性優先**：選擇與查詢最相關的內容
- **權威性考慮**：優先選擇官方或權威來源
- **時效性檢查**：確保引用內容是最新的
- **多樣性平衡**：避免過度依賴單一來源

### 2. 內容摘要技巧

- **關鍵信息提取**：突出核心觀點
- **上下文保持**：保持語義完整性
- **長度控制**：適中的摘要長度
- **可讀性優化**：清晰易懂的表達

### 3. 用戶體驗設計

- **非侵入式顯示**：不影響閱讀流暢性
- **互動友好**：提供便捷的查看方式
- **視覺層次**：清晰的信息層級
- **響應式設計**：適配不同設備

### 4. 質量保證

- **自動驗證**：實施引用質量檢查
- **人工審核**：定期審查引用質量
- **用戶反饋**：收集使用體驗反饋
- **持續改進**：基於數據優化策略

---

**規格版本：** v1.0  
**最後更新：** 2025-01-05  
**負責人：** 技術團隊

