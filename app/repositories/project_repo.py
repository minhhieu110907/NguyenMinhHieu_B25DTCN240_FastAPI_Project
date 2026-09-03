from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.projects import Project
from app.models.project_members import ProjectMember
from app.models.tasks import Task
from app.models.roles import Role
from app.models.activity_logs import ActivityLog
class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        
    def add_activity_log(
        self,
        user_id: int,
        actor_role: str,
        action: str,
        entity_type: str,
        entity_id: int,
        payload: Optional[dict] = None
    ) -> None:
        log = ActivityLog(
            user_id=user_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload
        )
        self.db.add(log)
        self.db.flush()

    # PROJECT MANAGEMENT & SOFT DELETE
    def get_by_id(self, project_id: int, include_deleted: bool = False) -> Optional[Project]:
        """Get project information by id,skip deleted project"""
        query = self.db.query(Project).filter(Project.id == project_id)
        if not include_deleted:
            query = query.filter(Project.is_deleted == False)
        return query.first()

    def get_user_projects(
        self, 
        user_id: int, 
        search: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Project]:
        """Get project's user list, search and pagination"""
        query = (
            self.db.query(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .filter(
                ProjectMember.user_id == user_id,
                Project.is_deleted == False
            )
        )
        if search:
            query = query.filter(Project.name.ilike(f"%{search.strip()}%"))
            
        return query.offset(skip).limit(limit).all()

    def create(self, name: str, description: Optional[str], created_by: int) -> Project:
        """Create project"""
        project = Project(
            name=name.strip(),
            description=description.strip() if description else None,
            created_by=created_by,
            is_deleted=False
        )
        self.db.add(project)
        self.db.flush()
        return project

    def update(
        self, 
        project: Project, 
        name: Optional[str] = None, 
        description: Optional[str] = None
    ) -> Project:
        """Update project information."""
        if name is not None:
            project.name = name.strip()
        if description is not None:
            project.description = description.strip()
        self.db.flush()
        return project

    def soft_delete(self, project: Project) -> None:
        """Soft delete project"""
        project.is_deleted = True
        project.deleted_at = datetime.now(timezone.utc)
        self.db.flush()

    # PROJECT MEMBERS & PESSIMISTIC LOCKING
    def get_member(self, project_id: int, user_id: int) -> Optional[ProjectMember]:
        return (
            self.db.query(ProjectMember)
            .options(
                joinedload(ProjectMember.user),
                joinedload(ProjectMember.project_role)
            )
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
            .first()
        )

    def get_members_by_project_id(self, project_id: int) -> List[ProjectMember]:
        """Get all project's members."""
        return (
            self.db.query(ProjectMember)
            .options(
                joinedload(ProjectMember.user),
                joinedload(ProjectMember.project_role)
            )
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

    def add_member(self, project_id: int, user_id: int, project_role_id: int) -> ProjectMember:
        """Add member to project."""
        new_member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            project_role_id=project_role_id
        )
        self.db.add(new_member)
        self.db.flush()
        return new_member

    def get_owners_with_lock(self, project_id: int) -> List[ProjectMember]:
        """Pessimistic Lock record OWNER."""
        return (
            self.db.query(ProjectMember)
            .join(ProjectMember.project_role)
            .filter(
                ProjectMember.project_id == project_id,
                func.upper(Role.name) == "OWNER"
            )
            .with_for_update()
            .all()
        )

    def count_active_tasks(self, project_id: int, user_id: int) -> int:
        """Count task (TODO, IN_PROGRESS)"""
        return (
            self.db.query(func.count(Task.id))
            .filter(
                Task.project_id == project_id,
                Task.assignee_id == user_id,
                Task.status.in_(["TODO", "IN_PROGRESS"])
            )
            .scalar()
        ) or 0

    def delete_member(self, project_id: int, user_id: int) -> None:
        """Delete member from project_members."""
        self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).delete(synchronize_session=False)