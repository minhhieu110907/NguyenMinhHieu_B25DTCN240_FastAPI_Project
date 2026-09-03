import logging
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

logger = logging.getLogger(__name__)


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
                    message="The assignee is not a member of this project.",
                    error_code="INVALID_ASSIGNEE"
                )

    def create_task(self, payload: TaskCreate, current_user: User) -> Task:
        project = self.project_repo.get_by_id(payload.project_id)
        if not project:
            raise NotFoundException("The project does not exist or has been deleted.")

        self._validate_assignee(payload.project_id, payload.assignee_id)

        try:
            task = self.task_repo.create_task(
                project_id=payload.project_id,
                creator_id=current_user.id,
                title=payload.title,
                description=payload.description,
                status=payload.status,
                priority=payload.priority,
                due_date=payload.due_date,
                assignee_id=payload.assignee_id
            )

            self.project_repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="TASK_CREATE",
                entity_type="TASK",
                entity_id=task.id,
                payload={
                    "project_id": payload.project_id,
                    "title": payload.title,
                    "assignee_id": payload.assignee_id,
                    "status": payload.status,
                    "priority": payload.priority
                }
            )

            self.db.commit()
            logger.info(
                f"AUDIT | User [ID: {current_user.id}] created Task [ID: {task.id}] "
                f"in Project [ID: {payload.project_id}]"
            )

            return self.task_repo.get_by_id(task.id)

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to create task in Project [ID: {payload.project_id}] "
                f"by User [ID: {current_user.id}]: {str(e)}"
            )
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

        is_admin = getattr(current_user, "system_role_id", None) == 1
        is_owner = getattr(current_user, "current_project_role", "") == "OWNER"
        is_assignee = task.assignee_id == current_user.id

        if not (is_admin or is_owner):
            if is_assignee:
                disallowed_fields = [k for k in update_dict.keys() if k != "status"]
                if disallowed_fields:
                    raise ForbiddenError(
                        f"Assignee can only update the status field, cannot change: {', '.join(disallowed_fields)}"
                    )
            else:
                raise ForbiddenError("You do not have permission to edit this task.")

        if "assignee_id" in update_dict:
            self._validate_assignee(task.project_id, update_dict["assignee_id"])

        try:
            self.task_repo.update_task(task, update_dict)

            self.project_repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="TASK_UPDATE",
                entity_type="TASK",
                entity_id=task.id,
                payload={"project_id": task.project_id, "updated_fields": list(update_dict.keys())}
            )

            self.db.commit()

            logger.info(
                f"AUDIT | User [ID: {current_user.id}] updated Task [ID: {task.id}] "
                f"with fields: {list(update_dict.keys())}"
            )

            return self.task_repo.get_by_id(task.id)

        except (BadRequestException, ForbiddenError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to update Task [ID: {task.id}] by User [ID: {current_user.id}]: {str(e)}"
            )
            raise e

    def delete_task(self, task: Task, current_user: User) -> None:
        try:
            task_id = task.id
            project_id = task.project_id

            self.task_repo.delete_task(task)

            self.project_repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="TASK_DELETE",
                entity_type="TASK",
                entity_id=task_id,
                payload={"project_id": project_id, "title": task.title}
            )

            self.db.commit()

            logger.info(
                f"AUDIT | User [ID: {current_user.id}] deleted Task [ID: {task_id}] "
                f"from Project [ID: {project_id}]"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to delete Task [ID: {task.id}] by User [ID: {current_user.id}]: {str(e)}"
            )
            raise e

    def create_comment(self, payload: CommentCreate, current_user: User) -> Comment:
        task = self.task_repo.get_by_id(payload.task_id)
        if not task:
            raise NotFoundException("Task does not exist or the project has been deleted.")

        try:
            comment = self.task_repo.add_comment(
                task_id=payload.task_id,
                user_id=current_user.id,
                content=payload.content
            )
            self.db.commit()
            self.db.refresh(comment)

            # Comment only writes console log, not duplicated into DB ActivityLog
            logger.info(
                f"AUDIT | User [ID: {current_user.id}] commented on Task [ID: {payload.task_id}]"
            )

            return comment

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to comment on Task [ID: {payload.task_id}] by User [ID: {current_user.id}]: {str(e)}"
            )
            raise e

    def list_comments(self, task_id: int) -> List[Comment]:
        return self.task_repo.get_task_comments(task_id)