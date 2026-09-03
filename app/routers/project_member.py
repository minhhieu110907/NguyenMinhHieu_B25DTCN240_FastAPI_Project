from typing import List
from fastapi import APIRouter, Depends, status, Path, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.dependencies import get_current_user
from app.dependencies.dependencies import RequireScopes, RequireCurrentScopes

from app.dependencies.project_role import RequireProjectRole
from app.security.scopes import Scope
from app.models.users import User
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberResponse
from app.services.project_member_services import ProjectMemberService

router = APIRouter(prefix="/projects/{project_id}/members", tags=["Project Members"])


@router.get(
    "",
    response_model=List[ProjectMemberResponse],
    dependencies=[
        Depends(RequireScopes({Scope.MEMBER_READ})),
        Depends(RequireProjectRole(["OWNER", "MEMBER"])),
    ],
)
def get_project_members(
    project_id: int = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
):
    service = ProjectMemberService(db)
    return service.get_members(project_id)


@router.post(
    "",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(RequireScopes({Scope.MEMBER_ADD})),
        Depends(RequireProjectRole(["OWNER"])),
    ],
)
def add_project_member(
    payload: ProjectMemberCreate,
    project_id: int = Path(..., description="Project ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectMemberService(db)
    return service.add_member_by_email(project_id=project_id, payload=payload,current_user=current_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(RequireCurrentScopes({Scope.MEMBER_REMOVE})),
        Depends(RequireProjectRole(["OWNER"])),
    ],
)
def remove_project_member(
    project_id: int = Path(..., description="Project ID"),
    user_id: int = Path(..., description="ID of the user to remove"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectMemberService(db)
    service.remove_member_safely(project_id, user_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)