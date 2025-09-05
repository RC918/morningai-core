#!/bin/bash
"""
聊天模組離線評測腳本
用於評估 GPT+RAG 系統的準確率和質量指標
"""

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASET_DIR="$SCRIPT_DIR/dataset"
RESULTS_DIR="$SCRIPT_DIR/results"
API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
EVAL_CONFIG="$SCRIPT_DIR/eval-config.json"

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
    
    if ! command -v jq &> /dev/null; then
        log_error "jq 未安裝，請先安裝: sudo apt-get install jq"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安裝，請先安裝: sudo apt-get install curl"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 未安裝"
        exit 1
    fi
    
    log_success "依賴檢查完成"
}

# 初始化目錄
init_directories() {
    log_info "初始化目錄結構..."
    
    mkdir -p "$DATASET_DIR"
    mkdir -p "$RESULTS_DIR"
    
    # 創建時間戳目錄
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    CURRENT_RESULTS_DIR="$RESULTS_DIR/$TIMESTAMP"
    mkdir -p "$CURRENT_RESULTS_DIR"
    
    log_success "目錄初始化完成: $CURRENT_RESULTS_DIR"
}

# 獲取認證令牌
get_auth_token() {
    log_info "獲取認證令牌..."
    
    local email="${EVAL_USER_EMAIL:-manager@morningai.com}"
    local password="${EVAL_USER_PASSWORD:-manager123}"
    
    TOKEN=$(curl -s -X POST "$API_BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\"}" \
        | jq -r '.access_token // empty')
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        log_error "無法獲取認證令牌"
        exit 1
    fi
    
    log_success "認證令牌獲取成功"
}

# 載入測試數據集
load_dataset() {
    log_info "載入測試數據集..."
    
    local dataset_file="$DATASET_DIR/chat_eval_dataset.json"
    
    if [ ! -f "$dataset_file" ]; then
        log_warning "測試數據集不存在，創建示例數據集..."
        create_sample_dataset "$dataset_file"
    fi
    
    # 驗證數據集格式
    if ! jq empty "$dataset_file" 2>/dev/null; then
        log_error "數據集格式無效: $dataset_file"
        exit 1
    fi
    
    DATASET_SIZE=$(jq length "$dataset_file")
    log_success "數據集載入完成，共 $DATASET_SIZE 條測試案例"
}

# 創建示例數據集
create_sample_dataset() {
    local output_file="$1"
    
    cat > "$output_file" << 'EOF'
[
  {
    "id": "test_001",
    "category": "product_info",
    "question": "MorningAI 有什麼主要功能？",
    "expected_keywords": ["聊天", "推薦", "內容管理", "多租戶"],
    "expected_intent": "question",
    "context_required": true,
    "difficulty": "easy"
  },
  {
    "id": "test_002", 
    "category": "referral",
    "question": "如何使用推薦碼？",
    "expected_keywords": ["推薦碼", "邀請", "朋友", "獎勵"],
    "expected_intent": "question",
    "context_required": true,
    "difficulty": "medium"
  },
  {
    "id": "test_003",
    "category": "account",
    "question": "忘記密碼怎麼辦？",
    "expected_keywords": ["密碼", "重置", "忘記", "郵箱"],
    "expected_intent": "help",
    "context_required": true,
    "difficulty": "easy"
  },
  {
    "id": "test_004",
    "category": "greeting",
    "question": "你好",
    "expected_keywords": ["歡迎", "助手", "幫助"],
    "expected_intent": "greeting",
    "context_required": false,
    "difficulty": "easy"
  },
  {
    "id": "test_005",
    "category": "complex",
    "question": "我想了解推薦系統的技術架構和實現細節",
    "expected_keywords": ["推薦系統", "架構", "技術"],
    "expected_intent": "question",
    "context_required": true,
    "difficulty": "hard"
  }
]
EOF
    
    log_info "示例數據集已創建: $output_file"
}

# 執行單個測試案例
run_single_test() {
    local test_case="$1"
    local test_id=$(echo "$test_case" | jq -r '.id')
    local question=$(echo "$test_case" | jq -r '.question')
    local expected_intent=$(echo "$test_case" | jq -r '.expected_intent')
    local expected_keywords=$(echo "$test_case" | jq -r '.expected_keywords[]')
    local context_required=$(echo "$test_case" | jq -r '.context_required')
    local difficulty=$(echo "$test_case" | jq -r '.difficulty')
    
    log_info "執行測試案例: $test_id - $question"
    
    # 發送聊天請求
    local start_time=$(date +%s.%N)
    
    local response=$(curl -s -X POST "$API_BASE/chat/send" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"$question\"}" \
        2>/dev/null)
    
    local end_time=$(date +%s.%N)
    local response_time=$(echo "$end_time - $start_time" | bc -l)
    
    # 檢查回應是否成功
    if [ -z "$response" ] || ! echo "$response" | jq empty 2>/dev/null; then
        log_error "測試案例 $test_id 失敗: API 回應無效"
        return 1
    fi
    
    # 提取回應數據
    local assistant_response=$(echo "$response" | jq -r '.response // empty')
    local detected_intent=$(echo "$response" | jq -r '.intent_analysis.primary_intent // empty')
    local confidence=$(echo "$response" | jq -r '.intent_analysis.confidence // 0')
    local knowledge_used=$(echo "$response" | jq -r '.knowledge_used // false')
    local session_id=$(echo "$response" | jq -r '.session_id // empty')
    local message_id=$(echo "$response" | jq -r '.message_id // empty')
    
    # 評估結果
    local intent_match="false"
    if [ "$detected_intent" = "$expected_intent" ]; then
        intent_match="true"
    fi
    
    # 關鍵詞匹配檢查
    local keyword_matches=0
    local total_keywords=0
    
    while IFS= read -r keyword; do
        if [ -n "$keyword" ]; then
            total_keywords=$((total_keywords + 1))
            if echo "$assistant_response" | grep -qi "$keyword"; then
                keyword_matches=$((keyword_matches + 1))
            fi
        fi
    done <<< "$expected_keywords"
    
    local keyword_score=0
    if [ $total_keywords -gt 0 ]; then
        keyword_score=$(echo "scale=2; $keyword_matches / $total_keywords" | bc -l)
    fi
    
    # 上下文使用評估
    local context_score="N/A"
    if [ "$context_required" = "true" ]; then
        if [ "$knowledge_used" = "true" ]; then
            context_score="1.0"
        else
            context_score="0.0"
        fi
    fi
    
    # 回應長度和質量簡單評估
    local response_length=${#assistant_response}
    local quality_score="medium"
    
    if [ $response_length -lt 20 ]; then
        quality_score="low"
    elif [ $response_length -gt 100 ]; then
        quality_score="high"
    fi
    
    # 生成測試結果
    local test_result=$(cat << EOF
{
  "test_id": "$test_id",
  "question": "$question",
  "response": "$assistant_response",
  "expected_intent": "$expected_intent",
  "detected_intent": "$detected_intent",
  "intent_match": $intent_match,
  "confidence": $confidence,
  "keyword_score": $keyword_score,
  "keyword_matches": $keyword_matches,
  "total_keywords": $total_keywords,
  "context_required": $context_required,
  "knowledge_used": $knowledge_used,
  "context_score": "$context_score",
  "response_time": $response_time,
  "response_length": $response_length,
  "quality_score": "$quality_score",
  "difficulty": "$difficulty",
  "session_id": "$session_id",
  "message_id": "$message_id",
  "timestamp": "$(date -Iseconds)"
}
EOF
)
    
    echo "$test_result"
    
    # 簡單的成功/失敗判斷
    if [ "$intent_match" = "true" ] && (( $(echo "$keyword_score >= 0.5" | bc -l) )); then
        log_success "測試案例 $test_id 通過"
        return 0
    else
        log_warning "測試案例 $test_id 部分通過或失敗"
        return 1
    fi
}

# 執行完整評測
run_evaluation() {
    log_info "開始執行完整評測..."
    
    local dataset_file="$DATASET_DIR/chat_eval_dataset.json"
    local results_file="$CURRENT_RESULTS_DIR/eval_results.json"
    local summary_file="$CURRENT_RESULTS_DIR/eval_summary.json"
    
    # 初始化結果文件
    echo "[]" > "$results_file"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # 逐個執行測試案例
    while IFS= read -r test_case; do
        if [ -n "$test_case" ] && [ "$test_case" != "null" ]; then
            total_tests=$((total_tests + 1))
            
            if run_single_test "$test_case"; then
                passed_tests=$((passed_tests + 1))
            else
                failed_tests=$((failed_tests + 1))
            fi
            
            # 保存測試結果
            local result=$(run_single_test "$test_case" 2>/dev/null)
            if [ -n "$result" ]; then
                # 將結果添加到結果文件
                jq --argjson new_result "$result" '. += [$new_result]' "$results_file" > "$results_file.tmp"
                mv "$results_file.tmp" "$results_file"
            fi
            
            # 短暫延遲避免API限制
            sleep 1
        fi
    done < <(jq -c '.[]' "$dataset_file")
    
    # 計算總體指標
    local pass_rate=0
    if [ $total_tests -gt 0 ]; then
        pass_rate=$(echo "scale=2; $passed_tests / $total_tests * 100" | bc -l)
    fi
    
    # 生成評測摘要
    local summary=$(cat << EOF
{
  "evaluation_timestamp": "$(date -Iseconds)",
  "dataset_size": $total_tests,
  "total_tests": $total_tests,
  "passed_tests": $passed_tests,
  "failed_tests": $failed_tests,
  "pass_rate_percent": $pass_rate,
  "api_base": "$API_BASE",
  "results_file": "$results_file"
}
EOF
)
    
    echo "$summary" > "$summary_file"
    
    log_success "評測完成！"
    log_info "總測試案例: $total_tests"
    log_info "通過案例: $passed_tests"
    log_info "失敗案例: $failed_tests"
    log_info "通過率: ${pass_rate}%"
    log_info "結果文件: $results_file"
    log_info "摘要文件: $summary_file"
}

# 生成評測報告
generate_report() {
    log_info "生成評測報告..."
    
    local results_file="$CURRENT_RESULTS_DIR/eval_results.json"
    local summary_file="$CURRENT_RESULTS_DIR/eval_summary.json"
    local report_file="$CURRENT_RESULTS_DIR/eval_report.md"
    
    if [ ! -f "$results_file" ] || [ ! -f "$summary_file" ]; then
        log_error "評測結果文件不存在，請先執行評測"
        return 1
    fi
    
    # 讀取摘要數據
    local total_tests=$(jq -r '.total_tests' "$summary_file")
    local passed_tests=$(jq -r '.passed_tests' "$summary_file")
    local pass_rate=$(jq -r '.pass_rate_percent' "$summary_file")
    local timestamp=$(jq -r '.evaluation_timestamp' "$summary_file")
    
    # 生成 Markdown 報告
    cat > "$report_file" << EOF
# 聊天模組評測報告

**評測時間:** $timestamp  
**API 端點:** $API_BASE  
**數據集大小:** $total_tests  

## 評測結果摘要

- **總測試案例:** $total_tests
- **通過案例:** $passed_tests
- **失敗案例:** $((total_tests - passed_tests))
- **通過率:** ${pass_rate}%

## 95% 準確率目標

EOF
    
    if (( $(echo "$pass_rate >= 95.0" | bc -l) )); then
        echo "✅ **已達成 95% 準確率目標**" >> "$report_file"
    else
        echo "❌ **未達成 95% 準確率目標** (目前: ${pass_rate}%)" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

## 詳細結果分析

### 按難度分類
EOF
    
    # 按難度統計
    for difficulty in "easy" "medium" "hard"; do
        local difficulty_results=$(jq --arg diff "$difficulty" '[.[] | select(.difficulty == $diff)]' "$results_file")
        local difficulty_total=$(echo "$difficulty_results" | jq length)
        local difficulty_passed=$(echo "$difficulty_results" | jq '[.[] | select(.intent_match == true and (.keyword_score | tonumber) >= 0.5)] | length')
        
        if [ $difficulty_total -gt 0 ]; then
            local difficulty_rate=$(echo "scale=1; $difficulty_passed / $difficulty_total * 100" | bc -l)
            echo "- **${difficulty^}:** $difficulty_passed/$difficulty_total (${difficulty_rate}%)" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

### 按分類統計
EOF
    
    # 按分類統計
    local categories=$(jq -r '[.[].question | split(" ")[0]] | unique | .[]' "$results_file" 2>/dev/null || echo "")
    
    cat >> "$report_file" << EOF

### 性能指標

- **平均響應時間:** $(jq '[.[].response_time | tonumber] | add / length' "$results_file" 2>/dev/null || echo "N/A") 秒
- **平均信心分數:** $(jq '[.[].confidence | tonumber] | add / length' "$results_file" 2>/dev/null || echo "N/A")
- **知識庫使用率:** $(jq '[.[] | select(.knowledge_used == true)] | length' "$results_file")/$total_tests

## 改進建議

EOF
    
    if (( $(echo "$pass_rate < 95.0" | bc -l) )); then
        cat >> "$report_file" << EOF
1. **提升準確率:**
   - 優化 RAG 檢索算法
   - 改進 prompt 工程
   - 增加訓練數據

2. **增強上下文理解:**
   - 改進意圖分析模型
   - 優化知識庫結構
   - 提升語義匹配精度

3. **性能優化:**
   - 減少響應時間
   - 提高併發處理能力
   - 優化緩存策略
EOF
    else
        cat >> "$report_file" << EOF
1. **維持高準確率:**
   - 持續監控性能指標
   - 定期更新知識庫
   - 優化用戶體驗

2. **擴展功能:**
   - 支援更多語言
   - 增加專業領域知識
   - 提升對話連貫性
EOF
    fi
    
    cat >> "$report_file" << EOF

## 測試環境

- **API 基礎 URL:** $API_BASE
- **認證方式:** JWT Bearer Token
- **測試用戶:** manager@morningai.com
- **評測工具版本:** 1.0.0

---

*此報告由自動化評測系統生成*
EOF
    
    log_success "評測報告已生成: $report_file"
}

# 快速測試
quick_test() {
    log_info "執行快速測試..."
    
    # 創建小型測試數據集
    local quick_dataset="$CURRENT_RESULTS_DIR/quick_test.json"
    cat > "$quick_dataset" << 'EOF'
[
  {
    "id": "quick_001",
    "category": "greeting",
    "question": "你好",
    "expected_keywords": ["歡迎", "助手"],
    "expected_intent": "greeting",
    "context_required": false,
    "difficulty": "easy"
  },
  {
    "id": "quick_002",
    "category": "product",
    "question": "MorningAI 有什麼功能？",
    "expected_keywords": ["功能", "聊天", "推薦"],
    "expected_intent": "question",
    "context_required": true,
    "difficulty": "medium"
  }
]
EOF
    
    # 執行快速測試
    local passed=0
    local total=0
    
    while IFS= read -r test_case; do
        if [ -n "$test_case" ] && [ "$test_case" != "null" ]; then
            total=$((total + 1))
            if run_single_test "$test_case" >/dev/null 2>&1; then
                passed=$((passed + 1))
            fi
        fi
    done < <(jq -c '.[]' "$quick_dataset")
    
    log_success "快速測試完成: $passed/$total 通過"
}

# 主函數
main() {
    echo "🤖 MorningAI 聊天模組離線評測系統"
    echo "=================================="
    
    local command="${1:-full}"
    
    case "$command" in
        "full")
            check_dependencies
            init_directories
            get_auth_token
            load_dataset
            run_evaluation
            generate_report
            ;;
        "quick")
            check_dependencies
            init_directories
            get_auth_token
            quick_test
            ;;
        "report")
            generate_report
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [command]"
            echo ""
            echo "命令:"
            echo "  full    執行完整評測 (默認)"
            echo "  quick   執行快速測試"
            echo "  report  生成評測報告"
            echo "  help    顯示此幫助信息"
            echo ""
            echo "環境變數:"
            echo "  API_BASE              API 基礎 URL (默認: http://localhost:8000/api/v1)"
            echo "  EVAL_USER_EMAIL       評測用戶郵箱 (默認: manager@morningai.com)"
            echo "  EVAL_USER_PASSWORD    評測用戶密碼 (默認: manager123)"
            ;;
        *)
            log_error "未知命令: $command"
            echo "使用 '$0 help' 查看幫助信息"
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"

