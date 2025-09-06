# MorningAI Core - 雲端架構設計文檔 (D+3)

## 📊 架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                    MorningAI Core 雲端架構                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐ │
│  │   GitHub    │    │   Render.com │    │   Supabase      │ │
│  │   Actions   │───▶│   FastAPI    │───▶│   PostgreSQL    │ │
│  │   CI/CD     │    │   Staging    │    │   + pgvector    │ │
│  └─────────────┘    └──────────────┘    └─────────────────┘ │
│         │                   │                      │        │
│         │            ┌──────────────┐             │        │
│         │            │   Render     │             │        │
│         │            │   Redis      │─────────────┘        │
│         │            └──────────────┘                      │
│         │                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐ │
│  │   GHCR      │    │  Monitoring  │    │   Secrets       │ │
│  │  Container  │    │  Grafana +   │    │   GitHub        │ │
│  │  Registry   │    │  Sentry      │    │   Environments  │ │
│  └─────────────┘    └──────────────┘    └─────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 技術選型與理由

### 後端部署：Render.com
- **優勢**：
  - 原生 Docker 支援，自動 CI/CD
  - 內建 Redis 服務，簡化架構
  - 免費 SSL，自動擴展
  - 與 GitHub 深度整合
- **服務配置**：
  - Web Service: FastAPI 應用
  - Redis Service: 緩存和會話管理
  - Environment: staging, production

### 資料庫：Supabase PostgreSQL + pgvector
- **優勢**：
  - 原生 pgvector 支援，向量搜索優化
  - 受管服務，自動備份和擴展
  - 內建 API 和即時功能
  - 完整的監控和日誌
- **配置**：
  - PostgreSQL 15+ with pgvector extension
  - Connection pooling enabled
  - Row Level Security (RLS) for multi-tenancy

### 容器化：GitHub Container Registry (GHCR)
- **優勢**：
  - 與 GitHub 原生整合
  - 免費私有倉庫
  - 精細權限控制
  - 自動化 CI/CD 觸發

### 祕密管理：GitHub Environments + Secrets
- **配置**：
  - staging environment
  - production environment
  - 分離的祕密管理
  - 最小權限原則

## 🔐 祕密與權限清單

### GitHub Secrets (Repository Level)
```yaml
# 容器倉庫
GHCR_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# Render.com 部署
RENDER_API_KEY: rnd_RyMehnBc7bcLT3L8C4HRyt2tUcTx

# Supabase 資料庫
SUPABASE_URL: https://[project-id].supabase.co
SUPABASE_ANON_KEY: [public-anon-key]
SUPABASE_SERVICE_KEY: [service-role-key]

# OpenAI API
OPENAI_API_KEY: [openai-key]
OPENAI_API_BASE: https://api.openai.com/v1

# 監控服務
SENTRY_DSN: [sentry-dsn]
GRAFANA_API_KEY: [grafana-key]
```

### GitHub Environments
#### Staging Environment
```yaml
environment: staging
secrets:
  - DATABASE_URL: postgresql://[staging-db-url]
  - REDIS_URL: redis://[staging-redis-url]
  - API_BASE_URL: https://morningai-core-staging.onrender.com
protection_rules:
  - required_reviewers: 0
  - wait_timer: 0
```

#### Production Environment
```yaml
environment: production
secrets:
  - DATABASE_URL: postgresql://[production-db-url]
  - REDIS_URL: redis://[production-redis-url]
  - API_BASE_URL: https://morningai-core.onrender.com
protection_rules:
  - required_reviewers: 1
  - wait_timer: 5
```

### 權限原則 (最小化)
```yaml
# GitHub Actions 權限
permissions:
  contents: read
  packages: write
  deployments: write
  id-token: write

# Render.com 服務權限
render_permissions:
  - deploy: staging, production
  - logs: read
  - metrics: read
  - env_vars: write (limited)

# Supabase 權限
supabase_permissions:
  - database: read, write, migrate
  - auth: manage
  - storage: read, write
  - edge_functions: deploy
```

## 🚀 部署流程

### 1. 容器化構建
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder
FROM python:3.11-slim as runtime
COPY --from=builder /app /app
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. CI/CD 管道
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Build and Push to GHCR
      - name: Deploy to Render
      - name: Run DB Migrations
      - name: Health Check
      - name: Run Evaluation Tests
```

### 3. 資料庫遷移
```bash
# 雲端一鍵執行
curl -X POST https://morningai-core-staging.onrender.com/admin/migrate \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 回滾機制
curl -X POST https://morningai-core-staging.onrender.com/admin/rollback \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"target_version": "v3.1.0"}'
```

## 📊 監控與觀測

### OpenTelemetry 配置
```python
# 自動儀表化
from opentelemetry.auto_instrumentation import sitecustomize

# 自定義指標
from opentelemetry import metrics
meter = metrics.get_meter(__name__)

# 關鍵指標
response_time_histogram = meter.create_histogram("api_response_time")
rag_hit_rate_counter = meter.create_counter("rag_hit_rate")
error_rate_counter = meter.create_counter("api_error_rate")
```

### Grafana Dashboard 指標
```yaml
key_metrics:
  - name: "API Response Time P95"
    query: "histogram_quantile(0.95, api_response_time)"
    target: "< 3000ms"
  
  - name: "Error Rate"
    query: "rate(api_error_rate[5m])"
    target: "< 1%"
  
  - name: "RAG Hit Rate"
    query: "rate(rag_hit_rate[5m]) / rate(chat_requests[5m])"
    target: "> 90%"
  
  - name: "Database Connection Pool"
    query: "pg_stat_activity_count"
    target: "< 80% of max_connections"
```

### Sentry 錯誤追蹤
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="staging"
)
```

## 🧪 評測管線 (雲端觸發)

### GitHub Actions 觸發
```bash
# 手動觸發評測
gh workflow run evaluation.yml \
  --ref main \
  --field environment=staging \
  --field test_suite=full

# API 觸發
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/RC918/morningai-core/actions/workflows/evaluation.yml/dispatches \
  -d '{"ref":"main","inputs":{"environment":"staging","test_suite":"full"}}'
```

### CLI 指令觸發
```bash
# 直接 API 調用
curl -X POST https://morningai-core-staging.onrender.com/evaluation/run \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @evaluation_config.json

# 結果下載
curl -X GET https://morningai-core-staging.onrender.com/evaluation/latest/report \
  -H "Authorization: Bearer $API_TOKEN" \
  -o evaluation_report_$(date +%Y%m%d).json
```

## 📋 驗收檢查清單

### D+3 交付物
- [x] 雲端架構設計文檔 (本文檔)
- [x] 技術選型理由說明
- [x] 祕密與權限清單
- [x] 部署流程設計
- [x] 監控指標定義

### D+5 目標
- [ ] Supabase 專案建立並配置 pgvector
- [ ] Render.com 服務建立 (API + Redis)
- [ ] GitHub Environments 和 Secrets 配置
- [ ] 容器化 Dockerfile 完成
- [ ] Staging API Health Check 通過

### D+7 目標
- [ ] CI/CD 自動化管道運行
- [ ] 資料庫遷移雲端執行成功
- [ ] 評測管線雲端觸發成功
- [ ] 監控面板顯示關鍵指標
- [ ] T+14 優化前基線報告

## 🎯 成功標準

1. **Staging URL 可用**: https://morningai-core-staging.onrender.com/health 返回 200
2. **版本一致性**: API 版本與 GitHub tag 一致
3. **DB 操作**: 遷移和回滾在雲端可執行
4. **評測自動化**: GitHub Actions 可觸發完整評測
5. **監控可見**: Grafana 面板顯示 P95、錯誤率、RAG 命中率
6. **祕密安全**: 無硬編碼，最小權限原則

---

**文檔版本**: v1.0  
**建立日期**: 2025-09-05  
**負責人**: MorningAI 開發團隊  
**審核狀態**: 待 CTO 審核

