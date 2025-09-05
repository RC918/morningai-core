#!/bin/bash

# MorningAI Phase 5 聊天模組快速測試腳本
# 執行聊天系統的核心功能測試

set -e

# 配置
API_BASE_URL=${API_BASE_URL:-"http://localhost:8000/api/v1"}
TEST_EMAIL="manager@morningai.com"
TEST_PASSWORD="manager123"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log_info "檢查依賴..."
    
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安裝"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq 未安裝"
        exit 1
    fi
    
    log_success "依賴檢查通過"
}

# 檢查 API 健康狀態
check_api_health() {
    log_info "檢查 API 健康狀態..."
    
    local health_response
    health_response=$(curl -s -f "${API_BASE_URL%/api/v1}/health" || echo "")
    
    if [[ -z "$health_response" ]]; then
        log_error "API 服務不可用，請檢查服務是否啟動"
        log_info "嘗試啟動服務: docker-compose up -d"
        exit 1
    fi
    
    log_success "API 服務正常"
}

# 用戶登入
user_login() {
    log_info "用戶登入..."
    
    local login_response
    login_response=$(curl -s -X POST "${API_BASE_URL}/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")
    
    if [[ -z "$login_response" ]]; then
        log_error "登入請求失敗"
        exit 1
    fi
    
    ACCESS_TOKEN=$(echo "$login_response" | jq -r '.access_token // empty')
    
    if [[ -z "$ACCESS_TOKEN" || "$ACCESS_TOKEN" == "null" ]]; then
        log_error "登入失敗，無法獲取 access token"
        echo "響應: $login_response"
        exit 1
    fi
    
    log_success "登入成功"
}

# 創建聊天會話
create_chat_session() {
    log_info "創建聊天會話..."
    
    local session_response
    session_response=$(curl -s -X POST "${API_BASE_URL}/chat/sessions" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"title":"快速測試會話","metadata":{"source":"quick_test"}}')
    
    if [[ -z "$session_response" ]]; then
        log_error "創建會話請求失敗"
        exit 1
    fi
    
    SESSION_ID=$(echo "$session_response" | jq -r '.data.id // .id // empty')
    
    if [[ -z "$SESSION_ID" || "$SESSION_ID" == "null" ]]; then
        log_error "創建會話失敗"
        echo "響應: $session_response"
        exit 1
    fi
    
    log_success "會話創建成功: $SESSION_ID"
}

# 發送聊天消息
send_chat_message() {
    local message="$1"
    local description="$2"
    
    log_info "$description"
    
    local chat_response
    chat_response=$(curl -s -X POST "${API_BASE_URL}/chat/send" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\":\"${SESSION_ID}\",\"message\":\"${message}\"}")
    
    if [[ -z "$chat_response" ]]; then
        log_error "發送消息請求失敗"
        return 1
    fi
    
    local success
    success=$(echo "$chat_response" | jq -r '.success // false')
    
    if [[ "$success" == "true" ]]; then
        local response_text
        local response_type
        local processing_time
        
        response_text=$(echo "$chat_response" | jq -r '.data.response // "無回應"')
        response_type=$(echo "$chat_response" | jq -r '.data.response_type // "unknown"')
        processing_time=$(echo "$chat_response" | jq -r '.data.processing_time // 0')
        
        log_success "消息發送成功"
        echo "  回應類型: $response_type"
        echo "  處理時間: ${processing_time}s"
        echo "  回應內容: ${response_text:0:100}..."
        
        # 保存最後一個消息 ID
        LAST_MESSAGE_ID=$(echo "$chat_response" | jq -r '.data.message_id // empty')
    else
        local error_message
        error_message=$(echo "$chat_response" | jq -r '.message // "未知錯誤"')
        log_error "消息發送失敗: $error_message"
        return 1
    fi
}

# 搜索知識庫
search_knowledge() {
    log_info "搜索知識庫..."
    
    local search_response
    search_response=$(curl -s -X POST "${API_BASE_URL}/chat/knowledge/search" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"query":"定價方案","top_k":3}')
    
    if [[ -z "$search_response" ]]; then
        log_error "知識庫搜索請求失敗"
        return 1
    fi
    
    local success
    success=$(echo "$search_response" | jq -r '.success // false')
    
    if [[ "$success" == "true" ]]; then
        local result_count
        result_count=$(echo "$search_response" | jq -r '.data.results | length')
        log_success "知識庫搜索成功，找到 $result_count 個結果"
    else
        log_warning "知識庫搜索失敗或無結果"
    fi
}

# 提交反饋
submit_feedback() {
    if [[ -z "$LAST_MESSAGE_ID" ]]; then
        log_warning "跳過反饋測試，沒有可用的消息 ID"
        return 0
    fi
    
    log_info "提交聊天反饋..."
    
    local feedback_response
    feedback_response=$(curl -s -X POST "${API_BASE_URL}/chat/feedback" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\":\"${SESSION_ID}\",\"message_id\":\"${LAST_MESSAGE_ID}\",\"score\":1,\"reason\":\"helpful\",\"comment\":\"測試反饋\"}")
    
    if [[ -z "$feedback_response" ]]; then
        log_error "提交反饋請求失敗"
        return 1
    fi
    
    local success
    success=$(echo "$feedback_response" | jq -r '.success // false')
    
    if [[ "$success" == "true" ]]; then
        log_success "反饋提交成功"
    else
        log_warning "反饋提交失敗"
    fi
}

# 獲取會話列表
get_sessions() {
    log_info "獲取會話列表..."
    
    local sessions_response
    sessions_response=$(curl -s -X GET "${API_BASE_URL}/chat/sessions?page=1&size=5" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")
    
    if [[ -z "$sessions_response" ]]; then
        log_error "獲取會話列表請求失敗"
        return 1
    fi
    
    local success
    success=$(echo "$sessions_response" | jq -r '.success // false')
    
    if [[ "$success" == "true" ]]; then
        local session_count
        session_count=$(echo "$sessions_response" | jq -r '.data.sessions | length')
        log_success "獲取會話列表成功，共 $session_count 個會話"
    else
        log_warning "獲取會話列表失敗"
    fi
}

# 獲取聊天歷史
get_chat_history() {
    log_info "獲取聊天歷史..."
    
    local history_response
    history_response=$(curl -s -X GET "${API_BASE_URL}/chat/sessions/${SESSION_ID}/history?page=1&size=10" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")
    
    if [[ -z "$history_response" ]]; then
        log_error "獲取聊天歷史請求失敗"
        return 1
    fi
    
    local success
    success=$(echo "$history_response" | jq -r '.success // false')
    
    if [[ "$success" == "true" ]]; then
        local message_count
        message_count=$(echo "$history_response" | jq -r '.data.messages | length')
        log_success "獲取聊天歷史成功，共 $message_count 條消息"
    else
        log_warning "獲取聊天歷史失敗"
    fi
}

# 清理測試數據
cleanup_test_data() {
    if [[ -n "$SESSION_ID" ]]; then
        log_info "清理測試數據..."
        
        curl -s -X DELETE "${API_BASE_URL}/chat/sessions/${SESSION_ID}" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" > /dev/null
        
        log_success "測試數據清理完成"
    fi
}

# 主測試流程
run_quick_tests() {
    echo "=========================================="
    echo "MorningAI Phase 5 聊天模組快速測試"
    echo "=========================================="
    
    # 檢查環境
    check_dependencies
    check_api_health
    
    # 認證
    user_login
    
    # 聊天功能測試
    create_chat_session
    
    # 測試不同類型的消息
    send_chat_message "你好，請介紹一下 MorningAI" "測試基本問候和產品介紹"
    send_chat_message "你們的定價方案是什麼？" "測試產品信息查詢"
    send_chat_message "我想了解技術支援服務" "測試技術支援查詢"
    
    # 知識庫測試
    search_knowledge
    
    # 反饋測試
    submit_feedback
    
    # 會話管理測試
    get_sessions
    get_chat_history
    
    # 清理
    cleanup_test_data
    
    echo "=========================================="
    log_success "快速測試完成！"
    echo "=========================================="
}

# 錯誤處理
trap 'log_error "測試過程中發生錯誤，正在清理..."; cleanup_test_data; exit 1' ERR

# 執行測試
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_quick_tests
fi

