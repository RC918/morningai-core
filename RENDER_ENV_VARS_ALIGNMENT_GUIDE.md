# Render 環境變數對齊指南

本指南將引導您完成 Render 服務的環境變數設置和核對。

## 1. 登入 Render Dashboard

- 前往 [Render Dashboard](https://dashboard.render.com/) 並登入您的帳戶。
- 選擇 `morningai-core` 服務。

## 2. 導航到環境變數設置

- 在服務頁面，導航到 **Environment**。

## 3. 設置/核對環境變數

- 請確保以下環境變數已正確設置：

  - **`ALLOWED_HOSTS`**
    - **值**: `api.morningai.me,morningai-core.onrender.com,localhost,127.0.0.1`
    - **說明**: 用於 FastAPI 的 `TrustedHostMiddleware`，限制允許的 Host 標頭。

  - **`TRUSTED_PROXY_COUNT`**
    - **值**: `1`
    - **說明**: 告訴 FastAPI 應用程序它運行在一個代理之後（例如 Cloudflare 和 Render 的負載均衡器），以便正確處理 `X-Forwarded-For` 等標頭。

- **其他變數**:
  - 請核對其他現有的資料庫、Supabase、遙測和 Sentry 相關的環境變數，確保它們的值保持不變且正確無誤。

## 4. 產出：截圖

- 完成上述步驟後，請截取一張 **Environment** 頁面的圖片。
- **重要提示**: 在截圖前，請務必遮罩或隱藏所有敏感信息，例如資料庫密碼、API 金鑰等。
- 請將此截圖作為 PR 的一部分提交。


