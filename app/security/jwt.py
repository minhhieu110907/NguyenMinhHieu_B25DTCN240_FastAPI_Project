from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.token import AccessTokenPayload
from app.core.exceptions import TokenInvalidError

class JWTService:
    def __init__(self) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._issuer = settings.JWT_ISSUER

    def create_access_token(self, *, user_id: int, role: str, scope: str) -> tuple[str, str]:
        jti = str(uuid4())
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),
            "role": role,
            "scope": scope,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "iss": self._issuer,
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return token, jti

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                options={"require": ["sub", "role", "scope", "jti", "iat", "exp", "iss"]},
            )
            return AccessTokenPayload(**payload)
        except JWTError as exc:
            raise TokenInvalidError() from exc


jwt_service = JWTService()
