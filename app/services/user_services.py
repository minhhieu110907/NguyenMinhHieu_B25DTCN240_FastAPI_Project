from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.user_repo import UserRepository
from app.models.users import User

class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def get_list_users(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        return self.user_repo.search_users(
            name=name, 
            email=email, 
            is_active=is_active, 
            skip=skip, 
            limit=limit
        )