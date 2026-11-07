"""Authentication service for OIDC token validation and user management"""

import httpx
from typing import Optional
from datetime import datetime, timezone
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.models.user import User, UserRole


class AuthService:
    """Service for OIDC authentication and user management"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self._jwks_cache: Optional[dict] = None
        self._jwks_fetched_at: Optional[datetime] = None

    async def _get_jwks(self) -> dict:
        """Fetch and cache JWKS from Keycloak"""
        if (
            self._jwks_cache
            and self._jwks_fetched_at
            and (datetime.now(timezone.utc) - self._jwks_fetched_at).total_seconds() < 3600
        ):
            return self._jwks_cache

        async with httpx.AsyncClient() as client:
            response = await client.get(self.settings.keycloak_jwks_url, timeout=10.0)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_fetched_at = datetime.now(timezone.utc)
            return self._jwks_cache

    async def validate_token(self, token: str) -> dict:
        """Validate OIDC access token and return claims"""
        jwks = await self._get_jwks()
        
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
            
            if not key:
                raise JWTError("No matching key found in JWKS")
            
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.settings.keycloak_client_id,
                issuer=self.settings.keycloak_issuer_url,
            )
            return claims
            
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")

    async def get_or_create_user(self, claims: dict) -> User:
        """Get existing user or create new one from token claims"""
        keycloak_id = claims.get("sub")
        if not keycloak_id:
            raise ValueError("Token missing subject claim")
        
        result = await self.db.execute(
            select(User).where(User.keycloak_id == keycloak_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.last_login = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        
        realm_roles = claims.get("realm_access", {}).get("roles", [])
        role = UserRole.VIEWER
        if "admin" in realm_roles:
            role = UserRole.ADMIN
        elif "operator" in realm_roles:
            role = UserRole.OPERATOR
        
        user = User(
            keycloak_id=keycloak_id,
            username=claims.get("preferred_username", claims.get("email", "unknown")),
            email=claims.get("email", ""),
            full_name=claims.get("name"),
            role=role,
            is_active=True,
            last_login=datetime.now(timezone.utc),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    def require_role(self, user: User, required_roles: list[UserRole]) -> None:
        """Check if user has one of the required roles"""
        if user.role not in required_roles:
            raise ValueError(f"Insufficient permissions: requires one of {[r.value for r in required_roles]}")
