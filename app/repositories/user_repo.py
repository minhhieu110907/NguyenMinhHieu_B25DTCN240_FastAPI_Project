from typing import Optional,List
from sqlalchemy.orm import Session
from app.models.users import User

class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()


    def search_users(
        self, 
        name: Optional[str] = None, 
        email: Optional[str] = None, 
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        query = self.db.query(User)
        
        if name:
            query = query.filter(User.full_name.ilike(f"%{name}%"))
        if email:
            query = query.filter(User.email.ilike(f"%{email}%"))
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
            
        if skip is not None and limit is not None:
            query = query.offset(skip).limit(limit)
        return query.all()