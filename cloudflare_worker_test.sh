#!/bin/bash

# Cloudflare Worker 干擾問題測試腳本
# 用於診斷和驗證 api.morningai.me 健康檢查端點問題

echo "=== Cloudflare Worker 干擾問題診斷 ==="
echo "時間: $(date)"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試函數
test_endpoint() {
    local url=$1
    local name=$2
    local expected_status=$3
    
    echo "測試 $name:"
    echo "URL: $url"
    
    # 執行請求並獲取狀態碼和響應
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}\nCONTENT_TYPE:%{content_type}" "$url")
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
    content_type=$(echo "$response" | grep "CONTENT_TYPE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d' | sed '/TIME_TOTAL:/d' | sed '/CONTENT_TYPE:/d')
    
    echo "  HTTP狀態碼: $http_code"
    echo "  響應時間: ${time_total}s"
    echo "  Content-Type: $content_type"
    echo "  響應內容: $body"
    
    # 判斷結果
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "  結果: ${GREEN}✅ 通過${NC}"
        return 0
    else
        echo -e "  結果: ${RED}❌ 失敗${NC} (期望: $expected_status, 實際: $http_code)"
        return 1
    fi
}

# 測試 Render 直接 URL（對照組）
echo "1. 測試 Render 直接 URL（對照組）"
echo "================================"

render_health_pass=0
render_healthz_pass=0

test_endpoint "https://morningai-core-staging.onrender.com/health" "Render /health" "200"
if [ $? -eq 0 ]; then
    render_health_pass=1
fi

echo ""

test_endpoint "https://morningai-core-staging.onrender.com/healthz" "Render /healthz" "200"
if [ $? -eq 0 ]; then
    render_healthz_pass=1
fi

echo ""
echo "================================"
echo ""

# 測試 Cloudflare 代理 URL（問題組）
echo "2. 測試 Cloudflare 代理 URL（問題組）"
echo "===================================="

cf_health_pass=0
cf_healthz_pass=0

test_endpoint "https://api.morningai.me/health" "Cloudflare /health" "200"
if [ $? -eq 0 ]; then
    cf_health_pass=1
fi

echo ""

test_endpoint "https://api.morningai.me/healthz" "Cloudflare /healthz" "200"
if [ $? -eq 0 ]; then
    cf_healthz_pass=1
fi

echo ""
echo "===================================="
echo ""

# 詳細診斷
echo "3. 詳細診斷分析"
echo "================"

# 檢查 DNS 解析
echo "DNS 解析檢查:"
echo "api.morningai.me 解析結果:"
dig +short api.morningai.me | head -5
echo ""

# 檢查響應頭差異
echo "響應頭比較:"
echo ""
echo "Render 直接 URL 響應頭:"
curl -I -s https://morningai-core-staging.onrender.com/health | head -10
echo ""
echo "Cloudflare 代理 URL 響應頭:"
curl -I -s https://api.morningai.me/health | head -10
echo ""

# 檢查是否有 Cloudflare 特有的響應頭
echo "Cloudflare 特徵檢查:"
cf_headers=$(curl -I -s https://api.morningai.me/health | grep -i "cf-\|cloudflare")
if [ -n "$cf_headers" ]; then
    echo "發現 Cloudflare 響應頭:"
    echo "$cf_headers"
else
    echo "未發現 Cloudflare 響應頭"
fi
echo ""

# 總結報告
echo "4. 診斷總結"
echo "==========="

echo "測試結果統計:"
echo "  Render /health:     $([ $render_health_pass -eq 1 ] && echo -e "${GREEN}✅ 通過${NC}" || echo -e "${RED}❌ 失敗${NC}")"
echo "  Render /healthz:    $([ $render_healthz_pass -eq 1 ] && echo -e "${GREEN}✅ 通過${NC}" || echo -e "${RED}❌ 失敗${NC}")"
echo "  Cloudflare /health: $([ $cf_health_pass -eq 1 ] && echo -e "${GREEN}✅ 通過${NC}" || echo -e "${RED}❌ 失敗${NC}")"
echo "  Cloudflare /healthz:$([ $cf_healthz_pass -eq 1 ] && echo -e "${GREEN}✅ 通過${NC}" || echo -e "${RED}❌ 失敗${NC}")"
echo ""

# 問題診斷
if [ $render_health_pass -eq 1 ] && [ $render_healthz_pass -eq 1 ]; then
    echo -e "${GREEN}✅ Render 服務正常${NC} - 後端應用程序工作正常"
else
    echo -e "${RED}❌ Render 服務異常${NC} - 需要檢查後端應用程序"
fi

if [ $cf_health_pass -eq 0 ] && [ $cf_healthz_pass -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Cloudflare Worker 干擾${NC} - /health 路徑被攔截，/healthz 正常"
    echo ""
    echo "建議解決方案:"
    echo "1. 檢查 Cloudflare Dashboard 中的 Workers & Pages"
    echo "2. 查找綁定到 api.morningai.me 的 Workers"
    echo "3. 檢查 Worker 路由規則是否包含 /health 路徑"
    echo "4. 暫時禁用相關 Worker 或修改路由規則"
    echo "5. 參考 CLOUDFLARE_WORKER_TROUBLESHOOTING_GUIDE.md"
elif [ $cf_health_pass -eq 0 ] && [ $cf_healthz_pass -eq 0 ]; then
    echo -e "${RED}❌ Cloudflare 代理問題${NC} - 所有端點都失敗"
    echo ""
    echo "建議解決方案:"
    echo "1. 檢查 Cloudflare DNS 設置"
    echo "2. 檢查 SSL/TLS 配置"
    echo "3. 檢查 Cloudflare 防火牆規則"
elif [ $cf_health_pass -eq 1 ] && [ $cf_healthz_pass -eq 1 ]; then
    echo -e "${GREEN}✅ Cloudflare 代理正常${NC} - 問題已解決"
else
    echo -e "${YELLOW}⚠️  部分異常${NC} - 需要進一步調查"
fi

echo ""
echo "診斷完成時間: $(date)"
echo ""
echo "如需更多幫助，請參考:"
echo "- CLOUDFLARE_WORKER_TROUBLESHOOTING_GUIDE.md"
echo "- Cloudflare Dashboard: https://dash.cloudflare.com/"

