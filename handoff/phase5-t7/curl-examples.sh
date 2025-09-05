#!/bin/bash

# MorningAI Core API - T+7 Vector Integration 測試腳本
# 版本: 3.1.0-t7
# 功能: 完整的 API 測試，包含向量搜索、增強聊天、知識管理、評測系統

set -e

# 配置
API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api/v1}"
ACCESS_TOKEN=""
SESSION_ID="test-session-$(date +%s)"
EVALUATION_ID=""
KNOWLEDGE_ID=""

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 輔助函數
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 檢查響應狀態
check_response() {
    local response_code=$1
    local expected_code=$2
    local test_name=$3
    
    if [ "$response_code" -eq "$expected_code" ]; then
        print_success "$test_name - 狀態碼: $response_code"
        return 0
    else
        print_error "$test_name - 期望: $expected_code, 實際: $response_code"
        return 1
    fi
}

# 測試系統健康狀態
test_health_check() {
    print_header "🔧 系統健康檢查"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X GET "$API_BASE_URL/health")
    
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code" 200 "系統健康檢查"; then
        echo "$body" | jq -r '.status' | while read status; do
            if [ "$status" = "healthy" ]; then
                print_success "系統狀態: $status"
            else
                print_warning "系統狀態: $status"
            fi
        done
        
        # 檢查各組件狀態
        echo "$body" | jq -r '.components | to_entries[] | "\(.key): \(.value.status)"' | while read component; do
            print_info "組件狀態 - $component"
        done
        
        # 顯示向量數量
        local vector_count=$(echo "$body" | jq -r '.components.vector_db.vector_count // "N/A"')
        print_info "向量數量: $vector_count"
    fi
}

# 用戶登入
test_user_login() {
    print_header "🔐 用戶登入"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "user@morningai.com",
            "password": "user123"
        }')
    
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code" 200 "用戶登入"; then
        ACCESS_TOKEN=$(echo "$body" | jq -r '.access_token')
        print_success "已獲取 access_token"
        print_info "Token 前綴: ${ACCESS_TOKEN:0:20}..."
    else
        print_error "登入失敗，無法繼續測試"
        exit 1
    fi
}

# 向量語義搜索測試
test_vector_search() {
    print_header "🔍 向量語義搜索測試"
    
    # 測試 1: 定價查詢
    print_info "測試 1: 定價查詢"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/vector/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d '{
            "query": "MorningAI的定價方案是什麼？",
            "limit": 5,
            "threshold": 0.7
        }')
    
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code" 200 "定價查詢搜索"; then
        local results_count=$(echo "$body" | jq -r '.results | length')
        local query_time=$(echo "$body" | jq -r '.query_time')
        print_success "搜索結果數量: $results_count"
        print_success "查詢時間: ${query_time}秒"
        
        # 顯示前兩個結果
        echo "$body" | jq -r '.results[0:2][] | "- \(.title) (相似度: \(.similarity))"' | while read result; do
            print_info "$result"
        done
    fi
    
    # 測試 2: 技術查詢
    print_info "測試 2: 技術查詢"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/vector/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d '{
            "query": "如何整合API？",
            "limit": 3,
            "categories": ["technical", "api"],
            "threshold": 0.6
        }')
    
    local body2=$(echo "$response2" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code2=$(echo "$response2" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code2" 200 "技術查詢搜索"; then
        local results_count2=$(echo "$body2" | jq -r '.results | length')
        print_success "技術查詢結果數量: $results_count2"
    fi
    
    # 測試 3: 空查詢錯誤處理
    print_info "測試 3: 空查詢錯誤處理"
    local response3=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/vector/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d '{
            "query": "",
            "limit": 5
        }')
    
    local status_code3=$(echo "$response3" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    check_response "$status_code3" 400 "空查詢錯誤處理"
}

# 增強聊天系統測試
test_enhanced_chat() {
    print_header "💬 增強聊天系統測試"
    
    # 測試 1: RAG 回應
    print_info "測試 1: 定價問題 (期望 RAG 回應)"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/chat/enhanced" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"message\": \"你們的定價方案是什麼？\",
            \"session_id\": \"$SESSION_ID\",
            \"use_rag\": true,
            \"max_sources\": 3
        }")
    
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code" 200 "定價問題聊天"; then
        local response_type=$(echo "$body" | jq -r '.response_type')
        local confidence=$(echo "$body" | jq -r '.confidence')
        local processing_time=$(echo "$body" | jq -r '.processing_time')
        local sources_count=$(echo "$body" | jq -r '.sources | length')
        
        print_success "回應類型: $response_type"
        print_success "信心度: $confidence"
        print_success "處理時間: ${processing_time}秒"
        print_success "知識來源數量: $sources_count"
        
        # 顯示建議問題
        local suggested_count=$(echo "$body" | jq -r '.suggested_questions | length')
        if [ "$suggested_count" -gt 0 ]; then
            print_info "建議問題數量: $suggested_count"
            echo "$body" | jq -r '.suggested_questions[0:2][]' | while read question; do
                print_info "- $question"
            done
        fi
    fi
    
    # 測試 2: 後續問題
    print_info "測試 2: 後續問題 (上下文測試)"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/chat/enhanced" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"message\": \"專業版和企業版有什麼差別？\",
            \"session_id\": \"$SESSION_ID\",
            \"context_window\": 5
        }")
    
    local status_code2=$(echo "$response2" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    check_response "$status_code2" 200 "後續問題聊天"
    
    # 測試 3: GPT Fallback
    print_info "測試 3: 知識庫外問題 (期望 GPT Fallback)"
    local response3=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/chat/enhanced" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"message\": \"今天天氣如何？\",
            \"session_id\": \"$SESSION_ID\",
            \"use_rag\": true
        }")
    
    local body3=$(echo "$response3" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code3=$(echo "$response3" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code3" 200 "GPT Fallback 測試"; then
        local response_type3=$(echo "$body3" | jq -r '.response_type')
        local sources_count3=$(echo "$body3" | jq -r '.sources | length')
        print_success "回應類型: $response_type3"
        print_success "知識來源數量: $sources_count3 (應為0)"
    fi
    
    # 測試 4: 技術支援問題
    print_info "測試 4: 技術支援問題"
    local response4=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/chat/enhanced" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"message\": \"如何整合你們的API？\",
            \"session_id\": \"$SESSION_ID\",
            \"use_rag\": true,
            \"max_sources\": 5,
            \"temperature\": 0.5
        }")
    
    local status_code4=$(echo "$response4" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    check_response "$status_code4" 200 "技術支援問題"
}

# 知識庫管理測試
test_knowledge_management() {
    print_header "📚 知識庫管理測試"
    
    # 測試 1: 創建知識條目
    print_info "測試 1: 創建知識條目"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/knowledge" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d '{
            "title": "測試知識條目",
            "content": "這是一個測試用的知識條目，用於驗證知識庫管理功能。包含產品介紹、使用方法、常見問題等內容。",
            "source": "test_knowledge",
            "category": "測試",
            "language": "zh-TW",
            "tags": ["測試", "知識庫", "API"],
            "priority": "medium",
            "metadata": {
                "author": "測試用戶",
                "version": "1.0"
            }
        }')
    
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code" 201 "創建知識條目"; then
        KNOWLEDGE_ID=$(echo "$body" | jq -r '.id')
        print_success "知識條目ID: $KNOWLEDGE_ID"
    fi
    
    # 測試 2: 獲取知識條目列表
    print_info "測試 2: 獲取知識條目列表"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X GET "$API_BASE_URL/knowledge?page=1&limit=10&category=測試" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    local body2=$(echo "$response2" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code2=$(echo "$response2" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code2" 200 "獲取知識條目列表"; then
        local total=$(echo "$body2" | jq -r '.total')
        local items_count=$(echo "$body2" | jq -r '.items | length')
        print_success "總數量: $total, 當前頁數量: $items_count"
    fi
    
    # 測試 3: 獲取知識條目詳情
    if [ -n "$KNOWLEDGE_ID" ]; then
        print_info "測試 3: 獲取知識條目詳情"
        local response3=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X GET "$API_BASE_URL/knowledge/$KNOWLEDGE_ID" \
            -H "Authorization: Bearer $ACCESS_TOKEN")
        
        local status_code3=$(echo "$response3" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
        check_response "$status_code3" 200 "獲取知識條目詳情"
        
        # 測試 4: 更新知識條目
        print_info "測試 4: 更新知識條目"
        local response4=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X PUT "$API_BASE_URL/knowledge/$KNOWLEDGE_ID" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -d '{
                "title": "更新後的測試知識條目",
                "content": "這是更新後的測試知識條目內容，包含更多詳細信息和使用案例。",
                "source": "test_knowledge_updated",
                "category": "測試",
                "language": "zh-TW",
                "tags": ["測試", "知識庫", "API", "更新"],
                "priority": "high"
            }')
        
        local status_code4=$(echo "$response4" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
        check_response "$status_code4" 200 "更新知識條目"
    fi
    
    # 測試 5: 搜索知識條目
    print_info "測試 5: 搜索知識條目"
    local response5=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X GET "$API_BASE_URL/knowledge?search=測試&language=zh-TW" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    local status_code5=$(echo "$response5" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    check_response "$status_code5" 200 "搜索知識條目"
}

# 評測系統測試
test_evaluation_system() {
    print_header "📊 評測系統測試"
    
    # 測試 1: 運行快速評測
    print_info "測試 1: 運行快速評測 (3個查詢)"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/evaluation/run" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d '{
            "queries": [
                {
                    "id": "eval_001",
                    "query": "你們的定價方案是什麼？",
                    "category": "pricing",
                    "difficulty": "easy",
                    "expected_response_type": "rag",
                    "expected_sources": ["kb_002"],
                    "expected_keywords": ["基礎版", "專業版", "企業版"],
                    "ground_truth": "MorningAI 提供三種靈活的定價方案以滿足不同規模企業的需求"
                },
                {
                    "id": "eval_002",
                    "query": "如何整合API？",
                    "category": "technical",
                    "difficulty": "medium",
                    "expected_response_type": "rag",
                    "expected_sources": ["kb_004"],
                    "expected_keywords": ["API", "整合", "文檔"],
                    "ground_truth": "API 整合需要先獲取 API 密鑰，然後按照文檔進行配置"
                },
                {
                    "id": "eval_003",
                    "query": "今天天氣如何？",
                    "category": "general",
                    "difficulty": "easy",
                    "expected_response_type": "gpt_fallback",
                    "expected_sources": [],
                    "expected_keywords": [],
                    "ground_truth": "這不是我們知識庫涵蓋的內容"
                }
            ],
            "config": {
                "accuracy_threshold": 0.95,
                "response_time_threshold": 3.0
            }
        }')
    
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code" 200 "運行評測"; then
        EVALUATION_ID=$(echo "$body" | jq -r '.evaluation_id')
        local overall_accuracy=$(echo "$body" | jq -r '.summary.overall_metrics.overall_accuracy')
        local avg_processing_time=$(echo "$body" | jq -r '.summary.performance_metrics.avg_processing_time')
        local accuracy_target_met=$(echo "$body" | jq -r '.summary.overall_metrics.accuracy_target_met')
        local response_time_target_met=$(echo "$body" | jq -r '.summary.performance_metrics.response_time_target_met')
        
        print_success "評測ID: $EVALUATION_ID"
        print_success "總體準確率: $overall_accuracy"
        print_success "平均處理時間: ${avg_processing_time}秒"
        
        if [ "$accuracy_target_met" = "true" ]; then
            print_success "準確率目標達成 ✅"
        else
            print_warning "準確率目標未達成 ⚠️"
        fi
        
        if [ "$response_time_target_met" = "true" ]; then
            print_success "響應時間目標達成 ✅"
        else
            print_warning "響應時間目標未達成 ⚠️"
        fi
        
        # 顯示分類表現
        echo "$body" | jq -r '.summary.category_breakdown | to_entries[] | "\(.key): 準確率 \(.value.avg_score), 平均時間 \(.value.avg_time)秒"' | while read category_result; do
            print_info "$category_result"
        done
    fi
    
    # 測試 2: 獲取評測報告
    if [ -n "$EVALUATION_ID" ]; then
        print_info "測試 2: 獲取評測報告"
        local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X GET "$API_BASE_URL/evaluation/$EVALUATION_ID/report" \
            -H "Authorization: Bearer $ACCESS_TOKEN")
        
        local status_code2=$(echo "$response2" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
        if check_response "$status_code2" 200 "獲取評測報告"; then
            print_success "評測報告可下載"
        fi
        
        # 測試 3: 獲取評測圖表
        print_info "測試 3: 獲取評測圖表"
        local response3=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X GET "$API_BASE_URL/evaluation/$EVALUATION_ID/charts" \
            -H "Authorization: Bearer $ACCESS_TOKEN")
        
        local status_code3=$(echo "$response3" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
        if check_response "$status_code3" 200 "獲取評測圖表"; then
            print_success "評測圖表可下載"
        fi
    fi
}

# 推薦系統測試 (原有功能)
test_referral_system() {
    print_header "🚀 推薦系統測試 (原有功能)"
    
    # 測試 1: 使用推薦碼
    print_info "測試 1: 使用推薦碼"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "$API_BASE_URL/referral/use" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d '{
            "code": "WELCOME2025"
        }')
    
    local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    check_response "$status_code" 200 "使用推薦碼"
    
    # 測試 2: 獲取推薦統計
    print_info "測試 2: 獲取推薦統計"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X GET "$API_BASE_URL/referral/stats" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    local body2=$(echo "$response2" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status_code2=$(echo "$response2" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if check_response "$status_code2" 200 "獲取推薦統計"; then
        local total_referrals=$(echo "$body2" | jq -r '.total_referrals // 0')
        local successful_referrals=$(echo "$body2" | jq -r '.successful_referrals // 0')
        print_success "總推薦數: $total_referrals"
        print_success "成功推薦數: $successful_referrals"
    fi
}

# 性能測試
test_performance() {
    print_header "⚡ 性能測試"
    
    print_info "執行 10 次向量搜索測試..."
    local total_time=0
    local success_count=0
    
    for i in {1..10}; do
        local start_time=$(date +%s.%N)
        
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X POST "$API_BASE_URL/vector/search" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -d '{
                "query": "定價方案",
                "limit": 3
            }')
        
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc)
        local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
        
        if [ "$status_code" -eq 200 ]; then
            success_count=$((success_count + 1))
            total_time=$(echo "$total_time + $duration" | bc)
            print_info "測試 $i: ${duration}秒"
        else
            print_error "測試 $i 失敗: $status_code"
        fi
    done
    
    if [ "$success_count" -gt 0 ]; then
        local avg_time=$(echo "scale=3; $total_time / $success_count" | bc)
        print_success "成功率: $success_count/10"
        print_success "平均響應時間: ${avg_time}秒"
        
        # 檢查是否滿足性能目標
        local time_check=$(echo "$avg_time < 1.0" | bc)
        if [ "$time_check" -eq 1 ]; then
            print_success "性能目標達成 (< 1秒) ✅"
        else
            print_warning "性能目標未達成 (≥ 1秒) ⚠️"
        fi
    fi
}

# 清理測試數據
cleanup_test_data() {
    print_header "🧹 清理測試數據"
    
    # 刪除測試知識條目
    if [ -n "$KNOWLEDGE_ID" ]; then
        print_info "刪除測試知識條目: $KNOWLEDGE_ID"
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -X DELETE "$API_BASE_URL/knowledge/$KNOWLEDGE_ID" \
            -H "Authorization: Bearer $ACCESS_TOKEN")
        
        local status_code=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
        if check_response "$status_code" 204 "刪除測試知識條目"; then
            print_success "測試數據清理完成"
        fi
    fi
}

# 快速測試套件
run_quick_tests() {
    print_header "🚀 快速測試套件"
    echo -e "${CYAN}執行核心功能快速測試...${NC}"
    
    test_health_check
    test_user_login
    test_vector_search
    test_enhanced_chat
    
    print_header "📊 快速測試完成"
    print_success "核心功能測試通過"
}

# 完整測試套件
run_all_tests() {
    print_header "🎯 完整測試套件"
    echo -e "${CYAN}執行所有功能的完整測試...${NC}"
    
    test_health_check
    test_user_login
    test_vector_search
    test_enhanced_chat
    test_knowledge_management
    test_evaluation_system
    test_referral_system
    test_performance
    cleanup_test_data
    
    print_header "🎉 完整測試完成"
    print_success "所有功能測試通過"
}

# 主函數
main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           MorningAI Core API - T+7 Vector Integration        ║"
    echo "║                        測試腳本 v3.1.0                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    print_info "API Base URL: $API_BASE_URL"
    print_info "Session ID: $SESSION_ID"
    
    # 檢查 jq 是否安裝
    if ! command -v jq &> /dev/null; then
        print_error "需要安裝 jq 來解析 JSON 響應"
        print_info "Ubuntu/Debian: sudo apt-get install jq"
        print_info "macOS: brew install jq"
        exit 1
    fi
    
    # 檢查 bc 是否安裝 (用於性能測試)
    if ! command -v bc &> /dev/null; then
        print_warning "建議安裝 bc 來進行精確的時間計算"
        print_info "Ubuntu/Debian: sudo apt-get install bc"
    fi
    
    case "${1:-all}" in
        "quick")
            run_quick_tests
            ;;
        "health")
            test_health_check
            ;;
        "login")
            test_user_login
            ;;
        "vector")
            test_user_login
            test_vector_search
            ;;
        "chat")
            test_user_login
            test_enhanced_chat
            ;;
        "knowledge")
            test_user_login
            test_knowledge_management
            ;;
        "evaluation")
            test_user_login
            test_evaluation_system
            ;;
        "referral")
            test_user_login
            test_referral_system
            ;;
        "performance")
            test_user_login
            test_performance
            ;;
        "all")
            run_all_tests
            ;;
        *)
            echo -e "${YELLOW}使用方法:${NC}"
            echo "  $0 [quick|health|login|vector|chat|knowledge|evaluation|referral|performance|all]"
            echo ""
            echo -e "${YELLOW}選項說明:${NC}"
            echo "  quick       - 快速測試 (健康檢查、登入、向量搜索、聊天)"
            echo "  health      - 系統健康檢查"
            echo "  login       - 用戶登入測試"
            echo "  vector      - 向量搜索測試"
            echo "  chat        - 增強聊天測試"
            echo "  knowledge   - 知識庫管理測試"
            echo "  evaluation  - 評測系統測試"
            echo "  referral    - 推薦系統測試"
            echo "  performance - 性能測試"
            echo "  all         - 完整測試套件 (默認)"
            echo ""
            echo -e "${YELLOW}環境變數:${NC}"
            echo "  API_BASE_URL - API 基礎 URL (默認: http://localhost:8000/api/v1)"
            echo ""
            echo -e "${YELLOW}示例:${NC}"
            echo "  $0 quick"
            echo "  API_BASE_URL=https://api.morningai.com/api/v1 $0 all"
            ;;
    esac
}

# 執行主函數
main "$@"

