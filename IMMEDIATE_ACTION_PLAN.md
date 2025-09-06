# 立即行動計劃 - CI/CD 修復後續硬化

## 執行時程
- **今日 EOD 前**：完成立即指令 1-5 + 驗證手順
- **明日中午前**：完成收尾硬化

## 1. 立即指令（今日完成）

### 1.1 修正 Render 來源倉庫 🔧
**目標**：將 Render 服務的 GitHub 來源改為 RC918/morningai-core

**操作步驟**：
1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 找到 `morningai-core-staging` 服務
3. 進入 Settings → Repository
4. 將來源從 `morning-ai-saas-mvp` 改為 `RC918/morningai-core`
5. 開啟 Auto-Deploy
6. 執行 "Clear build cache & Deploy"

**驗證**：確認服務指向正確的倉庫並自動部署最新代碼

### 1.2 Cloudflare Worker 規則調整 ⚙️
**目標**：暫停或繞過會匹配到 /health、/healthz 的 Worker

**操作步驟**：
1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 選擇 `morningai.me` 域名
3. 進入 Workers & Pages
4. 檢查綁定到 `api.morningai.me` 的 Workers
5. 修改路由規則，排除 `/health*` 和 `/healthz*` 路徑
6. 或在 Worker 代碼中添加直通邏輯：
```javascript
if (url.pathname === '/health' || url.pathname === '/healthz') {
  return fetch(request);
}
```

**驗證**：測試 `https://api.morningai.me/health` 返回 200 狀態

### 1.3 Host 白名單與 Proxy 信任 🛡️
**目標**：配置正確的環境變數和中間件

**操作步驟**：
1. 在 Render 環境變數中添加：
```
ALLOWED_HOSTS=api.morningai.me,morningai-core.onrender.com,localhost,127.0.0.1
```
2. 確認 main.py 中的 TrustedHostMiddleware 配置正確
3. 確認 ProxyHeadersMiddleware 已啟用

**驗證**：檢查應用程序日誌，確認 allowed_hosts 正確打印

### 1.4 Python/依賴鎖定 🔒
**目標**：確保依賴版本一致性

**操作步驟**：
1. 確認 `runtime.txt` 為 `python-3.11.9`
2. 檢查 `requirements.txt` 和 `constraints.txt` 無 aiohttp 引用
3. 在 CI 中添加守門檢查（見下方 CI 配置）

**驗證**：運行 `grep -r "aiohttp" . --exclude-dir=.git` 確認無殘留

### 1.5 健康檢查穩定化 ❤️
**目標**：確保健康檢查端點穩定可靠

**當前狀態**：
- `/health`：輕量版，不連 DB，永遠 200 ✅
- `/healthz`：全量版，含 DB 檢查，失敗時返回 200 + degraded 狀態 ✅

**驗證**：測試兩個端點都返回 200 狀態碼

## 2. 驗證手順

### 2.1 測試執行
完成上述修正後，執行以下測試：

```bash
# 使用我們提供的驗證腳本
./final_deployment_verification.sh

# 或手動測試關鍵端點
curl -v https://api.morningai.me/health
curl -v https://api.morningai.me/healthz
```

**目標**：成功率 ≥ 95%，健康檢查全部 200

### 2.2 證據收集
需要回傳的三項證據：

1. **Render 來源倉庫截圖**
   - 顯示服務指向 `RC918/morningai-core`
   - 顯示 Auto-Deploy=On

2. **Cloudflare Routes/Workers 截圖**
   - 顯示 `/health*` 已被排除或直通
   - 顯示路由規則配置

3. **測試輸出**
   - 運行 `final_deployment_verification.sh` 的完整日誌
   - 或 Postman/Newman 測試結果

## 3. 收尾硬化（明日前完成）

### 3.1 CI 增強檢查
在 `.github/workflows/ci.yml` 中添加：

```yaml
- name: Check for aiohttp residue
  run: |
    if grep -r "aiohttp" . --exclude-dir=.git --exclude-dir=node_modules; then
      echo "❌ Found aiohttp references"
      exit 1
    fi
    echo "✅ No aiohttp residue found"

- name: Health check validation
  run: |
    response=$(curl -s -o /dev/null -w "%{http_code}" https://api.morningai.me/health)
    if [ "$response" != "200" ]; then
      echo "❌ CF routing risk - /health returned $response"
      exit 1
    fi
    echo "✅ Health check passed"
```

### 3.2 監控配置
1. **Sentry**：配置後端專案 DSN
2. **UptimeRobot**：監控 `/health` 端點
3. **Grafana**：匯入監控面板

### 3.3 Runbook 補充
更新運維手冊，包含：
- Cloudflare Worker 變更影響面
- 回滾步驟
- 故障排除流程

## 4. 檢查清單

### 立即指令完成確認
- [ ] Render 來源倉庫已修正為 RC918/morningai-core
- [ ] Auto-Deploy 已開啟
- [ ] Cloudflare Worker 規則已調整
- [ ] 環境變數 ALLOWED_HOSTS 已配置
- [ ] Python 版本鎖定為 3.11.x
- [ ] 健康檢查端點穩定運行

### 驗證手順完成確認
- [ ] 測試成功率 ≥ 95%
- [ ] 健康檢查全部返回 200
- [ ] 三項證據截圖已準備

### 收尾硬化完成確認
- [ ] CI 增強檢查已添加
- [ ] 監控系統已配置
- [ ] Runbook 已更新

---
**執行負責人**：開發團隊  
**驗收負責人**：CTO  
**完成期限**：今日 EOD（立即指令）+ 明日中午（硬化）

