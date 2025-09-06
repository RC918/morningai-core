"""
應用程序配置設置
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """應用程序設置"""
    
    # 基本配置
    APP_NAME: str = Field(default="MorningAI Core", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(env="SECRET_KEY")
    
    # 數據庫配置
    DATABASE_URL: str = Field(env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_TIMEOUT: int = Field(default=30, env="DATABASE_TIMEOUT")
    
    # Redis 配置
    REDIS_URL: str = Field(env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")
    
    # JWT 配置
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # 外部 API 配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    OPENAI_MODEL: str = Field(default="gpt-4", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = Field(default=None, env="LINE_CHANNEL_ACCESS_TOKEN")
    LINE_CHANNEL_SECRET: Optional[str] = Field(default=None, env="LINE_CHANNEL_SECRET")
    LINE_WEBHOOK_URL: Optional[str] = Field(default=None, env="LINE_WEBHOOK_URL")
    
    # CORS 配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    ALLOWED_HOSTS: List[str] = Field(
        default=[
            "api.morningai.me",
            "admin.morningai.me", 
            "morning-ai-api.onrender.com",
            "localhost",
            "127.0.0.1"
        ], 
        env="ALLOWED_HOSTS"
    )
    
    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # 文件上傳配置
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # 電子郵件配置
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    EMAIL_FROM_NAME: str = Field(default="MorningAI", env="EMAIL_FROM_NAME")
    EMAIL_FROM_ADDRESS: str = Field(default="noreply@morningai.com", env="EMAIL_FROM_ADDRESS")
    
    # 監控配置
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # 功能開關
    FEATURE_CHAT_ENABLED: bool = Field(default=True, env="FEATURE_CHAT_ENABLED")
    FEATURE_REFERRAL_ENABLED: bool = Field(default=True, env="FEATURE_REFERRAL_ENABLED")
    FEATURE_CMS_ENABLED: bool = Field(default=True, env="FEATURE_CMS_ENABLED")
    FEATURE_NOTIFICATIONS_ENABLED: bool = Field(default=True, env="FEATURE_NOTIFICATIONS_ENABLED")
    
    # 文檔配置
    DOCS_ENABLED: bool = Field(default=True, env="DOCS_ENABLED")
    
    # 通知配置
    NOTIFICATION_MAX_PER_WEEK: int = Field(default=3, env="NOTIFICATION_MAX_PER_WEEK")
    NOTIFICATION_COOLDOWN_HOURS: int = Field(default=24, env="NOTIFICATION_COOLDOWN_HOURS")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """解析 CORS 來源"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """解析允許的主機"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.APP_ENV == "production"
    
    @property
    def is_development(self) -> bool:
        """是否為開發環境"""
        return self.APP_ENV == "development"
    
    @property
    def is_testing(self) -> bool:
        """是否為測試環境"""
        return self.APP_ENV == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 創建全局設置實例
settings = Settings()

