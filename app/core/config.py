from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import SettingsConfigDict,BaseSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "Project Management"
    ENVIRONMEMT: Literal["development","production","staging"] = "development"
    DEBUG: bool = False

    REDIS_URL: str = Field(...,description="redis://:password@localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = 50

    RATE_LIMIT_LOGIN_IP: int = 5
    RATE_LIMIT_LOGIN_IP_WINDOW: int = 60

    RATE_LIMIT_LOGIN_ACCOUNT: int = 5
    RATE_LIMIT_LOGIN_ACCOUNT_WINDOW: int = 60

    RATE_LIMIT_REGISTER_IP: int = 3
    RATE_LIMIT_REGISTER_IP_WINDOW: int = 60

    RATE_LIMIT_REFRESH_IP: int = 10
    RATE_LIMIT_REFRESH_IP_WINDOW: int = 60


    DATABASE_URL: str = Field(...,description="mysql+pymysql://user:pass@host:3306/lms")

    JWT_SECRET_KEY: str = Field(...,min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "prj-manager-api"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAY: int = 7

    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15


    # Redis failure policy
    RL_FAIL_MODE:str="closed"
    USE_TRUSTED_PROXY: bool = False

    @property
    def is_production(self):
        return self.ENVIRONMEMT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg]


settings = get_settings()
