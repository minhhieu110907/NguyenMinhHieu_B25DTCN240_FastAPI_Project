from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, Annotated
from datetime import datetime

ActionType = Annotated[str, Field(pattern="^(CREATE|UPDATE|DELETE|UPLOAD)$")]
EntityType = Annotated[str, Field(pattern="^(PROJECT|TASK|MEMBER)$")]

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: ActionType
    entity_type: EntityType
    entity_id: int
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)