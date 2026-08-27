from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.task_repo import TaskRepository
from app.repositories.project_repo import ProjectRepository
from app.models.tasks import Task
from app.models.comments import Comment
from app.models.users import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.comment import CommentCreate
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenError


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)

    def _validate_assignee(self, project_id: int, assignee_id: Optional[int]) -> None:
        if assignee_id is not None:
            member = self.project_repo.get_member(project_id, assignee_id)
            if not member:
                raise BadRequestException(
                    message="Người được giao việc (assignee) không phải là thành viên của dự án này.",
                    error_code="INVALID_ASSIGNEE"
                )

    def create_task(self, payload: TaskCreate, creator_id: int) -> Task:
        project = self.project_repo.get_by_id(payload.project_id)
        if not project:
            raise NotFoundException("Dự án không tồn tại hoặc đã bị xóa.")

        self._validate_assignee(payload.project_id, payload.assignee_id)

        try:
            task = self.task_repo.create_task(
                project_id=payload.project_id,
                creator_id=creator_id,
                title=payload.title,
                description=payload.description,
                status=payload.status,
                priority=payload.priority,
                due_date=payload.due_date,
                assignee_id=payload.assignee_id
            )
            self.db.commit()
            return self.task_repo.get_by_id(task.id)
        except Exception as e:
            self.db.rollback()
            raise e

    def get_tasks_by_project(
        self,
        project_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        skip: int = 0,
        limit: int = 20
    ) -> List[Task]:
        return self.task_repo.get_project_tasks(
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

    def update_task_with_matrix(
        self,
        task: Task,
        payload: TaskUpdate,
        current_user: User
    ) -> Task:
        update_dict = payload.model_dump(exclude_unset=True)
        if not update_dict:
            return task

        is_admin = current_user.system_role_id == 1
        is_owner = getattr(current_user, "current_project_role", "") == "OWNER"
        is_assignee = task.assignee_id == current_user.id

        if not (is_admin or is_owner):
            if is_assignee:
                disallowed_fields = [k for k in update_dict.keys() if k != "status"]
                if disallowed_fields:
                    raise ForbiddenError(
                        f"Assignee chỉ được cập nhật trạng thái (status), không được sửa: {', '.join(disallowed_fields)}"
                    )
            else:
                raise ForbiddenError("Bạn không có quyền chỉnh sửa task này.")

        if "assignee_id" in update_dict:
            self._validate_assignee(task.project_id, update_dict["assignee_id"])

        try:
            self.task_repo.update_task(task, update_dict)
            self.db.commit()
            return self.task_repo.get_by_id(task.id)
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_task(self, task: Task) -> None:
        try:
            self.task_repo.delete_task(task)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def create_comment(self, payload: CommentCreate, user_id: int) -> Comment:
        task = self.task_repo.get_by_id(payload.task_id)
        if not task:
            raise NotFoundException("Task không tồn tại hoặc dự án đã bị xóa.")

        try:
            comment = self.task_repo.add_comment(
                task_id=payload.task_id,
                user_id=user_id,
                content=payload.content
            )
            self.db.commit()
            self.db.refresh(comment)
            return comment
        except Exception as e:
            self.db.rollback()
            raise e

    def list_comments(self, task_id: int) -> List[Comment]:
        return self.task_repo.get_task_comments(task_id)