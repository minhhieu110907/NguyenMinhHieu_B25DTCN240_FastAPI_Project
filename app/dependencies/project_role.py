from fastapi import Depends, Path
from sqlalchemy.orm import Session

from app.dependencies.dependencies import get_current_user
from app.database.database import get_db
from app.models.users import User
from app.repositories.project_repo import ProjectRepository
from app.core.exceptions import ForbiddenError, NotFoundException


class RequireProjectRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = [r.upper() for r in allowed_roles]

    def __call__(
        self, 
        project_id: int = Path(..., description="Project ID"),
        current_user: User = Depends(get_current_user), 
        db: Session = Depends(get_db)
    ) -> User:
        repo = ProjectRepository(db)

        project = repo.get_by_id(project_id)
        if not project:
            raise NotFoundException("The project does not exist or has been deleted.")

        # System Admin Override
        if current_user.system_role_id == 1:
            return current_user

        # Check role
        member = repo.get_member(project_id, current_user.id)
        if not member:
            raise ForbiddenError("You are not a member of this project.")

        role_name = member.project_role.name.upper() if member.project_role else ""
        if role_name not in self.allowed_roles:
            raise ForbiddenError(
                f"Action denied. Required role: {', '.join(self.allowed_roles)} in the project."
            )

        current_user.current_project_role = role_name
        return current_user
    