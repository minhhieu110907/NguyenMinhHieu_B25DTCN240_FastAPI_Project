import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository

from app.security.password import verify_password, hash_password
from app.security.jwt import jwt_service
from app.security.scopes import scopes_to_string
from app.security.generate_token import generate_refresh_token

from app.core.exceptions import (
    InvalidCredentialsError,
    AccountInactiveError,
    TokenInvalidError,
    UserAlreadyExistsError,
    ForbiddenError
)
from app.schemas.auth import RegisterRequest
from app.models.users import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.permission_repo = PermissionRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)

    def authenticate_user(self, email: str, plain_password: str) -> tuple[str, str]:
        """
        Execute the full authentication workflow:
        1. Validate user existence and password hash.
        2. Verify account activation status.
        3. Resolve role-based system scopes.
        4. Issue dual tokens (Short-lived Access Token + Persistent Refresh Token).
        
        Returns:
            tuple[str, str]: (access_token, refresh_token)
        """
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(plain_password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        scopes_set = self.permission_repo.get_scopes_by_role_id(user.system_role_id)
        scopes_str = scopes_to_string(scopes_set)
        role_name = user.system_role.name if user.system_role else "USER"

        access_token, _ = jwt_service.create_access_token(
            user_id=user.id,
            role=role_name,
            scope=scopes_str
        )
        refresh_token = generate_refresh_token()

        try:
            self.refresh_token_repo.create(
                user_id=user.id,
                token_str=refresh_token,
                expires_days=settings.REFRESH_TOKEN_EXPIRE_DAY
            )
            self.db.commit()

            logger.info(f"AUDIT | User [ID: {user.id}, Email: {user.email}] logged in successfully")
            return access_token, refresh_token

        except Exception as e:
            self.db.rollback()
            logger.error(f"ERROR | Login failed for email {email}: {str(e)}")
            raise e

    def refresh_tokens(self, refresh_token_str: str) -> tuple[str, str]:
        """
        Execute token rotation with automatic reuse detection:
        1. Check token existence.
        2. If the token is already revoked, trigger a security breach protocol (revoke all user sessions).
        3. Verify token expiration.
        4. Verify user status.
        5. Atomically rotate tokens: revoke old token and issue new token pair within a single transaction.
        """
        token_record = self.refresh_token_repo.get_by_token(refresh_token_str)

        # 1. Validate token existence
        if not token_record:
            raise TokenInvalidError()

        # 2. AUTOMATIC REUSE DETECTION (RFC 6749)
        # Attempting to refresh using an already-revoked token indicates token compromise/theft.
        if token_record.is_revoked:
            self.refresh_token_repo.revoke_all_for_user(token_record.user_id)
            self.db.commit()
            logger.warning(
                f"SECURITY ALERT | Compromised refresh token reuse attempt for User [ID: {token_record.user_id}]. "
                f"All active sessions have been revoked!"
            )
            raise ForbiddenError(
                "Security breach detected: This refresh token has previously been revoked. "
                "All active sessions have been invalidated for security reasons."
            )

        # 3. Check expiration
        if token_record.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            self.refresh_token_repo.mark_revoked(token_record)
            self.db.commit()
            raise TokenInvalidError()

        # 4. Validate user status
        user = self.user_repo.get_user_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise AccountInactiveError()

        # 5. Generate new access token and rotate refresh token
        scopes_set = self.permission_repo.get_scopes_by_role_id(user.system_role_id)
        scopes_str = scopes_to_string(scopes_set)
        role_name = user.system_role.name if user.system_role else "USER"

        new_access, _ = jwt_service.create_access_token(
            user_id=user.id,
            role=role_name,
            scope=scopes_str
        )
        new_refresh_str = generate_refresh_token()

        try:
            # ATOMIC TOKEN ROTATION (Single Transaction Unit)
            self.refresh_token_repo.mark_revoked(token_record)
            self.refresh_token_repo.create(
                user_id=user.id,
                token_str=new_refresh_str,
                expires_days=settings.REFRESH_TOKEN_EXPIRE_DAY
            )
            self.db.commit()

            logger.info(f"AUDIT | User [ID: {user.id}] rotated tokens successfully")
            return new_access, new_refresh_str

        except Exception as e:
            self.db.rollback()
            logger.error(f"ERROR | Failed to rotate token for User [ID: {user.id}]: {str(e)}")
            raise e

    def logout(self, refresh_token_str: str) -> None:
        """Single-device logout: Invalidate the current session's refresh token."""
        token_record = self.refresh_token_repo.get_by_token(refresh_token_str)
        if token_record and not token_record.is_revoked:
            try:
                self.refresh_token_repo.mark_revoked(token_record)
                self.db.commit()
                logger.info(f"AUDIT | User [ID: {token_record.user_id}] logged out session")
            except Exception as e:
                self.db.rollback()
                logger.error(f"ERROR | Logout failed: {str(e)}")
                raise e

    def logout_all(self, user_id: int) -> None:
        """Global logout: Invalidate all active sessions across all devices for the target user."""
        try:
            revoked_count = self.refresh_token_repo.revoke_all_for_user(user_id)
            self.db.commit()
            logger.info(f"AUDIT | User [ID: {user_id}] logged out from all devices ({revoked_count} sessions revoked)")
        except Exception as e:
            self.db.rollback()
            logger.error(f"ERROR | Logout all failed for User [ID: {user_id}]: {str(e)}")
            raise e

    def register_user(self, data: RegisterRequest) -> User:
        """Register a new user account with default system privileges."""
        if self.user_repo.get_user_by_email(data.email):
            raise UserAlreadyExistsError()

        new_user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
            system_role_id=2  # Default system role: USER
        )
        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            logger.info(f"AUDIT | New user registered [ID: {new_user.id}, Email: {new_user.email}]")
            return new_user

        except Exception as e:
            self.db.rollback()
            logger.error(f"ERROR | Failed to register user {data.email}: {str(e)}")
            raise e