from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Annotated
from datetime import datetime, timezone
from app.schemas.user import UserResponse

TaskStatus = Annotated[str, Field(pattern="^(TODO|IN_PROGRESS|DONE)$")]
TaskPriority = Annotated[str, Field(pattern="^(LOW|MEDIUM|HIGH)$")]
String255 = Annotated[str, Field(min_length=3, max_length=255)]

def validate_due_date(value: Optional[datetime]) -> Optional[datetime]:
    if value:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if value < now:
            raise ValueError(
                "The due date cannot be in the past."
            )

    return value


class TaskBase(BaseModel):
    title: String255
    description: Optional[str] = Field(None, max_length=5000)
    status: TaskStatus = "TODO"
    priority: TaskPriority = "MEDIUM"
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = Field(None, gt=0)

    @field_validator("due_date")
    @classmethod
    def validate_due_date_field(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        return validate_due_date(value)


class TaskCreate(TaskBase):
    project_id: int = Field(..., gt=0)


class TaskUpdate(BaseModel):
    title: Optional[String255] = None
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = Field(None, gt=0)

    @field_validator("due_date")
    @classmethod
    def validate_due_date_field(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        return validate_due_date(value)


class TaskResponse(TaskBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    assignee: Optional["UserResponse"] = None 
    
    model_config = ConfigDict(from_attributes=True)