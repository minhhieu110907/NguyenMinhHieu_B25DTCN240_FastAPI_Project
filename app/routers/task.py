from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, status, Path, Query, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.dependencies import get_current_user
from app.dependencies.dependencies import RequireScopes, RequireCurrentScopes
from app.dependencies.project_role import RequireProjectRole
from app.dependencies.task_access import RequireTaskAccess
from app.security.scopes import Scope
from app.models.users import User
from app.models.tasks import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.task_services import TaskService

router = APIRouter(tags=["Tasks"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    description=(
        "For `due_date`, use the format "
        "`YYYY-MM-DDTHH:MM:SS`.\n\n"
        "Example: `2026-08-30T15:30:00`."
    ),
    dependencies=[
        Depends(RequireScopes({Scope.TASK_CREATE})),
        Depends(RequireProjectRole(["OWNER", "MEMBER"]))
    ]
)
def create_task(
    payload: TaskCreate,
    project_id: int = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payload.project_id = project_id
    service = TaskService(db)
    return service.create_task(payload, current_user=current_user)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[TaskResponse],
    dependencies=[
        Depends(RequireScopes({Scope.TASK_READ})),
        Depends(RequireProjectRole(["OWNER", "MEMBER"]))
    ]
)
def get_project_tasks(
    project_id: int = Path(..., description="Project ID"),
    search: Optional[str] = Query(None, description="Search by task title"),
    status: Optional[str] = Query(None, pattern="^(TODO|IN_PROGRESS|DONE)$"),
    priority: Optional[str] = Query(None, pattern="^(LOW|MEDIUM|HIGH)$"),
    assignee_id: Optional[int] = Query(None, gt=0),
    sort_by: Literal["created_at", "due_date"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    return service.get_tasks_by_project(
        project_id=project_id,
        search=search,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        sort_by=sort_by,
        order=order,
        skip=skip,
        limit=limit
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    dependencies=[Depends(RequireScopes({Scope.TASK_READ}))]
)
def get_task_detail(
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER", "MEMBER"]))
):
    return task


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    description=(
        "For `due_date`, use the format "
        "`YYYY-MM-DDTHH:MM:SS`.\n\n"
        "Example: `2026-08-30T15:30:00`."
    ),
    dependencies=[Depends(RequireScopes({Scope.TASK_UPDATE}))]
)
def update_task(
    payload: TaskUpdate,
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER", "MEMBER"], allow_assignee_override=True)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    return service.update_task_with_matrix(task, payload, current_user=current_user)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequireCurrentScopes({Scope.TASK_DELETE}))]
)
def delete_task(
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER"])),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    service.delete_task(task, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequireScopes({Scope.COMMENT_CREATE}))]
)
def create_comment(
    payload: CommentCreate,
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER", "MEMBER"])),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payload.task_id = task.id
    service = TaskService(db)
    return service.create_comment(payload, current_user=current_user)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=List[CommentResponse],
    dependencies=[Depends(RequireScopes({Scope.COMMENT_READ}))]
)
def list_comments(
    task: Task = Depends(RequireTaskAccess(allowed_project_roles=["OWNER", "MEMBER"])),
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    return service.list_comments(task.id)