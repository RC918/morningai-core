# 修正 Render 來源倉庫並開啟 Auto-Deploy

本指南將引導您完成修正 Render 服務的來源倉庫並開啟自動部署 (Auto-Deploy) 的步驟。

## 1. 登入 Render Dashboard

- 前往 [Render Dashboard](https://dashboard.render.com/) 並登入您的帳戶。
- 選擇 `morningai-core` 服務。

## 2. 修正來源倉庫

- 在服務頁面，導航到 **Settings** > **Source**。
- 點擊 **"Connect a different repository"**。
- 在彈出的視窗中，搜索並選擇 `RC918/morningai-core`。
- 確認分支為 `main`。

## 3. 開啟 Auto-Deploy

- 在 **Settings** > **Build & Deploy** 中，找到 **Auto-Deploy** 選項。
- 確保 Auto-Deploy 已設置為 **"Yes"**。
- 這將確保每次推送到 `main` 或 `staging` 分支時，都會自動觸發新的部署。

## 4. 產出：截圖

- 完成上述步驟後，請截取一張 **Settings** 頁面的圖片，確保截圖中清晰顯示以下兩點：
    1. **Repository**: `RC918/morningai-core`
    2. **Auto-Deploy**: `Yes`

- 請將此截圖作為 PR 的一部分提交。


