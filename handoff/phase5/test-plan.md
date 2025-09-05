# MorningAI Core API 測試計劃

## 概述

本文檔描述了 MorningAI Core API 的完整測試計劃，涵蓋認證系統和推薦系統的所有核心功能。

## 測試環境

### 測試帳戶
基於 `seed.sql` 中的測試數據：

| 角色 | 郵箱 | 密碼 | 權限 |
|------|------|------|------|
| 系統管理員 | admin@morningai.com | admin123 | 全部權限 |
| 租戶管理員 | manager@morningai.com | manager123 | 租戶管理權限 |
| 一般用戶 | user@morningai.com | user123 | 基本用戶權限 |
| Demo 用戶 | demo@morningai.com | demo123 | 基本用戶權限 |

### 測試推薦碼
| 推薦碼 | 擁有者 | 最大使用次數 | 狀態 |
|--------|--------|--------------|------|
| WELCOME2025 | admin@morningai.com | 1000 | 啟用 |
| FRIEND50 | manager@morningai.com | 50 | 啟用 |
| DEMO100 | demo@morningai.com | 100 | 啟用 |

## 測試案例

### 1. 認證系統測試

#### 1.1 用戶註冊測試

**測試案例 1.1.1: 正常註冊**
```bash
# 請求
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "NewUser123",
  "username": "newuser",
  "display_name": "New User",
  "first_name": "New",
  "last_name": "User",
  "referral_code": "WELCOME2025",
  "language": "zh-TW",
  "timezone": "Asia/Taipei"
}

# 預期響應
HTTP/1.1 200 OK
{
  "success": true,
  "message": "註冊成功",
  "data": {
    "user_id": "uuid",
    "email": "newuser@example.com",
    "referral_code": "NEWUSER2025"
  }
}
```

**測試案例 1.1.2: 重複郵箱註冊**
```bash
# 請求
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "admin@morningai.com",
  "password": "Test123456"
}

# 預期響應
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "用戶創建失敗，郵箱或用戶名可能已存在"
}
```

**測試案例 1.1.3: 無效推薦碼註冊**
```bash
# 請求
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "Test123456",
  "referral_code": "INVALID"
}

# 預期響應
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "推薦碼不存在"
}
```

**測試案例 1.1.4: 密碼強度驗證**
```bash
# 請求
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "weak"
}

# 預期響應
HTTP/1.1 422 Unprocessable Entity
{
  "success": false,
  "message": "請求數據驗證失敗",
  "errors": [
    {
      "loc": ["body", "password"],
      "msg": "密碼長度至少需要8個字符",
      "type": "value_error"
    }
  ]
}
```

#### 1.2 用戶登入測試

**測試案例 1.2.1: 正常登入**
```bash
# 請求
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@morningai.com",
  "password": "user123",
  "remember_me": false
}

# 預期響應
HTTP/1.1 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**測試案例 1.2.2: 錯誤密碼登入**
```bash
# 請求
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@morningai.com",
  "password": "wrongpassword"
}

# 預期響應
HTTP/1.1 401 Unauthorized
{
  "success": false,
  "message": "郵箱或密碼錯誤"
}
```

**測試案例 1.2.3: 不存在的用戶登入**
```bash
# 請求
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "nonexistent@example.com",
  "password": "password123"
}

# 預期響應
HTTP/1.1 401 Unauthorized
{
  "success": false,
  "message": "郵箱或密碼錯誤"
}
```

#### 1.3 令牌刷新測試

**測試案例 1.3.1: 正常刷新令牌**
```bash
# 請求
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "valid_refresh_token"
}

# 預期響應
HTTP/1.1 200 OK
{
  "access_token": "new_access_token",
  "refresh_token": "same_refresh_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**測試案例 1.3.2: 無效刷新令牌**
```bash
# 請求
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "invalid_refresh_token"
}

# 預期響應
HTTP/1.1 401 Unauthorized
{
  "success": false,
  "message": "無效的刷新令牌"
}
```

#### 1.4 用戶資料測試

**測試案例 1.4.1: 獲取用戶資料**
```bash
# 請求
GET /api/v1/auth/profile
Authorization: Bearer <access_token>

# 預期響應
HTTP/1.1 200 OK
{
  "id": "user_uuid",
  "email": "user@morningai.com",
  "username": "user",
  "display_name": "Test User",
  "language": "zh-TW",
  "timezone": "Asia/Taipei",
  "referral_code": "USER2025",
  "is_email_verified": false,
  "is_active": true,
  "roles": ["user"],
  "permissions": ["user.read", "chat.create", "referral.read"],
  "tenant_name": "MorningAI Demo",
  "login_count": 1,
  "created_at": "2025-09-05T00:00:00Z"
}
```

**測試案例 1.4.2: 更新用戶資料**
```bash
# 請求
PUT /api/v1/auth/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "display_name": "Updated User",
  "bio": "Updated bio",
  "language": "en"
}

# 預期響應
HTTP/1.1 200 OK
{
  "success": true,
  "message": "用戶資料更新成功",
  "data": {
    "user_id": "user_uuid",
    "updated_fields": ["display_name", "bio", "language"]
  }
}
```

#### 1.5 密碼更改測試

**測試案例 1.5.1: 正常更改密碼**
```bash
# 請求
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "user123",
  "new_password": "NewPassword123"
}

# 預期響應
HTTP/1.1 200 OK
{
  "success": true,
  "message": "密碼更改成功",
  "data": {
    "user_id": "user_uuid"
  }
}
```

**測試案例 1.5.2: 錯誤舊密碼**
```bash
# 請求
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "wrongpassword",
  "new_password": "NewPassword123"
}

# 預期響應
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "舊密碼錯誤或密碼更改失敗"
}
```

### 2. 推薦系統測試

#### 2.1 推薦碼驗證測試

**測試案例 2.1.1: 驗證有效推薦碼**
```bash
# 請求
GET /api/v1/referral/validate/WELCOME2025

# 預期響應
HTTP/1.1 200 OK
{
  "valid": true,
  "code": "WELCOME2025",
  "owner_name": "Admin User",
  "remaining_uses": 999,
  "expires_at": null,
  "message": "推薦碼有效"
}
```

**測試案例 2.1.2: 驗證無效推薦碼**
```bash
# 請求
GET /api/v1/referral/validate/INVALID

# 預期響應
HTTP/1.1 200 OK
{
  "valid": false,
  "code": "INVALID",
  "message": "推薦碼不存在"
}
```

#### 2.2 推薦碼使用測試

**測試案例 2.2.1: 正常使用推薦碼**
```bash
# 請求
POST /api/v1/referral/use
Authorization: Bearer <user_access_token>
Content-Type: application/json

{
  "code": "FRIEND50"
}

# 預期響應
HTTP/1.1 200 OK
{
  "success": true,
  "message": "推薦碼使用成功",
  "data": {
    "user_id": "user_uuid",
    "code": "FRIEND50"
  }
}
```

**測試案例 2.2.2: 重複使用推薦碼**
```bash
# 請求（同一用戶再次使用）
POST /api/v1/referral/use
Authorization: Bearer <user_access_token>
Content-Type: application/json

{
  "code": "DEMO100"
}

# 預期響應
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "您已經使用過推薦碼"
}
```

**測試案例 2.2.3: 使用自己的推薦碼**
```bash
# 請求（用戶使用自己的推薦碼）
POST /api/v1/referral/use
Authorization: Bearer <demo_access_token>
Content-Type: application/json

{
  "code": "DEMO100"
}

# 預期響應
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "不能使用自己的推薦碼"
}
```

#### 2.3 推薦碼管理測試

**測試案例 2.3.1: 創建推薦碼**
```bash
# 請求
POST /api/v1/referral/codes
Authorization: Bearer <manager_access_token>
Content-Type: application/json

{
  "custom_code": "MANAGER2025",
  "max_uses": 50,
  "expires_at": "2025-12-31T23:59:59Z"
}

# 預期響應
HTTP/1.1 200 OK
{
  "success": true,
  "message": "推薦碼創建成功",
  "data": {
    "referral_code_id": "new_code_uuid",
    "code": "MANAGER2025"
  }
}
```

**測試案例 2.3.2: 創建重複推薦碼**
```bash
# 請求
POST /api/v1/referral/codes
Authorization: Bearer <manager_access_token>
Content-Type: application/json

{
  "custom_code": "WELCOME2025"
}

# 預期響應
HTTP/1.1 400 Bad Request
{
  "success": false,
  "message": "推薦碼創建失敗，可能是自定義推薦碼已存在"
}
```

**測試案例 2.3.3: 獲取推薦碼列表**
```bash
# 請求
GET /api/v1/referral/codes?page=1&size=10
Authorization: Bearer <manager_access_token>

# 預期響應
HTTP/1.1 200 OK
{
  "items": [
    {
      "id": "code_uuid",
      "code": "FRIEND50",
      "owner_id": "manager_uuid",
      "owner_name": "Manager User",
      "max_uses": 50,
      "current_uses": 1,
      "is_active": true,
      "expires_at": null,
      "created_at": "2025-09-05T00:00:00Z",
      "updated_at": "2025-09-05T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

#### 2.4 推薦統計測試

**測試案例 2.4.1: 獲取推薦統計**
```bash
# 請求
GET /api/v1/referral/stats
Authorization: Bearer <manager_access_token>

# 預期響應
HTTP/1.1 200 OK
{
  "referral_codes": [
    {
      "id": "code_uuid",
      "code": "FRIEND50",
      "owner_id": "manager_uuid",
      "owner_name": "Manager User",
      "max_uses": 50,
      "current_uses": 1,
      "is_active": true,
      "expires_at": null,
      "created_at": "2025-09-05T00:00:00Z",
      "updated_at": "2025-09-05T00:00:00Z"
    }
  ],
  "total_referrals": 1,
  "rewarded_referrals": 1,
  "total_rewards": 100,
  "recent_referrals": [
    {
      "id": "relation_uuid",
      "referrer_id": "manager_uuid",
      "referrer_name": "Manager User",
      "referred_id": "user_uuid",
      "referred_name": "Test User",
      "referral_code_id": "code_uuid",
      "referral_code": "FRIEND50",
      "reward_given": true,
      "reward_amount": 100,
      "created_at": "2025-09-05T10:30:00Z"
    }
  ]
}
```

**測試案例 2.4.2: 獲取推薦排行榜**
```bash
# 請求
GET /api/v1/referral/leaderboard?limit=5
Authorization: Bearer <user_access_token>

# 預期響應
HTTP/1.1 200 OK
[
  {
    "user_id": "admin_uuid",
    "display_name": "Admin User",
    "email": "admin@morningai.com",
    "referral_count": 0,
    "total_rewards": 0
  },
  {
    "user_id": "manager_uuid",
    "display_name": "Manager User",
    "email": "manager@morningai.com",
    "referral_count": 1,
    "total_rewards": 100
  }
]
```

### 3. 權限控制測試

#### 3.1 RBAC 權限測試

**測試案例 3.1.1: 無權限創建推薦碼**
```bash
# 請求（一般用戶嘗試創建推薦碼）
POST /api/v1/referral/codes
Authorization: Bearer <user_access_token>
Content-Type: application/json

{
  "custom_code": "USERCODE"
}

# 預期響應
HTTP/1.1 403 Forbidden
{
  "success": false,
  "message": "Permission 'referral.create' required"
}
```

**測試案例 3.1.2: 無權限訪問他人推薦碼**
```bash
# 請求（用戶嘗試修改他人的推薦碼）
PUT /api/v1/referral/codes/manager_code_uuid
Authorization: Bearer <user_access_token>
Content-Type: application/json

{
  "is_active": false
}

# 預期響應
HTTP/1.1 403 Forbidden
{
  "success": false,
  "message": "無權限修改此推薦碼"
}
```

### 4. 速率限制測試

#### 4.1 註冊速率限制測試

**測試案例 4.1.1: 註冊速率限制**
```bash
# 連續發送6次註冊請求（超過5次/小時限制）
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"test$i@example.com\",\"password\":\"Test123456\"}"
done

# 第6次請求預期響應
HTTP/1.1 429 Too Many Requests
{
  "success": false,
  "message": "Rate limit exceeded"
}
```

#### 4.2 推薦碼使用速率限制測試

**測試案例 4.2.1: 推薦碼使用速率限制**
```bash
# 連續發送6次推薦碼使用請求（超過5次/小時限制）
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/referral/use \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d "{\"code\":\"INVALID$i\"}"
done

# 第6次請求預期響應
HTTP/1.1 429 Too Many Requests
{
  "success": false,
  "message": "Rate limit exceeded"
}
```

### 5. 錯誤處理測試

#### 5.1 認證錯誤測試

**測試案例 5.1.1: 無效 JWT 令牌**
```bash
# 請求
GET /api/v1/auth/profile
Authorization: Bearer invalid_token

# 預期響應
HTTP/1.1 401 Unauthorized
{
  "success": false,
  "message": "Invalid authentication credentials"
}
```

**測試案例 5.1.2: 過期 JWT 令牌**
```bash
# 請求
GET /api/v1/auth/profile
Authorization: Bearer expired_token

# 預期響應
HTTP/1.1 401 Unauthorized
{
  "success": false,
  "message": "Invalid authentication credentials"
}
```

#### 5.2 數據驗證錯誤測試

**測試案例 5.2.1: 無效郵箱格式**
```bash
# 請求
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "invalid-email",
  "password": "Test123456"
}

# 預期響應
HTTP/1.1 422 Unprocessable Entity
{
  "success": false,
  "message": "請求數據驗證失敗",
  "errors": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 測試執行指南

### 1. 環境準備

1. 啟動 API 服務器：
```bash
cd morningai-core/backend/morningai-api
python src/main_simple.py
```

2. 初始化數據庫：
```bash
# 執行遷移腳本
psql -h localhost -U postgres -d morningai_core < handoff/phase3/09-seed-and-migration/migration.sql

# 執行種子數據
psql -h localhost -U postgres -d morningai_core < handoff/phase3/09-seed-and-migration/seed.sql
```

### 2. 測試工具

推薦使用以下工具進行測試：

1. **Postman**: 圖形化 API 測試工具
2. **curl**: 命令行 HTTP 客戶端
3. **HTTPie**: 用戶友好的命令行 HTTP 客戶端
4. **pytest**: Python 自動化測試框架

### 3. 自動化測試腳本

可以使用以下 Python 腳本進行自動化測試：

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_user_registration():
    """測試用戶註冊"""
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "test@example.com",
        "password": "Test123456",
        "referral_code": "WELCOME2025"
    })
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_user_login():
    """測試用戶登入"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "user@morningai.com",
        "password": "user123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

def test_referral_code_validation():
    """測試推薦碼驗證"""
    response = requests.get(f"{BASE_URL}/referral/validate/WELCOME2025")
    assert response.status_code == 200
    assert response.json()["valid"] == True

if __name__ == "__main__":
    test_user_registration()
    token = test_user_login()
    test_referral_code_validation()
    print("所有測試通過！")
```

## 測試報告

測試完成後，應生成包含以下內容的測試報告：

1. **測試執行摘要**
   - 總測試案例數
   - 通過/失敗案例數
   - 測試覆蓋率

2. **功能測試結果**
   - 認證系統測試結果
   - 推薦系統測試結果
   - 權限控制測試結果

3. **性能測試結果**
   - 響應時間統計
   - 併發處理能力
   - 速率限制效果

4. **安全測試結果**
   - 認證安全性
   - 權限控制有效性
   - 輸入驗證完整性

5. **問題和建議**
   - 發現的問題
   - 改進建議
   - 後續測試計劃

