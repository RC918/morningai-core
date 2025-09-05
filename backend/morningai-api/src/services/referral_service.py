"""
推薦系統服務層
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import structlog

from src.models.referral import ReferralCode, ReferralRelation
from src.models.user import User
from src.models.audit import AuditLog
from src.core.security import generate_referral_code
from src.core.redis import cache, rate_limiter

logger = structlog.get_logger()


class ReferralService:
    """推薦系統服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_referral_code_by_code(self, code: str) -> Optional[ReferralCode]:
        """根據推薦碼獲取推薦碼記錄"""
        try:
            stmt = select(ReferralCode).options(
                selectinload(ReferralCode.owner)
            ).where(ReferralCode.code == code)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get referral code", code=code, error=str(e))
            return None
    
    async def get_referral_code_by_id(self, referral_code_id: UUID) -> Optional[ReferralCode]:
        """根據ID獲取推薦碼記錄"""
        try:
            stmt = select(ReferralCode).options(
                selectinload(ReferralCode.owner)
            ).where(ReferralCode.id == referral_code_id)
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get referral code by ID", referral_code_id=str(referral_code_id), error=str(e))
            return None
    
    async def create_referral_code(
        self,
        owner_id: UUID,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        custom_code: Optional[str] = None
    ) -> Optional[ReferralCode]:
        """創建推薦碼"""
        try:
            # 生成推薦碼
            if custom_code:
                # 檢查自定義推薦碼是否已存在
                existing_code = await self.get_referral_code_by_code(custom_code)
                if existing_code:
                    logger.warning("Custom referral code already exists", code=custom_code)
                    return None
                code = custom_code
            else:
                code = await self._generate_unique_referral_code()
            
            # 創建推薦碼記錄
            referral_code = ReferralCode(
                code=code,
                owner_id=owner_id,
                max_uses=max_uses,
                expires_at=expires_at,
                is_active=True
            )
            
            self.db.add(referral_code)
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="referral_code_created",
                resource_type="referral_code",
                resource_id=str(referral_code.id),
                user_id=owner_id,
                description=f"Referral code created: {code}"
            )
            
            logger.info("Referral code created successfully", 
                       referral_code_id=str(referral_code.id), code=code)
            return referral_code
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create referral code", owner_id=str(owner_id), error=str(e))
            return None
    
    async def use_referral_code(
        self,
        code: str,
        referred_user_id: UUID,
        reward_amount: Optional[int] = None
    ) -> tuple[bool, str]:
        """使用推薦碼"""
        try:
            # 檢查速率限制
            rate_key = f"referral_use:{referred_user_id}"
            allowed, _ = await rate_limiter.is_allowed(rate_key, limit=5, window=3600)
            
            if not allowed:
                return False, "推薦碼使用過於頻繁，請稍後再試"
            
            # 獲取推薦碼
            referral_code = await self.get_referral_code_by_code(code)
            if not referral_code:
                return False, "推薦碼不存在"
            
            # 檢查推薦碼是否可用
            if not referral_code.can_be_used:
                if not referral_code.is_active:
                    return False, "推薦碼已停用"
                elif referral_code.is_expired:
                    return False, "推薦碼已過期"
                elif referral_code.is_exhausted:
                    return False, "推薦碼使用次數已達上限"
                else:
                    return False, "推薦碼不可用"
            
            # 檢查是否為自己的推薦碼
            if referral_code.owner_id == referred_user_id:
                return False, "不能使用自己的推薦碼"
            
            # 檢查用戶是否已經被推薦過
            existing_relation = await self._get_user_referral_relation(referred_user_id)
            if existing_relation:
                return False, "您已經使用過推薦碼"
            
            # 創建推薦關係
            referral_relation = ReferralRelation(
                referrer_id=referral_code.owner_id,
                referred_id=referred_user_id,
                referral_code_id=referral_code.id,
                reward_amount=reward_amount,
                reward_given=False
            )
            
            self.db.add(referral_relation)
            
            # 更新推薦碼使用次數
            referral_code.current_uses += 1
            
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="referral_code_used",
                resource_type="referral_relation",
                resource_id=str(referral_relation.id),
                user_id=referred_user_id,
                description=f"Referral code used: {code}"
            )
            
            logger.info("Referral code used successfully", 
                       code=code, referred_user_id=str(referred_user_id))
            
            return True, "推薦碼使用成功"
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to use referral code", code=code, error=str(e))
            return False, "推薦碼使用失敗"
    
    async def get_user_referral_stats(self, user_id: UUID) -> Dict[str, Any]:
        """獲取用戶推薦統計"""
        try:
            # 獲取用戶的推薦碼
            stmt = select(ReferralCode).where(ReferralCode.owner_id == user_id)
            result = await self.db.execute(stmt)
            referral_codes = result.scalars().all()
            
            # 獲取推薦關係統計
            referral_stats_stmt = select(
                func.count(ReferralRelation.id).label('total_referrals'),
                func.count(ReferralRelation.id).filter(
                    ReferralRelation.reward_given == True
                ).label('rewarded_referrals'),
                func.sum(ReferralRelation.reward_amount).label('total_rewards')
            ).where(ReferralRelation.referrer_id == user_id)
            
            stats_result = await self.db.execute(referral_stats_stmt)
            stats = stats_result.first()
            
            # 獲取最近的推薦記錄
            recent_referrals_stmt = select(ReferralRelation).options(
                selectinload(ReferralRelation.referred),
                selectinload(ReferralRelation.referral_code)
            ).where(
                ReferralRelation.referrer_id == user_id
            ).order_by(
                ReferralRelation.created_at.desc()
            ).limit(10)
            
            recent_result = await self.db.execute(recent_referrals_stmt)
            recent_referrals = recent_result.scalars().all()
            
            return {
                "referral_codes": [code.to_dict() for code in referral_codes],
                "total_referrals": stats.total_referrals or 0,
                "rewarded_referrals": stats.rewarded_referrals or 0,
                "total_rewards": stats.total_rewards or 0,
                "recent_referrals": [relation.to_dict() for relation in recent_referrals]
            }
            
        except Exception as e:
            logger.error("Failed to get user referral stats", user_id=str(user_id), error=str(e))
            return {
                "referral_codes": [],
                "total_referrals": 0,
                "rewarded_referrals": 0,
                "total_rewards": 0,
                "recent_referrals": []
            }
    
    async def get_referral_leaderboard(
        self,
        tenant_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """獲取推薦排行榜"""
        try:
            # 構建查詢
            stmt = select(
                User.id,
                User.display_name,
                User.email,
                func.count(ReferralRelation.id).label('referral_count'),
                func.sum(ReferralRelation.reward_amount).label('total_rewards')
            ).select_from(
                User
            ).join(
                ReferralRelation, User.id == ReferralRelation.referrer_id
            ).group_by(
                User.id, User.display_name, User.email
            ).order_by(
                func.count(ReferralRelation.id).desc()
            ).limit(limit)
            
            # 如果指定租戶，添加租戶過濾
            if tenant_id:
                stmt = stmt.where(User.tenant_id == tenant_id)
            
            result = await self.db.execute(stmt)
            leaderboard = result.all()
            
            return [
                {
                    "user_id": str(row.id),
                    "display_name": row.display_name,
                    "email": row.email,
                    "referral_count": row.referral_count,
                    "total_rewards": row.total_rewards or 0
                }
                for row in leaderboard
            ]
            
        except Exception as e:
            logger.error("Failed to get referral leaderboard", error=str(e))
            return []
    
    async def update_referral_code(
        self,
        referral_code_id: UUID,
        **kwargs
    ) -> Optional[ReferralCode]:
        """更新推薦碼"""
        try:
            referral_code = await self.get_referral_code_by_id(referral_code_id)
            if not referral_code:
                return None
            
            # 記錄舊值
            old_values = {}
            new_values = {}
            
            # 更新允許的字段
            allowed_fields = ['max_uses', 'expires_at', 'is_active']
            
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(referral_code, field):
                    old_values[field] = getattr(referral_code, field)
                    setattr(referral_code, field, value)
                    new_values[field] = value
            
            await self.db.commit()
            
            # 記錄審計日誌
            if old_values:
                await self._create_audit_log(
                    action="referral_code_updated",
                    resource_type="referral_code",
                    resource_id=str(referral_code.id),
                    user_id=referral_code.owner_id,
                    description=f"Referral code updated: {referral_code.code}",
                    old_values=old_values,
                    new_values=new_values
                )
            
            logger.info("Referral code updated successfully", 
                       referral_code_id=str(referral_code.id))
            return referral_code
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update referral code", 
                        referral_code_id=str(referral_code_id), error=str(e))
            return None
    
    async def deactivate_referral_code(
        self,
        referral_code_id: UUID,
        deactivated_by: UUID
    ) -> bool:
        """停用推薦碼"""
        try:
            referral_code = await self.get_referral_code_by_id(referral_code_id)
            if not referral_code:
                return False
            
            referral_code.is_active = False
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="referral_code_deactivated",
                resource_type="referral_code",
                resource_id=str(referral_code.id),
                user_id=deactivated_by,
                description=f"Referral code deactivated: {referral_code.code}"
            )
            
            logger.info("Referral code deactivated successfully", 
                       referral_code_id=str(referral_code.id))
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to deactivate referral code", 
                        referral_code_id=str(referral_code_id), error=str(e))
            return False
    
    async def give_referral_reward(
        self,
        referral_relation_id: UUID,
        reward_amount: int
    ) -> bool:
        """發放推薦獎勵"""
        try:
            stmt = select(ReferralRelation).where(ReferralRelation.id == referral_relation_id)
            result = await self.db.execute(stmt)
            relation = result.scalar_one_or_none()
            
            if not relation:
                return False
            
            if relation.reward_given:
                logger.warning("Reward already given", referral_relation_id=str(referral_relation_id))
                return False
            
            relation.reward_given = True
            relation.reward_amount = reward_amount
            
            await self.db.commit()
            
            # 記錄審計日誌
            await self._create_audit_log(
                action="referral_reward_given",
                resource_type="referral_relation",
                resource_id=str(relation.id),
                user_id=relation.referrer_id,
                description=f"Referral reward given: {reward_amount}"
            )
            
            logger.info("Referral reward given successfully", 
                       referral_relation_id=str(referral_relation_id), 
                       reward_amount=reward_amount)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to give referral reward", 
                        referral_relation_id=str(referral_relation_id), error=str(e))
            return False
    
    async def _generate_unique_referral_code(self) -> str:
        """生成唯一的推薦碼"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            code = generate_referral_code()
            existing_code = await self.get_referral_code_by_code(code)
            
            if not existing_code:
                return code
        
        # 如果多次嘗試都失敗，使用更長的推薦碼
        return generate_referral_code(12)
    
    async def _get_user_referral_relation(self, user_id: UUID) -> Optional[ReferralRelation]:
        """獲取用戶的推薦關係"""
        try:
            stmt = select(ReferralRelation).where(ReferralRelation.referred_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get user referral relation", user_id=str(user_id), error=str(e))
            return None
    
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

