from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.schemas.user import UserResponse
from app.schemas.user import RoleRead

class ProjectMemberCreate(BaseModel):
    email: EmailStr 
    project_role_id: int

class ProjectMemberResponse(BaseModel):
    project_id: int
    user_id: int
    project_role_id: int
    joined_at: datetime
    user: "UserResponse" # Dùng chuỗi để tránh lỗi Circular Import
    project_role: "RoleRead" 
    
    model_config = ConfigDict(from_attributes=True)