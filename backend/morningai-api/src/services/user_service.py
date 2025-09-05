"""
用戶服務層
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import structlog

from src.models.user import User
from src.models.tenant import Tenant
from src.models.role import Role, UserRole
from src.models.audit import AuditLog
from src.core.security import get_password_hash, verify_password, generate_referral_code
from src.core.redis import cache

logger = structlog.get_logger()


class UserService:
    """用戶服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根據ID獲取用戶"""
        try:
            stmt = select(User).options(
                selectinload(User.tenant),
                selectinload(User.user_roles).selectinload(UserRole.role)
            ).where(User.id == user_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get user by ID", user_id=str(user_id), error=str(e))
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根據郵箱獲取用戶"""
        try:
            stmt = select(User).options(
                selectinload(User.tenant),
                selectinload(User.user_roles).selectinload(UserRole.role)
            ).where(User.email == email.lower())
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根據用戶名獲取用戶"""
        try:
            stmt = select(User).options(
                selectinload(User.tenant),
                selectinload(User.user_roles).selectinload(UserRole.role)
            ).where(User.username == username)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get user by username", username=username, error=str(e))
            return None
    
    async def get_user_by_referral_code(self, referral_code: str) -> Optional[User]:
        """根據推薦碼獲取用戶"""
        try:
            stmt = select(User).where(User.referral_code == referral_code)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get user by referral code", referral_code=referral_code, error=str(e))
            return None
    
    async def create_user(
        self,
        email: str,
        password: str,
        tenant_id: UUID,
        username: Optional[str] = None,
        display_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        referred_by_id: Optional[UUID] = None,
        language: str = "zh-TW",
        timezone: str = "Asia/Taipei"
    ) -> Optional[User]:
        """創建新用戶"""
        try:
            # 檢查郵箱是否已存在
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                logger.warning("Email already exists", email=email)
                return None
            
            # 檢查用戶名是否已存在
            if username:
                existing_username = await self.get_user_by_username(username)
                if existing_username:
                    logger.warning("Username already exists", username=username)
                    return None
            
            # 生成唯一的推薦碼
            referral_code = await self._generate_unique_referral_code()
            
            # 創建用戶
            user = User(
                email=email.lower(),
                username=username,
                display_name=display_name or email.split('@')[0],
                password_hash=get_password_hash(password),
                tenant_id=tenant_id,
                first_name=first_name,
                last_name=last_name,
                referred_by_id=referred_by_id,
                language=language,
                timezone=timezone,
                referral_code=referral_code,
                is_email_verified=False,
                is_active=True
            )
            
            self.db.add(user)
            await self.db.flush()  # 獲取用戶ID
            
            # 分配預設角色（user）
            await self._assign_default_role(user.id)
            
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="user_created",
                resource_type="user",
                resource_id=str(user.id),
                user_id=user.id,
                tenant_id=tenant_id,
                description=f"User created: {email}"
            )
            
            logger.info("User created successfully", user_id=str(user.id), email=email)
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create user", email=email, error=str(e))
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """驗證用戶登入"""
        try:
            user = await self.get_user_by_email(email)
            
            if not user:
                logger.warning("User not found during authentication", email=email)
                return None
            
            if not user.is_active:
                logger.warning("Inactive user attempted login", email=email)
                return None
            
            if not verify_password(password, user.password_hash):
                logger.warning("Invalid password during authentication", email=email)
                return None
            
            # 更新登入信息
            await self._update_login_info(user)
            
            logger.info("User authenticated successfully", user_id=str(user.id), email=email)
            return user
            
        except Exception as e:
            logger.error("Authentication failed", email=email, error=str(e))
            return None
    
    async def update_user(
        self,
        user_id: UUID,
        **kwargs
    ) -> Optional[User]:
        """更新用戶信息"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # 記錄舊值
            old_values = {}
            new_values = {}
            
            # 更新允許的字段
            allowed_fields = [
                'username', 'display_name', 'first_name', 'last_name',
                'bio', 'avatar_url', 'language', 'timezone'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    old_values[field] = getattr(user, field)
                    setattr(user, field, value)
                    new_values[field] = value
            
            await self.db.commit()
            
            # 記錄審計日誌
            if old_values:
                await self._create_audit_log(
                    action="user_updated",
                    resource_type="user",
                    resource_id=str(user.id),
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    description=f"User updated: {user.email}",
                    old_values=old_values,
                    new_values=new_values
                )
            
            logger.info("User updated successfully", user_id=str(user.id))
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update user", user_id=str(user_id), error=str(e))
            return None
    
    async def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str
    ) -> bool:
        """更改密碼"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 驗證舊密碼
            if not verify_password(old_password, user.password_hash):
                logger.warning("Invalid old password during password change", user_id=str(user_id))
                return False
            
            # 更新密碼
            user.password_hash = get_password_hash(new_password)
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="password_changed",
                resource_type="user",
                resource_id=str(user.id),
                user_id=user.id,
                tenant_id=user.tenant_id,
                description=f"Password changed for user: {user.email}"
            )
            
            logger.info("Password changed successfully", user_id=str(user.id))
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to change password", user_id=str(user_id), error=str(e))
            return False
    
    async def deactivate_user(self, user_id: UUID, deactivated_by: UUID) -> bool:
        """停用用戶"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = False
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="user_deactivated",
                resource_type="user",
                resource_id=str(user.id),
                user_id=deactivated_by,
                tenant_id=user.tenant_id,
                description=f"User deactivated: {user.email}"
            )
            
            logger.info("User deactivated successfully", user_id=str(user.id))
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to deactivate user", user_id=str(user_id), error=str(e))
            return False
    
    async def get_users_by_tenant(
        self,
        tenant_id: UUID,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """獲取租戶下的用戶列表"""
        try:
            # 構建查詢
            stmt = select(User).options(
                selectinload(User.user_roles).selectinload(UserRole.role)
            ).where(User.tenant_id == tenant_id)
            
            # 搜索條件
            if search:
                search_term = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        User.email.ilike(search_term),
                        User.username.ilike(search_term),
                        User.display_name.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term)
                    )
                )
            
            # 計算總數
            count_stmt = select(User.id).where(User.tenant_id == tenant_id)
            if search:
                search_term = f"%{search}%"
                count_stmt = count_stmt.where(
                    or_(
                        User.email.ilike(search_term),
                        User.username.ilike(search_term),
                        User.display_name.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term)
                    )
                )
            
            count_result = await self.db.execute(count_stmt)
            total = len(count_result.all())
            
            # 分頁
            offset = (page - 1) * size
            stmt = stmt.offset(offset).limit(size)
            
            result = await self.db.execute(stmt)
            users = result.scalars().all()
            
            return list(users), total
            
        except Exception as e:
            logger.error("Failed to get users by tenant", tenant_id=str(tenant_id), error=str(e))
            return [], 0
    
    async def _generate_unique_referral_code(self) -> str:
        """生成唯一的推薦碼"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            code = generate_referral_code()
            existing_user = await self.get_user_by_referral_code(code)
            
            if not existing_user:
                return code
        
        # 如果多次嘗試都失敗，使用更長的推薦碼
        return generate_referral_code(12)
    
    async def _assign_default_role(self, user_id: UUID) -> None:
        """分配預設角色"""
        try:
            # 獲取 user 角色
            stmt = select(Role).where(Role.name == "user")
            result = await self.db.execute(stmt)
            user_role = result.scalar_one_or_none()
            
            if user_role:
                user_role_assignment = UserRole(
                    user_id=user_id,
                    role_id=user_role.id,
                    granted_by_id=user_id,  # 自動分配
                    is_active=True
                )
                
                self.db.add(user_role_assignment)
                
        except Exception as e:
            logger.error("Failed to assign default role", user_id=str(user_id), error=str(e))
    
    async def _update_login_info(self, user: User) -> None:
        """更新登入信息"""
        try:
            from datetime import datetime
            
            user.last_login_at = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            
            await self.db.commit()
            
        except Exception as e:
            logger.error("Failed to update login info", user_id=str(user.id), error=str(e))
    
    async def _create_audit_log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        description: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None
    ) -> None:
        """創建審計日誌"""
        try:
            audit_log = AuditLog.create_log(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                tenant_id=tenant_id,
                description=description,
                old_values=old_values,
                new_values=new_values
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            
        except Exception as e:
            logger.error("Failed to create audit log", action=action, error=str(e))

