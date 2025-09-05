# Prompt 版本化管理文檔

## 概述

本文檔定義 MorningAI 聊天模組的 Prompt 版本化管理策略、模型版本控制和 A/B 測試框架，確保 AI 回應質量的持續改進和可追溯性。

## Prompt 版本化策略

### 版本命名規範

```python
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import semver

class PromptType(Enum):
    """Prompt 類型"""
    SYSTEM = "system"           # 系統提示詞
    USER = "user"              # 用戶提示詞
    ASSISTANT = "assistant"     # 助手提示詞
    FUNCTION = "function"       # 函數調用提示詞
    RAG_CONTEXT = "rag_context" # RAG 上下文提示詞
    INTENT_DETECTION = "intent_detection"  # 意圖識別提示詞

class PromptCategory(Enum):
    """Prompt 分類"""
    GENERAL_CHAT = "general_chat"           # 一般聊天
    TECHNICAL_SUPPORT = "technical_support" # 技術支援
    PRODUCT_INFO = "product_info"           # 產品信息
    TROUBLESHOOTING = "troubleshooting"     # 問題排查
    ONBOARDING = "onboarding"               # 用戶引導
    FEEDBACK = "feedback"                   # 反饋收集

@dataclass
class PromptVersion:
    """Prompt 版本信息"""
    id: str
    name: str
    version: str  # 遵循 semver 格式 (major.minor.patch)
    type: PromptType
    category: PromptCategory
    content: str
    description: str
    author: str
    created_at: datetime
    status: str  # draft, testing, active, deprecated
    parent_version: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        # 驗證版本格式
        if not semver.VersionInfo.isvalid(self.version):
            raise ValueError(f"Invalid version format: {self.version}")

class PromptVersionManager:
    """Prompt 版本管理器"""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
        self.active_versions = {}  # 緩存活躍版本
    
    def create_version(self, prompt_data: Dict) -> PromptVersion:
        """創建新的 Prompt 版本"""
        # 生成版本號
        latest_version = self._get_latest_version(prompt_data["name"])
        if latest_version:
            # 根據變更類型決定版本號增長
            change_type = prompt_data.get("change_type", "patch")
            if change_type == "major":
                new_version = semver.bump_major(latest_version.version)
            elif change_type == "minor":
                new_version = semver.bump_minor(latest_version.version)
            else:
                new_version = semver.bump_patch(latest_version.version)
        else:
            new_version = "1.0.0"
        
        prompt_version = PromptVersion(
            id=self._generate_id(),
            name=prompt_data["name"],
            version=new_version,
            type=PromptType(prompt_data["type"]),
            category=PromptCategory(prompt_data["category"]),
            content=prompt_data["content"],
            description=prompt_data["description"],
            author=prompt_data["author"],
            created_at=datetime.utcnow(),
            status="draft",
            parent_version=latest_version.id if latest_version else None,
            metadata=prompt_data.get("metadata", {})
        )
        
        # 保存到存儲
        self.storage.save_prompt_version(prompt_version)
        
        return prompt_version
    
    def get_active_prompt(self, name: str, category: PromptCategory) -> Optional[PromptVersion]:
        """獲取活躍的 Prompt 版本"""
        cache_key = f"{name}:{category.value}"
        
        if cache_key in self.active_versions:
            return self.active_versions[cache_key]
        
        # 從存儲加載
        active_prompt = self.storage.get_active_prompt(name, category)
        if active_prompt:
            self.active_versions[cache_key] = active_prompt
        
        return active_prompt
    
    def promote_version(self, version_id: str, target_status: str) -> bool:
        """提升版本狀態"""
        valid_transitions = {
            "draft": ["testing"],
            "testing": ["active", "draft"],
            "active": ["deprecated"],
            "deprecated": []
        }
        
        prompt_version = self.storage.get_prompt_version(version_id)
        if not prompt_version:
            return False
        
        if target_status not in valid_transitions.get(prompt_version.status, []):
            raise ValueError(f"Invalid status transition: {prompt_version.status} -> {target_status}")
        
        # 如果提升為 active，需要將同名的其他版本設為 deprecated
        if target_status == "active":
            self._deprecate_other_versions(prompt_version.name, prompt_version.category, version_id)
        
        prompt_version.status = target_status
        self.storage.update_prompt_version(prompt_version)
        
        # 更新緩存
        if target_status == "active":
            cache_key = f"{prompt_version.name}:{prompt_version.category.value}"
            self.active_versions[cache_key] = prompt_version
        
        return True
```

### Prompt 模板系統

```python
from jinja2 import Template, Environment, meta
import json

class PromptTemplate:
    """Prompt 模板"""
    
    def __init__(self, template_content: str, variables: Dict = None):
        self.template_content = template_content
        self.template = Template(template_content)
        self.variables = variables or {}
        self.required_vars = self._extract_required_variables()
    
    def _extract_required_variables(self) -> List[str]:
        """提取模板中的必需變量"""
        env = Environment()
        ast = env.parse(self.template_content)
        return list(meta.find_undeclared_variables(ast))
    
    def render(self, context: Dict) -> str:
        """渲染模板"""
        # 檢查必需變量
        missing_vars = set(self.required_vars) - set(context.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        return self.template.render(**context)
    
    def validate_context(self, context: Dict) -> Dict[str, List[str]]:
        """驗證上下文"""
        errors = []
        warnings = []
        
        # 檢查必需變量
        missing_vars = set(self.required_vars) - set(context.keys())
        if missing_vars:
            errors.append(f"Missing required variables: {missing_vars}")
        
        # 檢查多餘變量
        extra_vars = set(context.keys()) - set(self.required_vars)
        if extra_vars:
            warnings.append(f"Unused variables: {extra_vars}")
        
        return {"errors": errors, "warnings": warnings}

class PromptLibrary:
    """Prompt 庫"""
    
    SYSTEM_PROMPTS = {
        "general_chat": {
            "v1.0.0": PromptTemplate("""
你是 MorningAI 的智能助手，專門幫助用戶解決問題和提供信息。

核心原則：
1. 友善和專業的語調
2. 準確和有用的信息
3. 承認不確定性，不編造信息
4. 引導用戶使用相關功能

用戶信息：
- 用戶ID: {{ user_id }}
- 租戶: {{ tenant_name }}
- 語言偏好: {{ language }}

當前時間: {{ current_time }}

請根據用戶的問題提供幫助。如果需要更多信息，請主動詢問。
            """),
            
            "v1.1.0": PromptTemplate("""
你是 MorningAI 的智能助手，專門幫助用戶解決問題和提供信息。

核心原則：
1. 友善和專業的語調
2. 準確和有用的信息  
3. 承認不確定性，不編造信息
4. 引導用戶使用相關功能
5. 主動提供相關建議

用戶信息：
- 用戶ID: {{ user_id }}
- 租戶: {{ tenant_name }}
- 語言偏好: {{ language }}
- 用戶角色: {{ user_role }}

當前時間: {{ current_time }}
會話上下文: {{ session_context }}

請根據用戶的問題提供幫助。如果需要更多信息，請主動詢問。
對於複雜問題，請提供步驟化的解決方案。
            """)
        },
        
        "technical_support": {
            "v1.0.0": PromptTemplate("""
你是 MorningAI 的技術支援專家，專門協助用戶解決技術問題。

支援範圍：
- API 使用問題
- 功能操作指導
- 錯誤排查
- 最佳實踐建議

用戶信息：
- 用戶ID: {{ user_id }}
- 技術水平: {{ tech_level }}
- 問題類型: {{ issue_type }}

請提供：
1. 清晰的問題診斷
2. 步驟化的解決方案
3. 相關文檔連結
4. 預防措施建議

如果問題超出範圍，請引導用戶聯繫人工支援。
            """)
        }
    }
    
    RAG_PROMPTS = {
        "context_integration": {
            "v1.0.0": PromptTemplate("""
基於以下知識庫內容回答用戶問題：

相關內容：
{% for item in knowledge_items %}
[{{ loop.index }}] {{ item.title }}
{{ item.content }}
來源: {{ item.source }}
相關性: {{ item.relevance_score }}

{% endfor %}

用戶問題: {{ user_query }}

請根據上述內容回答問題。如果內容不足以完整回答，請說明需要更多信息。
在回答中引用相關內容的編號 [1], [2] 等。
            """),
            
            "v2.0.0": PromptTemplate("""
基於以下知識庫內容回答用戶問題：

相關內容：
{% for item in knowledge_items %}
[{{ loop.index }}] {{ item.title }}
內容: {{ item.content }}
來源: {{ item.source }}
相關性: {{ item.relevance_score }}
最後更新: {{ item.updated_at }}

{% endfor %}

用戶問題: {{ user_query }}
用戶上下文: {{ user_context }}

回答要求：
1. 基於提供的內容回答問題
2. 在回答中使用引用標記 [1], [2] 等
3. 如果內容不足，明確說明並建議獲取更多信息的方式
4. 考慮內容的時效性和相關性
5. 提供實用的後續建議

請提供準確、有用的回答。
            """)
        }
    }
    
    @classmethod
    def get_prompt_template(cls, category: str, name: str, version: str = None) -> PromptTemplate:
        """獲取 Prompt 模板"""
        if category == "system":
            prompts = cls.SYSTEM_PROMPTS
        elif category == "rag":
            prompts = cls.RAG_PROMPTS
        else:
            raise ValueError(f"Unknown prompt category: {category}")
        
        if name not in prompts:
            raise ValueError(f"Unknown prompt name: {name}")
        
        prompt_versions = prompts[name]
        
        if version:
            if version not in prompt_versions:
                raise ValueError(f"Unknown prompt version: {version}")
            return prompt_versions[version]
        else:
            # 返回最新版本
            latest_version = max(prompt_versions.keys(), key=lambda v: semver.VersionInfo.parse(v))
            return prompt_versions[latest_version]
```

## A/B 測試框架

### 實驗設計

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import random

@dataclass
class ExperimentConfig:
    """實驗配置"""
    id: str
    name: str
    description: str
    prompt_variants: Dict[str, str]  # variant_name -> prompt_version_id
    traffic_allocation: Dict[str, float]  # variant_name -> percentage
    target_metrics: List[str]
    start_date: datetime
    end_date: datetime
    min_sample_size: int
    significance_level: float = 0.05
    status: str = "draft"  # draft, running, paused, completed
    
    def __post_init__(self):
        # 驗證流量分配總和為 100%
        total_allocation = sum(self.traffic_allocation.values())
        if abs(total_allocation - 1.0) > 0.001:
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total_allocation}")

class PromptExperimentManager:
    """Prompt 實驗管理器"""
    
    def __init__(self, storage_backend, analytics_client):
        self.storage = storage_backend
        self.analytics = analytics_client
        self.active_experiments = {}
    
    def create_experiment(self, config: ExperimentConfig) -> str:
        """創建新實驗"""
        # 驗證配置
        self._validate_experiment_config(config)
        
        # 保存實驗配置
        experiment_id = self.storage.save_experiment(config)
        
        return experiment_id
    
    def assign_variant(self, user_id: str, experiment_id: str) -> str:
        """為用戶分配實驗變體"""
        experiment = self.storage.get_experiment(experiment_id)
        if not experiment or experiment.status != "running":
            return "control"  # 默認控制組
        
        # 使用一致性哈希確保用戶總是分配到同一變體
        hash_input = f"{user_id}:{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized_hash = (hash_value % 10000) / 10000.0
        
        # 根據流量分配確定變體
        cumulative_allocation = 0.0
        for variant_name, allocation in experiment.traffic_allocation.items():
            cumulative_allocation += allocation
            if normalized_hash <= cumulative_allocation:
                # 記錄分配
                self._record_assignment(user_id, experiment_id, variant_name)
                return variant_name
        
        return "control"  # 默認返回控制組
    
    def get_prompt_for_user(self, user_id: str, prompt_name: str, category: str) -> str:
        """為用戶獲取適當的 Prompt"""
        # 檢查活躍實驗
        active_experiments = self._get_active_experiments_for_prompt(prompt_name, category)
        
        for experiment in active_experiments:
            variant = self.assign_variant(user_id, experiment.id)
            if variant in experiment.prompt_variants:
                prompt_version_id = experiment.prompt_variants[variant]
                return self.storage.get_prompt_content(prompt_version_id)
        
        # 沒有實驗時返回默認版本
        default_prompt = self.storage.get_active_prompt(prompt_name, category)
        return default_prompt.content if default_prompt else ""
    
    def record_interaction(self, user_id: str, experiment_id: str, metrics: Dict[str, Any]):
        """記錄用戶互動數據"""
        interaction_data = {
            "user_id": user_id,
            "experiment_id": experiment_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
        # 保存到分析系統
        self.analytics.track("prompt_experiment_interaction", interaction_data)
    
    async def analyze_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """分析實驗結果"""
        experiment = self.storage.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        # 獲取實驗數據
        experiment_data = await self.analytics.get_experiment_data(
            experiment_id, 
            experiment.start_date, 
            experiment.end_date
        )
        
        # 計算統計指標
        results = {
            "experiment_id": experiment_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "variants": {},
            "statistical_significance": {},
            "recommendations": []
        }
        
        # 為每個變體計算指標
        for variant_name in experiment.prompt_variants.keys():
            variant_data = experiment_data.get(variant_name, [])
            results["variants"][variant_name] = self._calculate_variant_metrics(
                variant_data, experiment.target_metrics
            )
        
        # 統計顯著性檢驗
        results["statistical_significance"] = await self._perform_significance_tests(
            experiment_data, experiment.target_metrics
        )
        
        # 生成建議
        results["recommendations"] = self._generate_recommendations(results)
        
        return results
    
    def _calculate_variant_metrics(self, variant_data: List[Dict], target_metrics: List[str]) -> Dict[str, Any]:
        """計算變體指標"""
        if not variant_data:
            return {"sample_size": 0}
        
        metrics = {
            "sample_size": len(variant_data),
            "metrics": {}
        }
        
        for metric in target_metrics:
            values = [item.get(metric) for item in variant_data if item.get(metric) is not None]
            
            if values:
                if metric in ["response_time", "accuracy_score", "user_satisfaction"]:
                    # 數值型指標
                    metrics["metrics"][metric] = {
                        "mean": sum(values) / len(values),
                        "median": sorted(values)[len(values) // 2],
                        "std": self._calculate_std(values),
                        "min": min(values),
                        "max": max(values)
                    }
                elif metric in ["click_through_rate", "conversion_rate"]:
                    # 比率型指標
                    success_count = sum(1 for v in values if v)
                    metrics["metrics"][metric] = {
                        "rate": success_count / len(values),
                        "count": success_count,
                        "total": len(values)
                    }
        
        return metrics
```

### 實驗監控

```python
class ExperimentMonitor:
    """實驗監控器"""
    
    def __init__(self, experiment_manager, alert_service):
        self.experiment_manager = experiment_manager
        self.alerts = alert_service
    
    async def monitor_active_experiments(self):
        """監控活躍實驗"""
        active_experiments = self.experiment_manager.get_active_experiments()
        
        for experiment in active_experiments:
            try:
                # 檢查實驗健康狀況
                health_check = await self._check_experiment_health(experiment)
                
                if health_check["status"] == "unhealthy":
                    await self._handle_unhealthy_experiment(experiment, health_check)
                
                # 檢查是否達到最小樣本量
                if health_check["sample_size"] >= experiment.min_sample_size:
                    await self._check_early_stopping_criteria(experiment)
                
            except Exception as e:
                await self.alerts.send_alert(
                    f"Experiment monitoring error for {experiment.id}: {str(e)}",
                    severity="high"
                )
    
    async def _check_experiment_health(self, experiment: ExperimentConfig) -> Dict[str, Any]:
        """檢查實驗健康狀況"""
        # 獲取最近24小時的數據
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        recent_data = await self.experiment_manager.analytics.get_experiment_data(
            experiment.id, start_time, end_time
        )
        
        health_status = {
            "status": "healthy",
            "sample_size": sum(len(variant_data) for variant_data in recent_data.values()),
            "issues": []
        }
        
        # 檢查流量分配是否正常
        total_traffic = sum(len(variant_data) for variant_data in recent_data.values())
        if total_traffic > 0:
            for variant_name, expected_allocation in experiment.traffic_allocation.items():
                actual_count = len(recent_data.get(variant_name, []))
                actual_allocation = actual_count / total_traffic
                
                # 允許 ±5% 的偏差
                if abs(actual_allocation - expected_allocation) > 0.05:
                    health_status["issues"].append(
                        f"Traffic allocation deviation for {variant_name}: "
                        f"expected {expected_allocation:.2%}, actual {actual_allocation:.2%}"
                    )
        
        # 檢查錯誤率
        error_rates = {}
        for variant_name, variant_data in recent_data.items():
            error_count = sum(1 for item in variant_data if item.get("error"))
            error_rate = error_count / len(variant_data) if variant_data else 0
            error_rates[variant_name] = error_rate
            
            if error_rate > 0.05:  # 5% 錯誤率閾值
                health_status["issues"].append(
                    f"High error rate for {variant_name}: {error_rate:.2%}"
                )
        
        if health_status["issues"]:
            health_status["status"] = "unhealthy"
        
        return health_status
    
    async def _check_early_stopping_criteria(self, experiment: ExperimentConfig):
        """檢查提前停止條件"""
        results = await self.experiment_manager.analyze_experiment_results(experiment.id)
        
        # 檢查統計顯著性
        for metric, significance_test in results["statistical_significance"].items():
            if significance_test.get("p_value", 1.0) < experiment.significance_level:
                # 達到統計顯著性，可以考慮提前停止
                await self.alerts.send_alert(
                    f"Experiment {experiment.id} reached statistical significance for {metric}. "
                    f"Consider early stopping.",
                    severity="medium"
                )
```

## 模型版本管理

### 模型配置

```python
@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    version: str
    provider: str  # openai, anthropic, etc.
    model_id: str  # gpt-4, claude-3, etc.
    parameters: Dict[str, Any]
    cost_per_token: Dict[str, float]  # input, output
    rate_limits: Dict[str, int]
    capabilities: List[str]
    created_at: datetime
    status: str = "active"  # active, deprecated, testing

class ModelManager:
    """模型管理器"""
    
    SUPPORTED_MODELS = {
        "gpt-4": ModelConfig(
            name="GPT-4",
            version="2024-01-01",
            provider="openai",
            model_id="gpt-4",
            parameters={
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            cost_per_token={"input": 0.00003, "output": 0.00006},
            rate_limits={"requests_per_minute": 500, "tokens_per_minute": 150000},
            capabilities=["text_generation", "function_calling", "json_mode"],
            created_at=datetime(2024, 1, 1)
        ),
        
        "gpt-3.5-turbo": ModelConfig(
            name="GPT-3.5 Turbo",
            version="2024-01-01", 
            provider="openai",
            model_id="gpt-3.5-turbo",
            parameters={
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            cost_per_token={"input": 0.0000015, "output": 0.000002},
            rate_limits={"requests_per_minute": 3500, "tokens_per_minute": 90000},
            capabilities=["text_generation", "function_calling"],
            created_at=datetime(2024, 1, 1)
        )
    }
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
        self.active_models = {}
    
    def get_model_for_task(self, task_type: str, user_tier: str = "standard") -> ModelConfig:
        """根據任務類型和用戶等級選擇模型"""
        model_selection_rules = {
            "general_chat": {
                "free": "gpt-3.5-turbo",
                "standard": "gpt-4",
                "premium": "gpt-4"
            },
            "technical_support": {
                "free": "gpt-3.5-turbo", 
                "standard": "gpt-4",
                "premium": "gpt-4"
            },
            "complex_analysis": {
                "free": "gpt-3.5-turbo",
                "standard": "gpt-4",
                "premium": "gpt-4"
            }
        }
        
        model_id = model_selection_rules.get(task_type, {}).get(user_tier, "gpt-3.5-turbo")
        return self.SUPPORTED_MODELS.get(model_id)
    
    async def track_model_usage(self, model_id: str, usage_data: Dict[str, Any]):
        """追蹤模型使用情況"""
        usage_record = {
            "model_id": model_id,
            "timestamp": datetime.utcnow().isoformat(),
            "input_tokens": usage_data.get("input_tokens", 0),
            "output_tokens": usage_data.get("output_tokens", 0),
            "response_time": usage_data.get("response_time", 0),
            "user_id": usage_data.get("user_id"),
            "task_type": usage_data.get("task_type"),
            "success": usage_data.get("success", True)
        }
        
        await self.storage.save_usage_record(usage_record)
```

### 性能監控

```python
class ModelPerformanceMonitor:
    """模型性能監控器"""
    
    def __init__(self, storage_backend, metrics_client):
        self.storage = storage_backend
        self.metrics = metrics_client
    
    async def collect_performance_metrics(self, time_range: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """收集性能指標"""
        end_time = datetime.utcnow()
        start_time = end_time - time_range
        
        usage_data = await self.storage.get_usage_data(start_time, end_time)
        
        metrics = {
            "collection_time": end_time.isoformat(),
            "time_range_hours": time_range.total_seconds() / 3600,
            "models": {}
        }
        
        # 按模型分組統計
        model_groups = {}
        for record in usage_data:
            model_id = record["model_id"]
            if model_id not in model_groups:
                model_groups[model_id] = []
            model_groups[model_id].append(record)
        
        for model_id, records in model_groups.items():
            metrics["models"][model_id] = self._calculate_model_metrics(records)
        
        return metrics
    
    def _calculate_model_metrics(self, records: List[Dict]) -> Dict[str, Any]:
        """計算單個模型的指標"""
        if not records:
            return {}
        
        total_requests = len(records)
        successful_requests = sum(1 for r in records if r.get("success", True))
        
        response_times = [r.get("response_time", 0) for r in records if r.get("response_time")]
        input_tokens = [r.get("input_tokens", 0) for r in records]
        output_tokens = [r.get("output_tokens", 0) for r in records]
        
        return {
            "total_requests": total_requests,
            "success_rate": successful_requests / total_requests,
            "error_rate": (total_requests - successful_requests) / total_requests,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "p95_response_time": self._percentile(response_times, 95) if response_times else 0,
            "total_input_tokens": sum(input_tokens),
            "total_output_tokens": sum(output_tokens),
            "avg_input_tokens": sum(input_tokens) / len(input_tokens) if input_tokens else 0,
            "avg_output_tokens": sum(output_tokens) / len(output_tokens) if output_tokens else 0,
            "cost_estimate": self._calculate_cost_estimate(input_tokens, output_tokens)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """計算百分位數"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
```

## 質量評估

### 自動化評估

```python
class PromptQualityEvaluator:
    """Prompt 質量評估器"""
    
    def __init__(self, model_client, reference_data):
        self.model_client = model_client
        self.reference_data = reference_data
    
    async def evaluate_prompt_version(self, prompt_version: PromptVersion, test_cases: List[Dict]) -> Dict[str, Any]:
        """評估 Prompt 版本質量"""
        evaluation_results = {
            "prompt_version_id": prompt_version.id,
            "evaluation_date": datetime.utcnow().isoformat(),
            "test_cases_count": len(test_cases),
            "metrics": {},
            "detailed_results": []
        }
        
        # 對每個測試案例進行評估
        for i, test_case in enumerate(test_cases):
            try:
                result = await self._evaluate_single_case(prompt_version, test_case)
                evaluation_results["detailed_results"].append(result)
            except Exception as e:
                evaluation_results["detailed_results"].append({
                    "test_case_id": i,
                    "error": str(e),
                    "status": "failed"
                })
        
        # 計算總體指標
        evaluation_results["metrics"] = self._calculate_overall_metrics(
            evaluation_results["detailed_results"]
        )
        
        return evaluation_results
    
    async def _evaluate_single_case(self, prompt_version: PromptVersion, test_case: Dict) -> Dict[str, Any]:
        """評估單個測試案例"""
        # 渲染 Prompt
        template = PromptTemplate(prompt_version.content)
        rendered_prompt = template.render(test_case["context"])
        
        # 調用模型生成回應
        response = await self.model_client.generate_response(
            rendered_prompt,
            test_case.get("user_input", "")
        )
        
        # 評估回應質量
        quality_scores = await self._assess_response_quality(
            response,
            test_case.get("expected_output"),
            test_case.get("evaluation_criteria", [])
        )
        
        return {
            "test_case_id": test_case.get("id"),
            "input": test_case.get("user_input"),
            "expected_output": test_case.get("expected_output"),
            "actual_output": response,
            "quality_scores": quality_scores,
            "status": "completed"
        }
    
    async def _assess_response_quality(self, response: str, expected: str, criteria: List[str]) -> Dict[str, float]:
        """評估回應質量"""
        scores = {}
        
        # 準確性評分
        if expected:
            scores["accuracy"] = await self._calculate_accuracy_score(response, expected)
        
        # 相關性評分
        scores["relevance"] = await self._calculate_relevance_score(response, criteria)
        
        # 完整性評分
        scores["completeness"] = await self._calculate_completeness_score(response, criteria)
        
        # 清晰度評分
        scores["clarity"] = await self._calculate_clarity_score(response)
        
        # 安全性評分
        scores["safety"] = await self._calculate_safety_score(response)
        
        return scores
    
    async def _calculate_accuracy_score(self, response: str, expected: str) -> float:
        """計算準確性分數"""
        # 使用語義相似度計算準確性
        similarity_prompt = f"""
        請評估以下兩個回答的語義相似度，返回 0-1 之間的分數：
        
        期望回答: {expected}
        實際回答: {response}
        
        請只返回數字分數。
        """
        
        similarity_response = await self.model_client.generate_response(similarity_prompt)
        
        try:
            return float(similarity_response.strip())
        except ValueError:
            return 0.5  # 默認中等分數
```

## 部署和回滾

### 自動化部署

```python
class PromptDeploymentManager:
    """Prompt 部署管理器"""
    
    def __init__(self, version_manager, experiment_manager, quality_evaluator):
        self.version_manager = version_manager
        self.experiment_manager = experiment_manager
        self.quality_evaluator = quality_evaluator
    
    async def deploy_prompt_version(self, version_id: str, deployment_config: Dict) -> Dict[str, Any]:
        """部署 Prompt 版本"""
        deployment_result = {
            "version_id": version_id,
            "deployment_id": self._generate_deployment_id(),
            "start_time": datetime.utcnow().isoformat(),
            "status": "in_progress",
            "stages": {}
        }
        
        try:
            # 階段 1: 預部署檢查
            deployment_result["stages"]["pre_deployment"] = await self._pre_deployment_checks(version_id)
            
            # 階段 2: 金絲雀部署
            if deployment_config.get("canary_enabled", True):
                deployment_result["stages"]["canary"] = await self._canary_deployment(
                    version_id, deployment_config.get("canary_percentage", 5)
                )
            
            # 階段 3: 全量部署
            deployment_result["stages"]["full_deployment"] = await self._full_deployment(version_id)
            
            # 階段 4: 部署後驗證
            deployment_result["stages"]["post_deployment"] = await self._post_deployment_validation(version_id)
            
            deployment_result["status"] = "completed"
            deployment_result["end_time"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            deployment_result["status"] = "failed"
            deployment_result["error"] = str(e)
            deployment_result["end_time"] = datetime.utcnow().isoformat()
            
            # 自動回滾
            await self._auto_rollback(version_id, deployment_result["deployment_id"])
        
        return deployment_result
    
    async def _canary_deployment(self, version_id: str, percentage: float) -> Dict[str, Any]:
        """金絲雀部署"""
        # 創建金絲雀實驗
        canary_config = ExperimentConfig(
            id=f"canary_{version_id}_{int(datetime.utcnow().timestamp())}",
            name=f"Canary deployment for {version_id}",
            description="Automated canary deployment",
            prompt_variants={
                "control": self._get_current_active_version(),
                "canary": version_id
            },
            traffic_allocation={
                "control": 1.0 - percentage / 100,
                "canary": percentage / 100
            },
            target_metrics=["accuracy", "user_satisfaction", "error_rate"],
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(hours=2),  # 2小時金絲雀測試
            min_sample_size=100
        )
        
        experiment_id = self.experiment_manager.create_experiment(canary_config)
        self.experiment_manager.start_experiment(experiment_id)
        
        # 等待金絲雀測試完成
        await asyncio.sleep(7200)  # 2小時
        
        # 分析結果
        results = await self.experiment_manager.analyze_experiment_results(experiment_id)
        
        # 決定是否繼續部署
        if self._should_continue_deployment(results):
            return {"status": "passed", "results": results}
        else:
            raise Exception("Canary deployment failed quality checks")
    
    async def rollback_deployment(self, deployment_id: str, target_version_id: str = None) -> Dict[str, Any]:
        """回滾部署"""
        rollback_result = {
            "deployment_id": deployment_id,
            "rollback_id": self._generate_rollback_id(),
            "start_time": datetime.utcnow().isoformat(),
            "status": "in_progress"
        }
        
        try:
            # 確定回滾目標版本
            if not target_version_id:
                target_version_id = await self._get_last_stable_version()
            
            # 執行回滾
            await self._execute_rollback(target_version_id)
            
            # 驗證回滾
            validation_result = await self._validate_rollback(target_version_id)
            
            rollback_result.update({
                "status": "completed",
                "target_version_id": target_version_id,
                "validation": validation_result,
                "end_time": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            rollback_result.update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.utcnow().isoformat()
            })
        
        return rollback_result
```

## 最佳實踐

### 1. 版本管理

- **語義化版本**：使用 semver 格式管理版本號
- **變更記錄**：詳細記錄每個版本的變更內容
- **向後兼容**：確保新版本不破壞現有功能
- **測試覆蓋**：每個版本都要有充分的測試

### 2. 實驗設計

- **假設驅動**：基於明確假設設計實驗
- **統計功效**：確保足夠的樣本量
- **多指標評估**：不只關注單一指標
- **長期影響**：考慮變更的長期效果

### 3. 質量保證

- **自動化評估**：建立自動化的質量評估流程
- **人工審查**：重要變更需要人工審查
- **A/B 測試**：使用實驗驗證改進效果
- **監控告警**：實時監控部署後的表現

### 4. 部署策略

- **漸進式部署**：使用金絲雀部署降低風險
- **快速回滾**：準備快速回滾機制
- **監控驗證**：部署後持續監控
- **文檔更新**：及時更新相關文檔

---

**版本控制文檔版本：** v1.0  
**最後更新：** 2025-01-05  
**負責人：** AI 工程團隊

