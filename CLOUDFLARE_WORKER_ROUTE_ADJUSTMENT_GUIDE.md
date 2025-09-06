# Cloudflare Worker 路由調整指南

本指南將引導您完成 Cloudflare Worker 的路由調整，以排除健康檢查和公開文件路徑。

## 1. 登入 Cloudflare Dashboard

- 前往 [Cloudflare Dashboard](https://dash.cloudflare.com/) 並登入您的帳戶。
- 選擇 `morningai.me` 域名。

## 2. 導航到 Workers & Pages

- 在左側菜單中，選擇 **Workers & Pages**。
- 點擊 `morning-ai-api-proxy` Worker 進入其配置頁面。

## 3. 調整路由

- 導航到 **Routes** 標籤頁。
- 您將看到現有的路由規則。我們需要修改或添加規則，以確保健康檢查等路徑不被 Worker 處理。

### 選項 A：修改現有路由（推薦）

- 如果您當前有一條 `api.morningai.me/*` 的路由，請將其修改為 `api.morningai.me/api/*`。
- 這樣，只有 `/api/` 開頭的路徑會被 Worker 處理，而 `/health`, `/healthz`, `/openapi.json`, `/docs` 等將被繞過。

### 選項 B：添加排除路由

- 如果您希望保持 `api.morningai.me/*` 的主路由，可以為需要排除的路徑添加 **None** Worker 的路由。
- 點擊 **"Add route"** 並創建以下路由：
    - **Route**: `api.morningai.me/health`
    - **Worker**: `None`
    - **Route**: `api.morningai.me/healthz`
    - **Worker**: `None`
    - **Route**: `api.morningai.me/openapi.json`
    - **Worker**: `None`
    - **Route**: `api.morningai.me/docs*`
    - **Worker**: `None`

## 4. 產出：截圖

- 完成上述步驟後，請截取一張 **Routes** 標籤頁的圖片，確保截圖中清晰顯示 `/health*` 等路徑已被排除或設置為直通。
- 請將此截圖作為 PR 的一部分提交。


