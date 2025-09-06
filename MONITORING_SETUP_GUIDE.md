# 監控系統設置指南

本指南說明如何為 morningai-core 後端服務配置 Sentry、UptimeRobot 和 Grafana 監控。

## 1. Sentry 錯誤追蹤

Sentry 用於即時追蹤和調試生產環境中的錯誤。

### 配置步驟：

1.  **登入 Sentry**: 前往 [Sentry.io](https://sentry.io/) 並登入您的帳戶。
2.  **獲取 DSN**: 
    *   如果您尚未為 `morningai-core` 創建專案，請先創建一個新的 Python 專案。
    *   導航到 **[Project] -> Settings -> Client Keys (DSN)**。
    *   複製 DSN 字串。
3.  **設置環境變數**: 
    *   在 Render 服務的環境變數中，添加一個新的鍵值對：
      *   **Key**: `SENTRY_DSN`
      *   **Value**: `在此處貼上您的 Sentry DSN`
4.  **重新部署**: 保存環境變數後，觸發一次新的部署以使配置生效。

**驗證**: 部署完成後，您可以通過觸發一個測試錯誤來驗證 Sentry 是否正常工作。

## 2. UptimeRobot 服務可用性監控

UptimeRobot 用於監控 `/health` 端點，確保服務持續在線。

### 配置步驟：

1.  **登入 UptimeRobot**: 前往 [UptimeRobot.com](https://uptimerobot.com/) 並登入。
2.  **新增監控器**: 
    *   點擊 "Add New Monitor"。
    *   **Monitor Type**: 選擇 `HTTP(s)`。
    *   **Friendly Name**: 輸入 `morningai-core API Health`。
    *   **URL (or IP)**: 輸入 `https://api.morningai.me/health`。
    *   **Monitoring Interval**: 建議設置為 `5 minutes`。
    *   **Monitor Timeout**: 建議設置為 `30 seconds`。
3.  **警報通知**: 
    *   在 "Alert Contacts to Notify" 部分，選擇您希望接收警報的通知渠道（例如，Email、Slack）。
4.  **保存**: 點擊 "Create Monitor" 完成設置。

**驗證**: 創建後，UptimeRobot 將立即開始檢查端點。您應該會在幾分鐘內看到第一個綠色的 "Up" 狀態。

## 3. Grafana 儀表板

Grafana 用於可視化關鍵性能指標 (KPIs)。

### 配置步驟：

1.  **準備儀表板 JSON**: 
    *   您需要一個預先定義好的 Grafana 儀表板 JSON 模型。如果沒有，您需要先創建一個，導出其 JSON。
    *   儀表板應包含以下指標：
        *   P95 Latency
        *   Error Rate (from Sentry or logs)
        *   Database Connection Pool Usage
        *   RAG Hit Rate
        *   Request per minute (RPM)

2.  **導入儀表板**: 
    *   登入您的 Grafana 實例。
    *   導航到 **Dashboards -> Import**。
    *   **Import via panel json**: 貼上您的儀表板 JSON 內容。
    *   點擊 "Load"。
3.  **配置數據源**: 
    *   在導入過程中，Grafana 會要求您為儀表板中的每個面板選擇對應的數據源（例如，Prometheus、PostgreSQL）。
    *   確保數據源已正確配置並連接。
4.  **保存儀表板**: 點擊 "Import" 完成。

**驗證**: 導入後，儀表板應開始顯示來自您數據源的即時數據。請檢查所有面板是否正常加載且無錯誤。

### 儀表板範例 JSON (佔位符)

```json
{
  "__inputs": [],
  "__requires": [],
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "title": "P95 Latency",
      "type": "graph",
      "datasource": "Prometheus",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[5m])) by (le))"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "stat",
      "datasource": "Prometheus",
      "targets": [
        {
          "expr": "sum(rate(http_server_requests_seconds_count{status=~\"5..\"}[5m])) / sum(rate(http_server_requests_seconds_count[5m]))"
        }
      ]
    }
  ],
  "schemaVersion": 36,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "MorningAI Core API Dashboard",
  "uid": "unique-dashboard-id-placeholder",
  "version": 1
}
```

**注意**: 上述 JSON 是一個簡化的範例。您需要根據您的實際數據源和指標進行調整。


