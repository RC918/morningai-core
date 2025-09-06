# Render 環境變數設置指南

## 必需環境變數配置

### 1. Host 白名單配置
```
變數名: ALLOWED_HOSTS
變數值: api.morningai.me,morningai-core.onrender.com,localhost,127.0.0.1
```

### 2. 數據庫配置（如果使用）
```
變數名: DATABASE_URL
變數值: [您的數據庫連接字符串]
```

### 3. OpenAI API 配置（如果使用）
```
變數名: OPENAI_API_KEY
變數值: [您的 OpenAI API 密鑰]
```

### 4. 環境標識
```
變數名: ENVIRONMENT
變數值: production
```

## 設置步驟

### 步驟 1：登入 Render Dashboard
1. 訪問 [Render Dashboard](https://dashboard.render.com/)
2. 登入您的帳戶

### 步驟 2：找到服務
1. 在服務列表中找到 `morningai-core-staging`
2. 點擊進入服務詳情頁面

### 步驟 3：修改來源倉庫
1. 點擊左側導航的 "Settings"
2. 在 "Repository" 部分：
   - 點擊 "Connect a different repo"
   - 選擇 `RC918/morningai-core`
   - 確認分支為 `main`
3. 在 "Auto-Deploy" 部分：
   - 確保 "Auto-Deploy" 開關為 **ON**

### 步驟 4：配置環境變數
1. 在 Settings 頁面，找到 "Environment Variables" 部分
2. 點擊 "Add Environment Variable"
3. 逐一添加上述必需的環境變數

### 步驟 5：清除緩存並重新部署
1. 在服務詳情頁面，點擊右上角的 "Manual Deploy"
2. 選擇 "Clear build cache & deploy"
3. 等待部署完成

## 驗證步驟

### 1. 檢查部署狀態
- 在 Render Dashboard 中確認部署狀態為 "Live"
- 檢查部署日誌，確認沒有錯誤

### 2. 測試健康檢查端點
```bash
# 測試 Render 直接 URL
curl https://morningai-core-staging.onrender.com/health

# 測試 Cloudflare 代理 URL（修復 Worker 後）
curl https://api.morningai.me/health
```

### 3. 檢查應用程序日誌
在 Render Dashboard 的 "Logs" 標籤中，查找以下日誌：
```
[STARTUP] TrustedHostMiddleware allowed_hosts: ['api.morningai.me', 'morningai-core.onrender.com', 'localhost', '127.0.0.1']
```

## 故障排除

### 問題 1：部署失敗
**可能原因**：
- 來源倉庫配置錯誤
- 環境變數缺失
- Python 版本不匹配

**解決方案**：
1. 檢查來源倉庫是否為 `RC918/morningai-core`
2. 確認所有必需的環境變數都已設置
3. 檢查 `runtime.txt` 是否為 `python-3.11.9`

### 問題 2：健康檢查失敗
**可能原因**：
- Host 白名單配置錯誤
- Cloudflare Worker 干擾

**解決方案**：
1. 檢查 `ALLOWED_HOSTS` 環境變數
2. 參考 `CLOUDFLARE_WORKER_TROUBLESHOOTING_GUIDE.md`

### 問題 3：自動部署不工作
**可能原因**：
- Auto-Deploy 未開啟
- GitHub webhook 配置問題

**解決方案**：
1. 確認 Auto-Deploy 開關為 ON
2. 在 GitHub 倉庫設置中檢查 webhooks

## 安全注意事項

1. **敏感信息保護**：
   - 不要在代碼中硬編碼 API 密鑰
   - 使用 Render 的環境變數功能

2. **最小權限原則**：
   - 只設置應用程序實際需要的環境變數
   - 定期輪換 API 密鑰

3. **監控和日誌**：
   - 定期檢查應用程序日誌
   - 設置監控告警

## 完成檢查清單

- [ ] 來源倉庫已改為 `RC918/morningai-core`
- [ ] Auto-Deploy 已開啟
- [ ] `ALLOWED_HOSTS` 環境變數已設置
- [ ] 其他必需環境變數已配置
- [ ] 清除緩存並重新部署已執行
- [ ] 部署狀態為 "Live"
- [ ] 健康檢查端點返回 200
- [ ] 應用程序日誌顯示正確的 allowed_hosts

---
**注意**：完成所有設置後，請截圖保存 Render 設置頁面，作為驗證證據。

