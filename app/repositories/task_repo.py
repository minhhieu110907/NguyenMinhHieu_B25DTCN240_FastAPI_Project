from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from app.models.tasks import Task
from app.models.comments import Comment
from app.models.projects import Project


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, task_id: int) -> Optional[Task]:
        return (
            self.db.query(Task)
            .join(Project, Project.id == Task.project_id)
            .options(joinedload(Task.assignee))
            .filter(Task.id == task_id, Project.is_deleted == False)
            .first()
        )

    def get_project_tasks(
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
        query = (
            self.db.query(Task)
            .options(joinedload(Task.assignee))
            .filter(Task.project_id == project_id)
        )

        if search:
            query = query.filter(Task.title.ilike(f"%{search.strip()}%"))
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if assignee_id is not None:
            query = query.filter(Task.assignee_id == assignee_id)

        sort_column = getattr(Task, sort_by, Task.created_at)
        query = query.order_by(desc(sort_column) if order.lower() == "desc" else asc(sort_column))

        return query.offset(skip).limit(limit).all()

    def create_task(self, project_id: int, creator_id: int, **data) -> Task:
        task = Task(project_id=project_id, creator_id=creator_id, **data)
        self.db.add(task)
        self.db.flush()
        return task

    def update_task(self, task: Task, update_data: dict) -> Task:
        for field, value in update_data.items():
            setattr(task, field, value)
        self.db.flush()
        return task

    def delete_task(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()

    def add_comment(self, task_id: int, user_id: int, content: str) -> Comment:
        comment = Comment(task_id=task_id, user_id=user_id, content=content.strip())
        self.db.add(comment)
        self.db.flush()
        return comment

    def get_task_comments(self, task_id: int) -> List[Comment]:
        return (
            self.db.query(Comment)
            .filter(Comment.task_id == task_id)
            .order_by(asc(Comment.created_at))
            .all()
        )