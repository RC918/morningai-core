# 監控設置指南

## 🎯 監控目標
為 MorningAI API 建立完整的監控和告警系統，確保生產環境的穩定性和可觀測性。

## 📊 監控組件

### 1. Sentry 錯誤追蹤

#### 設置步驟：
1. **創建 Sentry 項目**:
   - 登入 https://sentry.io
   - 創建新項目：`morningai-api-production`
   - 選擇平台：Python/FastAPI

2. **獲取 DSN**:
   ```
   SENTRY_DSN=https://your-key@sentry.io/project-id
   ```

3. **Render 環境變數配置**:
   ```bash
   SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   SENTRY_ENVIRONMENT=production
   SENTRY_RELEASE=v1.0.0
   ```

4. **告警規則**:
   - 錯誤率 > 1%：立即告警
   - 新錯誤類型：立即告警
   - 性能問題：P95 > 1000ms

#### 驗證方式：
```bash
# 測試 Sentry 集成
curl -X POST https://api.morningai.me/test-error
# 應該在 Sentry Dashboard 中看到錯誤
```

### 2. Uptime Robot 可用性監控

#### 監控配置：
```yaml
Monitor Type: HTTP(s)
URL: https://api.morningai.me/health
Friendly Name: MorningAI API Health
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
```

#### 告警設置：
- **Down Alert**: 連續 3 次失敗（15分鐘）
- **Up Alert**: 服務恢復時
- **通知方式**: Email + Slack/Discord

#### 高級監控：
```yaml
# 多端點監控
Endpoints:
  - https://api.morningai.me/health (基本健康)
  - https://api.morningai.me/healthz (詳細健康)
  - https://api.morningai.me/api/v1/health (API 健康)

# 關鍵字監控
Expected Keywords:
  - "healthy"
  - "operational"
  - "200"
```

### 3. 資料庫連線池監控

#### 監控指標：
```python
# 在 FastAPI 應用中添加監控端點
@app.get("/metrics/db-pool")
async def db_pool_metrics():
    pool_info = await get_db_pool_info()
    return {
        "total_connections": pool_info.total,
        "active_connections": pool_info.active,
        "idle_connections": pool_info.idle,
        "usage_percentage": (pool_info.active / pool_info.total) * 100
    }
```

#### 告警閾值：
- **80% 使用率**: 黃燈警告
- **90% 使用率**: 紅燈告警
- **95% 使用率**: 緊急告警

### 4. 性能監控

#### 關鍵指標：
```yaml
Response Time:
  - P50 < 200ms
  - P95 < 500ms
  - P99 < 1000ms

Throughput:
  - RPS (Requests Per Second)
  - 錯誤率 < 1%

Resource Usage:
  - CPU < 80%
  - Memory < 85%
  - Disk I/O
```

#### Prometheus 集成：
```python
# 在 FastAPI 中添加 Prometheus 指標
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🚨 告警配置

### 1. 緊急告警（立即通知）
- API 服務完全不可用
- 錯誤率 > 5%
- 資料庫連線池 > 95%
- P95 響應時間 > 2000ms

### 2. 警告告警（5分鐘內通知）
- 錯誤率 > 1%
- 資料庫連線池 > 80%
- P95 響應時間 > 500ms
- 新錯誤類型出現

### 3. 資訊告警（30分鐘內通知）
- 部署完成
- 配置變更
- 定期健康報告

## 📱 通知渠道

### 1. Email 通知
```yaml
Primary: team@morningai.com
Secondary: admin@morningai.com
Emergency: on-call@morningai.com
```

### 2. Slack/Discord 集成
```yaml
Channel: #alerts-production
Webhook: https://hooks.slack.com/services/...
Format: Structured alerts with context
```

### 3. SMS 通知（緊急情況）
```yaml
Emergency Contacts:
  - +1-xxx-xxx-xxxx (Primary)
  - +1-xxx-xxx-xxxx (Secondary)
```

## 📈 監控儀表板

### 1. Grafana Dashboard
```yaml
Panels:
  - API Response Time (P50, P95, P99)
  - Request Rate (RPS)
  - Error Rate (%)
  - Database Connection Pool
  - System Resources (CPU, Memory)
  - Uptime Percentage
```

### 2. Sentry Dashboard
```yaml
Views:
  - Error Trends
  - Performance Issues
  - Release Health
  - User Impact
```

### 3. Uptime Robot Dashboard
```yaml
Metrics:
  - Uptime Percentage
  - Response Time Trends
  - Incident History
  - SLA Compliance
```

## 🔧 實施檢查清單

### Phase B1: 基礎監控（今日完成）
- [ ] Sentry 項目創建和 DSN 配置
- [ ] Uptime Robot 基本監控設置
- [ ] Render 環境變數更新
- [ ] 基礎告警規則配置

### Phase B2: 高級監控（本週完成）
- [ ] 資料庫連線池監控
- [ ] Prometheus 指標集成
- [ ] Grafana 儀表板設置
- [ ] 多端點監控配置

### Phase B3: 告警優化（下週完成）
- [ ] 告警閾值調優
- [ ] 通知渠道測試
- [ ] 值班輪換設置
- [ ] 監控文檔完善

## 🧪 監控驗證

### 驗證腳本：
```bash
# 1. 測試 Sentry 集成
curl -X POST https://api.morningai.me/test-sentry

# 2. 測試告警觸發
curl https://api.morningai.me/trigger-alert

# 3. 檢查監控端點
curl https://api.morningai.me/metrics

# 4. 驗證 Uptime Robot
# 在 Uptime Robot Dashboard 檢查狀態
```

### 驗收標準：
- ✅ Sentry 能接收到錯誤報告
- ✅ Uptime Robot 正常監控並發送測試告警
- ✅ 所有監控端點返回正確數據
- ✅ 告警通知渠道正常工作

## 📋 監控 SLA

### 服務等級目標：
```yaml
Availability: 99.9% (8.76 hours downtime/year)
Response Time: P95 < 500ms
Error Rate: < 0.1%
MTTR: < 15 minutes (Mean Time To Recovery)
```

### 監控覆蓋率：
```yaml
API Endpoints: 100%
Database Queries: 100%
External Dependencies: 100%
System Resources: 100%
```

---
**創建時間**: 2025-09-06 09:35 UTC  
**實施目標**: Phase B1 今日完成  
**負責人**: DevOps Team + AI 協助

