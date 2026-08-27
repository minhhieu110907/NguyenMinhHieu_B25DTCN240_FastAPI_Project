from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from datetime import datetime

class AttachmentBase(BaseModel):
    file_url: HttpUrl 

class AttachmentCreate(AttachmentBase):
    task_id: int = Field(..., gt=0)

class AttachmentResponse(AttachmentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    
    # Ép kiểu HttpUrl thành chuỗi string khi trả về JSON cho Frontend
    model_config = ConfigDict(from_attributes=True, json_encoders={HttpUrl: str})