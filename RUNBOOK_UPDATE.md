# Runbook 更新：Cloudflare Worker 變更影響與回滾

本文件旨在補充現有 Runbook，詳細說明 Cloudflare Worker 的變更、潛在影響以及緊急情況下的回滾步驟。

## 1. Cloudflare Worker 變更摘要

為了修復 `Host` 標頭驗證問題並確保健康檢查端點 (`/health`, `/healthz`) 的可用性，我們對 Cloudflare Worker 的路由規則進行了以下調整：

- **舊規則**: `api.morningai.me/*` 的所有請求都會被 Worker 攔截和處理。
- **新規則**: 只有 `api.morningai.me/api/*` 路徑下的請求會被 Worker 攔截。其他路徑（包括根路徑 `/` 以及 `/health`, `/healthz`, `/version.json` 等）將直接穿透到源服務器 (Render)。

### 影響分析：

- **正面影響**:
  - **解決 Host 驗證失敗**: 健康檢查請求現在可以直接到達 Render 服務，避免了因 Worker 修改 `Host` 標頭而導致的 `403 Forbidden` 錯誤。
  - **提高監控準確性**: UptimeRobot 和其他監控工具現在可以直接檢查後端服務的真實健康狀態。
  - **簡化路由邏輯**: 路由規則更加清晰，減少了不必要的 Worker 執行。

- **潛在風險**:
  - **意外的路由行為**: 如果未來在根路徑下添加了需要 Worker 處理的新端點，可能會因為當前規則而繞過 Worker，導致功能異常。 **緩解措施**: 未來所有需要 Worker 處理的 API 都應規劃在 `/api/` 路徑下。
  - **回滾複雜性**: 如果需要回滾，必須同時考慮應用程序代碼和 Cloudflare 配置。

## 2. 緊急回滾步驟

在以下情況下，您可能需要執行緊急回滾：

-   部署新版本後，`api.morningai.me` 的核心功能出現大規模故障。
-   監控系統顯示服務在部署後持續不可用。

回滾分為兩個部分：**應用程序回滾** 和 **Cloudflare Worker 規則回滾**。在大多數情況下，僅回滾應用程序就足夠了。

### A. 應用程序回滾 (Render)

這是首選的快速回滾方案，預計可在 **2-3 分鐘** 內完成。

1.  **登入 Render Dashboard**:
    *   前往 [morningai-core 服務頁面](https://dashboard.render.com/web/srv-d2tgr0p5pdvs739ig030)。

2.  **導航到部署歷史**: 
    *   在左側菜單中選擇 **Deployments**。

3.  **選擇並重新部署舊版本**: 
    *   找到部署失敗前的最後一個成功部署記錄 (狀態為 `Live`)。
    *   點擊該部署記錄右側的 **"Redeploy"** 按鈕。

4.  **驗證回滾**: 
    *   等待部署完成（狀態變為 `Live`）。
    *   運行以下命令驗證服務是否恢復正常：
        ```bash
        curl -sS -I https://api.morningai.me/healthz
        ```
    *   預期應返回 `HTTP/2 200 OK`。

### B. Cloudflare Worker 規則回滾

**僅在確定問題是由於 Worker 路由規則更改引起時才執行此操作。**

1.  **登入 Cloudflare Dashboard**:
    *   前往 [Cloudflare 儀表板](https://dash.cloudflare.com/) 並選擇 `morningai.me` 域名。

2.  **導航到 Workers 路由**: 
    *   在左側菜單中選擇 **Workers & Pages**。
    *   在 `morning-ai-api-proxy` Worker 下，點擊 **Routes**。

3.  **修改路由規則**: 
    *   找到 `api.morningai.me/api/*` 這條規則。
    *   點擊 **Edit**。
    *   將 **Route** 從 `api.morningai.me/api/*` 修改回 `api.morningai.me/*`。
    *   點擊 **Save**。

4.  **驗證回滾**: 
    *   等待幾秒鐘讓變更生效。
    *   再次運行健康檢查，並測試之前出現問題的功能。

## 3. Runbook 維護

-   **定期審查**: 建議每季度審查一次此 Runbook，確保其與當前的系統架構保持一致。
-   **變更記錄**: 對 Cloudflare Worker 或 Render 部署流程的任何重大變更都應在此處更新。


