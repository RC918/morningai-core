# 聊天模組隱私保護政策

## 概述

本文檔定義 MorningAI 聊天模組的隱私保護政策、數據處理規範和用戶權利保障措施，確保符合 GDPR、CCPA 等國際隱私法規要求。

## 數據分類和處理

### 個人身份信息 (PII) 分類

#### 1. 直接識別信息
- **用戶ID**: 系統內部唯一標識符
- **郵箱地址**: 用於帳戶識別和通知
- **用戶名**: 顯示名稱和帳戶標識
- **IP地址**: 網絡訪問記錄

#### 2. 間接識別信息
- **設備指紋**: 瀏覽器和設備特徵
- **會話ID**: 聊天會話標識符
- **使用模式**: 訪問時間和頻率
- **偏好設置**: 語言和界面設置

#### 3. 敏感個人信息
- **聊天內容**: 用戶與AI的對話記錄
- **查詢歷史**: 搜索和問題記錄
- **反饋信息**: 用戶評分和評論
- **錯誤日誌**: 包含用戶輸入的系統日誌

### 數據處理原則

```python
from enum import Enum
from typing import Dict, List, Optional
import re
import hashlib

class DataSensitivity(Enum):
    """數據敏感度級別"""
    PUBLIC = "public"           # 公開信息
    INTERNAL = "internal"       # 內部信息
    CONFIDENTIAL = "confidential"  # 機密信息
    RESTRICTED = "restricted"   # 限制級信息

class PIIType(Enum):
    """PII 類型"""
    EMAIL = "email"
    PHONE = "phone"
    ID_NUMBER = "id_number"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"

class PrivacyProcessor:
    """隱私數據處理器"""
    
    def __init__(self):
        self.pii_patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            PIIType.ID_NUMBER: r'\b\d{15}|\d{18}\b',  # 身份證號
            PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            PIIType.NAME: r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # 簡化姓名模式
        }
    
    def detect_pii(self, text: str) -> Dict[PIIType, List[str]]:
        """檢測文本中的PII"""
        detected_pii = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected_pii[pii_type] = matches
        
        return detected_pii
    
    def mask_pii(self, text: str, mask_char: str = "*") -> str:
        """遮蔽PII信息"""
        masked_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type == PIIType.EMAIL:
                # 保留郵箱前2位和域名
                masked_text = re.sub(
                    pattern,
                    lambda m: f"{m.group()[:2]}***@{m.group().split('@')[1]}",
                    masked_text
                )
            elif pii_type == PIIType.PHONE:
                # 保留前3位和後4位
                masked_text = re.sub(
                    pattern,
                    lambda m: f"{m.group()[:3]}****{m.group()[-4:]}",
                    masked_text
                )
            else:
                # 其他類型完全遮蔽
                masked_text = re.sub(pattern, mask_char * 8, masked_text)
        
        return masked_text
    
    def anonymize_data(self, data: Dict) -> Dict:
        """數據匿名化"""
        anonymized = data.copy()
        
        # 移除直接標識符
        sensitive_fields = ['user_id', 'email', 'ip_address', 'session_id']
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = self._generate_anonymous_id(str(anonymized[field]))
        
        # 處理文本內容
        if 'content' in anonymized:
            anonymized['content'] = self.mask_pii(anonymized['content'])
        
        return anonymized
    
    def _generate_anonymous_id(self, original_id: str) -> str:
        """生成匿名ID"""
        return hashlib.sha256(original_id.encode()).hexdigest()[:16]
```

## 數據保留政策

### 保留期限

```python
from datetime import datetime, timedelta
from typing import Dict, Any

class DataRetentionPolicy:
    """數據保留政策"""
    
    RETENTION_PERIODS = {
        "chat_messages": timedelta(days=30),      # 聊天記錄 30 天
        "user_sessions": timedelta(days=7),       # 用戶會話 7 天
        "search_queries": timedelta(days=14),     # 搜索查詢 14 天
        "feedback_data": timedelta(days=90),      # 反饋數據 90 天
        "audit_logs": timedelta(days=365),        # 審計日誌 1 年
        "error_logs": timedelta(days=30),         # 錯誤日誌 30 天
        "analytics_data": timedelta(days=180),    # 分析數據 6 個月
        "user_preferences": timedelta(days=730),  # 用戶偏好 2 年
    }
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def cleanup_expired_data(self):
        """清理過期數據"""
        cleanup_results = {}
        
        for data_type, retention_period in self.RETENTION_PERIODS.items():
            cutoff_date = datetime.utcnow() - retention_period
            
            try:
                deleted_count = await self._delete_expired_data(data_type, cutoff_date)
                cleanup_results[data_type] = {
                    "deleted_count": deleted_count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "status": "success"
                }
            except Exception as e:
                cleanup_results[data_type] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        return cleanup_results
    
    async def _delete_expired_data(self, data_type: str, cutoff_date: datetime) -> int:
        """刪除指定類型的過期數據"""
        table_mapping = {
            "chat_messages": "messages",
            "user_sessions": "chat_sessions", 
            "search_queries": "search_logs",
            "feedback_data": "chat_feedback",
            "audit_logs": "audit_logs",
            "error_logs": "error_logs",
            "analytics_data": "analytics_events",
            "user_preferences": "user_preferences"
        }
        
        table_name = table_mapping.get(data_type)
        if not table_name:
            raise ValueError(f"Unknown data type: {data_type}")
        
        # 軟刪除：標記為已刪除而不是物理刪除
        query = f"""
        UPDATE {table_name} 
        SET is_deleted = true, deleted_at = NOW()
        WHERE created_at < %s AND (is_deleted = false OR is_deleted IS NULL)
        """
        
        result = await self.db.execute(query, (cutoff_date,))
        return result.rowcount
    
    async def schedule_data_cleanup(self):
        """調度數據清理任務"""
        # 每日凌晨2點執行清理
        import asyncio
        from datetime import time
        
        while True:
            now = datetime.now()
            next_cleanup = datetime.combine(now.date() + timedelta(days=1), time(2, 0))
            sleep_seconds = (next_cleanup - now).total_seconds()
            
            await asyncio.sleep(sleep_seconds)
            await self.cleanup_expired_data()
```

### 數據刪除流程

```python
class DataDeletionService:
    """數據刪除服務"""
    
    def __init__(self, db_connection, storage_client):
        self.db = db_connection
        self.storage = storage_client
    
    async def delete_user_data(self, user_id: str, deletion_type: str = "soft") -> Dict:
        """刪除用戶數據"""
        deletion_log = {
            "user_id": user_id,
            "deletion_type": deletion_type,
            "started_at": datetime.utcnow().isoformat(),
            "deleted_items": {}
        }
        
        try:
            # 1. 刪除聊天記錄
            chat_count = await self._delete_chat_data(user_id, deletion_type)
            deletion_log["deleted_items"]["chat_messages"] = chat_count
            
            # 2. 刪除會話數據
            session_count = await self._delete_session_data(user_id, deletion_type)
            deletion_log["deleted_items"]["chat_sessions"] = session_count
            
            # 3. 刪除反饋數據
            feedback_count = await self._delete_feedback_data(user_id, deletion_type)
            deletion_log["deleted_items"]["feedback_data"] = feedback_count
            
            # 4. 刪除分析數據
            analytics_count = await self._delete_analytics_data(user_id, deletion_type)
            deletion_log["deleted_items"]["analytics_data"] = analytics_count
            
            # 5. 刪除文件存儲
            if deletion_type == "hard":
                file_count = await self._delete_user_files(user_id)
                deletion_log["deleted_items"]["user_files"] = file_count
            
            deletion_log["completed_at"] = datetime.utcnow().isoformat()
            deletion_log["status"] = "success"
            
        except Exception as e:
            deletion_log["error"] = str(e)
            deletion_log["status"] = "failed"
            deletion_log["completed_at"] = datetime.utcnow().isoformat()
        
        # 記錄刪除日誌
        await self._log_deletion(deletion_log)
        
        return deletion_log
    
    async def _delete_chat_data(self, user_id: str, deletion_type: str) -> int:
        """刪除聊天數據"""
        if deletion_type == "soft":
            query = """
            UPDATE messages 
            SET is_deleted = true, deleted_at = NOW(), content = '[DELETED]'
            WHERE user_id = %s AND (is_deleted = false OR is_deleted IS NULL)
            """
        else:
            query = "DELETE FROM messages WHERE user_id = %s"
        
        result = await self.db.execute(query, (user_id,))
        return result.rowcount
    
    async def right_to_be_forgotten(self, user_id: str, request_data: Dict) -> Dict:
        """被遺忘權處理"""
        # 驗證請求
        if not self._validate_deletion_request(user_id, request_data):
            return {"status": "rejected", "reason": "Invalid request"}
        
        # 執行數據刪除
        deletion_result = await self.delete_user_data(user_id, "hard")
        
        # 通知相關系統
        await self._notify_deletion_completion(user_id, deletion_result)
        
        return {
            "status": "completed",
            "request_id": request_data.get("request_id"),
            "deletion_result": deletion_result
        }
```

## 數據加密和安全

### 傳輸加密

```python
import ssl
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionService:
    """加密服務"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode())
        else:
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感數據"""
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感數據"""
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = self.fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    
    @staticmethod
    def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
        """從密碼生成加密密鑰"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

# 數據庫加密配置
DATABASE_ENCRYPTION_CONFIG = {
    "encrypt_at_rest": True,
    "encryption_algorithm": "AES-256-GCM",
    "key_rotation_days": 90,
    "encrypted_fields": [
        "messages.content",
        "chat_sessions.metadata", 
        "users.email",
        "audit_logs.details"
    ]
}
```

### 存儲加密

```sql
-- 數據庫級別加密設置
-- PostgreSQL 透明數據加密 (TDE)
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/server.key';

-- 敏感字段加密
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 創建加密函數
CREATE OR REPLACE FUNCTION encrypt_pii(data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(encrypt(data::bytea, key::bytea, 'aes'), 'base64');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrypt_pii(encrypted_data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN convert_from(decrypt(decode(encrypted_data, 'base64'), key::bytea, 'aes'), 'UTF8');
END;
$$ LANGUAGE plpgsql;

-- 使用加密存儲敏感數據
INSERT INTO messages (user_id, content_encrypted, created_at)
VALUES (
    %s,
    encrypt_pii(%s, %s),  -- 加密內容
    NOW()
);
```

## 用戶權利保障

### 數據訪問權

```python
class UserRightsService:
    """用戶權利服務"""
    
    async def export_user_data(self, user_id: str, export_format: str = "json") -> Dict:
        """導出用戶數據"""
        user_data = {
            "export_info": {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "format": export_format
            },
            "personal_data": await self._get_personal_data(user_id),
            "chat_data": await self._get_chat_data(user_id),
            "preferences": await self._get_user_preferences(user_id),
            "activity_logs": await self._get_activity_logs(user_id)
        }
        
        if export_format == "json":
            return user_data
        elif export_format == "csv":
            return self._convert_to_csv(user_data)
        elif export_format == "xml":
            return self._convert_to_xml(user_data)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
    
    async def _get_personal_data(self, user_id: str) -> Dict:
        """獲取個人基本數據"""
        query = """
        SELECT id, email, username, created_at, last_login_at, preferences
        FROM users 
        WHERE id = %s AND (is_deleted = false OR is_deleted IS NULL)
        """
        result = await self.db.fetch_one(query, (user_id,))
        return dict(result) if result else {}
    
    async def _get_chat_data(self, user_id: str) -> List[Dict]:
        """獲取聊天數據"""
        query = """
        SELECT s.id as session_id, s.title, s.created_at as session_created,
               m.id as message_id, m.role, m.content, m.created_at as message_created
        FROM chat_sessions s
        LEFT JOIN messages m ON s.id = m.session_id
        WHERE s.user_id = %s AND (s.is_deleted = false OR s.is_deleted IS NULL)
        ORDER BY s.created_at, m.created_at
        """
        results = await self.db.fetch_all(query, (user_id,))
        return [dict(row) for row in results]
    
    async def request_data_correction(self, user_id: str, correction_data: Dict) -> Dict:
        """請求數據更正"""
        correction_request = {
            "request_id": str(uuid4()),
            "user_id": user_id,
            "requested_changes": correction_data,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 保存更正請求
        await self._save_correction_request(correction_request)
        
        # 通知管理員
        await self._notify_data_correction_request(correction_request)
        
        return {
            "request_id": correction_request["request_id"],
            "status": "submitted",
            "estimated_completion": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
```

### 同意管理

```python
class ConsentManager:
    """同意管理器"""
    
    CONSENT_TYPES = {
        "data_processing": "數據處理同意",
        "analytics": "分析數據收集同意", 
        "marketing": "營銷通訊同意",
        "third_party_sharing": "第三方數據共享同意"
    }
    
    async def record_consent(self, user_id: str, consent_data: Dict) -> Dict:
        """記錄用戶同意"""
        consent_record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "consent_type": consent_data["type"],
            "granted": consent_data["granted"],
            "consent_text": consent_data.get("consent_text"),
            "ip_address": consent_data.get("ip_address"),
            "user_agent": consent_data.get("user_agent"),
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self._save_consent_record(consent_record)
        
        return {
            "consent_id": consent_record["id"],
            "status": "recorded"
        }
    
    async def withdraw_consent(self, user_id: str, consent_type: str) -> Dict:
        """撤回同意"""
        # 記錄撤回
        withdrawal_record = {
            "user_id": user_id,
            "consent_type": consent_type,
            "withdrawn_at": datetime.utcnow().isoformat()
        }
        
        await self._save_consent_withdrawal(withdrawal_record)
        
        # 停止相關數據處理
        await self._stop_data_processing(user_id, consent_type)
        
        return {
            "status": "consent_withdrawn",
            "effective_date": withdrawal_record["withdrawn_at"]
        }
    
    async def get_consent_status(self, user_id: str) -> Dict:
        """獲取同意狀態"""
        query = """
        SELECT consent_type, granted, created_at
        FROM user_consents 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        """
        results = await self.db.fetch_all(query, (user_id,))
        
        consent_status = {}
        for row in results:
            consent_type = row["consent_type"]
            if consent_type not in consent_status:
                consent_status[consent_type] = {
                    "granted": row["granted"],
                    "last_updated": row["created_at"]
                }
        
        return consent_status
```

## 合規性檢查

### GDPR 合規

```python
class GDPRComplianceChecker:
    """GDPR 合規檢查器"""
    
    def __init__(self):
        self.required_measures = [
            "data_minimization",
            "purpose_limitation", 
            "accuracy",
            "storage_limitation",
            "integrity_confidentiality",
            "accountability"
        ]
    
    async def run_compliance_audit(self) -> Dict:
        """運行合規審計"""
        audit_results = {
            "audit_date": datetime.utcnow().isoformat(),
            "compliance_score": 0,
            "checks": {}
        }
        
        total_checks = len(self.required_measures)
        passed_checks = 0
        
        for measure in self.required_measures:
            check_result = await self._check_measure(measure)
            audit_results["checks"][measure] = check_result
            
            if check_result["status"] == "compliant":
                passed_checks += 1
        
        audit_results["compliance_score"] = (passed_checks / total_checks) * 100
        audit_results["overall_status"] = "compliant" if passed_checks == total_checks else "non_compliant"
        
        return audit_results
    
    async def _check_measure(self, measure: str) -> Dict:
        """檢查特定合規措施"""
        if measure == "data_minimization":
            return await self._check_data_minimization()
        elif measure == "storage_limitation":
            return await self._check_storage_limitation()
        elif measure == "integrity_confidentiality":
            return await self._check_security_measures()
        # ... 其他檢查
        
        return {"status": "not_implemented", "details": f"Check for {measure} not implemented"}
    
    async def _check_data_minimization(self) -> Dict:
        """檢查數據最小化原則"""
        # 檢查是否只收集必要數據
        unnecessary_data_count = await self._count_unnecessary_data()
        
        return {
            "status": "compliant" if unnecessary_data_count == 0 else "non_compliant",
            "details": f"Found {unnecessary_data_count} instances of unnecessary data collection",
            "recommendations": ["Review data collection practices", "Remove unnecessary fields"]
        }
```

### 審計日誌

```python
class PrivacyAuditLogger:
    """隱私審計日誌記錄器"""
    
    async def log_data_access(self, user_id: str, accessed_by: str, data_type: str, purpose: str):
        """記錄數據訪問"""
        audit_entry = {
            "event_type": "data_access",
            "user_id": user_id,
            "accessed_by": accessed_by,
            "data_type": data_type,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        
        await self._save_audit_entry(audit_entry)
    
    async def log_data_modification(self, user_id: str, modified_by: str, changes: Dict):
        """記錄數據修改"""
        audit_entry = {
            "event_type": "data_modification",
            "user_id": user_id,
            "modified_by": modified_by,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._save_audit_entry(audit_entry)
    
    async def generate_audit_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """生成審計報告"""
        query = """
        SELECT event_type, COUNT(*) as count
        FROM privacy_audit_logs
        WHERE timestamp BETWEEN %s AND %s
        GROUP BY event_type
        """
        
        results = await self.db.fetch_all(query, (start_date, end_date))
        
        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "event_summary": {row["event_type"]: row["count"] for row in results},
            "total_events": sum(row["count"] for row in results)
        }
```

## 實施檢查清單

### 技術實施

- [ ] **數據分類和標記**
  - [ ] 識別和分類所有PII
  - [ ] 實施數據敏感度標記
  - [ ] 建立數據處理清單

- [ ] **加密實施**
  - [ ] 傳輸中加密 (TLS 1.3)
  - [ ] 靜態數據加密 (AES-256)
  - [ ] 密鑰管理系統

- [ ] **訪問控制**
  - [ ] 基於角色的訪問控制
  - [ ] 最小權限原則
  - [ ] 定期訪問審查

- [ ] **數據保留**
  - [ ] 自動數據清理
  - [ ] 保留期限監控
  - [ ] 刪除確認機制

### 流程實施

- [ ] **隱私影響評估**
  - [ ] 新功能隱私評估
  - [ ] 風險識別和緩解
  - [ ] 定期評估更新

- [ ] **用戶權利響應**
  - [ ] 數據訪問請求處理
  - [ ] 數據更正流程
  - [ ] 數據刪除流程

- [ ] **事件響應**
  - [ ] 數據洩露響應計劃
  - [ ] 通知程序
  - [ ] 恢復措施

### 監控和審計

- [ ] **合規監控**
  - [ ] 自動合規檢查
  - [ ] 定期審計
  - [ ] 合規報告

- [ ] **培訓和意識**
  - [ ] 員工隱私培訓
  - [ ] 定期更新培訓
  - [ ] 合規意識提升

---

**政策版本：** v1.0  
**生效日期：** 2025-01-05  
**下次審查：** 2025-07-05  
**負責人：** 數據保護官 (DPO)

