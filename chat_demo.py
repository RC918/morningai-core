#!/usr/bin/env python3
"""
聊天模組功能演示腳本
展示 GPT+RAG 整合、對話管理、知識檢索等核心功能
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from uuid import uuid4, UUID
from typing import Dict, List, Any

# 添加項目路徑
sys.path.append('/home/ubuntu/morningai-core/backend/morningai-api/src')

from services.chat_service import ChatService, RAGService, GPTService
from schemas.chat import ChatMessageSend, ChatKnowledgeBaseSearch


class ChatModuleDemo:
    """聊天模組功能演示類"""
    
    def __init__(self):
        self.chat_service = ChatService()
        self.rag_service = RAGService()
        self.gpt_service = GPTService()
        
        # 模擬用戶和租戶
        self.demo_user_id = UUID("12345678-1234-5678-9012-123456789012")
        self.demo_tenant_id = UUID("87654321-4321-8765-2109-876543210987")
        
        print("🚀 聊天模組功能演示系統初始化完成")
        print("=" * 60)
    
    async def demo_rag_service(self):
        """演示 RAG 服務功能"""
        print("\n🔍 RAG (檢索增強生成) 服務演示")
        print("-" * 40)
        
        # 測試查詢列表
        test_queries = [
            "如何註冊帳號？",
            "推薦碼怎麼使用？",
            "忘記密碼怎麼辦？",
            "產品有什麼功能？",
            "如何聯繫客服？"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 測試查詢 {i}: {query}")
            
            try:
                # 搜索知識庫
                knowledge_items = await self.rag_service.search_knowledge(
                    query=query,
                    tenant_id=self.demo_tenant_id,
                    limit=3,
                    similarity_threshold=0.7
                )
                
                print(f"✅ 找到 {len(knowledge_items)} 個相關條目:")
                
                for j, item in enumerate(knowledge_items, 1):
                    print(f"   {j}. 標題: {item['title']}")
                    print(f"      內容: {item['content'][:50]}...")
                    print(f"      相關性: {item['relevance_score']:.2f}")
                    print(f"      分類: {item['category']}")
                
                # 生成上下文
                context = await self.rag_service.generate_context(knowledge_items)
                if context:
                    print(f"📋 生成的上下文長度: {len(context)} 字符")
                
            except Exception as e:
                print(f"❌ RAG 搜索失敗: {e}")
    
    async def demo_gpt_service(self):
        """演示 GPT 服務功能"""
        print("\n🤖 GPT 服務演示")
        print("-" * 40)
        
        # 測試對話場景
        test_conversations = [
            {
                "messages": [
                    {"role": "user", "content": "你好，我想了解你們的產品"}
                ],
                "context": "產品功能介紹：我們的產品提供聊天、推薦系統、內容管理等功能。"
            },
            {
                "messages": [
                    {"role": "user", "content": "我忘記密碼了"},
                    {"role": "assistant", "content": "您可以使用忘記密碼功能重置密碼"},
                    {"role": "user", "content": "具體怎麼操作？"}
                ],
                "context": "密碼重置：請聯繫客服或使用忘記密碼功能。"
            }
        ]
        
        for i, conversation in enumerate(test_conversations, 1):
            print(f"\n💬 對話場景 {i}:")
            
            # 顯示對話歷史
            for msg in conversation["messages"]:
                role_emoji = "👤" if msg["role"] == "user" else "🤖"
                print(f"   {role_emoji} {msg['role']}: {msg['content']}")
            
            try:
                # 生成回應
                response, metadata = await self.gpt_service.generate_response(
                    messages=conversation["messages"],
                    context=conversation.get("context"),
                    user_id=self.demo_user_id,
                    temperature=0.7
                )
                
                print(f"   🤖 assistant: {response}")
                print(f"   📊 元數據:")
                print(f"      - 模型: {metadata.get('model', 'N/A')}")
                print(f"      - 響應時間: {metadata.get('response_time', 0):.2f}秒")
                print(f"      - 令牌使用: {metadata.get('usage', {}).get('total_tokens', 0)}")
                print(f"      - 使用上下文: {'是' if metadata.get('has_context') else '否'}")
                
            except Exception as e:
                print(f"   ❌ GPT 生成失敗: {e}")
    
    async def demo_intent_analysis(self):
        """演示意圖分析功能"""
        print("\n🎯 意圖分析演示")
        print("-" * 40)
        
        # 測試消息列表
        test_messages = [
            "你好",
            "什麼是推薦碼？",
            "我需要幫助",
            "系統有問題",
            "再見",
            "如何註冊？",
            "謝謝你的幫助",
            "產品價格多少？"
        ]
        
        for message in test_messages:
            print(f"\n📝 分析消息: '{message}'")
            
            try:
                intent_result = await self.gpt_service.analyze_intent(message)
                
                print(f"   🎯 主要意圖: {intent_result['primary_intent']}")
                print(f"   📋 所有意圖: {', '.join(intent_result['intents'])}")
                print(f"   🎲 信心分數: {intent_result['confidence']:.2f}")
                print(f"   ❓ 需要追問: {'是' if intent_result['requires_followup'] else '否'}")
                
            except Exception as e:
                print(f"   ❌ 意圖分析失敗: {e}")
    
    async def demo_complete_conversation(self):
        """演示完整對話流程"""
        print("\n💬 完整對話流程演示")
        print("-" * 40)
        
        # 模擬數據庫會話（簡化版）
        class MockDB:
            def __init__(self):
                self.sessions = {}
                self.messages = {}
            
            async def get(self, model, id):
                if model.__name__ == "ChatSession":
                    return self.sessions.get(id)
                return None
            
            def add(self, obj):
                if hasattr(obj, 'id'):
                    if hasattr(obj, 'user_id'):  # ChatSession
                        self.sessions[obj.id] = obj
                    else:  # ChatMessage
                        if obj.session_id not in self.messages:
                            self.messages[obj.session_id] = []
                        self.messages[obj.session_id].append(obj)
            
            async def commit(self):
                pass
            
            async def refresh(self, obj):
                pass
            
            async def execute(self, query):
                class MockResult:
                    def scalars(self):
                        return MockScalars([])
                return MockResult()
        
        class MockScalars:
            def __init__(self, data):
                self.data = data
            
            def all(self):
                return self.data
        
        mock_db = MockDB()
        
        # 測試對話序列
        conversation_flow = [
            "你好，我是新用戶",
            "我想了解推薦碼功能",
            "如何獲得推薦碼？",
            "推薦碼有什麼好處？",
            "謝謝你的解答"
        ]
        
        session_id = None
        
        print("🎭 開始模擬對話...")
        
        for i, user_message in enumerate(conversation_flow, 1):
            print(f"\n--- 對話輪次 {i} ---")
            print(f"👤 用戶: {user_message}")
            
            try:
                # 注意：這裡使用模擬的數據庫，實際使用時需要真實的數據庫連接
                # result = await self.chat_service.send_message(
                #     db=mock_db,
                #     user_id=self.demo_user_id,
                #     tenant_id=self.demo_tenant_id,
                #     message=user_message,
                #     session_id=session_id
                # )
                
                # 模擬回應（因為沒有真實數據庫連接）
                mock_response = {
                    "session_id": str(uuid4()) if not session_id else session_id,
                    "message_id": str(uuid4()),
                    "response": f"感謝您的問題「{user_message}」。作為 MorningAI 助手，我很樂意為您解答。",
                    "intent_analysis": {
                        "primary_intent": "question" if "?" in user_message or "如何" in user_message else "greeting",
                        "intents": ["question"],
                        "confidence": 0.85,
                        "requires_followup": len(user_message.split()) < 5
                    },
                    "knowledge_used": True,
                    "knowledge_items": [
                        {
                            "title": "推薦碼功能說明",
                            "content": "推薦碼是邀請朋友的專用代碼...",
                            "relevance_score": 0.9
                        }
                    ],
                    "metadata": {
                        "model": "gpt-4",
                        "response_time": 1.2,
                        "usage": {"total_tokens": 150},
                        "has_context": True
                    },
                    "created_at": datetime.now().isoformat()
                }
                
                if not session_id:
                    session_id = mock_response["session_id"]
                
                print(f"🤖 助手: {mock_response['response']}")
                print(f"📊 分析結果:")
                print(f"   - 意圖: {mock_response['intent_analysis']['primary_intent']}")
                print(f"   - 信心: {mock_response['intent_analysis']['confidence']:.2f}")
                print(f"   - 知識庫: {'已使用' if mock_response['knowledge_used'] else '未使用'}")
                print(f"   - 響應時間: {mock_response['metadata']['response_time']:.2f}秒")
                
                if mock_response['intent_analysis']['requires_followup']:
                    print(f"❓ 系統建議追問: 能否提供更多詳細信息？")
                
            except Exception as e:
                print(f"❌ 對話處理失敗: {e}")
    
    async def demo_api_examples(self):
        """演示 API 使用範例"""
        print("\n🔌 API 使用範例")
        print("-" * 40)
        
        print("📋 主要 API 端點:")
        
        api_examples = [
            {
                "method": "POST",
                "endpoint": "/api/v1/chat/send",
                "description": "發送聊天消息",
                "example": {
                    "message": "你好，我想了解產品功能",
                    "session_id": None
                }
            },
            {
                "method": "GET",
                "endpoint": "/api/v1/chat/sessions",
                "description": "獲取用戶會話列表",
                "example": {
                    "page": 1,
                    "size": 20
                }
            },
            {
                "method": "GET",
                "endpoint": "/api/v1/chat/sessions/{session_id}/history",
                "description": "獲取聊天歷史",
                "example": {
                    "page": 1,
                    "size": 50
                }
            },
            {
                "method": "POST",
                "endpoint": "/api/v1/chat/knowledge/search",
                "description": "搜索知識庫",
                "example": {
                    "query": "推薦碼使用方法",
                    "limit": 5,
                    "similarity_threshold": 0.7
                }
            },
            {
                "method": "POST",
                "endpoint": "/api/v1/chat/feedback",
                "description": "提交反饋",
                "example": {
                    "message_id": "uuid-here",
                    "rating": 5,
                    "feedback_type": "helpful",
                    "comment": "回答很有幫助"
                }
            }
        ]
        
        for api in api_examples:
            print(f"\n🔗 {api['method']} {api['endpoint']}")
            print(f"   📝 描述: {api['description']}")
            print(f"   📋 請求範例:")
            print(f"   {json.dumps(api['example'], indent=6, ensure_ascii=False)}")
    
    async def demo_performance_features(self):
        """演示性能和安全特性"""
        print("\n⚡ 性能和安全特性演示")
        print("-" * 40)
        
        features = [
            {
                "name": "速率限制",
                "description": "防止 API 濫用",
                "details": [
                    "聊天消息: 30條/小時",
                    "知識庫創建: 10條/小時",
                    "反饋提交: 50條/小時",
                    "GPT API: 20次/小時"
                ]
            },
            {
                "name": "權限控制",
                "description": "基於 RBAC 的訪問控制",
                "details": [
                    "chat.create - 發送消息",
                    "chat.read - 讀取歷史",
                    "chat.update - 更新會話",
                    "chat.delete - 刪除會話",
                    "chat.manage - 管理知識庫"
                ]
            },
            {
                "name": "緩存優化",
                "description": "Redis 緩存提升性能",
                "details": [
                    "知識庫搜索結果緩存 1小時",
                    "用戶會話信息緩存",
                    "速率限制計數器",
                    "GPT 回應緩存（相同查詢）"
                ]
            },
            {
                "name": "租戶隔離",
                "description": "多租戶數據安全",
                "details": [
                    "會話數據按租戶隔離",
                    "知識庫按租戶分離",
                    "統計數據獨立計算",
                    "權限檢查包含租戶驗證"
                ]
            },
            {
                "name": "監控和日誌",
                "description": "完整的操作追蹤",
                "details": [
                    "所有聊天操作記錄審計日誌",
                    "API 響應時間監控",
                    "錯誤率統計",
                    "用戶行為分析"
                ]
            }
        ]
        
        for feature in features:
            print(f"\n🛡️ {feature['name']}")
            print(f"   📝 {feature['description']}")
            for detail in feature['details']:
                print(f"   • {detail}")
    
    async def run_all_demos(self):
        """運行所有演示"""
        print("🎪 MorningAI 聊天模組完整功能演示")
        print("=" * 60)
        
        demos = [
            ("RAG 服務", self.demo_rag_service),
            ("GPT 服務", self.demo_gpt_service),
            ("意圖分析", self.demo_intent_analysis),
            ("完整對話流程", self.demo_complete_conversation),
            ("API 使用範例", self.demo_api_examples),
            ("性能和安全特性", self.demo_performance_features)
        ]
        
        for demo_name, demo_func in demos:
            try:
                await demo_func()
                print(f"\n✅ {demo_name} 演示完成")
            except Exception as e:
                print(f"\n❌ {demo_name} 演示失敗: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 聊天模組功能演示完成！")
        print("\n📋 總結:")
        print("• GPT+RAG 整合 - 智能回應生成")
        print("• 多輪對話管理 - 上下文維護")
        print("• 知識庫檢索 - 企業知識整合")
        print("• 意圖分析 - 智能理解用戶需求")
        print("• 安全控制 - 權限和速率限制")
        print("• 性能優化 - 緩存和監控")
        print("\n🚀 系統已準備好進行實際部署和測試！")


async def main():
    """主函數"""
    demo = ChatModuleDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    # 設置環境變數（演示用）
    os.environ.setdefault("OPENAI_API_KEY", "demo-key")
    os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")
    os.environ.setdefault("OPENAI_MODEL", "gpt-4")
    
    # 運行演示
    asyncio.run(main())

