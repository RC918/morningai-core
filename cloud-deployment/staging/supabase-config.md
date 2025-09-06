# Supabase 專案配置

## 📊 專案信息

### 現有專案
發現已有 2 個 Supabase 專案：

1. **morningai** (Staging 用)
   - Project ID: `deuytovttpkgewgzqjxx`
   - Region: `ap-southeast-1` (Singapore)
   - Status: `ACTIVE_HEALTHY`
   - Database Host: `db.deuytovttpkgewgzqjxx.supabase.co`
   - PostgreSQL Version: `17.4.1.074`
   - Created: 2025-08-30

2. **morning-ai-production** (Production 用)
   - Project ID: `fkbxtbymcgzmyxvlpseu`
   - Region: `ap-southeast-1` (Singapore)
   - Status: `ACTIVE_HEALTHY`
   - Database Host: `db.fkbxtbymcgzmyxvlpseu.supabase.co`
   - PostgreSQL Version: `17.4.1.074`
   - Created: 2025-08-31

## 🎯 使用決策

**選擇 Staging 專案**: `morningai` (deuytovttpkgewgzqjxx)
- 適合用於 D+2 階段的 staging 環境測試
- PostgreSQL 17+ 支援 pgvector 擴展
- 已經是 ACTIVE_HEALTHY 狀態

## 🔧 連接配置

### Database URL 格式
```
postgresql://postgres:[password]@db.deuytovttpkgewgzqjxx.supabase.co:5432/postgres
```

### API URL
```
https://deuytovttpkgewgzqjxx.supabase.co
```

### 需要獲取的信息
- [ ] Database Password (從 Supabase Dashboard)
- [ ] API Keys (anon key, service_role key)
- [ ] 確認 pgvector 擴展狀態

## 📋 下一步行動
1. 獲取 database password 和 API keys
2. 測試資料庫連接
3. 啟用 pgvector 擴展
4. 執行 migration.sql
5. 設置 GitHub Environment Secrets

