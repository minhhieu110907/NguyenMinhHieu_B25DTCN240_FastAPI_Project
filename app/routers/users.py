from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.dependencies.dependencies import get_current_user, RequireScopes
from app.schemas.user import UserResponse
from app.security.scopes import Scope
from app.models.users import User
from app.services.user_services import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get(
    "", 
    response_model=List[UserResponse],
    dependencies=[Depends(RequireScopes({Scope.USER_READ}))]
)
def get_all_users(
    name: Optional[str] = Query(None, description="Search by name"),
    email: Optional[str] = Query(None, description="Search by email"),
    is_active: Optional[bool] = Query(None, description="Active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
        user_service = UserService(db)
        return user_service.get_list_users(name, email, is_active, skip, limit)

