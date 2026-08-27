from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.token import TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.dependencies.rate_limit import (
    rate_limit_login_ip,
    rate_limit_login_account,
    rate_limit_register_ip,
    rate_limit_refresh_ip,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(rate_limit_login_ip),
        Depends(rate_limit_login_account),
    ],
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    access_token, refresh_token = auth_service.authenticate_user(
        email=login_data.email,
        plain_password=login_data.password,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_refresh_ip)],
)
def refresh_token(
    request_data: RefreshRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    access, refresh = auth_service.refresh_tokens(request_data.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_register_ip)],
)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    new_user = auth_service.register_user(user_data)
    return UserResponse.model_validate(new_user)