# Render 環境變數配置檢查清單

## 🎯 目標
確保 Render 服務配置了所有必要的環境變數，以支持生產環境運行。

## 📋 必需環境變數

### 1. 資料庫配置
```bash
# Supabase PostgreSQL 連接
DATABASE_URL=postgresql://postgres.deuytovttpkgewgzqjxx:hgQtFxlxWefSJsmZ@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require

# 連接池配置
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30
```

### 2. 應用程序基本配置
```bash
# 應用環境
APP_NAME=MorningAI Core
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false

# 服務配置
PORT=10000
WORKERS=1
PYTHONPATH=/app
```

### 3. JWT 認證配置
```bash
# JWT 密鑰（自動生成或手動設置）
JWT_SECRET_KEY=[AUTO_GENERATED_OR_MANUAL]
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. 外部 API 配置
```bash
# OpenAI API
OPENAI_API_KEY=[REQUIRED - 需要手動設置]
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
```

### 5. CORS 和主機配置
```bash
# CORS 設置
CORS_ORIGINS=https://app.morningai.me,http://localhost:3000
CORS_ALLOW_CREDENTIALS=true

# 允許的主機
ALLOWED_HOSTS=api.morningai.me,admin.morningai.me,morning-ai-api.onrender.com,localhost,127.0.0.1
```

### 6. 監控和日誌配置
```bash
# Sentry 錯誤追蹤
SENTRY_DSN=[REQUIRED - 需要手動設置]
SENTRY_ENVIRONMENT=production

# 日誌配置
LOG_LEVEL=info
LOG_FORMAT=json
```

### 7. 功能開關
```bash
# 功能啟用/禁用
FEATURE_CHAT_ENABLED=true
FEATURE_REFERRAL_ENABLED=true
FEATURE_CMS_ENABLED=true
FEATURE_NOTIFICATIONS_ENABLED=true

# 文檔和調試
DOCS_ENABLED=false
```

### 8. 速率限制配置
```bash
# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

## 🔧 Render 配置步驟

### Step 1: 訪問環境變數設置
```
1. 登入 Render Dashboard
2. 選擇 morning-ai-api 服務
3. 進入 Settings → Environment
```

### Step 2: 批量添加環境變數
```bash
# 可以使用以下格式批量添加
KEY1=value1
KEY2=value2
KEY3=value3
```

### Step 3: 特殊配置注意事項

#### 自動生成的變數：
```bash
# 這些變數由 Render 自動生成，無需手動設置
JWT_SECRET_KEY=true  # 設置為 generateValue: true
```

#### 需要手動設置的敏感變數：
```bash
# 這些需要從外部服務獲取並手動設置
OPENAI_API_KEY=[從 OpenAI Dashboard 獲取]
SENTRY_DSN=[從 Sentry 項目設置獲取]
```

#### 從其他服務同步的變數：
```bash
# 如果有其他 Render 服務，可以設置同步
DATABASE_URL=fromService:pserv:morningai-postgres:connectionString
REDIS_URL=fromService:redis:morningai-redis:connectionString
```

## ✅ 驗證檢查清單

### 配置完成檢查：
- [ ] 所有必需變數已設置
- [ ] 敏感變數已正確配置
- [ ] 資料庫連接字串包含 `sslmode=require`
- [ ] CORS 來源包含生產域名
- [ ] 允許的主機包含自定義域名

### 功能驗證：
- [ ] 應用程序成功啟動
- [ ] 資料庫連接正常
- [ ] OpenAI API 連接正常
- [ ] 健康檢查端點返回 200
- [ ] 自定義域名正常工作

## 🚨 常見問題和解決方案

### 問題 1: 資料庫連接失敗
```bash
# 檢查項目
- DATABASE_URL 格式是否正確
- 是否包含 sslmode=require
- 密碼是否正確
- 連接池配置是否合理

# 解決方案
DATABASE_URL=postgresql://postgres.deuytovttpkgewgzqjxx:hgQtFxlxWefSJsmZ@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### 問題 2: OpenAI API 認證失敗
```bash
# 檢查項目
- OPENAI_API_KEY 是否正確
- API 配額是否充足
- 網路連接是否正常

# 解決方案
# 在 OpenAI Dashboard 重新生成 API Key
OPENAI_API_KEY=sk-...
```

### 問題 3: CORS 錯誤
```bash
# 檢查項目
- CORS_ORIGINS 是否包含前端域名
- 是否啟用了 credentials

# 解決方案
CORS_ORIGINS=https://app.morningai.me,http://localhost:3000
CORS_ALLOW_CREDENTIALS=true
```

### 問題 4: Invalid Host 錯誤
```bash
# 檢查項目
- ALLOWED_HOSTS 是否包含自定義域名
- TrustedHostMiddleware 是否正確配置

# 解決方案
ALLOWED_HOSTS=api.morningai.me,admin.morningai.me,morning-ai-api.onrender.com,localhost,127.0.0.1
```

## 📊 環境變數監控

### 監控腳本：
```python
# 檢查關鍵環境變數的腳本
import os

required_vars = [
    'DATABASE_URL',
    'OPENAI_API_KEY',
    'JWT_SECRET_KEY',
    'SENTRY_DSN',
    'ALLOWED_HOSTS',
    'CORS_ORIGINS'
]

missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"Missing environment variables: {missing_vars}")
else:
    print("All required environment variables are set")
```

### 健康檢查集成：
```python
# 在健康檢查端點中包含環境變數狀態
@app.get("/health/env")
async def env_health():
    return {
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "sentry_configured": bool(os.getenv("SENTRY_DSN")),
        "jwt_configured": bool(os.getenv("JWT_SECRET_KEY"))
    }
```

## 🔄 部署後驗證

### 驗證腳本：
```bash
#!/bin/bash
# 驗證環境變數配置

echo "Verifying environment variables..."

# 檢查健康端點
curl -s https://api.morningai.me/health/env | jq '.'

# 檢查資料庫連接
curl -s https://api.morningai.me/api/v1/health | jq '.connection_tests.database'

# 檢查 OpenAI 連接
curl -s https://api.morningai.me/api/v1/health | jq '.connection_tests.openai'

echo "Environment verification completed"
```

## 📋 部署檢查清單

### 部署前：
- [ ] 所有環境變數已配置
- [ ] 敏感資料已安全設置
- [ ] 配置已在 staging 環境測試

### 部署中：
- [ ] 監控部署日誌
- [ ] 檢查啟動錯誤
- [ ] 驗證服務狀態

### 部署後：
- [ ] 運行健康檢查
- [ ] 驗證所有功能
- [ ] 檢查監控告警

---
**創建時間**: 2025-09-06 09:45 UTC  
**檢查頻率**: 每次部署前  
**負責人**: DevOps Team

