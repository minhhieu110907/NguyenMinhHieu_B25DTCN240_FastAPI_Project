import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.project_repo import ProjectRepository
from app.models.projects import Project
from app.models.users import User
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def create_project_with_owner(
        self, 
        name: str, 
        description: Optional[str], 
        current_user: User, 
        owner_role_id: int = 3
    ) -> Project:
        """Create project, assign OWNER, and write Activity Log in 1 transaction."""
        try:
            project = self.repo.create(
                name=name,
                description=description,
                created_by=current_user.id
            )
            self.repo.add_member(
                project_id=project.id,
                user_id=current_user.id,
                project_role_id=owner_role_id
            )
            self.repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="PROJECT_CREATE",
                entity_type="PROJECT",
                entity_id=project.id,
                payload={"name": project.name, "description": project.description}
            )
            self.db.commit()
            self.db.refresh(project)

            logger.info(
                f"AUDIT | User [ID: {current_user.id}] created Project "
                f"[ID: {project.id}, Name: '{project.name}']"
            )
            return project

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to create project '{name}' by User [ID: {current_user.id}]: {str(e)}"
            )
            raise e

    def get_project_detail(self, project_id: int) -> Project:
        project = self.repo.get_by_id(project_id)
        if not project:
            raise NotFoundException("The project does not exist or has been deleted.")
        return project

    def list_my_projects(
        self, 
        user_id: int, 
        search: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Project]:
        return self.repo.get_user_projects(
            user_id=user_id,
            search=search,
            skip=skip,
            limit=limit
        )

    def update_project(
        self, 
        project_id: int, 
        current_user: User,
        name: Optional[str] = None, 
        description: Optional[str] = None
    ) -> Project:
        project = self.get_project_detail(project_id)
        try:
            updated_project = self.repo.update(
                project=project,
                name=name,
                description=description
            )
            self.repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="PROJECT_UPDATE",
                entity_type="PROJECT",
                entity_id=project_id,
                payload={"name": name, "description": description}
            )

            self.db.commit()
            self.db.refresh(updated_project)

            logger.info(
                f"AUDIT | User [ID: {current_user.id}] updated Project [ID: {project_id}]"
            )
            return updated_project

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to update Project [ID: {project_id}] by User [ID: {current_user.id}]: {str(e)}"
            )
            raise e

    def soft_delete_project(self, project_id: int, current_user: User) -> None:
        project = self.get_project_detail(project_id)
        try:
            self.repo.soft_delete(project)
            self.repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="PROJECT_DELETE",
                entity_type="PROJECT",
                entity_id=project_id,
                payload={"project_name": project.name}
            )

            self.db.commit()
            logger.info(
                f"AUDIT | User [ID: {current_user.id}] soft-deleted Project [ID: {project_id}]"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"ERROR | Failed to delete Project [ID: {project_id}] by User [ID: {current_user.id}]: {str(e)}"
            )
            raise e