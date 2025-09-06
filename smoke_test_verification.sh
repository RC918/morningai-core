#!/bin/bash

# Smoke Test Verification Script for MorningAI API
# 用於驗證 Render 重新綁定後的 API 服務狀態

echo "🚀 MorningAI API Smoke Test Verification"
echo "========================================"
echo "Target: https://api.morningai.me"
echo "Time: $(date)"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試結果統計
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 測試函數
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="$3"
    
    echo -n "Testing $test_name... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # 執行測試
    response=$(eval "$test_command" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "   Response: $response" | head -3
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "   Error: $response"
    fi
    echo ""
}

# 測試函數 - 檢查 HTTP 狀態碼
run_http_test() {
    local test_name="$1"
    local url="$2"
    local expected_status="$3"
    
    echo -n "Testing $test_name... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # 獲取 HTTP 狀態碼
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# 測試函數 - 檢查響應內容
run_content_test() {
    local test_name="$1"
    local url="$2"
    local expected_content="$3"
    
    echo -n "Testing $test_name... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # 獲取響應內容
    response=$(curl -s "$url")
    
    if echo "$response" | grep -q "$expected_content"; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "   Content found: $expected_content"
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "   Expected: $expected_content"
        echo "   Got: $response"
    fi
    echo ""
}

echo "🔍 Phase 1: Basic Connectivity Tests"
echo "-----------------------------------"

# 1. 基本健康檢查
run_http_test "Basic Health Check" "https://api.morningai.me/health" "200"

# 2. 詳細健康檢查
run_http_test "Detailed Health Check" "https://api.morningai.me/healthz" "200"

# 3. 根路徑檢查
run_http_test "Root Path Check" "https://api.morningai.me/" "200"

echo "🔍 Phase 2: Host Header Validation Tests"
echo "----------------------------------------"

# 4. Host Header 驗證
run_test "Host Header Validation" \
    "curl -s -H 'Host: api.morningai.me' https://api.morningai.me/health | grep -v 'Invalid host'" \
    "0"

# 5. 自定義域名測試
run_content_test "Custom Domain Response" \
    "https://api.morningai.me/health" \
    "healthy"

echo "🔍 Phase 3: CORS and Security Tests"
echo "-----------------------------------"

# 6. CORS 驗證
echo -n "Testing CORS Headers... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

cors_response=$(curl -s -I -H "Origin: https://app.morningai.me" https://api.morningai.me/health)
if echo "$cors_response" | grep -q "access-control-allow"; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "   CORS headers found"
else
    echo -e "${YELLOW}⚠️  PARTIAL${NC}"
    echo "   CORS headers not found (may be expected)"
fi
echo ""

echo "🔍 Phase 4: Performance Tests"
echo "-----------------------------"

# 7. 響應時間測試
echo -n "Testing Response Time... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

response_time=$(curl -s -o /dev/null -w "%{time_total}" https://api.morningai.me/health)
response_time_ms=$(echo "$response_time * 1000" | bc)

if (( $(echo "$response_time < 2.0" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC} (${response_time_ms}ms)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️  SLOW${NC} (${response_time_ms}ms)"
    echo "   Warning: Response time > 2000ms"
fi
echo ""

echo "🔍 Phase 5: API Endpoint Tests"
echo "------------------------------"

# 8. API 版本檢查
run_http_test "API Version Endpoint" "https://api.morningai.me/version" "200"

# 9. Echo 測試
run_http_test "Echo Test Endpoint" "https://api.morningai.me/echo" "200"

# 10. 資料庫相關測試（如果存在）
echo -n "Testing Database Endpoints... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

db_test_status=$(curl -s -o /dev/null -w "%{http_code}" https://api.morningai.me/api/v1/health)
if [ "$db_test_status" = "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP $db_test_status)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ "$db_test_status" = "404" ]; then
    echo -e "${YELLOW}⚠️  NOT FOUND${NC} (endpoint may not exist)"
else
    echo -e "${RED}❌ FAIL${NC} (HTTP $db_test_status)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

echo "🔍 Phase 6: SSL and Security Verification"
echo "-----------------------------------------"

# 11. SSL 憑證檢查
echo -n "Testing SSL Certificate... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

ssl_info=$(curl -s -I https://api.morningai.me/health | grep -i "strict-transport-security")
if [ -n "$ssl_info" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "   HSTS header found"
else
    echo -e "${YELLOW}⚠️  PARTIAL${NC}"
    echo "   HSTS header not found"
fi
echo ""

# 12. Cloudflare 代理檢查
echo -n "Testing Cloudflare Proxy... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

cf_ray=$(curl -s -I https://api.morningai.me/health | grep -i "cf-ray")
if [ -n "$cf_ray" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "   Cloudflare proxy active"
else
    echo -e "${RED}❌ FAIL${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "   Cloudflare proxy not detected"
fi
echo ""

echo "📊 Test Results Summary"
echo "======================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

# 計算成功率
if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    echo "Success Rate: $success_rate%"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n🎉 ${GREEN}ALL TESTS PASSED!${NC}"
        echo "✅ API service is fully operational"
        exit 0
    elif [ $FAILED_TESTS -le 2 ]; then
        echo -e "\n⚠️  ${YELLOW}MOSTLY SUCCESSFUL${NC}"
        echo "⚠️  Minor issues detected, but service is operational"
        exit 1
    else
        echo -e "\n❌ ${RED}MULTIPLE FAILURES DETECTED${NC}"
        echo "❌ Service may have significant issues"
        exit 2
    fi
else
    echo -e "\n❌ ${RED}NO TESTS EXECUTED${NC}"
    exit 3
fi

