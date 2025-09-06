# Render 存儲庫重新綁定操作指南

## 🎯 目標
將 Render 服務從 `RC918/morning-ai-saas-mvp` 重新綁定到 `RC918/morningai-core`，並完成部署驗證。

## A. 立即執行步驟（30分內完成）

### 1. 重新綁定正確的 repo

#### 操作步驟：
1. **登入 Render Console**: https://dashboard.render.com
2. **找到 API 服務**: `morning-ai-api` (Service ID: srv-d2q4s17diees73cjin20)
3. **進入設置**: 點擊服務 → Settings → Git
4. **更改存儲庫**: 
   - 點擊「Connect account or change repository」
   - 選擇 `RC918/morningai-core`
   - 確認主分支為 `main`
5. **啟用自動部署**: 
   - ✅ Enable Auto-Deploy on commit

#### 預期結果：
```
Repository: https://github.com/RC918/morningai-core
Branch: main
Auto-Deploy: Enabled
```

### 2. 清快取並重建

#### 操作步驟：
1. **進入部署頁面**: Deploys 標籤
2. **清除快取**: 點擊「Clear build cache & deploy」
3. **等待建置**: 監控建置進度和日誌

#### 預期結果：
- 新部署使用 commit: `6a0aa95558f5ade8080aaa622324c08bd68fcea1`
- 建置成功，服務狀態為 "Live"

### 3. 環境變數校正

#### 必要環境變數檢查清單：
```bash
# 資料庫配置
DATABASE_URL=postgresql://postgres.deuytovttpkgewgzqjxx:hgQtFxlxWefSJsmZ@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require

# API 配置
OPENAI_API_KEY=[需要設置]
OPENAI_API_BASE=https://api.openai.com/v1

# JWT 配置
JWT_SECRET_KEY=[自動生成或手動設置]
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 應用配置
APP_ENV=production
DEBUG=false
LOG_LEVEL=info

# CORS 和主機配置
CORS_ORIGINS=https://app.morningai.me,http://localhost:3000
ALLOWED_HOSTS=api.morningai.me,admin.morningai.me,morning-ai-api.onrender.com,localhost,127.0.0.1

# 監控配置
SENTRY_DSN=[需要設置]
SENTRY_ENVIRONMENT=production
```

#### 操作步驟：
1. **進入環境變數**: Settings → Environment
2. **檢查並更新**: 對照上述清單補齊缺失變數
3. **特別注意**: DATABASE_URL 必須包含 `sslmode=require`

### 4. 自訂網域綁定核對

#### 檢查項目：
1. **Custom Domains 狀態**:
   - `api.morningai.me`: ✅ Active
   - `admin.morningai.me`: ✅ Active

2. **SSL 憑證狀態**: Active

3. **Cloudflare 設置確認**:
   - SSL 模式: Full (Strict) ✅
   - 橘雲代理: 已啟用 ✅

#### TrustedHostMiddleware 確認：
我們的代碼已包含以下配置：
```python
ALLOWED_HOSTS = [
    "api.morningai.me",
    "admin.morningai.me",
    "morning-ai-api.onrender.com",
    "localhost",
    "127.0.0.1",
    "*.morningai.me"
]
```

### 5. 部署完成後 Smoke 檢查

#### 驗證腳本：
```bash
# 1. 基本健康檢查
curl -I https://api.morningai.me/health
# 預期: HTTP/2 200

# 2. 詳細健康檢查
curl -s https://api.morningai.me/healthz | jq '.'
# 預期: {"status": "ok", ...}

# 3. 資料庫測試（如果有）
curl -s https://api.morningai.me/db-test | jq '.'
# 預期: HTTP 200

# 4. 資料庫資訊（如果有）
curl -s https://api.morningai.me/db-info | jq '.'
# 預期: HTTP 200

# 5. Host Header 驗證
curl -sS https://api.morningai.me/health -H 'Host: api.morningai.me'
# 預期: 不再出現 "Invalid host"

# 6. CORS 驗證
curl -i https://api.morningai.me/health -H 'Origin: https://app.morningai.me'
# 預期: 包含 CORS headers
```

#### 性能目標：
- **P95 延遲**: < 500ms
- **錯誤率**: < 1%
- **可用性**: > 99.9%

## B. 後續保障（同日完成）

### 1. 分支保護 / CI Gate

#### GitHub Actions 檢查：
```bash
# 檢查 CI 工作流程
ls -la .github/workflows/
# 確認包含: ci.yml, db-smoke.yml (如果有)

# 設置分支保護規則
# GitHub → Settings → Branches → Add rule
# Branch name pattern: main
# Require status checks: ✅
# Require branches to be up to date: ✅
```

### 2. 事件追蹤與告警

#### Sentry 配置：
```bash
# 環境變數設置
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
```

#### Uptime 監控：
- **監控 URL**: https://api.morningai.me/health
- **檢查頻率**: 每 5 分鐘
- **告警條件**: 連續 3 次失敗

#### 連線池監控：
- **80% 使用率**: 黃燈警告
- **90% 使用率**: 紅燈告警

## C. 風險控制 / 回滾

### 回滾條件：
- 重綁後 10 分內無法成功部署
- 健康檢查持續失敗
- 嚴重性能問題

### 回滾步驟：
1. **手動部署**: Deploy latest commit (上一個成功版本)
2. **檢查日誌**: Render Build Log 是否引用舊 repo URL
3. **映像回滾**: 使用最後成功的 image
4. **服務保持**: 確保服務持續可用

### 舊專案處理：
- **解除綁定**: morning-ai-saas-mvp 在 Render 端解除綁定
- **標註狀態**: 標記為 deprecated
- **避免誤觸**: 防止後續意外觸發

## 📋 驗收清單

### 必須提供的截圖：
1. **Render Service 截圖**:
   - 服務名稱和關聯 repo 顯示
   - 確認綁定到 morningai-core

2. **最新部署 commit SHA**:
   - 顯示 commit: 6a0aa95558f5ade8080aaa622324c08bd68fcea1
   - 部署狀態: Live

3. **API 響應截圖**:
   - `/healthz` 響應內容
   - `/db-info` 響應內容（如果有）

4. **DNS/SSL 憑證狀態**:
   - Custom Domains 顯示 Active
   - SSL 憑證有效

### 驗收標準：
✅ 正確 repo 綁定 + Auto-Deploy 開啟  
✅ Custom Domain 運作，無 Invalid host  
✅ Smoke 測試全綠（所有端點返回 200）  
✅ 監控與分支保護規則啟用  

## 🚀 執行時間表

| 步驟 | 預估時間 | 狀態 |
|------|----------|------|
| 重新綁定 repo | 5 分鐘 | ⏳ |
| 清快取重建 | 10-15 分鐘 | ⏳ |
| 環境變數校正 | 5 分鐘 | ⏳ |
| 自訂網域核對 | 3 分鐘 | ⏳ |
| Smoke 檢查 | 5 分鐘 | ⏳ |
| **總計** | **30 分鐘** | ⏳ |

---
**創建時間**: 2025-09-06 09:30 UTC  
**目標完成**: 2025-09-06 10:00 UTC  
**負責人**: 用戶操作 + AI 協助驗證

