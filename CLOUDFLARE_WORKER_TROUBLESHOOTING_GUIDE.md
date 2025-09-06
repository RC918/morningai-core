# Cloudflare Worker 干擾問題排除指南

## 問題描述

根據測試結果，發現以下異常行為：

### 症狀
- ✅ **Render 直接 URL** 正常工作：
  - `https://morningai-core-staging.onrender.com/health` → 200 OK
  - `https://morningai-core-staging.onrender.com/healthz` → 200 OK

- ⚠️ **Cloudflare 代理 URL** 部分異常：
  - `https://api.morningai.me/health` → 400 "Invalid host" ❌
  - `https://api.morningai.me/healthz` → 200 OK ✅

### 問題分析
1. **路徑特異性**：只有 `/health` 路徑受影響，`/healthz` 正常
2. **代理特異性**：Render 直接 URL 完全正常，問題出現在 Cloudflare 層
3. **可能原因**：Cloudflare Worker 在 `/health` 路徑上運行，攔截請求

## 排除步驟

### 步驟 1：檢查 Cloudflare Workers
1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 選擇 `morningai.me` 域名
3. 進入 **Workers & Pages** 部分
4. 檢查是否有 Workers 綁定到 `api.morningai.me` 或 `*.morningai.me`

### 步驟 2：檢查 Worker 路由規則
查看是否有以下路由規則：
- `api.morningai.me/health*`
- `api.morningai.me/*`
- `*.morningai.me/health*`

### 步驟 3：檢查 Worker 代碼
如果找到相關 Worker，檢查代碼中是否有：
```javascript
// 可能的問題代碼
if (url.pathname === '/health') {
  return new Response('Invalid host', { status: 400 });
}

// 或者主機驗證邏輯
if (!allowedHosts.includes(request.headers.get('host'))) {
  return new Response('Invalid host', { status: 400 });
}
```

## 解決方案

### 方案 A：暫時禁用 Worker（推薦）
1. 在 Cloudflare Dashboard 中找到影響 `/health` 路徑的 Worker
2. 暫時禁用該 Worker 或修改路由規則
3. 測試 `https://api.morningai.me/health` 是否恢復正常

### 方案 B：修改 Worker 代碼
如果 Worker 必須保留，修改代碼以正確處理 `/health` 請求：
```javascript
// 修正後的代碼
if (url.pathname === '/health' || url.pathname === '/healthz') {
  // 直接代理到後端，不進行額外驗證
  return fetch(request);
}
```

### 方案 C：調整路由規則
修改 Worker 路由規則，排除健康檢查端點：
- 原規則：`api.morningai.me/*`
- 新規則：`api.morningai.me/*` 但排除 `/health*` 和 `/healthz*`

### 方案 D：使用替代端點
如果無法修改 Worker，可以：
1. 使用 `/healthz` 作為主要健康檢查端點
2. 或創建新的健康檢查路徑（如 `/status`、`/ping`）

## 驗證步驟

修改後，執行以下驗證：

```bash
# 測試 /health 端點
curl -v https://api.morningai.me/health

# 測試 /healthz 端點  
curl -v https://api.morningai.me/healthz

# 檢查響應頭
curl -I https://api.morningai.me/health
```

期望結果：
- HTTP 狀態碼：200
- 響應內容：JSON 格式的健康狀態
- 無 "Invalid host" 錯誤

## 監控建議

### 設置健康檢查監控
1. **Uptime Robot** 或類似服務：
   - 監控 `https://api.morningai.me/health`
   - 監控 `https://api.morningai.me/healthz`
   - 設置 1-5 分鐘檢查間隔

2. **Cloudflare Analytics**：
   - 檢查 Worker 執行統計
   - 監控 4xx 錯誤率

3. **Render 監控**：
   - 檢查直接 URL 的健康狀態
   - 監控應用程序日誌

## 預防措施

### 1. Worker 開發最佳實踐
- 避免在健康檢查路徑上添加額外驗證
- 使用白名單方式處理特殊路徑
- 添加詳細的錯誤日誌

### 2. 路由規則管理
- 明確定義 Worker 的作用範圍
- 避免過於寬泛的路由規則
- 定期審查和清理不必要的 Workers

### 3. 測試流程
- 部署 Worker 前先在測試環境驗證
- 包含健康檢查端點的回歸測試
- 設置自動化監控告警

## 常見問題

### Q: 為什麼 /healthz 正常但 /health 異常？
A: 可能 Worker 代碼中有特定的路徑處理邏輯，或者有不同的路由規則。

### Q: 如何確認是 Worker 問題？
A: 比較 Render 直接 URL 和 Cloudflare 代理 URL 的響應，如果直接 URL 正常，則問題在 Cloudflare 層。

### Q: 可以完全禁用 Cloudflare 代理嗎？
A: 可以將 DNS 記錄設為 "DNS only"（灰雲），但會失去 CDN 和安全防護功能。

## 聯繫支援

如果問題持續存在：
1. 收集 Worker 配置截圖
2. 提供測試 URL 和錯誤響應
3. 聯繫 Cloudflare 技術支援

---
**文檔版本**: 1.0  
**最後更新**: 2025-09-06  
**適用範圍**: api.morningai.me 健康檢查端點問題

