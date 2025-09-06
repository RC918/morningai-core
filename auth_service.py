"""
Authentication Service for MorningAI Core API
Phase 3 MVP - Auth/Referral Service Implementation
"""
import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
from passlib.context import CryptContext
import asyncpg
from auth_models import (
    UserRegisterRequest, UserLoginRequest, UserRegisterResponse, 
    UserLoginResponse, TokenResponse, UserProfile, ReferralStatsResponse,
    ReferralLeaderboardResponse, UserInDB, TenantInDB, RoleInDB,
    JWTPayload, ErrorResponse, ErrorDetail
)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_referral_code(self) -> str:
        """Generate unique referral code"""
        return secrets.token_urlsafe(8).upper()[:8]
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "jti": str(uuid.uuid4())})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[JWTPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return JWTPayload(**payload)
        except jwt.PyJWTError:
            return None
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[TenantInDB]:
        """Get tenant by slug"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tenants WHERE slug = $1 AND is_active = TRUE",
                slug
            )
            if row:
                return TenantInDB(**dict(row))
            return None
    
    async def get_role_by_name(self, name: str) -> Optional[RoleInDB]:
        """Get role by name"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM roles WHERE name = $1 AND is_active = TRUE",
                name
            )
            if row:
                return RoleInDB(**dict(row))
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            if row:
                return UserInDB(**dict(row))
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
            if row:
                return UserInDB(**dict(row))
            return None
    
    async def create_user(self, request: UserRegisterRequest) -> UserRegisterResponse:
        """Register new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(request.email)
        if existing_user:
            raise ValueError("用戶已存在")
        
        # Get tenant
        tenant = await self.get_tenant_by_slug(request.tenant_slug)
        if not tenant:
            raise ValueError("租戶不存在")
        
        # Get default role (user)
        role = await self.get_role_by_name("user")
        if not role:
            raise ValueError("默認角色不存在")
        
        # Generate referral code
        referral_code = self.generate_referral_code()
        
        # Hash password
        password_hash = self.hash_password(request.password)
        
        # Create user
        user_id = uuid.uuid4()
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Insert user
                await conn.execute("""
                    INSERT INTO users (
                        id, tenant_id, email, username, display_name, 
                        password_hash, referral_code, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, user_id, tenant.id, request.email, request.email.split('@')[0], 
                    request.name, password_hash, referral_code, True)
                
                # Assign role
                await conn.execute("""
                    INSERT INTO user_roles (user_id, role_id, is_active)
                    VALUES ($1, $2, $3)
                """, user_id, role.id, True)
                
                # Handle referral if provided
                if request.referral_code:
                    referrer = await conn.fetchrow(
                        "SELECT id FROM users WHERE referral_code = $1",
                        request.referral_code
                    )
                    if referrer:
                        await conn.execute("""
                            INSERT INTO referral_relations (
                                referrer_id, referred_id, referral_code_id
                            ) VALUES ($1, $2, (
                                SELECT id FROM referral_codes 
                                WHERE code = $3 AND is_active = TRUE
                                LIMIT 1
                            ))
                        """, referrer['id'], user_id, request.referral_code)
        
        # Get created user
        user = await self.get_user_by_id(str(user_id))
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "role": "user"
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        user_profile = UserProfile(
            id=str(user.id),
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            referral_code=user.referral_code,
            is_active=user.is_active,
            email_verified=user.email_verified,
            tenant_id=str(user.tenant_id),
            role="user",
            created_at=user.created_at
        )
        
        return UserRegisterResponse(
            user=user_profile,
            tokens=tokens,
            message="註冊成功"
        )
    
    async def authenticate_user(self, request: UserLoginRequest) -> UserLoginResponse:
        """Authenticate user login"""
        # Get user
        user = await self.get_user_by_email(request.email)
        if not user or not self.verify_password(request.password, user.password_hash):
            raise ValueError("郵箱或密碼錯誤")
        
        if not user.is_active:
            raise ValueError("用戶已被禁用")
        
        # Get user role
        async with self.db_pool.acquire() as conn:
            role_row = await conn.fetchrow("""
                SELECT r.name FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = $1 AND ur.is_active = TRUE
                LIMIT 1
            """, user.id)
            
            role_name = role_row['name'] if role_row else 'user'
            
            # Update last login
            await conn.execute("""
                UPDATE users SET 
                    last_login = NOW(),
                    login_count = login_count + 1
                WHERE id = $1
            """, user.id)
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "role": role_name
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        user_profile = UserProfile(
            id=str(user.id),
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            referral_code=user.referral_code,
            is_active=user.is_active,
            email_verified=user.email_verified,
            tenant_id=str(user.tenant_id),
            role=role_name,
            created_at=user.created_at
        )
        
        return UserLoginResponse(
            user=user_profile,
            tokens=tokens,
            message="登入成功"
        )
    
    async def get_referral_stats(self, user_id: str) -> ReferralStatsResponse:
        """Get user referral statistics"""
        async with self.db_pool.acquire() as conn:
            # Get user referral code
            user_row = await conn.fetchrow(
                "SELECT referral_code FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
            
            if not user_row:
                raise ValueError("用戶不存在")
            
            # Get referral stats
            stats_row = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_referrals,
                    COUNT(CASE WHEN rr.reward_given THEN 1 END) as successful_referrals,
                    COUNT(CASE WHEN NOT rr.reward_given THEN 1 END) as pending_referrals,
                    SUM(COALESCE(rr.reward_amount, 0)) as total_rewards
                FROM referral_relations rr
                WHERE rr.referrer_id = $1
            """, uuid.UUID(user_id))
            
            # Get recent referrals
            recent_rows = await conn.fetch("""
                SELECT 
                    u.id, u.email, u.display_name as name,
                    rr.created_at as registered_at,
                    COALESCE(rr.reward_amount, 0) as reward_amount
                FROM referral_relations rr
                JOIN users u ON rr.referred_id = u.id
                WHERE rr.referrer_id = $1
                ORDER BY rr.created_at DESC
                LIMIT 10
            """, uuid.UUID(user_id))
            
            # Get leaderboard rank
            rank_row = await conn.fetchrow("""
                WITH ranked_users AS (
                    SELECT 
                        referrer_id,
                        COUNT(*) as referral_count,
                        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank
                    FROM referral_relations
                    GROUP BY referrer_id
                )
                SELECT rank FROM ranked_users WHERE referrer_id = $1
            """, uuid.UUID(user_id))
            
            from auth_models import ReferralStats, ReferralUser
            
            stats = ReferralStats(
                total_referrals=stats_row['total_referrals'] or 0,
                successful_referrals=stats_row['successful_referrals'] or 0,
                pending_referrals=stats_row['pending_referrals'] or 0,
                total_rewards=float(stats_row['total_rewards'] or 0)
            )
            
            recent_referrals = [
                ReferralUser(
                    id=str(row['id']),
                    email=row['email'],
                    name=row['name'],
                    registered_at=row['registered_at'],
                    reward_amount=float(row['reward_amount'])
                )
                for row in recent_rows
            ]
            
            return ReferralStatsResponse(
                user_id=user_id,
                referral_code=user_row['referral_code'],
                stats=stats,
                recent_referrals=recent_referrals,
                leaderboard_rank=rank_row['rank'] if rank_row else None
            )
    
    async def get_referral_leaderboard(self, limit: int = 10) -> ReferralLeaderboardResponse:
        """Get referral leaderboard"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    u.id,
                    u.display_name as name,
                    COUNT(rr.referred_id) as referral_count,
                    SUM(COALESCE(rr.reward_amount, 0)) as total_rewards,
                    ROW_NUMBER() OVER (ORDER BY COUNT(rr.referred_id) DESC) as rank
                FROM users u
                LEFT JOIN referral_relations rr ON u.id = rr.referrer_id
                GROUP BY u.id, u.display_name
                HAVING COUNT(rr.referred_id) > 0
                ORDER BY referral_count DESC
                LIMIT $1
            """, limit)
            
            total_users_row = await conn.fetchrow(
                "SELECT COUNT(DISTINCT referrer_id) as total FROM referral_relations"
            )
            
            from auth_models import ReferralLeaderboard
            
            leaderboard = [
                ReferralLeaderboard(
                    rank=row['rank'],
                    user_id=str(row['id']),
                    name=row['name'],
                    referral_count=row['referral_count'],
                    total_rewards=float(row['total_rewards'])
                )
                for row in rows
            ]
            
            return ReferralLeaderboardResponse(
                leaderboard=leaderboard,
                total_users=total_users_row['total'] or 0,
                current_user_rank=None  # Will be set by the endpoint if user is authenticated
            )

