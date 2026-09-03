from fastapi import Depends, Path
from sqlalchemy.orm import Session

from app.dependencies.dependencies import get_current_user
from app.database.database import get_db
from app.models.users import User
from app.models.projects import Project
from app.models.project_members import ProjectMember
from app.models.roles import Role
from app.core.exceptions import ForbiddenError, NotFoundException


class RequireProjectRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = [r.upper() for r in allowed_roles]

    def __call__(
        self, 
        project_id: int = Path(..., description="Project ID"),
        current_user: User = Depends(get_current_user), 
        db: Session = Depends(get_db)
    ) -> None:
        row = (
            db.query(
                Project.id,
                ProjectMember.user_id,
                Role.name.label("role_name")
            )
            .outerjoin(
                ProjectMember,
                (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == current_user.id)
            )
            .outerjoin(Role, Role.id == ProjectMember.project_role_id)
            .filter(Project.id == project_id, Project.is_deleted == False)
            .first()
        )

        if not row:
            raise NotFoundException("The project does not exist or has been deleted.")
        if current_user.system_role_id == 1:
            return

        _, member_id, role_name = row

        if member_id is None:
            raise ForbiddenError("You are not a member of this project.")

        actual_role = (role_name or "").upper()
        if actual_role not in self.allowed_roles:
            raise ForbiddenError(
                f"Action denied. Required role: {', '.join(self.allowed_roles)} in the project."
            )