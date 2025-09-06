# MorningAI 專案資源清單

## 1. 平台資源對照表

| 平台 | 專案名稱 | 位置/Region | 用途 | 網域/端口 | 備份/測試 | 管理連結 | 狀態 |
|------|----------|-------------|------|-----------|-----------|----------|------|
| **Vercel** | morningai-core-staging | Global (Anycast) | 前端部署 + 反向代理 | https://morningai-core-staging.vercel.app | 自動回滾 + GitHub 版本 | [Vercel Dashboard](https://vercel.com/morning-ai/morningai-core-staging) | ✅ Live |
| **GitHub** | RC918/morningai-core | GitHub Actions | 程式碼管理 + CI/CD | N/A | GitHub 版本控制 | [GitHub Repo](https://github.com/RC918/morningai-core) | ✅ Active |
| **Cloudflare** | morningai.me (待確認) | Global Anycast | DNS + WAF | 指向 Vercel & Render | N/A | [Cloudflare Dashboard](https://dash.cloudflare.com/) | ❓ 待確認 |
| **Render** | morningai-core-staging | Oregon (預設) | FastAPI 後端 | https://morningai-core-staging.onrender.com:10000 | Render snapshot | [Render Dashboard](https://dashboard.render.com/web/srv-d2tsbb3e5dus73e51qqg) | ✅ Live |
| **Supabase** | deuytovttpkgewgzqjxx | ap-southeast-1 (Singapore) | PostgreSQL + pgvector | supabase.com:6543 | 每日備份 | [Supabase Project](https://app.supabase.com/project/deuytovttpkgewgzqjxx) | ✅ Active |
| **Sentry** | morningai-core-staging | Global | 錯誤監控 + 性能追蹤 | N/A | 事件日誌 | [Sentry Project](https://sentry.io/) | ✅ Integrated |

## 2. 詳細資源資訊

### 2.1 Vercel
- **專案名稱**: morningai-core-staging
- **組織**: Morning-Ai (Pro)
- **域名**: 
  - Primary: `morningai-core-staging.vercel.app`
  - Deployment: `morningai-core-staging-7oq6d2k80-morning-ai.vercel.app`
- **功能**: 
  - 前端靜態站點部署
  - 反向代理 `/api/*` → Render 後端
  - Firewall 已啟用 (Bot Protection)
- **連接**: GitHub RC918/morningai-core (main 分支)
- **最新部署**: commit `4d4e900` (fix: Correct Vercel proxy configuration)

### 2.2 GitHub
- **倉庫**: RC918/morningai-core
- **主分支**: main
- **CI/CD**: GitHub Actions
- **自動部署**: 
  - Vercel (前端)
  - Render (後端)
- **問題**: 
  - ❌ test-backend 失敗 (Process completed with exit code 1)
  - ❌ test-frontend 失敗 (Dependencies lock file not found)
  - ❌ lint-and-format 失敗 (Dependencies lock file not found)

### 2.3 Cloudflare
- **狀態**: ❓ 待確認是否已配置
- **預期配置**:
  - DNS: morningai.me → Vercel
  - DNS: api.morningai.me → Render (可選)
  - SSL/TLS 管理
  - WAF + Bot Management

### 2.4 Render
- **服務名稱**: morningai-core-staging
- **服務 ID**: srv-d2tsbb3e5dus73e51qqg
- **類型**: Web Service
- **運行時**: Python 3
- **URL**: https://morningai-core-staging.onrender.com
- **內部端口**: 10000 (uvicorn ASGI)
- **連接**: GitHub RC918/morningai-core (main 分支)
- **環境變數**:
  - `DATABASE_URL`: ✅ 已配置 (Supabase)
  - `OPENAI_API_KEY`: ✅ 已配置
  - `ENVIRONMENT`: staging
  - `RAG_ENABLED`: false
  - `CORS_ORIGINS`: https://morningai-core-staging.vercel.app
- **最新部署**: commit `4d4e900` (Live)

### 2.5 Supabase
- **專案 ID**: deuytovttpkgewgzqjxx
- **Region**: ap-southeast-1 (Singapore AWS)
- **資料庫**: PostgreSQL with pgvector extension
- **連接字串**: `postgresql://postgres.deuytovttpkgewgzqjxx:***@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres`
- **功能**: 
  - 主要資料庫服務
  - 向量搜尋 (pgvector)
  - 自動備份

### 2.6 Sentry
- **DSN**: `https://389e9db40bf58c06cb20317f24d357b@04509971383910400.ingest.us.sentry.io/4509971411894272`
- **功能**: 
  - 錯誤追蹤
  - 性能監控 (已禁用以避免事件迴圈衝突)
- **整合**: FastAPI 自動整合

## 3. 網路架構流程

```
用戶請求 → Cloudflare (DNS/WAF) → Vercel (前端/代理) → Render (後端 API) → Supabase (資料庫)
                                                    ↓
                                               Sentry (監控)
```

## 4. 需要確認/修復的項目

### 4.1 高優先級
- [ ] **Cloudflare 配置確認**: 檢查是否已設置 morningai.me 域名
- [ ] **GitHub CI/CD 修復**: 
  - 添加 `package-lock.json` 或 `yarn.lock`
  - 修復後端測試失敗問題

### 4.2 中優先級
- [ ] **Production 環境**: 確認是否需要 morningai-core (production) 專案
- [ ] **域名配置**: 確認 app.morningai.me 指向設置
- [ ] **SSL 憑證**: 確認所有域名的 SSL 狀態

### 4.3 低優先級
- [ ] **監控告警**: 設置 Sentry 告警到 Slack #morningai-alerts
- [ ] **備份策略**: 確認各平台的備份和災難恢復計劃

## 5. 聯絡資訊

- **GitHub 帳戶**: RC918
- **Vercel 組織**: Morning-Ai (Pro)
- **主要管理員**: ryan2939x-7499

---
*最後更新: 2025-09-06*
*文檔版本: v1.0*

