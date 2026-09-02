from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AttachmentBase(BaseModel):
    file_url: str = Field(..., description="Relative storage path or URL of the file")


class AttachmentCreate(AttachmentBase):
    task_id: int = Field(..., gt=0)


class AttachmentResponse(AttachmentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)