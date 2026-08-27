import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Path, Query, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.dependencies import get_current_user
from app.dependencies.dependencies import RequireScopes, RequireCurrentScopes

from app.dependencies.project_role import RequireProjectRole
from app.security.scopes import Scope
from app.models.users import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_services import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequireScopes({Scope.PROJECT_CREATE}))],
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    project = service.create_project_with_owner(
        name=payload.name, description=payload.description, creator_id=current_user.id
    )
    logger.info(
        f"AUDIT | User [ID: {current_user.id}] created Project [ID: {project.id}, Name: '{project.name}']"
    )
    return project


@router.get(
    "",
    response_model=List[ProjectResponse],
    dependencies=[Depends(RequireScopes({Scope.PROJECT_READ}))],
)
def get_my_projects(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên dự án"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return service.list_my_projects(
        user_id=current_user.id, search=search, skip=skip, limit=limit
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[
        Depends(RequireScopes({Scope.PROJECT_READ})),
        Depends(RequireProjectRole(["OWNER", "MEMBER"])),
    ],
)
def get_project_detail(
    project_id: int = Path(..., description="ID của dự án"),
    db: Session = Depends(get_db),
):
    service = ProjectService(db)
    return service.get_project_detail(project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[
        Depends(RequireScopes({Scope.PROJECT_UPDATE})),
        Depends(RequireProjectRole(["OWNER"])),
    ],
)
def update_project(
    payload: ProjectUpdate,
    project_id: int = Path(..., description="ID của dự án"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    updated_project = service.update_project(
        project_id=project_id, name=payload.name, description=payload.description
    )
    logger.info(
        f"AUDIT | User [ID: {current_user.id}] updated Project [ID: {project_id}]"
    )
    return updated_project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(RequireCurrentScopes({Scope.PROJECT_DELETE})),
        Depends(RequireProjectRole(["OWNER"])),
    ],
)
def delete_project(
    project_id: int = Path(..., description="ID của dự án"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    service.soft_delete_project(project_id)
    logger.info(
        f"AUDIT | User [ID: {current_user.id}] soft-deleted Project [ID: {project_id}]"
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
