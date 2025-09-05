"""
MorningAI 聊天系統評測系統
用於評估 RAG 系統的準確性和性能
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass, asdict
import statistics
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

from .vector_service import VectorService, RAGService, EmbeddingRequest
from .chat_integration import EnhancedChatService

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """單個評測結果"""
    query_id: str
    query: str
    category: str
    difficulty: str
    expected_response_type: str
    actual_response_type: str
    response: str
    processing_time: float
    confidence: float
    sources_count: int
    expected_sources: List[str]
    actual_sources: List[str]
    expected_keywords: List[str]
    ground_truth: str
    
    # 評分指標
    intent_match_score: float  # 意圖匹配分數 (0-1)
    keyword_match_score: float  # 關鍵詞匹配分數 (0-1)
    source_match_score: float  # 來源匹配分數 (0-1)
    semantic_similarity_score: float  # 語義相似度分數 (0-1)
    overall_score: float  # 總體分數 (0-1)
    
    # 額外信息
    error: Optional[str] = None
    timestamp: str = ""

class EvaluationSystem:
    """評測系統"""
    
    def __init__(self, chat_service: EnhancedChatService):
        self.chat_service = chat_service
        self.results: List[EvaluationResult] = []
        
        # 評測配置
        self.accuracy_threshold = 0.95  # 95% 準確率目標
        self.response_time_threshold = 3.0  # 3秒響應時間目標
        self.confidence_threshold = 0.8  # 信心度閾值
        
    async def run_evaluation(
        self, 
        knowledge_base_path: str,
        queries_path: str,
        tenant_id: str = "eval-tenant",
        user_id: str = "eval-user"
    ) -> Dict[str, Any]:
        """運行完整評測"""
        logger.info("開始運行評測系統...")
        start_time = time.time()
        
        try:
            # 1. 載入測試數據
            knowledge_base = await self._load_knowledge_base(knowledge_base_path)
            queries = await self._load_evaluation_queries(queries_path)
            
            # 2. 初始化知識庫
            await self._setup_knowledge_base(knowledge_base, tenant_id)
            
            # 3. 運行查詢評測
            await self._run_query_evaluation(queries, tenant_id, user_id)
            
            # 4. 計算評測指標
            metrics = await self._calculate_metrics()
            
            # 5. 生成報告
            report = await self._generate_report(metrics)
            
            total_time = time.time() - start_time
            logger.info(f"評測完成，總耗時: {total_time:.2f}秒")
            
            return {
                "summary": metrics,
                "detailed_results": [asdict(result) for result in self.results],
                "report": report,
                "evaluation_time": total_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"評測運行失敗: {e}")
            raise
    
    async def _load_knowledge_base(self, path: str) -> List[Dict[str, Any]]:
        """載入知識庫數據"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
            logger.info(f"載入知識庫: {len(knowledge_base)} 個條目")
            return knowledge_base
        except Exception as e:
            logger.error(f"載入知識庫失敗: {e}")
            raise
    
    async def _load_evaluation_queries(self, path: str) -> List[Dict[str, Any]]:
        """載入評測查詢"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                queries = json.load(f)
            logger.info(f"載入評測查詢: {len(queries)} 個")
            return queries
        except Exception as e:
            logger.error(f"載入評測查詢失敗: {e}")
            raise
    
    async def _setup_knowledge_base(self, knowledge_base: List[Dict[str, Any]], tenant_id: str):
        """設置知識庫"""
        logger.info("設置評測知識庫...")
        
        for item in knowledge_base:
            try:
                await self.chat_service.add_knowledge_to_vector_db(
                    title=item["title"],
                    content=item["content"],
                    source=item["source"],
                    tenant_id=tenant_id,
                    url=item.get("url"),
                    metadata={
                        "id": item["id"],
                        "category": item["category"],
                        "language": item["language"],
                        "tags": item["tags"],
                        "priority": item["metadata"]["priority"]
                    }
                )
                logger.debug(f"添加知識條目: {item['id']}")
                
            except Exception as e:
                logger.error(f"添加知識條目失敗 {item['id']}: {e}")
        
        logger.info("知識庫設置完成")
    
    async def _run_query_evaluation(self, queries: List[Dict[str, Any]], tenant_id: str, user_id: str):
        """運行查詢評測"""
        logger.info(f"開始評測 {len(queries)} 個查詢...")
        
        for i, query_data in enumerate(queries):
            try:
                logger.info(f"評測查詢 {i+1}/{len(queries)}: {query_data['query']}")
                
                # 執行聊天查詢
                start_time = time.time()
                response = await self.chat_service.process_chat_message(
                    message=query_data["query"],
                    session_id=f"eval-session-{query_data['id']}",
                    user_id=user_id,
                    tenant_id=tenant_id
                )
                processing_time = time.time() - start_time
                
                # 評估結果
                result = await self._evaluate_response(query_data, response, processing_time)
                self.results.append(result)
                
                logger.info(f"查詢 {query_data['id']} 評測完成，總分: {result.overall_score:.3f}")
                
            except Exception as e:
                logger.error(f"查詢評測失敗 {query_data['id']}: {e}")
                
                # 創建錯誤結果
                error_result = EvaluationResult(
                    query_id=query_data["id"],
                    query=query_data["query"],
                    category=query_data["category"],
                    difficulty=query_data["difficulty"],
                    expected_response_type=query_data["expected_response_type"],
                    actual_response_type="error",
                    response="",
                    processing_time=0.0,
                    confidence=0.0,
                    sources_count=0,
                    expected_sources=query_data["expected_sources"],
                    actual_sources=[],
                    expected_keywords=query_data["expected_keywords"],
                    ground_truth=query_data["ground_truth"],
                    intent_match_score=0.0,
                    keyword_match_score=0.0,
                    source_match_score=0.0,
                    semantic_similarity_score=0.0,
                    overall_score=0.0,
                    error=str(e),
                    timestamp=datetime.now().isoformat()
                )
                self.results.append(error_result)
        
        logger.info("查詢評測完成")
    
    async def _evaluate_response(
        self, 
        query_data: Dict[str, Any], 
        response: Dict[str, Any], 
        processing_time: float
    ) -> EvaluationResult:
        """評估單個回應"""
        
        # 提取實際來源
        actual_sources = []
        if "sources" in response:
            for source in response["sources"]:
                # 從 metadata 中提取知識庫 ID
                if "metadata" in source and "id" in source["metadata"]:
                    actual_sources.append(source["metadata"]["id"])
        
        # 計算各項評分
        intent_score = self._calculate_intent_match_score(
            query_data["expected_response_type"], 
            response.get("response_type", "")
        )
        
        keyword_score = self._calculate_keyword_match_score(
            query_data["expected_keywords"],
            response.get("response", "")
        )
        
        source_score = self._calculate_source_match_score(
            query_data["expected_sources"],
            actual_sources
        )
        
        semantic_score = self._calculate_semantic_similarity_score(
            query_data["ground_truth"],
            response.get("response", "")
        )
        
        # 計算總體分數
        overall_score = (intent_score * 0.3 + keyword_score * 0.25 + 
                        source_score * 0.25 + semantic_score * 0.2)
        
        return EvaluationResult(
            query_id=query_data["id"],
            query=query_data["query"],
            category=query_data["category"],
            difficulty=query_data["difficulty"],
            expected_response_type=query_data["expected_response_type"],
            actual_response_type=response.get("response_type", ""),
            response=response.get("response", ""),
            processing_time=processing_time,
            confidence=response.get("confidence", 0.0),
            sources_count=len(response.get("sources", [])),
            expected_sources=query_data["expected_sources"],
            actual_sources=actual_sources,
            expected_keywords=query_data["expected_keywords"],
            ground_truth=query_data["ground_truth"],
            intent_match_score=intent_score,
            keyword_match_score=keyword_score,
            source_match_score=source_score,
            semantic_similarity_score=semantic_score,
            overall_score=overall_score,
            timestamp=datetime.now().isoformat()
        )
    
    def _calculate_intent_match_score(self, expected: str, actual: str) -> float:
        """計算意圖匹配分數"""
        if expected == actual:
            return 1.0
        
        # 部分匹配規則
        if expected == "rag" and actual in ["rag", "rag_with_gpt_fallback"]:
            return 0.9
        elif expected == "gpt_fallback" and actual in ["gpt_fallback", "general_chat"]:
            return 0.9
        else:
            return 0.0
    
    def _calculate_keyword_match_score(self, expected_keywords: List[str], response: str) -> float:
        """計算關鍵詞匹配分數"""
        if not expected_keywords:
            return 1.0
        
        response_lower = response.lower()
        matched_keywords = []
        
        for keyword in expected_keywords:
            if keyword.lower() in response_lower:
                matched_keywords.append(keyword)
        
        return len(matched_keywords) / len(expected_keywords)
    
    def _calculate_source_match_score(self, expected_sources: List[str], actual_sources: List[str]) -> float:
        """計算來源匹配分數"""
        if not expected_sources:
            return 1.0
        
        if not actual_sources:
            return 0.0
        
        matched_sources = set(expected_sources) & set(actual_sources)
        return len(matched_sources) / len(expected_sources)
    
    def _calculate_semantic_similarity_score(self, ground_truth: str, response: str) -> float:
        """計算語義相似度分數"""
        # 簡化的語義相似度計算
        # 實際應用中可以使用更複雜的模型，如 sentence-transformers
        
        if not ground_truth or not response:
            return 0.0
        
        # 基於詞彙重疊的簡單相似度
        truth_words = set(ground_truth.lower().split())
        response_words = set(response.lower().split())
        
        if not truth_words:
            return 0.0
        
        intersection = truth_words & response_words
        union = truth_words | response_words
        
        # Jaccard 相似度
        jaccard_similarity = len(intersection) / len(union) if union else 0.0
        
        # 長度懲罰 (避免過長或過短的回應)
        length_ratio = min(len(response), len(ground_truth)) / max(len(response), len(ground_truth))
        length_penalty = 0.8 + 0.2 * length_ratio
        
        return jaccard_similarity * length_penalty
    
    async def _calculate_metrics(self) -> Dict[str, Any]:
        """計算評測指標"""
        if not self.results:
            return {}
        
        # 基本統計
        total_queries = len(self.results)
        successful_queries = len([r for r in self.results if r.error is None])
        
        # 準確率統計
        high_accuracy_queries = len([r for r in self.results if r.overall_score >= self.accuracy_threshold])
        overall_accuracy = sum(r.overall_score for r in self.results) / total_queries
        
        # 性能統計
        processing_times = [r.processing_time for r in self.results if r.error is None]
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        fast_responses = len([t for t in processing_times if t <= self.response_time_threshold])
        
        # 信心度統計
        confidences = [r.confidence for r in self.results if r.error is None]
        avg_confidence = statistics.mean(confidences) if confidences else 0
        high_confidence_queries = len([c for c in confidences if c >= self.confidence_threshold])
        
        # 按類別統計
        category_stats = {}
        for result in self.results:
            category = result.category
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "avg_score": 0,
                    "avg_time": 0,
                    "success_rate": 0
                }
            
            category_stats[category]["count"] += 1
            category_stats[category]["avg_score"] += result.overall_score
            category_stats[category]["avg_time"] += result.processing_time
            if result.error is None:
                category_stats[category]["success_rate"] += 1
        
        for category in category_stats:
            count = category_stats[category]["count"]
            category_stats[category]["avg_score"] /= count
            category_stats[category]["avg_time"] /= count
            category_stats[category]["success_rate"] /= count
        
        # 按難度統計
        difficulty_stats = {}
        for result in self.results:
            difficulty = result.difficulty
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {
                    "count": 0,
                    "avg_score": 0,
                    "success_rate": 0
                }
            
            difficulty_stats[difficulty]["count"] += 1
            difficulty_stats[difficulty]["avg_score"] += result.overall_score
            if result.error is None:
                difficulty_stats[difficulty]["success_rate"] += 1
        
        for difficulty in difficulty_stats:
            count = difficulty_stats[difficulty]["count"]
            difficulty_stats[difficulty]["avg_score"] /= count
            difficulty_stats[difficulty]["success_rate"] /= count
        
        return {
            "overall_metrics": {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": successful_queries / total_queries,
                "overall_accuracy": overall_accuracy,
                "accuracy_target_met": overall_accuracy >= self.accuracy_threshold,
                "high_accuracy_queries": high_accuracy_queries,
                "high_accuracy_rate": high_accuracy_queries / total_queries
            },
            "performance_metrics": {
                "avg_processing_time": avg_processing_time,
                "max_processing_time": max(processing_times) if processing_times else 0,
                "min_processing_time": min(processing_times) if processing_times else 0,
                "fast_responses": fast_responses,
                "fast_response_rate": fast_responses / len(processing_times) if processing_times else 0,
                "response_time_target_met": avg_processing_time <= self.response_time_threshold
            },
            "confidence_metrics": {
                "avg_confidence": avg_confidence,
                "high_confidence_queries": high_confidence_queries,
                "high_confidence_rate": high_confidence_queries / len(confidences) if confidences else 0
            },
            "category_breakdown": category_stats,
            "difficulty_breakdown": difficulty_stats,
            "detailed_scores": {
                "intent_match": statistics.mean([r.intent_match_score for r in self.results]),
                "keyword_match": statistics.mean([r.keyword_match_score for r in self.results]),
                "source_match": statistics.mean([r.source_match_score for r in self.results]),
                "semantic_similarity": statistics.mean([r.semantic_similarity_score for r in self.results])
            }
        }
    
    async def _generate_report(self, metrics: Dict[str, Any]) -> str:
        """生成評測報告"""
        report = f"""
# MorningAI 聊天系統評測報告 v1.0

**評測時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**評測版本**: Phase 5 - RAG 整合版本

## 📊 總體表現

### 🎯 核心指標
- **總體準確率**: {metrics['overall_metrics']['overall_accuracy']:.1%}
- **95% 準確率目標**: {'✅ 達成' if metrics['overall_metrics']['accuracy_target_met'] else '❌ 未達成'}
- **成功率**: {metrics['overall_metrics']['success_rate']:.1%}
- **平均處理時間**: {metrics['performance_metrics']['avg_processing_time']:.2f}秒
- **3秒響應目標**: {'✅ 達成' if metrics['performance_metrics']['response_time_target_met'] else '❌ 未達成'}

### 📈 詳細分數
- **意圖匹配**: {metrics['detailed_scores']['intent_match']:.1%}
- **關鍵詞匹配**: {metrics['detailed_scores']['keyword_match']:.1%}
- **來源匹配**: {metrics['detailed_scores']['source_match']:.1%}
- **語義相似度**: {metrics['detailed_scores']['semantic_similarity']:.1%}

## 📋 分類表現

"""
        
        # 添加分類統計
        for category, stats in metrics['category_breakdown'].items():
            report += f"### {category}\n"
            report += f"- 查詢數量: {stats['count']}\n"
            report += f"- 平均分數: {stats['avg_score']:.1%}\n"
            report += f"- 平均時間: {stats['avg_time']:.2f}秒\n"
            report += f"- 成功率: {stats['success_rate']:.1%}\n\n"
        
        report += "## 🎚️ 難度表現\n\n"
        
        # 添加難度統計
        for difficulty, stats in metrics['difficulty_breakdown'].items():
            report += f"### {difficulty.upper()}\n"
            report += f"- 查詢數量: {stats['count']}\n"
            report += f"- 平均分數: {stats['avg_score']:.1%}\n"
            report += f"- 成功率: {stats['success_rate']:.1%}\n\n"
        
        # 添加建議
        report += "## 💡 改進建議\n\n"
        
        if metrics['overall_metrics']['overall_accuracy'] < self.accuracy_threshold:
            report += "- ❗ **準確率未達標**: 需要優化知識庫內容和 RAG 檢索策略\n"
        
        if metrics['performance_metrics']['avg_processing_time'] > self.response_time_threshold:
            report += "- ⚡ **響應時間過長**: 需要優化向量搜索和 GPT 調用性能\n"
        
        if metrics['detailed_scores']['source_match'] < 0.8:
            report += "- 🎯 **來源匹配度偏低**: 需要改進知識庫索引和搜索相關性\n"
        
        if metrics['detailed_scores']['keyword_match'] < 0.7:
            report += "- 🔍 **關鍵詞匹配度偏低**: 需要優化回應生成的關鍵信息包含\n"
        
        report += "\n## 📊 數據可視化\n\n"
        report += "詳細的圖表分析請參考 `charts/` 目錄中的可視化文件。\n\n"
        
        report += "---\n"
        report += f"**報告生成時間**: {datetime.now().isoformat()}\n"
        report += "**評測系統版本**: v1.0\n"
        
        return report
    
    async def generate_charts(self, output_dir: str):
        """生成評測圖表"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 總體分數分布
        scores = [r.overall_score for r in self.results]
        plt.figure(figsize=(10, 6))
        plt.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(x=self.accuracy_threshold, color='red', linestyle='--', 
                   label=f'目標準確率 ({self.accuracy_threshold:.0%})')
        plt.xlabel('總體分數')
        plt.ylabel('查詢數量')
        plt.title('MorningAI 評測分數分布')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path / 'score_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 分類表現對比
        categories = list(set(r.category for r in self.results))
        category_scores = []
        for category in categories:
            category_results = [r for r in self.results if r.category == category]
            avg_score = sum(r.overall_score for r in category_results) / len(category_results)
            category_scores.append(avg_score)
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(categories, category_scores, color='lightcoral', alpha=0.7)
        plt.axhline(y=self.accuracy_threshold, color='red', linestyle='--', 
                   label=f'目標準確率 ({self.accuracy_threshold:.0%})')
        plt.xlabel('查詢類別')
        plt.ylabel('平均分數')
        plt.title('各類別查詢表現')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 添加數值標籤
        for bar, score in zip(bars, category_scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'category_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 處理時間分析
        processing_times = [r.processing_time for r in self.results if r.error is None]
        plt.figure(figsize=(10, 6))
        plt.hist(processing_times, bins=15, alpha=0.7, color='lightgreen', edgecolor='black')
        plt.axvline(x=self.response_time_threshold, color='red', linestyle='--',
                   label=f'目標響應時間 ({self.response_time_threshold}秒)')
        plt.xlabel('處理時間 (秒)')
        plt.ylabel('查詢數量')
        plt.title('查詢處理時間分布')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path / 'processing_time_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. 各項指標雷達圖
        metrics_names = ['意圖匹配', '關鍵詞匹配', '來源匹配', '語義相似度']
        metrics_values = [
            statistics.mean([r.intent_match_score for r in self.results]),
            statistics.mean([r.keyword_match_score for r in self.results]),
            statistics.mean([r.source_match_score for r in self.results]),
            statistics.mean([r.semantic_similarity_score for r in self.results])
        ]
        
        # 雷達圖需要閉合
        metrics_names += [metrics_names[0]]
        metrics_values += [metrics_values[0]]
        
        angles = [n / float(len(metrics_names)-1) * 2 * 3.14159 for n in range(len(metrics_names))]
        
        plt.figure(figsize=(8, 8))
        ax = plt.subplot(111, projection='polar')
        ax.plot(angles, metrics_values, 'o-', linewidth=2, label='實際表現')
        ax.fill(angles, metrics_values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics_names[:-1])
        ax.set_ylim(0, 1)
        ax.set_title('各項評測指標表現', pad=20)
        ax.grid(True)
        plt.savefig(output_path / 'metrics_radar.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"圖表已生成到: {output_path}")


# 使用示例
async def run_evaluation_example():
    """運行評測示例"""
    # 配置
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/morningai"
    OPENAI_API_KEY = "your-openai-api-key"
    
    # 初始化服務
    from .vector_service import VectorService, RAGService
    from .chat_integration import EnhancedChatService
    
    vector_service = VectorService(DATABASE_URL, OPENAI_API_KEY)
    await vector_service.initialize()
    
    rag_service = RAGService(vector_service, OPENAI_API_KEY)
    chat_service = EnhancedChatService(vector_service, rag_service)
    
    # 初始化評測系統
    eval_system = EvaluationSystem(chat_service)
    
    try:
        # 運行評測
        results = await eval_system.run_evaluation(
            knowledge_base_path="test-data/knowledge_base.json",
            queries_path="test-data/evaluation_queries.json"
        )
        
        # 生成圖表
        await eval_system.generate_charts("charts")
        
        # 保存結果
        with open("evaluation_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存報告
        with open("evaluation_report.md", "w", encoding="utf-8") as f:
            f.write(results["report"])
        
        print("評測完成！")
        print(f"總體準確率: {results['summary']['overall_metrics']['overall_accuracy']:.1%}")
        print(f"平均處理時間: {results['summary']['performance_metrics']['avg_processing_time']:.2f}秒")
        
    finally:
        await vector_service.close()

if __name__ == "__main__":
    asyncio.run(run_evaluation_example())

