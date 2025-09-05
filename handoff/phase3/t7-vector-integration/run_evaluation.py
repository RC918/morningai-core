#!/usr/bin/env python3
"""
MorningAI 評測運行腳本
用於執行完整的 RAG 系統評測
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# 添加項目路徑
sys.path.append(str(Path(__file__).parent))

from integration.vector_service import VectorService, RAGService
from integration.chat_integration import EnhancedChatService
from integration.evaluation_system import EvaluationSystem

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EvaluationRunner:
    """評測運行器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.vector_service = None
        self.rag_service = None
        self.chat_service = None
        self.eval_system = None
    
    async def initialize_services(self):
        """初始化服務"""
        logger.info("初始化評測服務...")
        
        # 初始化向量服務
        self.vector_service = VectorService(
            self.config["database_url"],
            self.config["openai_api_key"]
        )
        await self.vector_service.initialize()
        
        # 初始化 RAG 服務
        self.rag_service = RAGService(
            self.vector_service,
            self.config["openai_api_key"]
        )
        
        # 初始化聊天服務
        self.chat_service = EnhancedChatService(
            self.vector_service,
            self.rag_service
        )
        
        # 初始化評測系統
        self.eval_system = EvaluationSystem(self.chat_service)
        
        logger.info("服務初始化完成")
    
    async def run_full_evaluation(self):
        """運行完整評測"""
        try:
            logger.info("開始完整評測...")
            
            # 運行評測
            results = await self.eval_system.run_evaluation(
                knowledge_base_path=self.config["knowledge_base_path"],
                queries_path=self.config["queries_path"],
                tenant_id=self.config.get("tenant_id", "eval-tenant"),
                user_id=self.config.get("user_id", "eval-user")
            )
            
            # 創建輸出目錄
            output_dir = Path(self.config.get("output_dir", "evaluation_output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成圖表
            charts_dir = output_dir / "charts"
            await self.eval_system.generate_charts(str(charts_dir))
            
            # 保存詳細結果
            results_file = output_dir / "evaluation_results.json"
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 保存報告
            report_file = output_dir / "evaluation_report_v1.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(results["report"])
            
            # 生成摘要
            await self._generate_summary(results, output_dir)
            
            logger.info(f"評測完成！結果保存在: {output_dir}")
            
            return results
            
        except Exception as e:
            logger.error(f"評測運行失敗: {e}")
            raise
    
    async def _generate_summary(self, results: dict, output_dir: Path):
        """生成評測摘要"""
        summary = results["summary"]
        
        summary_text = f"""
# MorningAI 評測摘要

**評測時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 關鍵指標

- **總體準確率**: {summary['overall_metrics']['overall_accuracy']:.1%}
- **95% 目標達成**: {'✅ 是' if summary['overall_metrics']['accuracy_target_met'] else '❌ 否'}
- **平均處理時間**: {summary['performance_metrics']['avg_processing_time']:.2f}秒
- **3秒目標達成**: {'✅ 是' if summary['performance_metrics']['response_time_target_met'] else '❌ 否'}
- **成功率**: {summary['overall_metrics']['success_rate']:.1%}

## 📊 分數分解

- **意圖匹配**: {summary['detailed_scores']['intent_match']:.1%}
- **關鍵詞匹配**: {summary['detailed_scores']['keyword_match']:.1%}
- **來源匹配**: {summary['detailed_scores']['source_match']:.1%}
- **語義相似度**: {summary['detailed_scores']['semantic_similarity']:.1%}

## 🏆 最佳表現類別

"""
        
        # 找出表現最好的類別
        best_category = max(
            summary['category_breakdown'].items(),
            key=lambda x: x[1]['avg_score']
        )
        worst_category = min(
            summary['category_breakdown'].items(),
            key=lambda x: x[1]['avg_score']
        )
        
        summary_text += f"- **最佳**: {best_category[0]} ({best_category[1]['avg_score']:.1%})\n"
        summary_text += f"- **待改進**: {worst_category[0]} ({worst_category[1]['avg_score']:.1%})\n"
        
        # 保存摘要
        summary_file = output_dir / "SUMMARY.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary_text)
    
    async def run_quick_test(self, num_queries: int = 5):
        """運行快速測試"""
        logger.info(f"運行快速測試 ({num_queries} 個查詢)...")
        
        # 載入查詢數據
        with open(self.config["queries_path"], 'r', encoding='utf-8') as f:
            all_queries = json.load(f)
        
        # 選擇前 N 個查詢
        test_queries = all_queries[:num_queries]
        
        # 創建臨時查詢文件
        temp_queries_file = "temp_quick_queries.json"
        with open(temp_queries_file, 'w', encoding='utf-8') as f:
            json.dump(test_queries, f, ensure_ascii=False, indent=2)
        
        try:
            # 運行評測
            results = await self.eval_system.run_evaluation(
                knowledge_base_path=self.config["knowledge_base_path"],
                queries_path=temp_queries_file,
                tenant_id=self.config.get("tenant_id", "eval-tenant"),
                user_id=self.config.get("user_id", "eval-user")
            )
            
            # 輸出快速結果
            summary = results["summary"]
            print(f"\n🚀 快速測試結果:")
            print(f"   總體準確率: {summary['overall_metrics']['overall_accuracy']:.1%}")
            print(f"   平均處理時間: {summary['performance_metrics']['avg_processing_time']:.2f}秒")
            print(f"   成功率: {summary['overall_metrics']['success_rate']:.1%}")
            
            return results
            
        finally:
            # 清理臨時文件
            if os.path.exists(temp_queries_file):
                os.remove(temp_queries_file)
    
    async def cleanup(self):
        """清理資源"""
        if self.vector_service:
            await self.vector_service.close()
        logger.info("資源清理完成")

def load_config(config_path: str = None) -> dict:
    """載入配置"""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默認配置
    return {
        "database_url": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/morningai"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
        "knowledge_base_path": "test-data/knowledge_base.json",
        "queries_path": "test-data/evaluation_queries.json",
        "output_dir": "evaluation_output",
        "tenant_id": "eval-tenant",
        "user_id": "eval-user"
    }

async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="MorningAI 評測系統")
    parser.add_argument("--config", help="配置文件路徑")
    parser.add_argument("--mode", choices=["full", "quick"], default="full", help="評測模式")
    parser.add_argument("--quick-count", type=int, default=5, help="快速測試查詢數量")
    parser.add_argument("--output", help="輸出目錄")
    
    args = parser.parse_args()
    
    # 載入配置
    config = load_config(args.config)
    
    if args.output:
        config["output_dir"] = args.output
    
    # 檢查必要文件
    if not os.path.exists(config["knowledge_base_path"]):
        logger.error(f"知識庫文件不存在: {config['knowledge_base_path']}")
        return 1
    
    if not os.path.exists(config["queries_path"]):
        logger.error(f"查詢文件不存在: {config['queries_path']}")
        return 1
    
    # 創建評測運行器
    runner = EvaluationRunner(config)
    
    try:
        # 初始化服務
        await runner.initialize_services()
        
        # 運行評測
        if args.mode == "full":
            results = await runner.run_full_evaluation()
            
            # 輸出結果摘要
            summary = results["summary"]
            print(f"\n🎉 評測完成!")
            print(f"   總查詢數: {summary['overall_metrics']['total_queries']}")
            print(f"   總體準確率: {summary['overall_metrics']['overall_accuracy']:.1%}")
            print(f"   95% 目標: {'✅ 達成' if summary['overall_metrics']['accuracy_target_met'] else '❌ 未達成'}")
            print(f"   平均處理時間: {summary['performance_metrics']['avg_processing_time']:.2f}秒")
            print(f"   3秒目標: {'✅ 達成' if summary['performance_metrics']['response_time_target_met'] else '❌ 未達成'}")
            
        elif args.mode == "quick":
            results = await runner.run_quick_test(args.quick_count)
        
        return 0
        
    except Exception as e:
        logger.error(f"評測失敗: {e}")
        return 1
        
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())

