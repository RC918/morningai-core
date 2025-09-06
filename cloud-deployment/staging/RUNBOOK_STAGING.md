# Staging 環境日常維運手冊

## 1. 服務概覽

- **前端 (Vercel)**: https://morningai-core-staging.vercel.app
- **後端 (Render)**: https://morningai-core-staging.onrender.com
- **資料庫 (Supabase)**: [Supabase Project](https://app.supabase.com/project/deuytovttpkgewgzqjxx)
- **監控 (Sentry)**: [Sentry Project](https://sentry.io/organizations/morning-ai/projects/morningai-core-staging/)

## 2. 日常檢查

- **健康檢查**: `curl -s https://morningai-core-staging.onrender.com/api/v1/health`
- **Vercel 代理**: `curl -s https://morningai-core-staging.vercel.app/api/v1/health`
- **Render 部署狀態**: [Render Dashboard](https://dashboard.render.com/web/srv-d2tsbb3e5dus73e51qqg)
- **Vercel 部署狀態**: [Vercel Dashboard](https://vercel.com/morning-ai/morningai-core-staging)

## 3. 部署流程

1. **推送代碼到 `main` 分支**
2. **Render 和 Vercel 自動觸發部署**
3. **在 Render 和 Vercel Dashboard 監控部署狀態**

## 4. 故障排除

- **5xx 錯誤**: 檢查 Sentry 的錯誤日誌和 Render 的應用程序日誌。
- **部署失敗**: 檢查 Render 或 Vercel 的部署日誌。
- **資料庫問題**: 檢查 Supabase 的監控面板。

## 5. 緊急回滾

- **Render**: 在 Render Dashboard 中選擇之前的成功部署並點擊 "Rollback"。
- **Vercel**: 在 Vercel Dashboard 中選擇之前的成功部署並點擊 "Promote to Production"。


