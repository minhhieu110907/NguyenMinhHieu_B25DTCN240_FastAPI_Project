from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.project_repo import ProjectRepository
from app.models.projects import Project
from app.core.exceptions import NotFoundException


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def create_project_with_owner(
        self, 
        name: str, 
        description: Optional[str], 
        creator_id: int, 
        owner_role_id: int = 1
    ) -> Project:
        """Create the project and assign the OWNER role to its creator."""
        try:
            project = self.repo.create(
                name=name,
                description=description,
                created_by=creator_id
            )
            self.repo.add_member(
                project_id=project.id,
                user_id=creator_id,
                project_role_id=owner_role_id
            )
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception as e:
            self.db.rollback()
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
            self.db.commit()
            self.db.refresh(updated_project)
            return updated_project
        except Exception as e:
            self.db.rollback()
            raise e

    def soft_delete_project(self, project_id: int) -> None:
        project = self.get_project_detail(project_id)
        try:
            self.repo.soft_delete(project)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e