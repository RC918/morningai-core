#!/bin/bash
# E段驗收測試腳本 - 按照指令要求執行4項驗收測試

BASE_URL="https://morningai-core.onrender.com"
echo "🔍 E段驗收測試開始 - $(date)"
echo "目標URL: $BASE_URL"
echo "=" * 60

# E1. OpenAPI可見性測試
echo "📋 E1. OpenAPI可見性測試"
echo "執行指令: curl -s $BASE_URL/openapi.json | jq -r '.paths | keys[]' | egrep '^/auth/|^/referral/'"

AUTH_REFERRAL_PATHS=$(curl -s $BASE_URL/openapi.json | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    paths = list(data.get('paths', {}).keys())
    auth_referral = [p for p in paths if '/auth/' in p or '/referral/' in p]
    for path in auth_referral:
        print(path)
except:
    pass
")

echo "找到的Auth/Referral路徑:"
echo "$AUTH_REFERRAL_PATHS"

TARGET_PATHS="/auth/register /auth/login /referral/stats"
FOUND_COUNT=0
for path in $TARGET_PATHS; do
    if echo "$AUTH_REFERRAL_PATHS" | grep -q "$path"; then
        echo "✅ $path - 找到"
        FOUND_COUNT=$((FOUND_COUNT + 1))
    else
        echo "❌ $path - 缺失"
    fi
done

echo "E1結果: $FOUND_COUNT/3 目標端點找到"
echo ""

# E2. 功能驗證測試
echo "📋 E2. 功能驗證測試"

# 測試註冊端點
echo "測試 POST /auth/register"
REGISTER_RESULT=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"p3m1@example.com","password":"Passw0rd!","referral_code":"ABC123"}' \
  -w "\n%{http_code}")

echo "註冊響應:"
echo "$REGISTER_RESULT"
echo ""

# 測試登入端點
echo "測試 POST /auth/login"
LOGIN_RESULT=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password"}' \
  -w "\n%{http_code}")

echo "登入響應:"
echo "$LOGIN_RESULT"

# 提取access_token (如果有)
ACCESS_TOKEN=$(echo "$LOGIN_RESULT" | python3 -c "
import json, sys
try:
    lines = sys.stdin.read().strip().split('\n')
    json_part = '\n'.join(lines[:-1])
    data = json.loads(json_part)
    print(data.get('access_token', ''))
except:
    pass
")

echo ""

# 測試推薦統計端點
echo "測試 GET /referral/stats"
if [ -n "$ACCESS_TOKEN" ]; then
    STATS_RESULT=$(curl -s $BASE_URL/referral/stats \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -w "\n%{http_code}")
else
    STATS_RESULT=$(curl -s $BASE_URL/referral/stats -w "\n%{http_code}")
fi

echo "推薦統計響應:"
echo "$STATS_RESULT"
echo ""

# E3. 檢查根路徑更新狀態
echo "📋 E3. 檢查部署狀態"
ROOT_RESULT=$(curl -s $BASE_URL/)
echo "根路徑響應:"
echo "$ROOT_RESULT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('消息:', data.get('message', 'N/A'))
    print('修復版本:', data.get('fix_version', 'N/A'))
    print('功能:', data.get('features', 'N/A'))
    print('時間戳:', data.get('timestamp', 'N/A'))
except:
    print('無法解析JSON響應')
"
echo ""

# 總結
echo "📊 E段驗收測試總結"
echo "=" * 60
echo "E1. OpenAPI可見性: $FOUND_COUNT/3 目標端點"
echo "E2. 功能驗證: 已執行註冊/登入/推薦統計測試"
echo "E3. 部署狀態: 已檢查根路徑更新狀態"
echo "E4. Render設定: 需要用戶提供截圖"
echo ""
echo "🎯 驗收狀態: $(if [ $FOUND_COUNT -eq 3 ]; then echo '✅ 通過'; else echo '❌ 需要修復'; fi)"
echo "完成時間: $(date)"

