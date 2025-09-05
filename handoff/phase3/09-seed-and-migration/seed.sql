-- MorningAI Core Database Seed Data
-- Phase 3 核心模組 (MVP) 種子資料
-- 版本: 1.0.0
-- 創建時間: 2025-09-05

-- 清理現有資料（僅在開發環境使用）
-- TRUNCATE TABLE audit_logs, notification_settings, notifications, cms_content_i18n, cms_contents, 
--          chat_messages, chat_sessions, referral_relations, referral_codes, role_permissions, 
--          user_roles, permissions, roles, users, tenants RESTART IDENTITY CASCADE;

-- 1. 創建租戶資料
INSERT INTO tenants (id, name, slug, description, is_active, is_trial, settings, max_users, max_storage_mb) VALUES
(
    '550e8400-e29b-41d4-a716-446655440001',
    'MorningAI Demo',
    'morningai-demo',
    'Demo 租戶用於展示和測試 MorningAI 核心功能',
    TRUE,
    TRUE,
    '{"theme": "default", "language": "zh-TW", "timezone": "Asia/Taipei", "features": {"chat": true, "cms": true, "referral": true, "notifications": true}}',
    1000,
    5000
),
(
    '550e8400-e29b-41d4-a716-446655440002',
    'Test Company',
    'test-company',
    '測試公司租戶',
    TRUE,
    FALSE,
    '{"theme": "corporate", "language": "zh-TW", "timezone": "Asia/Taipei"}',
    500,
    2000
);

-- 2. 創建角色資料
INSERT INTO roles (id, name, display_name, description, is_active, is_system) VALUES
(
    '660e8400-e29b-41d4-a716-446655440001',
    'admin',
    '系統管理員',
    '擁有系統所有權限的超級管理員角色',
    TRUE,
    TRUE
),
(
    '660e8400-e29b-41d4-a716-446655440002',
    'manager',
    '租戶管理員',
    '單一租戶的管理員，可管理該租戶下的用戶、內容和通知',
    TRUE,
    TRUE
),
(
    '660e8400-e29b-41d4-a716-446655440003',
    'user',
    '一般用戶',
    '一般用戶角色，可使用基本功能如註冊、聊天等',
    TRUE,
    TRUE
);

-- 3. 創建權限資料
INSERT INTO permissions (id, name, display_name, description, category, is_active) VALUES
-- 用戶管理權限
('770e8400-e29b-41d4-a716-446655440001', 'user.create', '創建用戶', '可以創建新用戶', 'user', TRUE),
('770e8400-e29b-41d4-a716-446655440002', 'user.read', '查看用戶', '可以查看用戶信息', 'user', TRUE),
('770e8400-e29b-41d4-a716-446655440003', 'user.update', '更新用戶', '可以更新用戶信息', 'user', TRUE),
('770e8400-e29b-41d4-a716-446655440004', 'user.delete', '刪除用戶', '可以刪除用戶', 'user', TRUE),
('770e8400-e29b-41d4-a716-446655440005', 'user.manage_roles', '管理用戶角色', '可以分配和移除用戶角色', 'user', TRUE),

-- 聊天功能權限
('770e8400-e29b-41d4-a716-446655440006', 'chat.create', '創建聊天', '可以創建新的聊天會話', 'chat', TRUE),
('770e8400-e29b-41d4-a716-446655440007', 'chat.read', '查看聊天', '可以查看聊天記錄', 'chat', TRUE),
('770e8400-e29b-41d4-a716-446655440008', 'chat.delete', '刪除聊天', '可以刪除聊天會話', 'chat', TRUE),

-- CMS 內容管理權限
('770e8400-e29b-41d4-a716-446655440009', 'cms.create', '創建內容', '可以創建 CMS 內容', 'cms', TRUE),
('770e8400-e29b-41d4-a716-446655440010', 'cms.read', '查看內容', '可以查看 CMS 內容', 'cms', TRUE),
('770e8400-e29b-41d4-a716-446655440011', 'cms.update', '更新內容', '可以更新 CMS 內容', 'cms', TRUE),
('770e8400-e29b-41d4-a716-446655440012', 'cms.delete', '刪除內容', '可以刪除 CMS 內容', 'cms', TRUE),
('770e8400-e29b-41d4-a716-446655440013', 'cms.publish', '發布內容', '可以發布 CMS 內容', 'cms', TRUE),

-- 推薦系統權限
('770e8400-e29b-41d4-a716-446655440014', 'referral.create', '創建推薦碼', '可以創建推薦碼', 'referral', TRUE),
('770e8400-e29b-41d4-a716-446655440015', 'referral.read', '查看推薦', '可以查看推薦信息', 'referral', TRUE),
('770e8400-e29b-41d4-a716-446655440016', 'referral.manage', '管理推薦', '可以管理推薦系統', 'referral', TRUE),

-- 通知系統權限
('770e8400-e29b-41d4-a716-446655440017', 'notification.create', '創建通知', '可以創建通知', 'notification', TRUE),
('770e8400-e29b-41d4-a716-446655440018', 'notification.read', '查看通知', '可以查看通知', 'notification', TRUE),
('770e8400-e29b-41d4-a716-446655440019', 'notification.send', '發送通知', '可以發送通知', 'notification', TRUE),
('770e8400-e29b-41d4-a716-446655440020', 'notification.manage', '管理通知', '可以管理通知系統', 'notification', TRUE),

-- 系統管理權限
('770e8400-e29b-41d4-a716-446655440021', 'system.admin', '系統管理', '系統管理員權限', 'system', TRUE),
('770e8400-e29b-41d4-a716-446655440022', 'tenant.manage', '租戶管理', '可以管理租戶', 'system', TRUE),
('770e8400-e29b-41d4-a716-446655440023', 'audit.read', '查看審計日誌', '可以查看審計日誌', 'system', TRUE);

-- 4. 分配角色權限
-- admin 角色擁有所有權限
INSERT INTO role_permissions (role_id, permission_id) 
SELECT '660e8400-e29b-41d4-a716-446655440001', id FROM permissions WHERE is_active = TRUE;

-- manager 角色權限（租戶管理員）
INSERT INTO role_permissions (role_id, permission_id) VALUES
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001'), -- user.create
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440002'), -- user.read
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003'), -- user.update
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440005'), -- user.manage_roles
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440007'), -- chat.read
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440009'), -- cms.create
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440010'), -- cms.read
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440011'), -- cms.update
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440012'), -- cms.delete
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440013'), -- cms.publish
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440015'), -- referral.read
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440016'), -- referral.manage
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440017'), -- notification.create
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440018'), -- notification.read
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440019'), -- notification.send
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440020'); -- notification.manage

-- user 角色權限（一般用戶）
INSERT INTO role_permissions (role_id, permission_id) VALUES
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440002'), -- user.read (自己的信息)
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440003'), -- user.update (自己的信息)
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440006'), -- chat.create
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440007'), -- chat.read
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440008'), -- chat.delete
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440010'), -- cms.read
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440014'), -- referral.create
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440015'), -- referral.read
('660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440018'); -- notification.read

-- 5. 創建用戶資料
INSERT INTO users (id, tenant_id, email, username, display_name, password_hash, is_email_verified, is_active, is_superuser, first_name, last_name, language, timezone, referral_code) VALUES
(
    '880e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440001',
    'admin@morningai.com',
    'admin',
    '系統管理員',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', -- password: admin123
    TRUE,
    TRUE,
    TRUE,
    '系統',
    '管理員',
    'zh-TW',
    'Asia/Taipei',
    'ADMIN2025'
),
(
    '880e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440001',
    'manager@morningai.com',
    'manager',
    '租戶管理員',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', -- password: manager123
    TRUE,
    TRUE,
    FALSE,
    '租戶',
    '管理員',
    'zh-TW',
    'Asia/Taipei',
    'MGR2025'
),
(
    '880e8400-e29b-41d4-a716-446655440003',
    '550e8400-e29b-41d4-a716-446655440001',
    'user@morningai.com',
    'testuser',
    '測試用戶',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', -- password: user123
    TRUE,
    TRUE,
    FALSE,
    '測試',
    '用戶',
    'zh-TW',
    'Asia/Taipei',
    'USER2025'
),
(
    '880e8400-e29b-41d4-a716-446655440004',
    '550e8400-e29b-41d4-a716-446655440001',
    'demo@morningai.com',
    'demouser',
    'Demo 用戶',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', -- password: demo123
    TRUE,
    TRUE,
    FALSE,
    'Demo',
    '用戶',
    'zh-TW',
    'Asia/Taipei',
    'DEMO2025'
);

-- 6. 分配用戶角色
INSERT INTO user_roles (user_id, role_id, granted_by_id) VALUES
('880e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001'), -- admin -> admin role
('880e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001'), -- manager -> manager role
('880e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440001'), -- testuser -> user role
('880e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440001'); -- demouser -> user role

-- 7. 創建推薦碼資料
INSERT INTO referral_codes (id, code, owner_id, max_uses, current_uses, is_active, expires_at) VALUES
(
    '990e8400-e29b-41d4-a716-446655440001',
    'WELCOME2025',
    '880e8400-e29b-41d4-a716-446655440002',
    100,
    0,
    TRUE,
    '2025-12-31 23:59:59'
),
(
    '990e8400-e29b-41d4-a716-446655440002',
    'FRIEND50',
    '880e8400-e29b-41d4-a716-446655440003',
    50,
    0,
    TRUE,
    '2025-06-30 23:59:59'
),
(
    '990e8400-e29b-41d4-a716-446655440003',
    'DEMO100',
    '880e8400-e29b-41d4-a716-446655440004',
    NULL, -- 無限制
    0,
    TRUE,
    NULL
);

-- 8. 創建 CMS 內容資料
INSERT INTO cms_contents (id, tenant_id, author_id, slug, content_type, status, is_featured, meta_title, meta_description, category, tags, published_at, view_count) VALUES
(
    'aa0e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440001',
    '880e8400-e29b-41d4-a716-446655440002',
    'welcome-to-morningai',
    'post',
    'published',
    TRUE,
    '歡迎使用 MorningAI',
    '了解 MorningAI 的核心功能和使用方法',
    'introduction',
    '["歡迎", "介紹", "功能"]',
    CURRENT_TIMESTAMP,
    156
),
(
    'aa0e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440001',
    '880e8400-e29b-41d4-a716-446655440002',
    'how-to-use-chat',
    'post',
    'published',
    FALSE,
    '如何使用聊天功能',
    '詳細介紹 MorningAI 的 GPT+RAG 聊天功能',
    'tutorial',
    '["教學", "聊天", "GPT", "RAG"]',
    CURRENT_TIMESTAMP,
    89
),
(
    'aa0e8400-e29b-41d4-a716-446655440003',
    '550e8400-e29b-41d4-a716-446655440001',
    '880e8400-e29b-41d4-a716-446655440002',
    'referral-system-guide',
    'post',
    'draft',
    FALSE,
    '推薦系統使用指南',
    '學習如何使用推薦系統獲得獎勵',
    'tutorial',
    '["推薦", "獎勵", "教學"]',
    NULL,
    0
);

-- 9. 創建 CMS 內容多語言資料
INSERT INTO cms_content_i18n (content_id, language, title, excerpt, content, is_default) VALUES
(
    'aa0e8400-e29b-41d4-a716-446655440001',
    'zh-TW',
    '歡迎使用 MorningAI',
    '歡迎來到 MorningAI 的世界！我們為您提供最先進的 AI 助手服務。',
    '# 歡迎使用 MorningAI

歡迎來到 MorningAI 的世界！我們很高興您選擇了我們的平台。

## 主要功能

### 1. 智能聊天
- 基於 GPT-4 的先進對話系統
- 整合 RAG 技術，提供更準確的回答
- 支援多輪對話和上下文理解

### 2. 推薦系統
- 邀請朋友獲得獎勵
- 簡單易用的推薦碼系統
- 透明的獎勵機制

### 3. 內容管理
- 多語言內容支援
- 靈活的內容發布系統
- 豐富的編輯功能

### 4. 通知系統
- 多渠道通知支援（Telegram、LINE、Email）
- 個人化通知設定
- 智能推播頻率控制

## 開始使用

1. 完成帳戶註冊
2. 設定個人偏好
3. 開始與 AI 助手對話
4. 邀請朋友加入

感謝您選擇 MorningAI！',
    TRUE
),
(
    'aa0e8400-e29b-41d4-a716-446655440001',
    'en',
    'Welcome to MorningAI',
    'Welcome to the world of MorningAI! We provide you with the most advanced AI assistant services.',
    '# Welcome to MorningAI

Welcome to the world of MorningAI! We are excited that you have chosen our platform.

## Key Features

### 1. Intelligent Chat
- Advanced conversation system based on GPT-4
- Integrated RAG technology for more accurate answers
- Support for multi-turn conversations and context understanding

### 2. Referral System
- Invite friends and earn rewards
- Simple and easy-to-use referral code system
- Transparent reward mechanism

### 3. Content Management
- Multi-language content support
- Flexible content publishing system
- Rich editing features

### 4. Notification System
- Multi-channel notification support (Telegram, LINE, Email)
- Personalized notification settings
- Smart push frequency control

## Getting Started

1. Complete account registration
2. Set personal preferences
3. Start chatting with AI assistant
4. Invite friends to join

Thank you for choosing MorningAI!',
    FALSE
),
(
    'aa0e8400-e29b-41d4-a716-446655440002',
    'zh-TW',
    '如何使用聊天功能',
    '詳細介紹 MorningAI 的 GPT+RAG 聊天功能使用方法。',
    '# 如何使用聊天功能

MorningAI 的聊天功能結合了最新的 GPT-4 技術和 RAG（檢索增強生成）系統，為您提供智能、準確的對話體驗。

## 開始聊天

1. 點擊「新建聊天」按鈕
2. 輸入您的問題或話題
3. AI 助手會根據上下文提供回答

## 功能特色

### GPT+RAG 技術
- **GPT-4 基礎**：使用最先進的語言模型
- **RAG 增強**：結合知識庫提供更準確的信息
- **Fallback 機制**：確保始終有回應

### 對話管理
- **會話記錄**：自動保存聊天歷史
- **上下文理解**：記住對話內容
- **多輪對話**：支援複雜的對話流程

## 使用技巧

1. **明確問題**：越具體的問題，回答越準確
2. **提供背景**：適當的背景信息有助於理解
3. **分步提問**：複雜問題可以分步驟詢問

## 注意事項

- 聊天記錄會被安全保存
- 支援多語言對話
- 回應時間通常在 2-5 秒內

開始您的 AI 對話之旅吧！',
    TRUE
);

-- 10. 創建通知設置資料
INSERT INTO notification_settings (user_id, notification_type, telegram_enabled, line_enabled, email_enabled, push_enabled, max_per_day, max_per_week) VALUES
('880e8400-e29b-41d4-a716-446655440001', 'system', TRUE, TRUE, TRUE, TRUE, 20, 10),
('880e8400-e29b-41d4-a716-446655440001', 'referral', TRUE, TRUE, TRUE, TRUE, 10, 5),
('880e8400-e29b-41d4-a716-446655440002', 'system', TRUE, TRUE, TRUE, TRUE, 15, 7),
('880e8400-e29b-41d4-a716-446655440002', 'referral', TRUE, TRUE, TRUE, TRUE, 10, 5),
('880e8400-e29b-41d4-a716-446655440002', 'cms', TRUE, TRUE, TRUE, TRUE, 10, 5),
('880e8400-e29b-41d4-a716-446655440003', 'system', TRUE, TRUE, TRUE, TRUE, 10, 3),
('880e8400-e29b-41d4-a716-446655440003', 'referral', TRUE, TRUE, TRUE, TRUE, 5, 3),
('880e8400-e29b-41d4-a716-446655440004', 'system', TRUE, TRUE, TRUE, TRUE, 10, 3),
('880e8400-e29b-41d4-a716-446655440004', 'referral', TRUE, TRUE, TRUE, TRUE, 5, 3);

-- 11. 創建示例通知資料
INSERT INTO notifications (id, tenant_id, user_id, sender_id, title, content, notification_type, priority, channels, status, is_read, sent_at) VALUES
(
    'bb0e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440001',
    '880e8400-e29b-41d4-a716-446655440003',
    '880e8400-e29b-41d4-a716-446655440001',
    '歡迎加入 MorningAI！',
    '歡迎您加入 MorningAI 平台！我們為您準備了豐富的功能，包括智能聊天、推薦系統等。快來探索吧！',
    'system',
    'normal',
    '["email", "push"]',
    'sent',
    FALSE,
    CURRENT_TIMESTAMP
),
(
    'bb0e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440001',
    '880e8400-e29b-41d4-a716-446655440004',
    '880e8400-e29b-41d4-a716-446655440001',
    '歡迎加入 MorningAI！',
    '歡迎您加入 MorningAI 平台！我們為您準備了豐富的功能，包括智能聊天、推薦系統等。快來探索吧！',
    'system',
    'normal',
    '["email", "push"]',
    'sent',
    TRUE,
    CURRENT_TIMESTAMP
);

-- 12. 創建示例聊天會話資料
INSERT INTO chat_sessions (id, user_id, title, context, is_active, message_count) VALUES
(
    'cc0e8400-e29b-41d4-a716-446655440001',
    '880e8400-e29b-41d4-a716-446655440003',
    '關於 MorningAI 的問題',
    '{"topic": "platform_introduction", "language": "zh-TW"}',
    TRUE,
    4
),
(
    'cc0e8400-e29b-41d4-a716-446655440002',
    '880e8400-e29b-41d4-a716-446655440004',
    '推薦系統諮詢',
    '{"topic": "referral_system", "language": "zh-TW"}',
    TRUE,
    2
);

-- 13. 創建示例聊天消息資料
INSERT INTO chat_messages (session_id, content, role, model, tokens_used, rag_sources, confidence_score, is_fallback, processing_time_ms) VALUES
(
    'cc0e8400-e29b-41d4-a716-446655440001',
    '你好！我想了解 MorningAI 平台有哪些功能？',
    'user',
    NULL,
    NULL,
    NULL,
    NULL,
    FALSE,
    NULL
),
(
    'cc0e8400-e29b-41d4-a716-446655440001',
    '您好！很高興為您介紹 MorningAI 平台。我們的平台主要提供以下核心功能：

1. **智能聊天系統**：基於 GPT-4 和 RAG 技術的先進對話系統
2. **推薦系統**：邀請朋友加入並獲得獎勵
3. **內容管理系統**：支援多語言的內容創建和管理
4. **通知系統**：多渠道的智能通知服務

您對哪個功能特別感興趣呢？我可以為您詳細介紹。',
    'assistant',
    'gpt-4',
    245,
    '[{"source": "platform_docs", "relevance": 0.95}]',
    0.95,
    FALSE,
    1250
),
(
    'cc0e8400-e29b-41d4-a716-446655440001',
    '推薦系統是如何運作的？',
    'user',
    NULL,
    NULL,
    NULL,
    NULL,
    FALSE,
    NULL
),
(
    'cc0e8400-e29b-41d4-a716-446655440001',
    '我們的推薦系統設計得非常簡單易用：

**運作流程：**
1. 每位用戶都會獲得專屬的推薦碼
2. 分享推薦碼給朋友
3. 朋友使用推薦碼註冊時，雙方都能獲得獎勵

**特色功能：**
- 推薦碼可設定使用次數限制
- 支援獎勵追蹤和統計
- 防止重複使用機制
- 透明的獎勵發放系統

您的推薦碼是 "USER2025"，可以開始邀請朋友加入了！',
    'assistant',
    'gpt-4',
    198,
    '[{"source": "referral_docs", "relevance": 0.92}]',
    0.92,
    FALSE,
    1100
),
(
    'cc0e8400-e29b-41d4-a716-446655440002',
    '我想了解推薦系統的獎勵機制',
    'user',
    NULL,
    NULL,
    NULL,
    NULL,
    FALSE,
    NULL
),
(
    'cc0e8400-e29b-41d4-a716-446655440002',
    '關於推薦系統的獎勵機制，我們採用雙向獎勵模式：

**推薦者獎勵：**
- 每成功推薦一位新用戶，獲得積分獎勵
- 累積推薦數量可解鎖更多特權

**被推薦者獎勵：**
- 使用推薦碼註冊即可獲得新手獎勵
- 享受平台功能的優先體驗權

**獎勵發放：**
- 自動檢測推薦關係
- 即時發放獎勵
- 可在個人中心查看獎勵記錄

您的推薦碼 "DEMO2025" 沒有使用次數限制，可以盡情分享！',
    'assistant',
    'gpt-4',
    176,
    '[{"source": "reward_system", "relevance": 0.88}]',
    0.88,
    FALSE,
    980
);

-- 14. 記錄種子資料創建的審計日誌
INSERT INTO audit_logs (action, resource_type, description, success, metadata) VALUES
('seed_data_creation', 'system', 'Phase 3 核心模組種子資料創建完成', TRUE, 
 '{"tenants": 2, "users": 4, "roles": 3, "permissions": 23, "referral_codes": 3, "cms_contents": 3, "notifications": 2, "chat_sessions": 2, "chat_messages": 6}');

-- 15. 更新統計信息
UPDATE referral_codes SET current_uses = 0 WHERE id IN ('990e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440003');
UPDATE chat_sessions SET message_count = (SELECT COUNT(*) FROM chat_messages WHERE session_id = chat_sessions.id);

-- 種子資料創建完成
-- 
-- 創建的測試帳戶：
-- 1. admin@morningai.com / admin123 (系統管理員)
-- 2. manager@morningai.com / manager123 (租戶管理員)  
-- 3. user@morningai.com / user123 (一般用戶)
-- 4. demo@morningai.com / demo123 (Demo 用戶)
--
-- 測試推薦碼：
-- 1. WELCOME2025 (manager 擁有，限制 100 次使用)
-- 2. FRIEND50 (testuser 擁有，限制 50 次使用)
-- 3. DEMO100 (demouser 擁有，無限制使用)
--
-- 可以使用這些帳戶和推薦碼來測試完整的註冊和推薦流程。

