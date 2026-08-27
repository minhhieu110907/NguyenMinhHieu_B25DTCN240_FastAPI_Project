from typing import Callable
from fastapi import Request
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.schemas.auth import LoginRequest

async def get_client_ip(request: Request) -> str:
    if settings.USE_TRUSTED_PROXY:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "0.0.0.0"

def rate_limit_ip_factory(prefix: str, limit: int, window: int) -> Callable:
    async def dependency(request: Request) -> None:
        ip = await get_client_ip(request)
        key = f"rl:{prefix}:ip:{ip}"
        await check_rate_limit(key=key, limit=limit, window=window)
    return dependency

rate_limit_login_ip = rate_limit_ip_factory(
    "login", settings.RATE_LIMIT_LOGIN_IP, settings.RATE_LIMIT_LOGIN_IP_WINDOW
)
rate_limit_register_ip = rate_limit_ip_factory(
    "register", settings.RATE_LIMIT_REGISTER_IP, settings.RATE_LIMIT_REGISTER_IP_WINDOW
)
rate_limit_refresh_ip = rate_limit_ip_factory(
    "refresh", settings.RATE_LIMIT_REFRESH_IP, settings.RATE_LIMIT_REFRESH_IP_WINDOW
)

async def rate_limit_login_account(login_data: LoginRequest) -> None:
    if not login_data.email:
        return
    key = f"rl:login:account:{login_data.email.lower()}"
    await check_rate_limit(
        key=key,
        limit=settings.RATE_LIMIT_LOGIN_ACCOUNT,
        window=settings.RATE_LIMIT_LOGIN_ACCOUNT_WINDOW,
    )