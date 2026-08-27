from typing import List
from fastapi import Depends, Path
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
        task_id: int = Path(..., description="ID của Task"),
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
            raise NotFoundException("Task không tồn tại hoặc dự án đã bị xóa.")

        if current_user.system_role_id == 1:
            return task

        project_repo = ProjectRepository(db)
        member = project_repo.get_member(task.project_id, current_user.id)
        if not member:
            raise ForbiddenError("Bạn không thuộc dự án chứa task này.")

        role_name = member.project_role.name.upper() if member.project_role else ""
        is_role_allowed = role_name in self.allowed_roles
        is_assignee = task.assignee_id == current_user.id

        if not is_role_allowed:
            if not (self.allow_assignee_override and is_assignee):
                raise ForbiddenError("Bạn không có quyền thực hiện hành động trên task này.")

        current_user.current_project_role = role_name
        return task