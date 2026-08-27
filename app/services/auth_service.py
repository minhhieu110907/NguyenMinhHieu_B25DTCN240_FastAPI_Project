from sqlalchemy.orm import Session
from datetime import datetime,timezone

from app.repositories.user_repo import UserRepository
from app.repositories.permission_repo import PermissionRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository

from app.security.password import verify_password
from app.security.jwt import jwt_service
from app.security.scopes import scopes_to_string
from app.security.generate_token import generate_refresh_token
from app.security.password import hash_password

from app.core.exceptions import InvalidCredentialsError, AccountInactiveError
from app.core.exceptions import TokenInvalidError
from app.core.exceptions import UserAlreadyExistsError

from app.schemas.auth import RegisterRequest

from app.models.users import User

from app.core.config import settings

class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.permission_repo = PermissionRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)

    def authenticate_user(self, email: str, plain_password: str) -> tuple[str, str]:
        """
        Thực thi toàn bộ luồng đăng nhập:
        1. Kiểm tra Email
        2. Kiểm tra Trạng thái tài khoản
        3. Kiểm tra Mật khẩu
        4. Gom quyền
        5. Sinh Access Token và Refresh Token
        
        -> Trả về tuple: (access_token, refresh_token)
        """
        user = self.user_repo.get_user_by_email(email)
        if not user:
            raise InvalidCredentialsError()
        
        if not user.is_active:
            raise AccountInactiveError()

        if not verify_password(plain_password, user.password_hash):
            raise InvalidCredentialsError()
        
        scopes_set = self.permission_repo.get_scopes_by_role_id(user.system_role_id)
        scopes_str = scopes_to_string(scopes_set)
        role_name = user.system_role.name if user.system_role else "USER"

        access_token, _ = jwt_service.create_access_token(
            user_id=user.id,
            role=role_name,
            scope=scopes_str
        )
        refresh_token = generate_refresh_token()
        self.refresh_token_repo.create(user_id=user.id,token_str=refresh_token,expires_days=settings.REFRESH_TOKEN_EXPIRE_DAY)

        return access_token, refresh_token

    def refresh_tokens(self, refresh_token_str: str) -> tuple[str, str]:
        """
        Luồng: Tìm Token trong DB -> Check còn sống không -> Sinh cặp mới -> Thu hồi cặp cũ.
        """
        token_record = self.refresh_token_repo.get_by_token(refresh_token_str)
        if not token_record or token_record.is_revoked:
            raise TokenInvalidError()
            
        if token_record.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            self.refresh_token_repo.revoke(refresh_token_str) 
            raise TokenInvalidError()

        user = self.user_repo.get_user_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise AccountInactiveError()

        scopes_set = self.permission_repo.get_scopes_by_role_id(user.system_role_id)
        scopes_str = scopes_to_string(scopes_set)
        role_name = user.system_role.name if user.system_role else "USER"

        new_access, _ = jwt_service.create_access_token(
            user_id=user.id, role=role_name, scope=scopes_str
        )
        new_refresh_str = generate_refresh_token()

        # Rotation
        self.refresh_token_repo.revoke(refresh_token_str)
        self.refresh_token_repo.create(user_id=user.id, token_str=new_refresh_str, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAY)

        return new_access, new_refresh_str

    def register_user(self, data: RegisterRequest) -> User:
        if self.user_repo.get_user_by_email(data.email):
            raise UserAlreadyExistsError()

        # Default system role is "user"
        new_user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
            system_role_id=2
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

