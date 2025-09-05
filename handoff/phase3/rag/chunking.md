# 文檔切片策略文檔

## 概述

文檔切片 (Document Chunking) 是 RAG 系統中的關鍵步驟，將長文檔分割成適合向量化和檢索的小片段。本文檔描述 MorningAI 聊天模組的切片策略、實施方法和最佳實踐。

## 切片策略

### 1. 遞歸字符切片 (Recursive Character Splitting)

**推薦策略**，適用於大多數文檔類型。

**工作原理：**
1. 按優先級順序使用分隔符
2. 遞歸分割直到達到目標大小
3. 保持語義完整性

**分隔符優先級：**
```python
SEPARATORS = [
    "\n\n",      # 段落分隔
    "\n",        # 行分隔  
    "。",        # 中文句號
    ".",         # 英文句號
    "！",        # 中文驚嘆號
    "!",         # 英文驚嘆號
    "？",        # 中文問號
    "?",         # 英文問號
    "；",        # 中文分號
    ";",         # 英文分號
    "，",        # 中文逗號
    ",",         # 英文逗號
    " ",         # 空格
    ""           # 字符級分割 (最後手段)
]
```

### 2. 語義切片 (Semantic Chunking)

**高級策略**，基於語義相似度進行分割。

**適用場景：**
- 技術文檔
- 學術論文
- 結構化內容

**實施方法：**
1. 計算句子間語義相似度
2. 在相似度低的位置分割
3. 確保切片語義連貫

### 3. 固定大小切片 (Fixed Size Chunking)

**簡單策略**，按固定字符數分割。

**優點：**
- 實施簡單
- 性能高效
- 大小可預測

**缺點：**
- 可能破壞語義
- 不考慮文檔結構
- 質量較低

## 配置參數

### 基礎配置

```json
{
  "chunking_config": {
    "strategy": "recursive_character",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "min_chunk_size": 100,
    "max_chunk_size": 1500,
    "separators": ["\n\n", "\n", "。", ".", " "],
    "keep_separator": true,
    "strip_whitespace": true
  }
}
```

### 高級配置

```json
{
  "advanced_config": {
    "semantic_chunking": {
      "enabled": false,
      "similarity_threshold": 0.5,
      "embedding_model": "text-embedding-ada-002"
    },
    "document_structure": {
      "respect_headers": true,
      "respect_paragraphs": true,
      "respect_lists": true
    },
    "language_specific": {
      "chinese": {
        "chunk_size": 800,
        "separators": ["。", "！", "？", "；", "\n\n", "\n"]
      },
      "english": {
        "chunk_size": 1000,
        "separators": [".", "!", "?", ";", "\n\n", "\n"]
      }
    }
  }
}
```

## 實施代碼

### 核心切片器類

```python
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ChunkMetadata:
    """切片元數據"""
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    separator_used: str
    language: str = "auto"

class DocumentChunker:
    """文檔切片器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.chunk_size = config.get("chunk_size", 1000)
        self.chunk_overlap = config.get("chunk_overlap", 200)
        self.min_chunk_size = config.get("min_chunk_size", 100)
        self.max_chunk_size = config.get("max_chunk_size", 1500)
        self.separators = config.get("separators", ["\n\n", "\n", "。", ".", " "])
        self.keep_separator = config.get("keep_separator", True)
        
    def chunk_document(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        將文檔分割成切片
        
        Args:
            text: 原始文檔內容
            metadata: 文檔元數據
            
        Returns:
            切片列表，每個切片包含內容和元數據
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            return []
        
        # 預處理文本
        text = self._preprocess_text(text)
        
        # 執行切片
        chunks = self._recursive_split(text, self.separators)
        
        # 後處理和添加元數據
        result = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) >= self.min_chunk_size:
                chunk_metadata = ChunkMetadata(
                    chunk_index=i,
                    start_char=text.find(chunk_text),
                    end_char=text.find(chunk_text) + len(chunk_text),
                    token_count=self._count_tokens(chunk_text),
                    separator_used=self._detect_separator(chunk_text),
                    language=self._detect_language(chunk_text)
                )
                
                result.append({
                    "content": chunk_text.strip(),
                    "metadata": {
                        **chunk_metadata.__dict__,
                        **(metadata or {})
                    }
                })
        
        return result
    
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """遞歸分割文本"""
        if len(text) <= self.chunk_size:
            return [text]
        
        if not separators:
            # 沒有分隔符時，強制按字符分割
            return self._split_by_length(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # 按當前分隔符分割
        splits = text.split(separator)
        
        # 重新組合分割結果
        chunks = []
        current_chunk = ""
        
        for split in splits:
            # 如果添加這個分割會超過大小限制
            test_chunk = current_chunk + (separator if current_chunk else "") + split
            
            if len(test_chunk) > self.chunk_size and current_chunk:
                # 當前塊已滿，處理它
                if len(current_chunk) > self.max_chunk_size:
                    # 當前塊太大，需要進一步分割
                    sub_chunks = self._recursive_split(current_chunk, remaining_separators)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(current_chunk)
                
                # 開始新塊
                current_chunk = split
            else:
                # 可以添加到當前塊
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
        
        # 處理最後一個塊
        if current_chunk:
            if len(current_chunk) > self.max_chunk_size:
                sub_chunks = self._recursive_split(current_chunk, remaining_separators)
                chunks.extend(sub_chunks)
            else:
                chunks.append(current_chunk)
        
        # 添加重疊
        if self.chunk_overlap > 0:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """添加切片間重疊"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            
            # 從前一個切片取重疊內容
            prev_chunk = chunks[i-1]
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # 合併重疊內容和當前切片
            overlapped_chunk = overlap_text + " " + chunk
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _split_by_length(self, text: str) -> List[str]:
        """按固定長度分割文本"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end
        
        return chunks
    
    def _preprocess_text(self, text: str) -> str:
        """預處理文本"""
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        
        # 統一換行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除HTML標籤 (如果存在)
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除多餘的標點符號
        text = re.sub(r'[。]{2,}', '。', text)
        text = re.sub(r'[.]{2,}', '.', text)
        
        return text.strip()
    
    def _count_tokens(self, text: str) -> int:
        """估算token數量"""
        # 簡單估算：中文字符=1token，英文單詞=1token
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        other_chars = len(text) - chinese_chars - sum(len(word) for word in re.findall(r'\b[a-zA-Z]+\b', text))
        
        return chinese_chars + english_words + max(0, other_chars // 4)
    
    def _detect_separator(self, text: str) -> str:
        """檢測使用的分隔符"""
        for sep in self.separators:
            if sep in text:
                return sep
        return "character"
    
    def _detect_language(self, text: str) -> str:
        """檢測文本語言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > chinese_chars:
            return "en"
        else:
            return "mixed"
```

### 專用切片器

```python
class MarkdownChunker(DocumentChunker):
    """Markdown文檔專用切片器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.separators = [
            "\n# ",      # H1標題
            "\n## ",     # H2標題  
            "\n### ",    # H3標題
            "\n\n",      # 段落
            "\n",        # 行
            "。", ".", " "
        ]
    
    def _preprocess_text(self, text: str) -> str:
        """Markdown特殊預處理"""
        text = super()._preprocess_text(text)
        
        # 保留標題結構
        text = re.sub(r'\n(#{1,6})\s+', r'\n\1 ', text)
        
        # 處理代碼塊
        text = re.sub(r'```[\s\S]*?```', '[CODE_BLOCK]', text)
        
        # 處理表格
        text = re.sub(r'\|.*\|', '[TABLE_ROW]', text)
        
        return text

class PDFChunker(DocumentChunker):
    """PDF文檔專用切片器"""
    
    def _preprocess_text(self, text: str) -> str:
        """PDF特殊預處理"""
        text = super()._preprocess_text(text)
        
        # 處理頁面分隔
        text = re.sub(r'\f', '\n\n', text)
        
        # 處理連字符
        text = re.sub(r'-\n', '', text)
        
        # 處理多列佈局
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
```

## 質量評估

### 切片質量指標

```python
class ChunkQualityEvaluator:
    """切片質量評估器"""
    
    def evaluate_chunks(self, chunks: List[Dict]) -> Dict[str, float]:
        """評估切片質量"""
        if not chunks:
            return {"overall_score": 0.0}
        
        scores = {
            "size_consistency": self._evaluate_size_consistency(chunks),
            "semantic_coherence": self._evaluate_semantic_coherence(chunks),
            "overlap_quality": self._evaluate_overlap_quality(chunks),
            "boundary_quality": self._evaluate_boundary_quality(chunks)
        }
        
        # 計算總體分數
        weights = {
            "size_consistency": 0.2,
            "semantic_coherence": 0.4,
            "overlap_quality": 0.2,
            "boundary_quality": 0.2
        }
        
        overall_score = sum(scores[key] * weights[key] for key in scores)
        scores["overall_score"] = overall_score
        
        return scores
    
    def _evaluate_size_consistency(self, chunks: List[Dict]) -> float:
        """評估大小一致性"""
        sizes = [len(chunk["content"]) for chunk in chunks]
        if not sizes:
            return 0.0
        
        mean_size = sum(sizes) / len(sizes)
        variance = sum((size - mean_size) ** 2 for size in sizes) / len(sizes)
        coefficient_of_variation = (variance ** 0.5) / mean_size if mean_size > 0 else 1.0
        
        # CV越小，一致性越好
        return max(0.0, 1.0 - coefficient_of_variation)
    
    def _evaluate_semantic_coherence(self, chunks: List[Dict]) -> float:
        """評估語義連貫性"""
        # 簡化實現：檢查句子完整性
        coherence_scores = []
        
        for chunk in chunks:
            content = chunk["content"]
            
            # 檢查是否以完整句子結尾
            ends_properly = content.rstrip().endswith(('。', '.', '!', '?', '！', '？'))
            
            # 檢查是否以完整句子開始
            starts_properly = content.lstrip()[0].isupper() if content.strip() else False
            
            # 檢查句子完整性
            sentence_score = (ends_properly + starts_properly) / 2
            coherence_scores.append(sentence_score)
        
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
    
    def _evaluate_overlap_quality(self, chunks: List[Dict]) -> float:
        """評估重疊質量"""
        if len(chunks) <= 1:
            return 1.0
        
        overlap_scores = []
        
        for i in range(1, len(chunks)):
            current_chunk = chunks[i]["content"]
            prev_chunk = chunks[i-1]["content"]
            
            # 簡單重疊檢測
            overlap_found = any(
                word in prev_chunk for word in current_chunk.split()[:10]
            )
            
            overlap_scores.append(1.0 if overlap_found else 0.0)
        
        return sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
    
    def _evaluate_boundary_quality(self, chunks: List[Dict]) -> float:
        """評估邊界質量"""
        boundary_scores = []
        
        for chunk in chunks:
            content = chunk["content"]
            
            # 檢查是否在合適位置分割
            good_boundary = (
                content.strip().endswith(('\n\n', '。', '.', '!', '?')) or
                content.strip().startswith(('#', '##', '###'))
            )
            
            boundary_scores.append(1.0 if good_boundary else 0.5)
        
        return sum(boundary_scores) / len(boundary_scores) if boundary_scores else 0.0
```

## 性能優化

### 批量處理

```python
async def batch_chunk_documents(documents: List[Dict], chunk_size: int = 100) -> List[Dict]:
    """批量處理文檔切片"""
    chunker = DocumentChunker(get_chunking_config())
    results = []
    
    for i in range(0, len(documents), chunk_size):
        batch = documents[i:i + chunk_size]
        batch_results = []
        
        for doc in batch:
            chunks = chunker.chunk_document(doc["content"], doc.get("metadata"))
            batch_results.extend(chunks)
        
        results.extend(batch_results)
        
        # 避免內存溢出
        if len(results) > 10000:
            await save_chunks_to_db(results)
            results = []
    
    if results:
        await save_chunks_to_db(results)
    
    return results
```

### 緩存策略

```python
from functools import lru_cache
import hashlib

class CachedChunker(DocumentChunker):
    """帶緩存的切片器"""
    
    @lru_cache(maxsize=1000)
    def chunk_document_cached(self, text_hash: str, text: str, metadata_str: str) -> tuple:
        """緩存版本的切片方法"""
        metadata = json.loads(metadata_str) if metadata_str else None
        chunks = self.chunk_document(text, metadata)
        return tuple(json.dumps(chunk) for chunk in chunks)
    
    def chunk_document(self, text: str, metadata: Dict = None) -> List[Dict]:
        """重寫以支持緩存"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        metadata_str = json.dumps(metadata, sort_keys=True) if metadata else ""
        
        cached_result = self.chunk_document_cached(text_hash, text, metadata_str)
        return [json.loads(chunk_str) for chunk_str in cached_result]
```

## 測試和驗證

### 單元測試

```python
import unittest

class TestDocumentChunker(unittest.TestCase):
    
    def setUp(self):
        self.config = {
            "chunk_size": 100,
            "chunk_overlap": 20,
            "min_chunk_size": 50,
            "separators": ["\n\n", "\n", ".", " "]
        }
        self.chunker = DocumentChunker(self.config)
    
    def test_basic_chunking(self):
        """測試基本切片功能"""
        text = "這是第一段。這是第二段。這是第三段。" * 10
        chunks = self.chunker.chunk_document(text)
        
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk["content"]), self.config["max_chunk_size"])
            self.assertGreaterEqual(len(chunk["content"]), self.config["min_chunk_size"])
    
    def test_overlap(self):
        """測試重疊功能"""
        text = "句子一。句子二。句子三。句子四。句子五。" * 20
        chunks = self.chunker.chunk_document(text)
        
        if len(chunks) > 1:
            # 檢查相鄰切片是否有重疊
            for i in range(1, len(chunks)):
                current = chunks[i]["content"]
                previous = chunks[i-1]["content"]
                # 簡單檢查是否有共同詞彙
                current_words = set(current.split())
                previous_words = set(previous.split())
                overlap = current_words.intersection(previous_words)
                self.assertGreater(len(overlap), 0)
    
    def test_metadata(self):
        """測試元數據"""
        text = "測試文檔內容。"
        metadata = {"source": "test", "category": "example"}
        chunks = self.chunker.chunk_document(text, metadata)
        
        for chunk in chunks:
            self.assertIn("metadata", chunk)
            self.assertEqual(chunk["metadata"]["source"], "test")
            self.assertEqual(chunk["metadata"]["category"], "example")
```

## 最佳實踐

### 1. 文檔類型適配

- **技術文檔**：尊重標題結構，保持代碼塊完整
- **法律文檔**：按條款分割，保持引用完整
- **新聞文章**：按段落分割，保持時間線
- **學術論文**：按章節分割，保持引用格式

### 2. 語言特殊處理

- **中文**：考慮詞語邊界，避免分割詞語
- **英文**：在句子邊界分割，保持語法完整
- **混合語言**：識別語言切換點，適當調整策略

### 3. 質量控制

- **預處理**：清理無用字符，統一格式
- **後處理**：驗證切片質量，修正邊界
- **監控**：追蹤切片效果，持續優化

### 4. 性能考量

- **批量處理**：減少I/O開銷
- **緩存策略**：避免重複計算
- **內存管理**：控制內存使用
- **並行處理**：提高處理速度

---

**文檔版本：** v1.0  
**最後更新：** 2025-01-05  
**負責人：** 技術團隊

