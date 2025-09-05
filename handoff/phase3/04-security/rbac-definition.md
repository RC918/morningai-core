# RBAC 權限系統定義

## 概述

MorningAI Core 採用基於角色的存取控制（RBAC）系統，提供靈活且可擴充的權限管理機制。系統設計支援多租戶架構，確保不同租戶間的資料隔離和安全性。

## 核心概念

### 1. 角色 (Roles)
角色是權限的集合，代表用戶在系統中的職責和能力範圍。

### 2. 權限 (Permissions)
權限是對特定資源執行特定操作的授權，採用 `resource.action` 的命名規範。

### 3. 用戶角色關聯 (User Roles)
用戶可以被分配多個角色，支援角色繼承和臨時授權。

### 4. 角色權限關聯 (Role Permissions)
角色與權限的多對多關聯，支援動態權限分配。

## 預定義角色

### 1. admin (系統管理員)
- **描述**: 擁有系統所有權限的超級管理員角色
- **適用範圍**: 全系統
- **權限**: 所有權限
- **特殊屬性**: `is_system = true`, `is_superuser = true`

### 2. manager (租戶管理員)
- **描述**: 單一租戶的管理員，可管理該租戶下的用戶、內容和通知
- **適用範圍**: 單一租戶
- **主要權限**:
  - 用戶管理（創建、查看、更新、角色分配）
  - CMS 內容管理（完整 CRUD + 發布）
  - 推薦系統管理
  - 通知系統管理
  - 聊天記錄查看
- **限制**: 無法管理系統級設置和其他租戶

### 3. user (一般用戶)
- **描述**: 一般用戶角色，可使用基本功能如註冊、聊天等
- **適用範圍**: 個人資料和功能
- **主要權限**:
  - 個人資料管理
  - 聊天功能（創建、查看、刪除自己的會話）
  - CMS 內容查看
  - 推薦碼創建和查看
  - 通知查看
- **限制**: 僅能操作自己的資料

## 權限分類

### 用戶管理權限 (user)
| 權限名稱 | 顯示名稱 | 描述 | admin | manager | user |
|---------|---------|------|-------|---------|------|
| user.create | 創建用戶 | 可以創建新用戶 | ✓ | ✓ | ✗ |
| user.read | 查看用戶 | 可以查看用戶信息 | ✓ | ✓ | ✓* |
| user.update | 更新用戶 | 可以更新用戶信息 | ✓ | ✓ | ✓* |
| user.delete | 刪除用戶 | 可以刪除用戶 | ✓ | ✗ | ✗ |
| user.manage_roles | 管理用戶角色 | 可以分配和移除用戶角色 | ✓ | ✓ | ✗ |

*註：user 角色僅能操作自己的資料

### 聊天功能權限 (chat)
| 權限名稱 | 顯示名稱 | 描述 | admin | manager | user |
|---------|---------|------|-------|---------|------|
| chat.create | 創建聊天 | 可以創建新的聊天會話 | ✓ | ✗ | ✓ |
| chat.read | 查看聊天 | 可以查看聊天記錄 | ✓ | ✓ | ✓* |
| chat.delete | 刪除聊天 | 可以刪除聊天會話 | ✓ | ✗ | ✓* |

*註：user 角色僅能操作自己的聊天會話

### CMS 內容管理權限 (cms)
| 權限名稱 | 顯示名稱 | 描述 | admin | manager | user |
|---------|---------|------|-------|---------|------|
| cms.create | 創建內容 | 可以創建 CMS 內容 | ✓ | ✓ | ✗ |
| cms.read | 查看內容 | 可以查看 CMS 內容 | ✓ | ✓ | ✓ |
| cms.update | 更新內容 | 可以更新 CMS 內容 | ✓ | ✓ | ✗ |
| cms.delete | 刪除內容 | 可以刪除 CMS 內容 | ✓ | ✓ | ✗ |
| cms.publish | 發布內容 | 可以發布 CMS 內容 | ✓ | ✓ | ✗ |

### 推薦系統權限 (referral)
| 權限名稱 | 顯示名稱 | 描述 | admin | manager | user |
|---------|---------|------|-------|---------|------|
| referral.create | 創建推薦碼 | 可以創建推薦碼 | ✓ | ✗ | ✓ |
| referral.read | 查看推薦 | 可以查看推薦信息 | ✓ | ✓ | ✓* |
| referral.manage | 管理推薦 | 可以管理推薦系統 | ✓ | ✓ | ✗ |

*註：user 角色僅能查看自己的推薦信息

### 通知系統權限 (notification)
| 權限名稱 | 顯示名稱 | 描述 | admin | manager | user |
|---------|---------|------|-------|---------|------|
| notification.create | 創建通知 | 可以創建通知 | ✓ | ✓ | ✗ |
| notification.read | 查看通知 | 可以查看通知 | ✓ | ✓ | ✓* |
| notification.send | 發送通知 | 可以發送通知 | ✓ | ✓ | ✗ |
| notification.manage | 管理通知 | 可以管理通知系統 | ✓ | ✓ | ✗ |

*註：user 角色僅能查看自己的通知

### 系統管理權限 (system)
| 權限名稱 | 顯示名稱 | 描述 | admin | manager | user |
|---------|---------|------|-------|---------|------|
| system.admin | 系統管理 | 系統管理員權限 | ✓ | ✗ | ✗ |
| tenant.manage | 租戶管理 | 可以管理租戶 | ✓ | ✗ | ✗ |
| audit.read | 查看審計日誌 | 可以查看審計日誌 | ✓ | ✗ | ✗ |

## 權限檢查機制

### 1. 超級用戶檢查
```python
if user.is_superuser:
    return True  # 超級用戶擁有所有權限
```

### 2. 角色權限檢查
```python
def has_permission(user, permission_name):
    for user_role in user.user_roles:
        if not user_role.is_active:
            continue
        if user_role.is_expired:
            continue
        for role_permission in user_role.role.role_permissions:
            if role_permission.permission.name == permission_name:
                return True
    return False
```

### 3. 租戶隔離檢查
```python
def check_tenant_access(user, resource):
    if user.is_superuser:
        return True
    return user.tenant_id == resource.tenant_id
```

## 角色分配規則

### 1. 預設角色分配
- 新註冊用戶自動分配 `user` 角色
- 租戶創建者自動分配 `manager` 角色
- 系統管理員手動分配 `admin` 角色

### 2. 角色升級路徑
```
user → manager → admin
```

### 3. 臨時授權
- 支援設定角色過期時間
- 支援臨時權限提升
- 自動清理過期角色

## 安全考量

### 1. 最小權限原則
- 用戶僅獲得執行其職責所需的最小權限
- 定期審查和調整權限分配

### 2. 權限繼承
- 高級角色包含低級角色的所有權限
- 避免權限衝突和遺漏

### 3. 審計追蹤
- 所有權限變更記錄在審計日誌中
- 包含授權者、被授權者、時間等信息

### 4. 動態權限檢查
- 每次請求都進行權限檢查
- 支援即時權限撤銷

## 擴展機制

### 1. 新增權限
```sql
INSERT INTO permissions (name, display_name, description, category, is_active)
VALUES ('new_feature.action', '新功能操作', '描述', 'category', TRUE);
```

### 2. 新增角色
```sql
INSERT INTO roles (name, display_name, description, is_active, is_system)
VALUES ('new_role', '新角色', '描述', TRUE, FALSE);
```

### 3. 權限分配
```sql
INSERT INTO role_permissions (role_id, permission_id, granted_by_id)
VALUES (role_id, permission_id, admin_user_id);
```

## API 權限裝飾器

### FastAPI 權限檢查
```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if not current_user.has_permission(permission):
                raise HTTPException(status_code=403, detail="Permission denied")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用範例
@app.post("/api/v1/users")
@require_permission("user.create")
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    # 創建用戶邏輯
    pass
```

## 測試場景

### 1. 基本權限測試
- 驗證每個角色的權限分配正確性
- 測試權限檢查機制的有效性

### 2. 租戶隔離測試
- 驗證不同租戶間的資料隔離
- 測試跨租戶存取的阻止機制

### 3. 角色升級測試
- 測試角色變更的即時生效
- 驗證權限繼承的正確性

### 4. 安全邊界測試
- 測試權限繞過攻擊的防護
- 驗證異常情況下的安全行為

## 維護指南

### 1. 定期權限審查
- 每季度審查用戶權限分配
- 清理不活躍用戶的權限

### 2. 權限變更流程
- 權限變更需要審批流程
- 記錄變更原因和影響範圍

### 3. 監控和告警
- 監控異常權限使用模式
- 設定權限濫用告警機制

## 總結

MorningAI Core 的 RBAC 系統提供了：
- **靈活性**: 支援動態權限分配和角色管理
- **安全性**: 多層次的權限檢查和租戶隔離
- **可擴展性**: 易於新增權限和角色
- **可維護性**: 清晰的權限結構和審計機制

這個設計確保了系統的安全性，同時提供了足夠的靈活性來支援未來的功能擴展。

