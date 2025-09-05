# Phase 5 事件追蹤清單

## 聊天系統事件

### 用戶互動事件

#### chat.session_created
**描述**: 用戶創建新的聊天會話
**觸發時機**: 調用 `POST /chat/sessions` 成功時
**事件數據**:
```json
{
  "event": "chat.session_created",
  "timestamp": "2025-01-05T10:30:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "properties": {
    "title": "會話標題",
    "source": "web_chat|mobile_app|api",
    "language": "zh-TW",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1"
  }
}
```

#### chat.message_sent
**描述**: 用戶發送聊天消息
**觸發時機**: 調用 `POST /chat/send` 時
**事件數據**:
```json
{
  "event": "chat.message_sent",
  "timestamp": "2025-01-05T10:31:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "message_id": "uuid",
  "properties": {
    "message_length": 45,
    "language": "zh-TW",
    "intent": "product_inquiry",
    "contains_pii": false,
    "source": "web_chat"
  }
}
```

#### chat.response_generated
**描述**: AI 生成回應
**觸發時機**: AI 成功生成回應時
**事件數據**:
```json
{
  "event": "chat.response_generated",
  "timestamp": "2025-01-05T10:31:02Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "message_id": "uuid",
  "properties": {
    "response_type": "rag_with_gpt_fallback",
    "processing_time": 1.2,
    "confidence_score": 0.92,
    "model_used": "gpt-4",
    "rag_sources_count": 3,
    "token_usage": {
      "input_tokens": 150,
      "output_tokens": 200
    },
    "cost": 0.0045
  }
}
```

#### chat.feedback_submitted
**描述**: 用戶提交反饋
**觸發時機**: 調用 `POST /chat/feedback` 成功時
**事件數據**:
```json
{
  "event": "chat.feedback_submitted",
  "timestamp": "2025-01-05T10:32:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "message_id": "uuid",
  "properties": {
    "score": 1,
    "reason": "helpful",
    "has_comment": true,
    "response_type": "rag_with_gpt_fallback"
  }
}
```

### 系統事件

#### chat.rag_search_performed
**描述**: 執行 RAG 知識庫搜索
**觸發時機**: RAG 系統搜索知識庫時
**事件數據**:
```json
{
  "event": "chat.rag_search_performed",
  "timestamp": "2025-01-05T10:31:01Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "properties": {
    "query": "定價方案",
    "search_type": "semantic",
    "results_count": 5,
    "search_time": 0.3,
    "top_similarity": 0.95,
    "threshold_met": true
  }
}
```

#### chat.gpt_fallback_triggered
**描述**: 觸發 GPT fallback
**觸發時機**: RAG 無法提供滿意答案，切換到 GPT 時
**事件數據**:
```json
{
  "event": "chat.gpt_fallback_triggered",
  "timestamp": "2025-01-05T10:31:01Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "properties": {
    "rag_results_count": 2,
    "max_similarity": 0.65,
    "threshold": 0.7,
    "fallback_reason": "low_similarity"
  }
}
```

#### chat.rate_limit_exceeded
**描述**: 速率限制超出
**觸發時機**: 用戶超出聊天速率限制時
**事件數據**:
```json
{
  "event": "chat.rate_limit_exceeded",
  "timestamp": "2025-01-05T10:31:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "properties": {
    "limit_type": "chat_messages",
    "limit": 30,
    "current_count": 31,
    "reset_time": "2025-01-05T11:00:00Z",
    "endpoint": "/chat/send"
  }
}
```

### 知識庫事件

#### knowledge.search_performed
**描述**: 執行知識庫搜索
**觸發時機**: 調用 `POST /chat/knowledge/search` 時
**事件數據**:
```json
{
  "event": "knowledge.search_performed",
  "timestamp": "2025-01-05T10:33:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "properties": {
    "query": "定價方案",
    "search_type": "semantic",
    "top_k": 5,
    "results_count": 3,
    "search_time": 0.25,
    "filters": {}
  }
}
```

#### knowledge.item_created
**描述**: 創建知識庫條目
**觸發時機**: 調用 `POST /chat/knowledge` 成功時
**事件數據**:
```json
{
  "event": "knowledge.item_created",
  "timestamp": "2025-01-05T10:34:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "properties": {
    "knowledge_id": "uuid",
    "title": "新產品功能介紹",
    "content_length": 1500,
    "source": "manual",
    "tags": ["product", "feature"],
    "language": "zh-TW"
  }
}
```

### 錯誤事件

#### chat.error_occurred
**描述**: 聊天系統發生錯誤
**觸發時機**: 聊天相關操作發生錯誤時
**事件數據**:
```json
{
  "event": "chat.error_occurred",
  "timestamp": "2025-01-05T10:31:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "session_id": "uuid",
  "properties": {
    "error_type": "openai_api_error",
    "error_code": "rate_limit_exceeded",
    "error_message": "Rate limit exceeded",
    "endpoint": "/chat/send",
    "retry_count": 2,
    "processing_time": 5.0
  }
}
```

## 認證系統事件 (繼承自 Phase 4)

### user.login_success
**描述**: 用戶登入成功
**事件數據**:
```json
{
  "event": "user.login_success",
  "timestamp": "2025-01-05T10:00:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "properties": {
    "email": "user@example.com",
    "role": "user",
    "login_method": "password",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  }
}
```

### referral.code_used
**描述**: 推薦碼被使用
**事件數據**:
```json
{
  "event": "referral.code_used",
  "timestamp": "2025-01-05T10:05:00Z",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "properties": {
    "referral_code": "WELCOME2025",
    "referrer_id": "uuid",
    "reward_amount": 100,
    "usage_count": 1
  }
}
```

## 事件收集配置

### Google Analytics 4 事件映射

```javascript
// GA4 事件配置
const ga4Events = {
  'chat.session_created': {
    event_name: 'chat_session_start',
    parameters: {
      session_id: 'session_id',
      source: 'source',
      language: 'language'
    }
  },
  'chat.message_sent': {
    event_name: 'chat_message_send',
    parameters: {
      message_length: 'message_length',
      intent: 'intent',
      language: 'language'
    }
  },
  'chat.response_generated': {
    event_name: 'chat_response_receive',
    parameters: {
      response_type: 'response_type',
      processing_time: 'processing_time',
      confidence_score: 'confidence_score'
    }
  },
  'chat.feedback_submitted': {
    event_name: 'chat_feedback_submit',
    parameters: {
      score: 'score',
      reason: 'reason'
    }
  }
};
```

### Mixpanel 事件配置

```javascript
// Mixpanel 事件配置
const mixpanelEvents = {
  'chat.session_created': 'Chat Session Created',
  'chat.message_sent': 'Chat Message Sent',
  'chat.response_generated': 'Chat Response Generated',
  'chat.feedback_submitted': 'Chat Feedback Submitted',
  'knowledge.search_performed': 'Knowledge Search Performed'
};
```

## 事件處理流程

### 1. 事件收集
- 在應用程序中的關鍵點插入事件追蹤代碼
- 使用統一的事件格式和命名規範
- 確保包含必要的用戶和會話上下文

### 2. 事件驗證
- 驗證事件數據格式和完整性
- 過濾敏感信息 (PII)
- 添加時間戳和會話信息

### 3. 事件路由
- 根據事件類型路由到不同的分析平台
- 支援多個目標 (GA4, Mixpanel, 內部分析)
- 實施重試機制處理失敗

### 4. 事件存儲
- 將事件存儲到數據倉庫用於深度分析
- 實施數據保留政策
- 支援實時和批量處理

## 隱私和合規

### 數據最小化
- 只收集必要的事件數據
- 避免收集敏感個人信息
- 實施數據匿名化

### 用戶同意
- 遵循 GDPR 和其他隱私法規
- 提供事件追蹤的選擇退出機制
- 明確告知用戶數據收集目的

### 數據保留
- 事件數據保留期：2 年
- 個人識別信息保留期：1 年
- 匿名化數據可永久保留

---

**版本**: v1.0  
**最後更新**: 2025-01-05  
**負責人**: 數據分析團隊

