from typing import List
from fastapi import Depends, Path, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.dependencies import get_current_user
from app.models.users import User
from app.models.tasks import Task
from app.models.projects import Project
from app.repositories.project_repo import ProjectRepository
from app.core.exceptions import NotFoundException, ForbiddenError


class RequireTaskAccess:
    def __init__(
        self, 
        allowed_project_roles: List[str] = ["OWNER", "MEMBER"],
        allow_assignee_override: bool = False
    ) -> None:
        self.allowed_roles = [r.upper() for r in allowed_project_roles]
        self.allow_assignee_override = allow_assignee_override

    def __call__(
        self,
        request: Request,
        task_id: int = Path(..., description="Task ID"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> Task:
        task = (
            db.query(Task)
            .join(Project, Project.id == Task.project_id)
            .filter(Task.id == task_id, Project.is_deleted == False)
            .first()
        )
        if not task:
            raise NotFoundException("Task does not exist or the project has been deleted.")

        if current_user.system_role_id == 1:
            request.state.project_role = "SYSTEM_ADMIN"
            return task

        project_repo = ProjectRepository(db)
        member = project_repo.get_member(task.project_id, current_user.id)
        if not member:
            raise ForbiddenError("You are not a member of the project that contains this task.")

        role_name = member.project_role.name.upper() if member.project_role else ""
        is_role_allowed = role_name in self.allowed_roles
        is_assignee = task.assignee_id == current_user.id

        if not is_role_allowed:
            if not (self.allow_assignee_override and is_assignee):
                raise ForbiddenError("You do not have permission to do this action on this task.")

        request.state.project_role = role_name
        return task