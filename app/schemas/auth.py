from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.security import PASSWORD_MIN_LENGTH, PASSWORD_PATTERN, PASSWORD_POLICY_MESSAGE

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(PASSWORD_POLICY_MESSAGE)
        return v

class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)