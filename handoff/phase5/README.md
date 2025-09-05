# Phase 5: 聊天模組與 GPT+RAG 整合 (Beta)

## 快速啟動 (3分鐘內可啟動demo)

### 1. 環境準備
```bash
# 複製環境變數
cp .env.sample .env

# 編輯必要的API密鑰
nano .env
# 設置 OPENAI_API_KEY=your_openai_key
```

### 2. 一鍵啟動
```bash
# 啟動所有服務 (PostgreSQL + Redis + FastAPI)
docker-compose up -d

# 等待服務啟動 (約30秒)
sleep 30

# 執行資料庫遷移
docker exec -i morningai-db psql -U postgres -d morningai < migration.sql

# 導入種子資料
docker exec -i morningai-db psql -U postgres -d morningai < seed.sql
```

### 3. 驗證服務
```bash
# 檢查API健康狀態
curl http://localhost:8000/health

# 檢查OpenAPI文檔
open http://localhost:8000/docs
```

## 功能演示

### 聊天模組 Smoke 測試
```bash
# 執行快速測試
./run_chat_quick_tests.sh

# 或使用 Postman 集合
# 導入 postman-collection.json 並執行 "Chat Module Tests" 資料夾
```

### 手動測試流程
```bash
# 1. 登入獲取令牌
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"manager@morningai.com","password":"manager123"}' | jq -r .access_token)

# 2. 創建聊天會話
SID=$(curl -s -X POST "http://localhost:8000/api/v1/chat/sessions" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Demo Chat","metadata":{"source":"manual_test"}}' | jq -r .id)

# 3. 發送消息 (觸發 RAG→GPT fallback)
curl -s -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SID\",\"message\":\"請介紹我們的定價方案\"}" | jq .

# 4. 搜索知識庫
curl -s -X POST "http://localhost:8000/api/v1/chat/knowledge/search" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"pricing","top_k":5}' | jq .
```

## 核心功能

### ✅ 已實現功能
- **GPT+RAG 整合**: 智能 fallback 機制，RAG 無法回答時自動切換到 GPT
- **多輪對話管理**: 維持對話上下文和會話狀態
- **意圖分析**: 自動理解用戶需求和意圖
- **自動追問**: 當信息不足時主動詢問用戶
- **知識庫檢索**: 企業知識語義搜索和相關性排序
- **RBAC 權限控制**: 5種細分權限 (create/read/update/delete/manage)
- **速率限制**: 聊天 30條/小時，GPT API 20次/小時
- **租戶隔離**: 完整的多租戶數據安全
- **審計日誌**: 完整的操作記錄和追蹤
- **緩存優化**: Redis 緩存提升響應速度

### 🔄 Beta 階段限制
- 向量檢索使用模擬實現，等待真實向量數據庫整合
- 95% 準確率目標尚在評測中
- 僅供內部測試，不面向最終用戶

## API 端點

### 聊天相關
- `POST /chat/send` - 發送消息並獲取 AI 回應
- `GET /chat/sessions` - 獲取用戶會話列表
- `GET /chat/sessions/{id}/history` - 獲取聊天歷史
- `POST /chat/sessions` - 創建新會話
- `PUT /chat/sessions/{id}` - 更新會話信息
- `DELETE /chat/sessions/{id}` - 刪除會話

### 知識庫相關
- `POST /chat/knowledge/search` - 搜索知識庫
- `POST /chat/knowledge` - 創建知識庫條目
- `PUT /chat/knowledge/{id}` - 更新知識庫條目
- `DELETE /chat/knowledge/{id}` - 刪除知識庫條目

### 反饋和統計
- `POST /chat/feedback` - 提交反饋
- `GET /chat/stats` - 獲取統計信息

## 測試

### 自動化測試
```bash
# 執行所有測試
./run_all_tests.sh

# 執行聊天模組測試
./run_chat_tests.sh

# 執行評測系統
cd eval && ./eval-run.sh quick
```

### Postman 測試
1. 導入 `postman-collection.json`
2. 設置環境變數 `base_url = http://localhost:8000`
3. 執行「Chat Module Tests」資料夾中的所有測試

## 監控和分析

### 關鍵指標
- **響應時間**: 平均 < 2秒
- **準確率**: 目標 95% (評測中)
- **Fallback 比例**: RAG → GPT 切換頻率
- **用戶滿意度**: 基於反饋評分

### 日誌查看
```bash
# 查看應用日誌
docker logs morningai-api

# 查看 Redis 日誌
docker logs morningai-redis

# 查看資料庫日誌
docker logs morningai-db
```

## 故障排除

### 常見問題

1. **OpenAI API 錯誤**
   - 檢查 `.env` 中的 `OPENAI_API_KEY` 是否正確
   - 確認 API 配額未超限

2. **資料庫連接失敗**
   - 確認 PostgreSQL 服務正在運行
   - 檢查資料庫連接字符串

3. **Redis 連接失敗**
   - 確認 Redis 服務正在運行
   - 檢查 Redis 連接配置

### 重置環境
```bash
# 停止所有服務
docker-compose down

# 清理數據卷
docker-compose down -v

# 重新啟動
docker-compose up -d
```

## 下一階段計劃

### T+3 天目標
- [ ] 向量數據庫整合 (pgvector)
- [ ] OpenAPI 規格完善
- [ ] 評測基線建立

### T+7 天目標
- [ ] 95% 準確率達成
- [ ] 完整監控面板
- [ ] 生產環境部署

### T+14 天目標
- [ ] 前端整合完成
- [ ] 用戶驗收測試
- [ ] 正式發布準備

## 技術架構

### 系統組件
- **FastAPI**: Web 框架和 API 服務
- **PostgreSQL**: 主數據庫
- **Redis**: 緩存和會話存儲
- **OpenAI GPT**: 語言模型服務
- **pgvector**: 向量數據庫 (計劃中)

### 安全特性
- JWT 認證和授權
- RBAC 權限控制
- 速率限制保護
- 數據加密傳輸
- 審計日誌記錄

---

**版本**: v3.0.0-phase5-chat-beta  
**更新日期**: 2025-01-05  
**狀態**: Beta (內測)  
**負責人**: AI 工程團隊

