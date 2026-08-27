from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

class CommentCreate(CommentBase):
    task_id: int = Field(..., gt=0)

class CommentResponse(CommentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)