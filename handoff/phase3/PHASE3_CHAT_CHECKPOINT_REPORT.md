# Phase 3 聊天模組驗收報告

## 驗收結論

各位辛苦了，已檢視本批「聊天系統核心架構 + API」交付。整體完成度高，介面清晰，具備 GPT+RAG、會話管理、意圖分析、自動追問、RBAC、Rate Limit、租戶隔離、監控與審計等關鍵能力。

### 一、驗收結論
- **功能面**：/chat/send、sessions、knowledge 搜索/CRUD、feedback、stats 等端點齊備，對話記憶與 fallback 策略合理。
- **安全/治理**：RBAC、速率限制（30/h）、審計日誌介面具雛形。
- **可運維性**：Redis 快取、統計/監控欄位完備。

**結論：驗收通過（條件式），可進入下一輪整合測試與優化。**

「條件式」定義：在向量庫實作與離線評測基線建立前，標記為 Beta，僅用於內測與資料收斂。

---

## 二、風險與需補強項（高優先）

### 1. RAG 真正向量檢索
- 需落地向量 DB（pgvector / Pinecone / Weaviate 任一），補齊：索引建置、chunking 策略、Embedding 模型、相似度閾值、Citation 回傳格式。

### 2. 可量化的準確率 95% 定義
- 製作離線評測（offline eval）管線與資料集（dev/test）
- 指標：Exact/Partial Match、Hallucination 率、含 RAG Citation 的 Quality 分數
- 產物：eval/ 目錄 + eval-run.sh + 報表（baseline 與門檻線）

### 3. 資料治理與隱私
- PII 遮蔽與脫敏（prompt 前與儲存前雙層處理）
- 保留期（≤30 天）與刪除流程（Right-to-be-forgotten）
- 產物：privacy-policy.md + retention-config.md + 程式層面開關

### 4. Token/模型與 Prompt 版本化
- 模型、溫度、top_p、system prompt 全納入 版本與審計（含 rollback）
- 產物：prompts/（版本檔）+ model-registry.json + 審計欄位

### 5. Refresh Token 與黑名單
- 補強 refresh token 有效期、撤銷/黑名單機制，異常外洩時可即時失效。

---

## 三、立即可執行的 Smoke 測試（供內部驗證）

以 manager 帳號進行（具租戶權限）

```bash
# 1) 登入取得 JWT
curl -s -X POST "$API_BASE/api/v1/auth/login" \
 -H "Content-Type: application/json" \
 -d '{"email":"manager@morningai.com","password":"manager123"}' | jq -r .access_token

# 2) 建立會話
curl -s -X POST "$API_BASE/api/v1/chat/sessions" \
 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
 -d '{"title":"Demo","metadata":{"source":"smoke"}}' | jq .

# 3) 發送訊息（會觸發 RAG→GPT fallback）
curl -s -X POST "$API_BASE/api/v1/chat/send" \
 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
 -d '{"session_id":"<SID>","message":"請介紹我們的定價方案"}' | jq .

# 4) 搜索知識庫（確認語義檢索/占位）
curl -s -X POST "$API_BASE/api/v1/chat/knowledge/search" \
 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
 -d '{"query":"pricing","top_k":5}' | jq .

# 5) 回饋
curl -s -X POST "$API_BASE/api/v1/chat/feedback" \
 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
 -d '{"session_id":"<SID>","message_id":"<MID>","score":1,"reason":"good"}' | jq .
```

---

## 四、交付物與檔案放置（請於本迭代內補齊）

### 必要文檔
- **openapi.yaml**：新增 /chat/ 全端點（schema + 範例 + 錯誤碼）
- **postman-collection.json**：加入 Chat 端點 + 測試資料夾（Sessions/Send/Knowledge/Feedback/Stats）
- **curl-examples.sh**：加入 run_chat_quick_tests 套件

### 評測系統
- **eval/**：dataset/, eval-run.sh, report.md（含 95% 定義與基線）

### RAG 系統
- **rag/**：vector-config.md、chunking.md、citation-spec.md

### 安全治理
- **security/**：privacy-policy.md、retention-config.md、rt-blacklist.md

### 版本管理
- **prompts/**：system_v1.md、assistant_v1.md、model-registry.json

**檔案一律放 morningai-core/handoff/phase3/，並同步提供 zip 打包（handoff-phase3-chat.zip）。同時 push 到 GitHub 並建立對應 tag（雙軌交付）。**

---

## 五、時程與里程碑（請照此推進）

### T+3 天（短期）
- 向量 DB 選型與 PoC（pgvector 或託管式向量庫）
- openapi.yaml/Postman/curl 補齊 Chat 端點
- 建立 eval/ 初版（小樣本可跑通）

### T+7 天（中期）
- 向量庫整合上線（檔案→切片→嵌入→索引→檢索→citation）
- 離線評測報告 v1（≥500 條樣本），給出目前準確率
- Refresh Token 黑名單實作與回歸測試

### T+14 天（穩定）
- 準確率達 ≥95%（以 report.md 指標計算）
- 隱私/保留期策略與刪除流程可驗證
- 監控儀表：響應時間、錯誤率、fallback 比例、citation 命中率

---

## 六、前端整合（與 morningai-web 對齊）

### UI 組件
- 新增 Chat UI（訊息串、思考中狀態、追問 UI、citation 展示）
- i18n 文案 keys：chat.input.placeholder, chat.followup.ask, chat.citation.title …
- 實作 撤回/重生、/new 會話、/rename、/delete

### 分析追蹤
- GA4 事件：chat.sent, chat.reply, chat.fallback, chat.feedback（含語言/租戶維度）

---

## 最終結論

✅ **本批 Chat 模組驗收通過（Beta），可進入 向量庫整合 + 離線評測 階段。**

請依上列 交付物清單與時程（T+3 / T+7 / T+14） 完成補強，並維持 zip + GitHub 雙軌交付與打 tag 規範。

---

**報告日期：** 2025-01-05  
**驗收人員：** CTO  
**狀態：** 條件式通過（Beta）  
**下一里程碑：** 向量庫整合與評測系統建立

