from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db

from app.security.jwt import jwt_service
from app.security.scopes import parse_scopes, has_required_scopes, Scope
from app.repositories.user_repo import UserRepository
from app.core.exceptions import TokenInvalidError, AccountInactiveError, ForbiddenError
from app.models.users import User
from app.repositories.permission_repo import PermissionRepository

security_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    
    payload = jwt_service.decode_access_token(token)
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(int(payload.sub))
    
    if not user:
        raise TokenInvalidError()
        
    if not user.is_active:
        raise AccountInactiveError()
    
    user.token_scopes = parse_scopes(payload.scope)
    
    return user

class RequireScopes:
    def __init__(self, required_scopes: set[Scope]):
        self.required_scopes = required_scopes

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not has_required_scopes(current_user.token_scopes, self.required_scopes):
            raise ForbiddenError("You do not have permission to access this resource.")
        return current_user


class RequireCurrentScopes:
    """
    Strict role checker
    """
    def __init__(self, required_scopes: set[Scope]):
        self.required_scopes = required_scopes

    def __call__(
        self, 
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        permission_repo = PermissionRepository(db)
        fresh_scopes = permission_repo.get_scopes_by_role_id(current_user.system_role_id)
        if not has_required_scopes(fresh_scopes, self.required_scopes):
            raise ForbiddenError("Your permissions have changed. You cannot do this action.")
            
        return current_user
    