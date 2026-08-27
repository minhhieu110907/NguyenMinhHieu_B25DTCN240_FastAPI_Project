from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AccessTokenPayload(BaseModel):
    sub: str
    role: str
    scope: str
    jti: str
    iat: int
    exp: int
    iss: str