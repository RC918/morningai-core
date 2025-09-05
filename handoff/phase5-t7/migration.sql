-- MorningAI Core Database Migration Script
-- Phase 3 核心模組 (MVP) 資料庫結構
-- 版本: 1.0.0
-- 創建時間: 2025-09-05

-- 啟用 UUID 擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 創建租戶表
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_trial BOOLEAN DEFAULT TRUE,
    settings JSON,
    max_users INTEGER DEFAULT 100,
    max_storage_mb INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建用戶表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    display_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    language VARCHAR(10) DEFAULT 'zh-TW',
    timezone VARCHAR(50) DEFAULT 'Asia/Taipei',
    referral_code VARCHAR(20) UNIQUE,
    referred_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建角色表
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建權限表
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建用戶角色關聯表
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, role_id)
);

-- 創建角色權限關聯表
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(role_id, permission_id)
);

-- 創建推薦碼表
CREATE TABLE referral_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建推薦關係表
CREATE TABLE referral_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referred_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referral_code_id UUID NOT NULL REFERENCES referral_codes(id) ON DELETE CASCADE,
    reward_given BOOLEAN DEFAULT FALSE,
    reward_amount INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(referred_id) -- 每個用戶只能被推薦一次
);

-- 創建聊天會話表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    context JSON,
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建聊天消息表
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    model VARCHAR(50),
    tokens_used INTEGER,
    rag_sources JSON,
    confidence_score FLOAT,
    is_fallback BOOLEAN DEFAULT FALSE,
    processing_time_ms INTEGER,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建 CMS 內容表
CREATE TABLE cms_contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'post',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    is_featured BOOLEAN DEFAULT FALSE,
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords TEXT,
    sort_order INTEGER DEFAULT 0,
    category VARCHAR(100),
    tags JSON,
    published_at TIMESTAMP,
    scheduled_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, slug)
);

-- 創建 CMS 內容多語言表
CREATE TABLE cms_content_i18n (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES cms_contents(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_id, language)
);

-- 創建通知表
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL 表示廣播通知
    sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    channels JSON DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    is_read BOOLEAN DEFAULT FALSE,
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    external_ids JSON,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建通知設置表
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    telegram_enabled BOOLEAN DEFAULT TRUE,
    telegram_chat_id VARCHAR(100),
    line_enabled BOOLEAN DEFAULT TRUE,
    line_user_id VARCHAR(100),
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    max_per_day INTEGER DEFAULT 10,
    max_per_week INTEGER DEFAULT 3,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, notification_type)
);

-- 創建審計日誌表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    description TEXT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(100),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引以提升查詢性能

-- 用戶表索引
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_users_referred_by_id ON users(referred_by_id);
CREATE INDEX idx_users_is_active ON users(is_active);

-- 用戶角色關聯表索引
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- 角色權限關聯表索引
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);

-- 推薦碼表索引
CREATE INDEX idx_referral_codes_owner_id ON referral_codes(owner_id);
CREATE INDEX idx_referral_codes_code ON referral_codes(code);
CREATE INDEX idx_referral_codes_is_active ON referral_codes(is_active);

-- 推薦關係表索引
CREATE INDEX idx_referral_relations_referrer_id ON referral_relations(referrer_id);
CREATE INDEX idx_referral_relations_referred_id ON referral_relations(referred_id);
CREATE INDEX idx_referral_relations_referral_code_id ON referral_relations(referral_code_id);

-- 聊天會話表索引
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_is_active ON chat_sessions(is_active);

-- 聊天消息表索引
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);

-- CMS 內容表索引
CREATE INDEX idx_cms_contents_tenant_id ON cms_contents(tenant_id);
CREATE INDEX idx_cms_contents_author_id ON cms_contents(author_id);
CREATE INDEX idx_cms_contents_slug ON cms_contents(slug);
CREATE INDEX idx_cms_contents_status ON cms_contents(status);
CREATE INDEX idx_cms_contents_content_type ON cms_contents(content_type);
CREATE INDEX idx_cms_contents_published_at ON cms_contents(published_at);

-- CMS 內容多語言表索引
CREATE INDEX idx_cms_content_i18n_content_id ON cms_content_i18n(content_id);
CREATE INDEX idx_cms_content_i18n_language ON cms_content_i18n(language);

-- 通知表索引
CREATE INDEX idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_sender_id ON notifications(sender_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_notification_type ON notifications(notification_type);
CREATE INDEX idx_notifications_scheduled_at ON notifications(scheduled_at);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- 通知設置表索引
CREATE INDEX idx_notification_settings_user_id ON notification_settings(user_id);
CREATE INDEX idx_notification_settings_notification_type ON notification_settings(notification_type);

-- 審計日誌表索引
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- 創建更新時間戳的觸發器函數
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 為需要自動更新 updated_at 的表創建觸發器
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_permissions_updated_at BEFORE UPDATE ON permissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_referral_codes_updated_at BEFORE UPDATE ON referral_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cms_contents_updated_at BEFORE UPDATE ON cms_contents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cms_content_i18n_updated_at BEFORE UPDATE ON cms_content_i18n FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_settings_updated_at BEFORE UPDATE ON notification_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 創建視圖以簡化常用查詢

-- 用戶完整信息視圖（包含租戶和角色信息）
CREATE VIEW user_details AS
SELECT 
    u.id,
    u.email,
    u.username,
    u.display_name,
    u.first_name,
    u.last_name,
    u.is_active,
    u.is_superuser,
    u.language,
    u.timezone,
    u.referral_code,
    u.login_count,
    u.last_login_at,
    u.created_at,
    t.name as tenant_name,
    t.slug as tenant_slug,
    t.is_active as tenant_is_active,
    ARRAY_AGG(DISTINCT r.name) as roles,
    ARRAY_AGG(DISTINCT p.name) as permissions
FROM users u
LEFT JOIN tenants t ON u.tenant_id = t.id
LEFT JOIN user_roles ur ON u.id = ur.user_id AND ur.is_active = TRUE
LEFT JOIN roles r ON ur.role_id = r.id AND r.is_active = TRUE
LEFT JOIN role_permissions rp ON r.id = rp.role_id AND rp.is_active = TRUE
LEFT JOIN permissions p ON rp.permission_id = p.id AND p.is_active = TRUE
GROUP BY u.id, t.id;

-- 推薦統計視圖
CREATE VIEW referral_stats AS
SELECT 
    u.id as user_id,
    u.email,
    u.referral_code,
    COUNT(rr.referred_id) as total_referrals,
    COUNT(CASE WHEN rr.reward_given THEN 1 END) as rewarded_referrals,
    SUM(COALESCE(rr.reward_amount, 0)) as total_rewards
FROM users u
LEFT JOIN referral_relations rr ON u.id = rr.referrer_id
GROUP BY u.id;

-- CMS 內容統計視圖
CREATE VIEW cms_content_stats AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    COUNT(c.id) as total_contents,
    COUNT(CASE WHEN c.status = 'published' THEN 1 END) as published_contents,
    COUNT(CASE WHEN c.status = 'draft' THEN 1 END) as draft_contents,
    SUM(c.view_count) as total_views
FROM tenants t
LEFT JOIN cms_contents c ON t.id = c.tenant_id
GROUP BY t.id;

-- 通知統計視圖
CREATE VIEW notification_stats AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    COUNT(n.id) as total_notifications,
    COUNT(CASE WHEN n.status = 'sent' THEN 1 END) as sent_notifications,
    COUNT(CASE WHEN n.status = 'failed' THEN 1 END) as failed_notifications,
    COUNT(CASE WHEN n.status = 'pending' THEN 1 END) as pending_notifications
FROM tenants t
LEFT JOIN notifications n ON t.id = n.tenant_id
GROUP BY t.id;

-- 添加註釋
COMMENT ON TABLE tenants IS '租戶表 - 支援多租戶架構';
COMMENT ON TABLE users IS '用戶表 - 包含基本用戶信息和推薦關係';
COMMENT ON TABLE roles IS '角色表 - RBAC 系統的角色定義';
COMMENT ON TABLE permissions IS '權限表 - RBAC 系統的權限定義';
COMMENT ON TABLE user_roles IS '用戶角色關聯表 - 多對多關係';
COMMENT ON TABLE role_permissions IS '角色權限關聯表 - 多對多關係';
COMMENT ON TABLE referral_codes IS '推薦碼表 - 管理推薦碼的生成和使用';
COMMENT ON TABLE referral_relations IS '推薦關係表 - 記錄推薦關係和獎勵';
COMMENT ON TABLE chat_sessions IS '聊天會話表 - GPT+RAG 聊天功能';
COMMENT ON TABLE chat_messages IS '聊天消息表 - 存儲聊天記錄和 AI 回應';
COMMENT ON TABLE cms_contents IS 'CMS 內容表 - 多語言內容管理';
COMMENT ON TABLE cms_content_i18n IS 'CMS 內容多語言表 - 支援多語言內容';
COMMENT ON TABLE notifications IS '通知表 - 病毒式推播通知系統';
COMMENT ON TABLE notification_settings IS '通知設置表 - 用戶通知偏好設置';
COMMENT ON TABLE audit_logs IS '審計日誌表 - 記錄所有重要操作';

-- 遷移完成
INSERT INTO audit_logs (action, resource_type, description, success, metadata)
VALUES (
    'database_migration',
    'system',
    'Phase 3 核心模組數據庫遷移完成',
    TRUE,
    '{"version": "1.0.0", "tables_created": 16, "indexes_created": 30, "views_created": 4}'
);

