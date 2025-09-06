# Phase 6 – 官網與 API 串接驗收報告

**驗收時間**: 2025-09-06 13:28:00 UTC  
**狀態**: ⚠️ **部分功能異常**

## 📋 **驗收項目與結果**

### 1. ✅ **前端環境變數更新**
- **Vercel 專案**: `morningai-web`
- **環境變數**: `NEXT_PUBLIC_API_URL=https://api.morningai.me`
- **狀態**: 已成功配置 ✅
- **Auto-Deploy**: 已啟用 ✅

### 2. ⚠️ **官網功能測試**
- **官網 URL**: https://app.morningai.me

#### **測試結果**:
1. **首頁載入**: ✅ 正常
   - API `/health` 回應 200 OK

2. **註冊 / 登入**: ❌ **失敗**
   - **錯誤**: 500 INTERNAL_SERVER_ERROR
   - **錯誤代碼**: `MIDDLEWARE_INVOCATION_FAILED`
   - **錯誤 ID**: `iad1::svp45-1757165199396-944a95f71bd3`

3. **推薦碼註冊**: ⛔ **未測試** (因註冊失敗)

4. **推薦排行榜**: ⛔ **未測試** (因登入失敗)

## 📸 **驗證證據**

### **Vercel 環境變數設定**

```json
{
  "key": "NEXT_PUBLIC_API_URL",
  "value": "https://api.morningai.me",
  "target": [
    "development",
    "preview",
    "production"
  ]
}
```

### **API 健康檢查 (/health)**

```json
{
  "ok": true,
  "status": "healthy",
  "service": "morningai-core-api"
}
```

### **登入頁面 500 錯誤**

- **截圖**: [app.morningai.me_2025-09-06_13-26-42_2940.webp](/home/ubuntu/screenshots/app_morningai_me_2025-09-06_13-26-42_2940.webp)

## 🔍 **問題分析與結論**

- **核心問題**: 前端 Vercel 服務在訪問 `/sign-in` 頁面時，其中間件調用失敗，導致 500 錯誤。
- **可能原因**:
  1. **環境變數未生效**: Vercel 需要重新部署才能完全應用新的環境變數。
  2. **中間件邏輯錯誤**: 前端中間件在處理 `/sign-in` 路由時可能存在 bug。
  3. **API 整合問題**: 雖然 `/health` 端點正常，但 `/auth` 相關端點可能存在問題。

- **結論**: Cloudflare + Render + Vercel 三端整合**尚未完全生效**。後端 API 服務本身健康，但前端應用在用戶認證流程中出現嚴重錯誤，導致核心功能無法使用。

## 🚀 **下一步行動建議**

1. **強制重新部署 Vercel**: 確保 `NEXT_PUBLIC_API_URL` 環境變數已在運行時生效。
2. **檢查前端中間件**: 調查 `middleware.ts` 或相關路由處理邏輯，定位 `MIDDLEWARE_INVOCATION_FAILED` 的根本原因。
3. **單獨測試 API**: 使用 Postman 或 curl 直接測試 `/auth/register` 和 `/auth/login` 端點，排除後端問題。
4. **查看 Vercel Logs**: 檢查 Vercel 專案的實時日誌，獲取更詳細的錯誤信息。

---

**Phase 6 驗收不通過**，需要開發團隊立即介入修復前端應用問題。

