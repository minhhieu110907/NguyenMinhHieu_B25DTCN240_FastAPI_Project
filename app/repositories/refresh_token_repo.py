from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken

class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, token_str: str, expires_days: int = 7) -> RefreshToken:
        """
        Create and store a new opaque refresh token in the database.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        new_token = RefreshToken(
            user_id=user_id,
            token=token_str,
            expires_at=expires_at,
            is_revoked=False
        )
        self.db.add(new_token)
        self.db.commit()
        self.db.refresh(new_token)
        return new_token

    def get_by_token(self, token_str: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token_str).first()

    def revoke(self, token_str: str) -> None:
        token_obj = self.get_by_token(token_str)
        if token_obj and not token_obj.is_revoked:
            token_obj.is_revoked = True
            self.db.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        """
        SECURITY FEATURE: Force logout from all devices.
        Revokes all active refresh tokens for a specific user ID.
        Uses bulk update for maximum database performance.
        """
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        self.db.commit()

