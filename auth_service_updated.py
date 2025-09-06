"""
Updated Authentication Service for MorningAI Core API
Phase 3 M1 - Compliant with OpenAPI specification
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
    UserLoginResponse, TokenData, UserData, ReferralStatsResponse
)

# Configuration from environment variables
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRES_IN", "60"))  # 1 hour default

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthServiceUpdated:
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
        return secrets.token_urlsafe(6).upper()[:8]
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({
            "exp": expire, 
            "iat": datetime.utcnow(), 
            "iss": "morningai-core-api",
            "jti": str(uuid.uuid4())
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    async def get_tenant_by_slug(self, slug: str = "morningai-demo"):
        """Get default tenant"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tenants WHERE slug = $1 AND is_active = TRUE LIMIT 1",
                slug
            )
            return dict(row) if row else None
    
    async def get_user_by_email(self, email: str):
        """Get user by email"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            return dict(row) if row else None
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        user = await self.get_user_by_email(email)
        return user is not None
    
    async def create_user(self, request: UserRegisterRequest) -> UserRegisterResponse:
        """Register new user according to OpenAPI spec"""
        # Check if user already exists (409 Conflict)
        if await self.email_exists(request.email):
            raise ValueError("EMAIL_EXISTS")
        
        # Get default tenant
        tenant = await self.get_tenant_by_slug()
        if not tenant:
            raise ValueError("TENANT_NOT_FOUND")
        
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
                """, user_id, uuid.UUID(tenant['id']), request.email, 
                    request.email.split('@')[0], request.name, 
                    password_hash, referral_code, True)
                
                # Handle referral if provided
                if request.referralCode:
                    # Find referrer by referral code
                    referrer = await conn.fetchrow(
                        "SELECT id FROM users WHERE referral_code = $1 AND is_active = TRUE",
                        request.referralCode
                    )
                    if referrer:
                        # Create referral relation
                        await conn.execute("""
                            INSERT INTO referral_relations (
                                referrer_id, referred_id, referral_code_id, created_at
                            ) VALUES ($1, $2, (
                                SELECT id FROM referral_codes 
                                WHERE code = $3 AND is_active = TRUE
                                LIMIT 1
                            ), NOW())
                        """, referrer['id'], user_id, request.referralCode)
        
        # Create JWT token
        token_data = {
            "sub": str(user_id),
            "email": request.email,
            "name": request.name
        }
        
        access_token = self.create_access_token(token_data)
        
        # Prepare response according to OpenAPI spec
        user_data = UserData(
            id=str(user_id),
            email=request.email,
            name=request.name
        )
        
        token_response = TokenData(
            accessToken=access_token,
            tokenType="Bearer",
            expiresIn=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return UserRegisterResponse(
            user=user_data,
            token=token_response
        )
    
    async def authenticate_user(self, request: UserLoginRequest) -> UserLoginResponse:
        """Authenticate user login according to OpenAPI spec"""
        # Get user
        user = await self.get_user_by_email(request.email)
        if not user:
            raise ValueError("INVALID_CREDENTIALS")
        
        # Verify password
        if not self.verify_password(request.password, user['password_hash']):
            raise ValueError("INVALID_CREDENTIALS")
        
        if not user['is_active']:
            raise ValueError("USER_INACTIVE")
        
        # Update last login
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET 
                    last_login_at = NOW(),
                    login_count = COALESCE(login_count, 0) + 1
                WHERE id = $1
            """, user['id'])
        
        # Create JWT token
        token_data = {
            "sub": str(user['id']),
            "email": user['email'],
            "name": user['display_name'] or user['username']
        }
        
        access_token = self.create_access_token(token_data)
        
        # Prepare response according to OpenAPI spec
        user_data = UserData(
            id=str(user['id']),
            email=user['email'],
            name=user['display_name'] or user['username'] or ""
        )
        
        token_response = TokenData(
            accessToken=access_token,
            tokenType="Bearer",
            expiresIn=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return UserLoginResponse(
            user=user_data,
            token=token_response
        )
    
    async def get_referral_stats(self, user_id: str, period: str = "all") -> ReferralStatsResponse:
        """Get user referral statistics according to OpenAPI spec"""
        async with self.db_pool.acquire() as conn:
            # Get total referrals
            total_row = await conn.fetchrow("""
                SELECT COUNT(*) as total_referrals
                FROM referral_relations rr
                WHERE rr.referrer_id = $1
            """, uuid.UUID(user_id))
            
            # Get unique referrers (this might be different logic based on requirements)
            unique_row = await conn.fetchrow("""
                SELECT COUNT(DISTINCT rr.referred_id) as unique_referrers
                FROM referral_relations rr
                WHERE rr.referrer_id = $1
            """, uuid.UUID(user_id))
            
            # Get recent referrals based on period
            period_filter = ""
            if period == "7d":
                period_filter = "AND rr.created_at >= NOW() - INTERVAL '7 days'"
            elif period == "30d":
                period_filter = "AND rr.created_at >= NOW() - INTERVAL '30 days'"
            
            recent_rows = await conn.fetch(f"""
                SELECT 
                    DATE(rr.created_at) as date,
                    COUNT(*) as count
                FROM referral_relations rr
                WHERE rr.referrer_id = $1 {period_filter}
                GROUP BY DATE(rr.created_at)
                ORDER BY date DESC
                LIMIT 10
            """, uuid.UUID(user_id))
            
            # Format recent data
            recent_data = [
                {"date": row['date'].isoformat(), "count": row['count']}
                for row in recent_rows
            ]
            
            return ReferralStatsResponse(
                totalReferrals=total_row['total_referrals'] or 0,
                uniqueReferrers=unique_row['unique_referrers'] or 0,
                recent=recent_data
            )
    
    async def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user info from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get('sub')
        if not user_id:
            return None
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1 AND is_active = TRUE",
                uuid.UUID(user_id)
            )
            return dict(row) if row else None

