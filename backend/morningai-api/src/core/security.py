"""
安全性和認證模組
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
import structlog

from src.core.config import settings

logger = structlog.get_logger()

# 密碼加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """生成密碼雜湊"""
    return pwd_context.hash(password)


def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
    """生成隨機字符串"""
    characters = string.ascii_letters + string.digits
    if include_symbols:
        characters += "!@#$%^&*"
    
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_referral_code(length: int = 8) -> str:
    """生成推薦碼"""
    # 使用大寫字母和數字，避免容易混淆的字符
    characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_verification_token() -> str:
    """生成驗證令牌"""
    return secrets.token_urlsafe(32)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """創建訪問令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create access token", error=str(e))
        raise


def create_refresh_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """創建刷新令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create refresh token", error=str(e))
        raise


def verify_token(token: str) -> Optional[dict]:
    """驗證令牌"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error during token verification", error=str(e))
        return None


def extract_user_id_from_token(token: str) -> Optional[str]:
    """從令牌中提取用戶ID"""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None


def is_token_expired(token: str) -> bool:
    """檢查令牌是否過期"""
    payload = verify_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.utcnow().timestamp() > exp


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """驗證密碼強度"""
    errors = []
    
    if len(password) < 8:
        errors.append("密碼長度至少需要8個字符")
    
    if not any(c.islower() for c in password):
        errors.append("密碼需要包含至少一個小寫字母")
    
    if not any(c.isupper() for c in password):
        errors.append("密碼需要包含至少一個大寫字母")
    
    if not any(c.isdigit() for c in password):
        errors.append("密碼需要包含至少一個數字")
    
    # 檢查常見弱密碼
    weak_passwords = [
        "password", "123456", "123456789", "qwerty", 
        "abc123", "password123", "admin", "root"
    ]
    
    if password.lower() in weak_passwords:
        errors.append("密碼過於簡單，請選擇更安全的密碼")
    
    return len(errors) == 0, errors


def validate_email(email: str) -> bool:
    """驗證電子郵件格式"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """清理用戶輸入"""
    if not text:
        return ""
    
    # 移除前後空白
    text = text.strip()
    
    # 限制長度
    if len(text) > max_length:
        text = text[:max_length]
    
    # 移除潛在的惡意字符
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text


def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, expected_token: str) -> bool:
    """驗證CSRF令牌"""
    return secrets.compare_digest(token, expected_token)


class SecurityHeaders:
    """安全標頭管理"""
    
    @staticmethod
    def get_security_headers() -> dict:
        """獲取安全標頭"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            )
        }


class IPWhitelist:
    """IP 白名單管理"""
    
    def __init__(self):
        self.whitelist = set()
        self.blacklist = set()
    
    def add_to_whitelist(self, ip: str) -> None:
        """添加到白名單"""
        self.whitelist.add(ip)
    
    def add_to_blacklist(self, ip: str) -> None:
        """添加到黑名單"""
        self.blacklist.add(ip)
    
    def is_allowed(self, ip: str) -> bool:
        """檢查IP是否被允許"""
        if ip in self.blacklist:
            return False
        
        if not self.whitelist:
            return True  # 如果沒有白名單，則允許所有IP
        
        return ip in self.whitelist
    
    def remove_from_whitelist(self, ip: str) -> None:
        """從白名單移除"""
        self.whitelist.discard(ip)
    
    def remove_from_blacklist(self, ip: str) -> None:
        """從黑名單移除"""
        self.blacklist.discard(ip)


# 創建全局實例
security_headers = SecurityHeaders()
ip_whitelist = IPWhitelist()

