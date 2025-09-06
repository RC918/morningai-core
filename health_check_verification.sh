#!/bin/bash

# 健康檢查端點驗證腳本
# 按照驗收指令要求進行5次連續探測

echo "=== 健康檢查端點驗證 ==="
echo "時間: $(date)"
echo ""

# 測試 /health 端點 (輕量版)
echo "1. 測試 /health 端點 (輕量版) - 5次連續探測"
echo "URL: https://api.morningai.me/health"
echo ""

total_time_health=0
success_count_health=0

for i in {1..5}; do
    echo "第 $i 次探測:"
    start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" \
        -H "Host: api.morningai.me" \
        https://api.morningai.me/health)
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d' | sed '/TIME_TOTAL:/d')
    
    echo "  HTTP狀態碼: $http_code"
    echo "  響應時間: ${time_total}s"
    echo "  響應內容: $body"
    
    if [ "$http_code" = "200" ]; then
        success_count_health=$((success_count_health + 1))
        total_time_health=$(echo "$total_time_health + $time_total" | bc -l)
    fi
    
    echo ""
    sleep 1
done

if [ $success_count_health -gt 0 ]; then
    avg_time_health=$(echo "scale=3; $total_time_health / $success_count_health" | bc -l)
    echo "/health 端點統計: 成功 $success_count_health/5 次，平均延遲 ${avg_time_health}s"
else
    echo "/health 端點統計: 全部失敗"
fi

echo ""
echo "================================"
echo ""

# 測試 /healthz 端點 (全量檢查)
echo "2. 測試 /healthz 端點 (全量檢查) - 5次連續探測"
echo "URL: https://api.morningai.me/healthz"
echo ""

total_time_healthz=0
success_count_healthz=0

for i in {1..5}; do
    echo "第 $i 次探測:"
    start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" \
        -H "Host: api.morningai.me" \
        https://api.morningai.me/healthz)
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d' | sed '/TIME_TOTAL:/d')
    
    echo "  HTTP狀態碼: $http_code"
    echo "  響應時間: ${time_total}s"
    echo "  響應內容: $body"
    
    if [ "$http_code" = "200" ]; then
        success_count_healthz=$((success_count_healthz + 1))
        total_time_healthz=$(echo "$total_time_healthz + $time_total" | bc -l)
    fi
    
    echo ""
    sleep 1
done

if [ $success_count_healthz -gt 0 ]; then
    avg_time_healthz=$(echo "scale=3; $total_time_healthz / $success_count_healthz" | bc -l)
    echo "/healthz 端點統計: 成功 $success_count_healthz/5 次，平均延遲 ${avg_time_healthz}s"
else
    echo "/healthz 端點統計: 全部失敗"
fi

echo ""
echo "================================"
echo ""

# 總結
echo "3. 驗證總結"
echo "時間: $(date)"
echo "/health 端點: 成功 $success_count_health/5 次"
echo "/healthz 端點: 成功 $success_count_healthz/5 次"

if [ $success_count_health -gt 0 ]; then
    echo "/health 平均延遲: ${avg_time_health}s"
fi

if [ $success_count_healthz -gt 0 ]; then
    echo "/healthz 平均延遲: ${avg_time_healthz}s"
fi

# 測試Render直接URL作為對照
echo ""
echo "4. Render直接URL對照測試"
echo "URL: https://morningai-core-staging.onrender.com/health"

response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" \
    https://morningai-core-staging.onrender.com/health)

http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_CODE:/d' | sed '/TIME_TOTAL:/d')

echo "Render直接URL - HTTP狀態碼: $http_code"
echo "Render直接URL - 響應時間: ${time_total}s"
echo "Render直接URL - 響應內容: $body"

echo ""
echo "驗證完成!"

