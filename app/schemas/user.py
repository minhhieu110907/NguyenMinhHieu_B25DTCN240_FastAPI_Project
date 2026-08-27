from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime

class RoleRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True
    system_role_id: int = Field(..., gt=0)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None
    system_role_id: Optional[int] = Field(None, gt=0)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    system_role: RoleRead 
    
    model_config = ConfigDict(from_attributes=True)