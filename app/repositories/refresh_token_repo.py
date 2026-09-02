from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, token_str: str, expires_days: int = 7) -> RefreshToken:
        """
        Create and stage a new opaque refresh token in the database session.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        new_token = RefreshToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at,
            is_revoked=False
        )
        self.db.add(new_token)
        self.db.flush()
        return new_token

    def get_by_token(self, token_str: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token_str).first()

    def mark_revoked(self, token_obj: RefreshToken) -> None:
        if token_obj and not token_obj.is_revoked:
            token_obj.is_revoked = True
            self.db.flush()

    def revoke_by_token_str(self, token_str: str) -> None:
        """Retrieve and revoke a token record by its token string."""
        token_obj = self.get_by_token(token_str)
        if token_obj:
            self.mark_revoked(token_obj)

    def revoke_all_for_user(self, user_id: int) -> int:
        """
        SECURITY FEATURE: Force logout from all active sessions.
        Revokes all non-revoked refresh tokens associated with a given user ID.
        """
        updated_count = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
            .update({"is_revoked": True}, synchronize_session=False)
        )
        self.db.flush()
        return updated_count