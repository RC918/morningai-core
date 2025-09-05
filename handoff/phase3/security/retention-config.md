# 數據保留配置文檔

## 概述

本文檔定義 MorningAI 聊天模組的數據保留策略、自動清理機制和合規要求，確保符合隱私法規並優化存儲成本。

## 數據保留策略

### 保留期限表

| 數據類型 | 保留期限 | 法律依據 | 業務需求 | 清理方式 |
|---------|----------|----------|----------|----------|
| 聊天消息 | 30天 | 隱私保護 | 用戶體驗 | 軟刪除 |
| 用戶會話 | 7天 | 技術需求 | 性能優化 | 物理刪除 |
| 搜索查詢 | 14天 | 分析需求 | 產品改進 | 匿名化 |
| 反饋數據 | 90天 | 質量改進 | 服務優化 | 軟刪除 |
| 審計日誌 | 1年 | 合規要求 | 安全審計 | 歸檔 |
| 錯誤日誌 | 30天 | 技術支援 | 問題診斷 | 物理刪除 |
| 分析數據 | 6個月 | 業務分析 | 決策支援 | 聚合保留 |
| 用戶偏好 | 2年 | 用戶體驗 | 個性化 | 軟刪除 |
| 知識庫內容 | 永久 | 業務核心 | 服務提供 | 版本管理 |
| 系統配置 | 永久 | 運維需求 | 系統恢復 | 備份保留 |

### 保留策略配置

```python
from datetime import timedelta
from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass

class RetentionAction(Enum):
    """保留動作類型"""
    SOFT_DELETE = "soft_delete"      # 軟刪除（標記刪除）
    HARD_DELETE = "hard_delete"      # 物理刪除
    ANONYMIZE = "anonymize"          # 匿名化
    ARCHIVE = "archive"              # 歸檔
    AGGREGATE = "aggregate"          # 聚合保留
    ENCRYPT = "encrypt"              # 加密保存

@dataclass
class RetentionRule:
    """數據保留規則"""
    data_type: str
    retention_period: timedelta
    action: RetentionAction
    legal_basis: str
    business_justification: str
    exceptions: Optional[List[str]] = None
    notification_required: bool = False

class DataRetentionConfig:
    """數據保留配置"""
    
    RETENTION_RULES = {
        "chat_messages": RetentionRule(
            data_type="chat_messages",
            retention_period=timedelta(days=30),
            action=RetentionAction.SOFT_DELETE,
            legal_basis="GDPR Article 5(1)(e) - Storage limitation",
            business_justification="用戶體驗和問題排查",
            exceptions=["legal_hold", "dispute_resolution"]
        ),
        
        "user_sessions": RetentionRule(
            data_type="user_sessions", 
            retention_period=timedelta(days=7),
            action=RetentionAction.HARD_DELETE,
            legal_basis="Technical necessity",
            business_justification="性能優化和存儲管理"
        ),
        
        "search_queries": RetentionRule(
            data_type="search_queries",
            retention_period=timedelta(days=14),
            action=RetentionAction.ANONYMIZE,
            legal_basis="Legitimate interest - Service improvement",
            business_justification="產品改進和用戶體驗優化"
        ),
        
        "feedback_data": RetentionRule(
            data_type="feedback_data",
            retention_period=timedelta(days=90),
            action=RetentionAction.SOFT_DELETE,
            legal_basis="Legitimate interest - Quality improvement",
            business_justification="服務質量改進和用戶滿意度提升"
        ),
        
        "audit_logs": RetentionRule(
            data_type="audit_logs",
            retention_period=timedelta(days=365),
            action=RetentionAction.ARCHIVE,
            legal_basis="Legal compliance - SOX, GDPR",
            business_justification="合規要求和安全審計",
            notification_required=True
        ),
        
        "error_logs": RetentionRule(
            data_type="error_logs",
            retention_period=timedelta(days=30),
            action=RetentionAction.HARD_DELETE,
            legal_basis="Technical necessity",
            business_justification="問題診斷和系統維護"
        ),
        
        "analytics_data": RetentionRule(
            data_type="analytics_data",
            retention_period=timedelta(days=180),
            action=RetentionAction.AGGREGATE,
            legal_basis="Legitimate interest - Business analytics",
            business_justification="業務分析和決策支援"
        ),
        
        "user_preferences": RetentionRule(
            data_type="user_preferences",
            retention_period=timedelta(days=730),  # 2年
            action=RetentionAction.SOFT_DELETE,
            legal_basis="User consent - Personalization",
            business_justification="個性化服務和用戶體驗"
        )
    }
    
    @classmethod
    def get_retention_rule(cls, data_type: str) -> Optional[RetentionRule]:
        """獲取數據類型的保留規則"""
        return cls.RETENTION_RULES.get(data_type)
    
    @classmethod
    def get_all_rules(cls) -> Dict[str, RetentionRule]:
        """獲取所有保留規則"""
        return cls.RETENTION_RULES.copy()
```

## 自動清理系統

### 清理調度器

```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class DataRetentionScheduler:
    """數據保留調度器"""
    
    def __init__(self, db_connection, storage_client, notification_service):
        self.db = db_connection
        self.storage = storage_client
        self.notifications = notification_service
        self.logger = logging.getLogger(__name__)
        self.config = DataRetentionConfig()
        
    async def start_scheduler(self):
        """啟動調度器"""
        self.logger.info("Starting data retention scheduler")
        
        # 每日清理任務 (凌晨2點)
        asyncio.create_task(self._schedule_daily_cleanup())
        
        # 每週歸檔任務 (週日凌晨3點)
        asyncio.create_task(self._schedule_weekly_archive())
        
        # 每月合規檢查 (每月1號凌晨4點)
        asyncio.create_task(self._schedule_monthly_compliance_check())
    
    async def _schedule_daily_cleanup(self):
        """調度每日清理任務"""
        while True:
            try:
                # 計算下次執行時間 (凌晨2點)
                now = datetime.now()
                next_run = datetime.combine(
                    now.date() + timedelta(days=1),
                    datetime.min.time().replace(hour=2)
                )
                sleep_seconds = (next_run - now).total_seconds()
                
                await asyncio.sleep(sleep_seconds)
                await self.run_daily_cleanup()
                
            except Exception as e:
                self.logger.error(f"Daily cleanup scheduling error: {e}")
                await asyncio.sleep(3600)  # 1小時後重試
    
    async def run_daily_cleanup(self) -> Dict[str, Any]:
        """執行每日清理任務"""
        cleanup_start = datetime.utcnow()
        cleanup_results = {
            "start_time": cleanup_start.isoformat(),
            "rules_processed": {},
            "total_deleted": 0,
            "errors": []
        }
        
        self.logger.info("Starting daily data cleanup")
        
        for data_type, rule in self.config.get_all_rules().items():
            try:
                result = await self._process_retention_rule(data_type, rule)
                cleanup_results["rules_processed"][data_type] = result
                cleanup_results["total_deleted"] += result.get("deleted_count", 0)
                
            except Exception as e:
                error_msg = f"Error processing {data_type}: {str(e)}"
                self.logger.error(error_msg)
                cleanup_results["errors"].append(error_msg)
        
        cleanup_results["end_time"] = datetime.utcnow().isoformat()
        cleanup_results["duration_seconds"] = (
            datetime.utcnow() - cleanup_start
        ).total_seconds()
        
        # 記錄清理結果
        await self._log_cleanup_results(cleanup_results)
        
        # 發送通知（如果有錯誤或大量刪除）
        if cleanup_results["errors"] or cleanup_results["total_deleted"] > 1000:
            await self._send_cleanup_notification(cleanup_results)
        
        self.logger.info(f"Daily cleanup completed. Deleted {cleanup_results['total_deleted']} records")
        return cleanup_results
    
    async def _process_retention_rule(self, data_type: str, rule: RetentionRule) -> Dict[str, Any]:
        """處理單個保留規則"""
        cutoff_date = datetime.utcnow() - rule.retention_period
        
        result = {
            "data_type": data_type,
            "cutoff_date": cutoff_date.isoformat(),
            "action": rule.action.value,
            "deleted_count": 0,
            "processed_count": 0,
            "status": "success"
        }
        
        try:
            if rule.action == RetentionAction.SOFT_DELETE:
                result["deleted_count"] = await self._soft_delete_data(data_type, cutoff_date)
            
            elif rule.action == RetentionAction.HARD_DELETE:
                result["deleted_count"] = await self._hard_delete_data(data_type, cutoff_date)
            
            elif rule.action == RetentionAction.ANONYMIZE:
                result["processed_count"] = await self._anonymize_data(data_type, cutoff_date)
            
            elif rule.action == RetentionAction.ARCHIVE:
                result["processed_count"] = await self._archive_data(data_type, cutoff_date)
            
            elif rule.action == RetentionAction.AGGREGATE:
                result["processed_count"] = await self._aggregate_data(data_type, cutoff_date)
            
            elif rule.action == RetentionAction.ENCRYPT:
                result["processed_count"] = await self._encrypt_data(data_type, cutoff_date)
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            raise
        
        return result
```

### 清理執行器

```python
class DataCleanupExecutor:
    """數據清理執行器"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    async def _soft_delete_data(self, data_type: str, cutoff_date: datetime) -> int:
        """軟刪除數據"""
        table_mapping = {
            "chat_messages": "messages",
            "feedback_data": "chat_feedback",
            "user_preferences": "user_preferences"
        }
        
        table_name = table_mapping.get(data_type)
        if not table_name:
            raise ValueError(f"No table mapping for data type: {data_type}")
        
        query = f"""
        UPDATE {table_name}
        SET is_deleted = true, 
            deleted_at = NOW(),
            content = CASE 
                WHEN content IS NOT NULL THEN '[DELETED]'
                ELSE content
            END
        WHERE created_at < %s 
          AND (is_deleted = false OR is_deleted IS NULL)
        """
        
        result = await self.db.execute(query, (cutoff_date,))
        self.logger.info(f"Soft deleted {result.rowcount} records from {table_name}")
        return result.rowcount
    
    async def _hard_delete_data(self, data_type: str, cutoff_date: datetime) -> int:
        """物理刪除數據"""
        table_mapping = {
            "user_sessions": "chat_sessions",
            "error_logs": "error_logs"
        }
        
        table_name = table_mapping.get(data_type)
        if not table_name:
            raise ValueError(f"No table mapping for data type: {data_type}")
        
        # 先備份要刪除的數據（可選）
        if data_type in ["error_logs"]:
            await self._backup_before_deletion(table_name, cutoff_date)
        
        query = f"DELETE FROM {table_name} WHERE created_at < %s"
        result = await self.db.execute(query, (cutoff_date,))
        
        self.logger.info(f"Hard deleted {result.rowcount} records from {table_name}")
        return result.rowcount
    
    async def _anonymize_data(self, data_type: str, cutoff_date: datetime) -> int:
        """匿名化數據"""
        if data_type == "search_queries":
            query = """
            UPDATE search_logs
            SET user_id = NULL,
                ip_address = '0.0.0.0',
                user_agent = '[ANONYMIZED]',
                query_text = regexp_replace(query_text, 
                    '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', 
                    '[EMAIL]', 'g')
            WHERE created_at < %s AND user_id IS NOT NULL
            """
            
            result = await self.db.execute(query, (cutoff_date,))
            self.logger.info(f"Anonymized {result.rowcount} search queries")
            return result.rowcount
        
        return 0
    
    async def _archive_data(self, data_type: str, cutoff_date: datetime) -> int:
        """歸檔數據"""
        if data_type == "audit_logs":
            # 1. 導出數據到歸檔存儲
            archive_data = await self._export_audit_logs(cutoff_date)
            
            # 2. 上傳到歸檔存儲
            archive_path = f"archives/audit_logs/{cutoff_date.strftime('%Y/%m')}/audit_logs.json.gz"
            await self._upload_to_archive_storage(archive_path, archive_data)
            
            # 3. 從主數據庫刪除
            query = "DELETE FROM audit_logs WHERE created_at < %s"
            result = await self.db.execute(query, (cutoff_date,))
            
            self.logger.info(f"Archived {result.rowcount} audit log records")
            return result.rowcount
        
        return 0
    
    async def _aggregate_data(self, data_type: str, cutoff_date: datetime) -> int:
        """聚合數據"""
        if data_type == "analytics_data":
            # 1. 創建聚合數據
            query = """
            INSERT INTO analytics_summary (date, event_type, count, created_at)
            SELECT 
                DATE(created_at) as date,
                event_type,
                COUNT(*) as count,
                NOW() as created_at
            FROM analytics_events
            WHERE created_at < %s
            GROUP BY DATE(created_at), event_type
            ON CONFLICT (date, event_type) DO UPDATE SET
                count = analytics_summary.count + EXCLUDED.count
            """
            
            await self.db.execute(query, (cutoff_date,))
            
            # 2. 刪除原始數據
            delete_query = "DELETE FROM analytics_events WHERE created_at < %s"
            result = await self.db.execute(delete_query, (cutoff_date,))
            
            self.logger.info(f"Aggregated {result.rowcount} analytics records")
            return result.rowcount
        
        return 0
    
    async def _backup_before_deletion(self, table_name: str, cutoff_date: datetime):
        """刪除前備份數據"""
        backup_query = f"""
        COPY (
            SELECT * FROM {table_name} 
            WHERE created_at < %s
        ) TO STDOUT WITH CSV HEADER
        """
        
        backup_data = await self.db.copy_to_string(backup_query, (cutoff_date,))
        
        # 上傳備份到存儲
        backup_path = f"backups/{table_name}/{datetime.now().strftime('%Y%m%d')}.csv"
        await self._upload_backup(backup_path, backup_data)
```

## 合規監控

### 保留期限監控

```python
class RetentionComplianceMonitor:
    """保留期限合規監控器"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    async def check_retention_compliance(self) -> Dict[str, Any]:
        """檢查保留期限合規性"""
        compliance_report = {
            "check_date": datetime.utcnow().isoformat(),
            "overall_status": "compliant",
            "violations": [],
            "warnings": [],
            "data_types": {}
        }
        
        for data_type, rule in DataRetentionConfig.get_all_rules().items():
            check_result = await self._check_data_type_compliance(data_type, rule)
            compliance_report["data_types"][data_type] = check_result
            
            if check_result["status"] == "violation":
                compliance_report["violations"].append({
                    "data_type": data_type,
                    "issue": check_result["issue"],
                    "overdue_count": check_result.get("overdue_count", 0)
                })
                compliance_report["overall_status"] = "non_compliant"
            
            elif check_result["status"] == "warning":
                compliance_report["warnings"].append({
                    "data_type": data_type,
                    "issue": check_result["issue"],
                    "at_risk_count": check_result.get("at_risk_count", 0)
                })
        
        return compliance_report
    
    async def _check_data_type_compliance(self, data_type: str, rule: RetentionRule) -> Dict[str, Any]:
        """檢查特定數據類型的合規性"""
        cutoff_date = datetime.utcnow() - rule.retention_period
        warning_date = datetime.utcnow() - rule.retention_period + timedelta(days=7)  # 7天警告期
        
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
            return {"status": "unknown", "issue": f"No table mapping for {data_type}"}
        
        # 檢查過期數據
        overdue_query = f"""
        SELECT COUNT(*) as count
        FROM {table_name}
        WHERE created_at < %s
          AND (is_deleted = false OR is_deleted IS NULL)
        """
        
        overdue_result = await self.db.fetch_one(overdue_query, (cutoff_date,))
        overdue_count = overdue_result["count"] if overdue_result else 0
        
        # 檢查即將過期數據
        warning_query = f"""
        SELECT COUNT(*) as count
        FROM {table_name}
        WHERE created_at BETWEEN %s AND %s
          AND (is_deleted = false OR is_deleted IS NULL)
        """
        
        warning_result = await self.db.fetch_one(warning_query, (cutoff_date, warning_date))
        at_risk_count = warning_result["count"] if warning_result else 0
        
        # 確定合規狀態
        if overdue_count > 0:
            return {
                "status": "violation",
                "issue": f"{overdue_count} records exceed retention period",
                "overdue_count": overdue_count,
                "cutoff_date": cutoff_date.isoformat()
            }
        elif at_risk_count > 0:
            return {
                "status": "warning", 
                "issue": f"{at_risk_count} records will expire within 7 days",
                "at_risk_count": at_risk_count,
                "warning_date": warning_date.isoformat()
            }
        else:
            return {
                "status": "compliant",
                "message": "All data within retention period"
            }
```

### 自動報告生成

```python
class RetentionReportGenerator:
    """保留期限報告生成器"""
    
    async def generate_monthly_report(self, year: int, month: int) -> Dict[str, Any]:
        """生成月度保留報告"""
        report_date = datetime(year, month, 1)
        next_month = report_date.replace(month=month+1) if month < 12 else report_date.replace(year=year+1, month=1)
        
        report = {
            "report_period": {
                "year": year,
                "month": month,
                "start_date": report_date.isoformat(),
                "end_date": (next_month - timedelta(days=1)).isoformat()
            },
            "summary": await self._generate_summary_stats(report_date, next_month),
            "data_types": {},
            "compliance_status": await self._get_compliance_summary(),
            "recommendations": []
        }
        
        # 為每種數據類型生成詳細統計
        for data_type, rule in DataRetentionConfig.get_all_rules().items():
            report["data_types"][data_type] = await self._generate_data_type_stats(
                data_type, rule, report_date, next_month
            )
        
        # 生成建議
        report["recommendations"] = await self._generate_recommendations(report)
        
        return report
    
    async def _generate_summary_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成摘要統計"""
        # 查詢期間內的清理統計
        cleanup_query = """
        SELECT 
            SUM(deleted_count) as total_deleted,
            SUM(processed_count) as total_processed,
            COUNT(*) as cleanup_runs
        FROM retention_cleanup_logs
        WHERE created_at BETWEEN %s AND %s
        """
        
        result = await self.db.fetch_one(cleanup_query, (start_date, end_date))
        
        return {
            "total_deleted": result["total_deleted"] or 0,
            "total_processed": result["total_processed"] or 0,
            "cleanup_runs": result["cleanup_runs"] or 0,
            "average_daily_deletion": (result["total_deleted"] or 0) / 30
        }
    
    async def export_report_to_pdf(self, report: Dict[str, Any], output_path: str):
        """導出報告為PDF"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # 標題
        title = Paragraph("數據保留月度報告", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # 報告期間
        period_text = f"報告期間: {report['report_period']['start_date']} 至 {report['report_period']['end_date']}"
        period = Paragraph(period_text, styles['Normal'])
        story.append(period)
        story.append(Spacer(1, 12))
        
        # 摘要統計表格
        summary_data = [
            ['指標', '數值'],
            ['總刪除記錄數', str(report['summary']['total_deleted'])],
            ['總處理記錄數', str(report['summary']['total_processed'])],
            ['清理執行次數', str(report['summary']['cleanup_runs'])],
            ['日均刪除量', f"{report['summary']['average_daily_deletion']:.1f}"]
        ]
        
        summary_table = Table(summary_data)
        story.append(summary_table)
        
        doc.build(story)
```

## 配置管理

### 環境配置

```yaml
# config/retention.yaml
retention:
  # 全局設置
  global:
    timezone: "UTC"
    batch_size: 1000
    max_concurrent_jobs: 5
    notification_threshold: 1000
    
  # 調度設置
  schedule:
    daily_cleanup:
      enabled: true
      time: "02:00"
      timezone: "UTC"
    
    weekly_archive:
      enabled: true
      day: "sunday"
      time: "03:00"
    
    monthly_compliance:
      enabled: true
      day: 1
      time: "04:00"
  
  # 存儲設置
  storage:
    archive_bucket: "morningai-archives"
    backup_bucket: "morningai-backups"
    compression: "gzip"
    encryption: "AES256"
  
  # 通知設置
  notifications:
    email:
      enabled: true
      recipients: ["dpo@morningai.com", "admin@morningai.com"]
    
    slack:
      enabled: false
      webhook_url: ""
      channel: "#data-governance"
  
  # 數據類型特定設置
  data_types:
    chat_messages:
      retention_days: 30
      action: "soft_delete"
      backup_before_delete: true
      
    audit_logs:
      retention_days: 365
      action: "archive"
      archive_format: "json"
      compression: true
```

### 動態配置更新

```python
class RetentionConfigManager:
    """保留配置管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.watchers = []
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        import yaml
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def update_retention_rule(self, data_type: str, new_rule: Dict[str, Any]) -> bool:
        """更新保留規則"""
        try:
            # 驗證新規則
            if not self._validate_rule(new_rule):
                return False
            
            # 更新配置
            if 'data_types' not in self.config['retention']:
                self.config['retention']['data_types'] = {}
            
            self.config['retention']['data_types'][data_type] = new_rule
            
            # 保存配置
            await self._save_config()
            
            # 通知觀察者
            await self._notify_config_change(data_type, new_rule)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update retention rule: {e}")
            return False
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """驗證保留規則"""
        required_fields = ['retention_days', 'action']
        
        for field in required_fields:
            if field not in rule:
                return False
        
        if rule['retention_days'] < 1:
            return False
        
        valid_actions = ['soft_delete', 'hard_delete', 'anonymize', 'archive', 'aggregate']
        if rule['action'] not in valid_actions:
            return False
        
        return True
```

## 監控和告警

### 關鍵指標

```python
class RetentionMetrics:
    """保留指標收集器"""
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集保留相關指標"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "storage_usage": await self._get_storage_usage(),
            "retention_compliance": await self._get_compliance_metrics(),
            "cleanup_performance": await self._get_cleanup_metrics(),
            "data_growth": await self._get_growth_metrics()
        }
        
        return metrics
    
    async def _get_storage_usage(self) -> Dict[str, Any]:
        """獲取存儲使用情況"""
        query = """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        
        results = await self.db.fetch_all(query)
        
        return {
            "tables": [dict(row) for row in results],
            "total_size_bytes": sum(row["size_bytes"] for row in results)
        }
```

### 告警規則

```python
class RetentionAlertManager:
    """保留告警管理器"""
    
    ALERT_RULES = {
        "retention_violation": {
            "condition": "overdue_records > 0",
            "severity": "critical",
            "message": "Data retention policy violation detected"
        },
        "cleanup_failure": {
            "condition": "failed_cleanups > 3",
            "severity": "high", 
            "message": "Multiple cleanup failures detected"
        },
        "storage_growth": {
            "condition": "growth_rate > 50",
            "severity": "medium",
            "message": "Rapid storage growth detected"
        }
    }
    
    async def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """檢查告警條件"""
        alerts = []
        
        # 檢查保留違規
        compliance = metrics.get("retention_compliance", {})
        if compliance.get("violations", 0) > 0:
            alerts.append({
                "type": "retention_violation",
                "severity": "critical",
                "message": f"Found {compliance['violations']} retention violations",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # 檢查清理失敗
        cleanup = metrics.get("cleanup_performance", {})
        if cleanup.get("failed_runs", 0) > 3:
            alerts.append({
                "type": "cleanup_failure", 
                "severity": "high",
                "message": f"{cleanup['failed_runs']} cleanup failures in recent period",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
```

## 最佳實踐

### 1. 保留期限設定

- **法律要求優先**：確保符合適用的法律法規
- **業務需求平衡**：在合規和業務需求間找到平衡
- **定期審查**：至少每年審查一次保留政策
- **文檔記錄**：詳細記錄設定理由和法律依據

### 2. 自動化實施

- **逐步實施**：從非關鍵數據開始，逐步擴展
- **充分測試**：在生產環境前進行充分測試
- **監控告警**：建立完善的監控和告警機制
- **回滾計劃**：準備數據恢復和回滾方案

### 3. 合規管理

- **定期審計**：定期檢查保留政策執行情況
- **培訓教育**：確保相關人員了解政策要求
- **變更管理**：建立正式的政策變更流程
- **記錄保存**：保留所有政策執行記錄

### 4. 性能優化

- **批量處理**：使用批量操作提高效率
- **非高峰執行**：在系統負載較低時執行清理
- **索引優化**：確保清理查詢有適當索引
- **資源監控**：監控清理過程的資源使用

---

**配置版本：** v1.0  
**最後更新：** 2025-01-05  
**下次審查：** 2025-04-05  
**負責人：** 數據治理團隊

