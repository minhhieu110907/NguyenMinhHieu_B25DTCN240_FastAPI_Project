from typing import List
from fastapi import APIRouter, Depends, status, UploadFile, File, Response, Path
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.dependencies import get_current_user, RequireScopes
from app.dependencies.task_access import RequireTaskAccess
from app.security.scopes import Scope
from app.models.users import User
from app.models.tasks import Task
from app.schemas.attachment import AttachmentResponse
from app.services.attachment_services import TaskAttachmentService

router = APIRouter(tags=["Attachments"])


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(RequireScopes({Scope.TASK_UPDATE})),
    ],
)
def upload_task_attachment(
    file: UploadFile = File(..., description="File to attach (Max 10MB)"),
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER", "MEMBER"])),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TaskAttachmentService(db)
    return service.upload_attachment(
        task=task,
        file=file,
        current_user=current_user
    )

@router.get(
    "/tasks/{task_id}/attachments",
    response_model=List[AttachmentResponse],
    dependencies=[
        Depends(RequireScopes({Scope.TASK_READ})),
    ],
)
def list_task_attachments(
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER", "MEMBER"])),
    db: Session = Depends(get_db),
):
    service = TaskAttachmentService(db)
    return service.list_attachments(task.id)


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(RequireScopes({Scope.TASK_UPDATE})),
    ],
)
def delete_attachment(
    attachment_id: int = Path(..., description="ID of the attachment to delete"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TaskAttachmentService(db)
    service.delete_attachment(attachment_id=attachment_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)