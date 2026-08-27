from pydantic import BaseModel, ConfigDict,Field,EmailStr
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(...,min_length=2,max_length= 255)
    description: Optional[str] = Field(None, max_length=1000)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class ProjectResponse(ProjectBase):
    id: int
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
# Embed metadata into a Comment
class UserBasicInfo(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

class CommentCreate(CommentBase):
    task_id: int = Field(..., gt=0)

class CommentResponse(CommentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    user: UserBasicInfo
    
    model_config = ConfigDict(from_attributes=True)