# MorningAI 聊天模組 API 使用範例

## 概述

MorningAI 聊天模組提供完整的 GPT+RAG 整合功能，支援智能對話、知識檢索、多輪會話管理等核心功能。

## 核心特色

- 🧠 **GPT+RAG 整合** - 95% 準確率目標
- 💬 **多輪對話管理** - 上下文維護和會話追蹤
- 🔍 **知識庫檢索** - 企業知識語義搜索
- 🎯 **意圖分析** - 智能理解用戶需求
- 🛡️ **安全控制** - RBAC 權限和速率限制
- ⚡ **性能優化** - 緩存策略和異步處理

## API 端點

### 1. 發送聊天消息

**端點:** `POST /api/v1/chat/send`

**功能特色:**
- GPT+RAG 智能回應
- 自動意圖分析
- 知識庫檢索
- 對話上下文維護
- 自動追問功能
- 速率限制保護 (30條/小時)

**請求範例:**
```json
{
    "message": "如何使用推薦碼？",
    "session_id": null
}
```

**回應範例:**
```json
{
    "session_id": "12345678-1234-5678-9012-123456789012",
    "message_id": "87654321-4321-8765-2109-876543210987",
    "response": "推薦碼是邀請朋友的專用代碼。每個用戶可以生成唯一推薦碼，朋友使用後雙方都能獲得獎勵。您可以在個人中心找到「我的推薦碼」功能。",
    "intent_analysis": {
        "primary_intent": "question",
        "intents": ["question"],
        "confidence": 0.9,
        "requires_followup": false
    },
    "knowledge_used": true,
    "knowledge_items": [
        {
            "id": "kb-001",
            "title": "推薦碼使用指南",
            "content": "推薦碼是邀請朋友的專用代碼...",
            "category": "guide",
            "relevance_score": 0.95
        }
    ],
    "metadata": {
        "model": "gpt-4",
        "response_time": 1.2,
        "usage": {
            "total_tokens": 150,
            "prompt_tokens": 100,
            "completion_tokens": 50
        },
        "has_context": true,
        "context_length": 200
    },
    "created_at": "2025-01-01T10:00:00Z"
}
```

### 2. 獲取用戶會話列表

**端點:** `GET /api/v1/chat/sessions`

**功能特色:**
- 分頁顯示
- 按更新時間排序
- 包含會話統計信息

**查詢參數:**
- `page`: 頁碼 (默認: 1)
- `size`: 每頁大小 (默認: 20, 最大: 100)

**回應範例:**
```json
{
    "sessions": [
        {
            "id": "12345678-1234-5678-9012-123456789012",
            "title": "關於推薦碼的對話",
            "message_count": 8,
            "created_at": "2025-01-01T10:00:00Z",
            "updated_at": "2025-01-01T10:30:00Z"
        },
        {
            "id": "87654321-4321-8765-2109-876543210987",
            "title": "產品功能咨詢",
            "message_count": 12,
            "created_at": "2025-01-01T09:00:00Z",
            "updated_at": "2025-01-01T09:45:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "size": 20,
        "total": 2,
        "pages": 1
    }
}
```

### 3. 獲取聊天歷史

**端點:** `GET /api/v1/chat/sessions/{session_id}/history`

**功能特色:**
- 分頁顯示
- 按時間順序排列
- 包含消息元數據
- 會話所有權驗證

**查詢參數:**
- `page`: 頁碼 (默認: 1)
- `size`: 每頁大小 (默認: 20, 最大: 100)

**回應範例:**
```json
{
    "session_id": "12345678-1234-5678-9012-123456789012",
    "messages": [
        {
            "id": "msg-001",
            "role": "user",
            "content": "如何使用推薦碼？",
            "metadata": {},
            "created_at": "2025-01-01T10:00:00Z"
        },
        {
            "id": "msg-002",
            "role": "assistant",
            "content": "推薦碼是邀請朋友的專用代碼...",
            "metadata": {
                "model": "gpt-4",
                "response_time": 1.2,
                "knowledge_used": true
            },
            "created_at": "2025-01-01T10:00:02Z"
        }
    ],
    "pagination": {
        "page": 1,
        "size": 20,
        "total": 2,
        "pages": 1
    }
}
```

### 4. 創建新會話

**端點:** `POST /api/v1/chat/sessions`

**請求範例:**
```json
{
    "title": "關於產品功能的咨詢"
}
```

**回應範例:**
```json
{
    "success": true,
    "message": "聊天會話創建成功",
    "data": {
        "session_id": "12345678-1234-5678-9012-123456789012",
        "title": "關於產品功能的咨詢",
        "created_at": "2025-01-01T10:00:00Z"
    }
}
```

### 5. 搜索知識庫

**端點:** `POST /api/v1/chat/knowledge/search`

**功能特色:**
- 語義搜索
- 分類和標籤過濾
- 相似度閾值控制
- 結果排序

**請求範例:**
```json
{
    "query": "推薦碼使用方法",
    "category": "guide",
    "tags": ["推薦碼"],
    "limit": 5,
    "similarity_threshold": 0.7
}
```

**回應範例:**
```json
{
    "query": "推薦碼使用方法",
    "items": [
        {
            "id": "kb-001",
            "title": "推薦碼使用指南",
            "content": "推薦碼是邀請朋友的專用代碼...",
            "category": "guide",
            "tags": ["推薦碼", "邀請", "獎勵"],
            "relevance_score": 0.95,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
    ],
    "total": 1,
    "search_time": 0.15
}
```

### 6. 提交反饋

**端點:** `POST /api/v1/chat/feedback`

**功能特色:**
- 消息評分
- 反饋分類
- 評論支援
- 用於改進AI回應質量

**請求範例:**
```json
{
    "message_id": "msg-002",
    "rating": 5,
    "feedback_type": "helpful",
    "comment": "回答很詳細，解決了我的問題"
}
```

**回應範例:**
```json
{
    "feedback_id": "fb-001",
    "message": "反饋提交成功，感謝您的意見！",
    "created_at": "2025-01-01T10:05:00Z"
}
```

## 安全特性

### 權限要求

- `chat.create` - 發送消息、創建會話、提交反饋
- `chat.read` - 讀取會話列表、聊天歷史、搜索知識庫
- `chat.update` - 更新會話信息
- `chat.delete` - 刪除會話
- `chat.manage` - 管理知識庫條目

### 速率限制

- 聊天消息: 30條/小時
- GPT API 調用: 20次/小時
- 知識庫創建: 10條/小時
- 反饋提交: 50條/小時

### 租戶隔離

- 所有數據按租戶隔離
- 會話和消息僅限本租戶用戶訪問
- 知識庫按租戶分離
- 統計數據獨立計算

## 錯誤處理

### 常見錯誤碼

- `400` - 請求參數錯誤
- `401` - 未授權訪問
- `403` - 權限不足
- `404` - 資源不存在
- `429` - 速率限制超出
- `500` - 服務器內部錯誤

### 錯誤回應格式

```json
{
    "detail": "Permission 'chat.create' required",
    "error_code": "PERMISSION_DENIED",
    "timestamp": "2025-01-01T10:00:00Z"
}
```

## 使用範例

### 完整對話流程

```bash
# 1. 用戶登入獲取 access_token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@morningai.com",
    "password": "user123"
  }'

# 2. 發送第一條消息（創建新會話）
curl -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想了解推薦碼功能"
  }'

# 3. 繼續對話（使用相同會話ID）
curl -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何獲得推薦碼？",
    "session_id": "12345678-1234-5678-9012-123456789012"
  }'

# 4. 查看聊天歷史
curl -X GET "http://localhost:8000/api/v1/chat/sessions/12345678-1234-5678-9012-123456789012/history" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 5. 提交反饋
curl -X POST "http://localhost:8000/api/v1/chat/feedback" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg-002",
    "rating": 5,
    "feedback_type": "helpful",
    "comment": "回答很有幫助"
  }'
```

## 性能優化建議

1. **緩存利用**
   - 相同查詢會使用緩存結果
   - 知識庫搜索結果緩存1小時

2. **批量操作**
   - 一次獲取多條聊天記錄
   - 分頁查詢避免大量數據傳輸

3. **異步處理**
   - 所有API都是異步處理
   - 支援高併發請求

4. **監控指標**
   - 響應時間監控
   - 錯誤率統計
   - 使用量分析

## 總結

MorningAI 聊天模組提供了完整的企業級聊天功能，結合了最新的 GPT 和 RAG 技術，確保高準確率和優秀的用戶體驗。通過完善的安全控制、性能優化和監控機制，為企業提供可靠的智能對話解決方案。

