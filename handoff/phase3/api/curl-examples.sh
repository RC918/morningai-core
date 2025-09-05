#!/bin/bash

# MorningAI Core API - curl 指令範例
# 
# 使用說明：
# 1. 設置 API_BASE_URL 環境變數
# 2. 執行相應的函數進行測試
# 
# 範例：
# export API_BASE_URL="http://localhost:8000/api/v1"
# source curl-examples.sh
# test_user_login
# test_user_profile

# 設置基礎 URL
API_BASE_URL=${API_BASE_URL:-"http://localhost:8000/api/v1"}

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輔助函數
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 檢查響應狀態
check_response() {
    local status_code=$1
    local expected=$2
    local description=$3
    
    if [ "$status_code" -eq "$expected" ]; then
        print_success "$description (HTTP $status_code)"
    else
        print_error "$description (Expected HTTP $expected, got HTTP $status_code)"
    fi
}

# 全局變數存儲令牌
ACCESS_TOKEN=""
REFRESH_TOKEN=""

# ==========================================
# 認證系統測試
# ==========================================

# 用戶註冊
test_user_registration() {
    print_header "用戶註冊測試"
    
    echo "測試案例 1: 正常註冊"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "newuser@example.com",
            "password": "NewUser123",
            "username": "newuser",
            "display_name": "New User",
            "first_name": "New",
            "last_name": "User",
            "referral_code": "WELCOME2025",
            "language": "zh-TW",
            "timezone": "Asia/Taipei"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "正常註冊"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 重複郵箱註冊"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@morningai.com",
            "password": "Test123456"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 400 "重複郵箱註冊"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 3: 無效推薦碼註冊"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "test@example.com",
            "password": "Test123456",
            "referral_code": "INVALID"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 400 "無效推薦碼註冊"
    echo "響應內容: $body"
    echo
}

# 用戶登入
test_user_login() {
    print_header "用戶登入測試"
    
    echo "測試案例 1: 正常登入"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "user@morningai.com",
            "password": "user123",
            "remember_me": false
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "正常登入"
    
    if [ "$status_code" -eq 200 ]; then
        ACCESS_TOKEN=$(echo $body | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        REFRESH_TOKEN=$(echo $body | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
        print_success "Access token 已保存: ${ACCESS_TOKEN:0:20}..."
        print_success "Refresh token 已保存: ${REFRESH_TOKEN:0:20}..."
    fi
    
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 錯誤密碼登入"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "user@morningai.com",
            "password": "wrongpassword"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 401 "錯誤密碼登入"
    echo "響應內容: $body"
    echo
}

# 管理員登入
test_admin_login() {
    print_header "管理員登入測試"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@morningai.com",
            "password": "admin123",
            "remember_me": false
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "管理員登入"
    
    if [ "$status_code" -eq 200 ]; then
        ACCESS_TOKEN=$(echo $body | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        REFRESH_TOKEN=$(echo $body | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
        print_success "Admin access token 已保存: ${ACCESS_TOKEN:0:20}..."
    fi
    
    echo "響應內容: $body"
    echo
}

# 租戶管理員登入
test_manager_login() {
    print_header "租戶管理員登入測試"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "manager@morningai.com",
            "password": "manager123",
            "remember_me": false
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "租戶管理員登入"
    
    if [ "$status_code" -eq 200 ]; then
        ACCESS_TOKEN=$(echo $body | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        REFRESH_TOKEN=$(echo $body | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
        print_success "Manager access token 已保存: ${ACCESS_TOKEN:0:20}..."
    fi
    
    echo "響應內容: $body"
    echo
}

# 刷新令牌
test_token_refresh() {
    print_header "令牌刷新測試"
    
    if [ -z "$REFRESH_TOKEN" ]; then
        print_error "需要先登入獲取 refresh token"
        return 1
    fi
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"$REFRESH_TOKEN\"
        }")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "令牌刷新"
    
    if [ "$status_code" -eq 200 ]; then
        NEW_ACCESS_TOKEN=$(echo $body | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        ACCESS_TOKEN=$NEW_ACCESS_TOKEN
        print_success "新的 access token 已保存: ${ACCESS_TOKEN:0:20}..."
    fi
    
    echo "響應內容: $body"
    echo
}

# 獲取用戶資料
test_user_profile() {
    print_header "用戶資料測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    echo "測試案例 1: 獲取用戶資料"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/auth/profile" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "獲取用戶資料"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 更新用戶資料"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT \
        "$API_BASE_URL/auth/profile" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "display_name": "Updated User",
            "bio": "Updated bio",
            "language": "en"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "更新用戶資料"
    echo "響應內容: $body"
    echo
}

# 更改密碼
test_password_change() {
    print_header "密碼更改測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    echo "測試案例 1: 正常更改密碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/change-password" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "old_password": "user123",
            "new_password": "NewPassword123"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "正常更改密碼"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 錯誤舊密碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/auth/change-password" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "old_password": "wrongpassword",
            "new_password": "NewPassword123"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 400 "錯誤舊密碼"
    echo "響應內容: $body"
    echo
}

# ==========================================
# 推薦系統測試
# ==========================================

# 推薦碼驗證
test_referral_validation() {
    print_header "推薦碼驗證測試"
    
    echo "測試案例 1: 驗證有效推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/referral/validate/WELCOME2025")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "驗證有效推薦碼"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 驗證無效推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/referral/validate/INVALID")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "驗證無效推薦碼"
    echo "響應內容: $body"
    echo
}

# 使用推薦碼
test_referral_use() {
    print_header "推薦碼使用測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    echo "測試案例 1: 正常使用推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/referral/use" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "code": "FRIEND50"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "正常使用推薦碼"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 重複使用推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/referral/use" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "code": "DEMO100"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 400 "重複使用推薦碼"
    echo "響應內容: $body"
    echo
}

# 創建推薦碼
test_referral_creation() {
    print_header "推薦碼創建測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token（需要管理員權限）"
        return 1
    fi
    
    echo "測試案例 1: 創建自定義推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/referral/codes" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "custom_code": "MANAGER2025",
            "max_uses": 50,
            "expires_at": "2025-12-31T23:59:59Z"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "創建自定義推薦碼"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 創建自動生成推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/referral/codes" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "max_uses": 100
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "創建自動生成推薦碼"
    echo "響應內容: $body"
    echo
}

# 獲取推薦碼列表
test_referral_list() {
    print_header "推薦碼列表測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/referral/codes?page=1&size=10" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "獲取推薦碼列表"
    echo "響應內容: $body"
    echo
}

# 獲取推薦統計
test_referral_stats() {
    print_header "推薦統計測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/referral/stats" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "獲取推薦統計"
    echo "響應內容: $body"
    echo
}

# 獲取推薦排行榜
test_referral_leaderboard() {
    print_header "推薦排行榜測試"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/referral/leaderboard?limit=10" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 200 "獲取推薦排行榜"
    echo "響應內容: $body"
    echo
}

# ==========================================
# 錯誤處理測試
# ==========================================

# 認證錯誤測試
test_auth_errors() {
    print_header "認證錯誤測試"
    
    echo "測試案例 1: 無效 JWT 令牌"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/auth/profile" \
        -H "Authorization: Bearer invalid_token")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 401 "無效 JWT 令牌"
    echo "響應內容: $body"
    echo
    
    echo "測試案例 2: 缺少 Authorization 標頭"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET \
        "$API_BASE_URL/auth/profile")
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 401 "缺少 Authorization 標頭"
    echo "響應內容: $body"
    echo
}

# 權限錯誤測試
test_permission_errors() {
    print_header "權限錯誤測試"
    
    # 先用一般用戶登入
    test_user_login > /dev/null 2>&1
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "需要先登入獲取 access token"
        return 1
    fi
    
    echo "測試案例 1: 無權限創建推薦碼"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        "$API_BASE_URL/referral/codes" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "custom_code": "USERCODE"
        }')
    
    status_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
    
    check_response $status_code 403 "無權限創建推薦碼"
    echo "響應內容: $body"
    echo
}

# ==========================================
# 完整測試套件
# ==========================================

# 運行所有測試
run_all_tests() {
    print_header "開始運行完整測試套件"
    echo "API Base URL: $API_BASE_URL"
    echo
    
    # 認證系統測試
    test_user_registration
    test_user_login
    test_token_refresh
    test_user_profile
    test_password_change
    
    # 推薦系統測試
    test_referral_validation
    test_referral_use
    test_referral_list
    test_referral_stats
    test_referral_leaderboard
    
    # 管理員功能測試
    test_manager_login
    test_referral_creation
    
    # 錯誤處理測試
    test_auth_errors
    test_permission_errors
    
    print_header "測試套件執行完成"
}

# 快速測試（基本功能）
run_quick_tests() {
    print_header "開始運行快速測試"
    echo "API Base URL: $API_BASE_URL"
    echo
    
    test_user_login
    test_user_profile
    test_referral_validation
    test_referral_use
    test_referral_stats
    
    print_header "快速測試執行完成"
}

# 顯示使用說明
show_usage() {
    echo "MorningAI Core API - curl 測試腳本"
    echo
    echo "使用方法："
    echo "  export API_BASE_URL=\"http://localhost:8000/api/v1\""
    echo "  source curl-examples.sh"
    echo
    echo "可用函數："
    echo "  認證系統："
    echo "    test_user_registration    - 用戶註冊測試"
    echo "    test_user_login          - 用戶登入測試"
    echo "    test_admin_login         - 管理員登入測試"
    echo "    test_manager_login       - 租戶管理員登入測試"
    echo "    test_token_refresh       - 令牌刷新測試"
    echo "    test_user_profile        - 用戶資料測試"
    echo "    test_password_change     - 密碼更改測試"
    echo
    echo "  推薦系統："
    echo "    test_referral_validation - 推薦碼驗證測試"
    echo "    test_referral_use        - 推薦碼使用測試"
    echo "    test_referral_creation   - 推薦碼創建測試"
    echo "    test_referral_list       - 推薦碼列表測試"
    echo "    test_referral_stats      - 推薦統計測試"
    echo "    test_referral_leaderboard - 推薦排行榜測試"
    echo
    echo "  錯誤處理："
    echo "    test_auth_errors         - 認證錯誤測試"
    echo "    test_permission_errors   - 權限錯誤測試"
    echo
    echo "  測試套件："
    echo "    run_all_tests           - 運行所有測試"
    echo "    run_quick_tests         - 運行快速測試"
    echo "    show_usage              - 顯示此說明"
    echo
    echo "範例："
    echo "  test_user_login"
    echo "  test_referral_validation"
    echo "  run_quick_tests"
}

# 如果直接執行腳本，顯示使用說明
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    show_usage
fi

