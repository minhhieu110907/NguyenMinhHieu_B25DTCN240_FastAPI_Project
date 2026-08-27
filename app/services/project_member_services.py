from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.project_repo import ProjectRepository
from app.repositories.user_repo import UserRepository
from app.models.project_members import ProjectMember
from app.schemas.project_member import ProjectMemberCreate
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)


class ProjectMemberService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    def get_members(self, project_id: int) -> List[ProjectMember]:
        return self.repo.get_members_by_project_id(project_id)

    def add_member_by_email(
        self, 
        project_id: int, 
        payload: ProjectMemberCreate
    ) -> ProjectMember:
        user = self.user_repo.get_user_by_email(payload.email)
        if not user:
            raise NotFoundException(f"The user with email '{payload.email}' does not exist.")

        try:
            self.repo.add_member(
                project_id=project_id,
                user_id=user.id,
                project_role_id=payload.project_role_id
            )
            self.db.commit()
            return self.repo.get_member(project_id, user.id)
        except IntegrityError:
            self.db.rollback()
            raise ConflictException(
                message="The user is already a member of this project.",
                error_code="MEMBER_ALREADY_EXISTS"
            )

    def remove_member_safely(self, project_id: int, user_id_to_remove: int) -> None:
        member = self.repo.get_member(project_id, user_id_to_remove)
        if not member:
            raise NotFoundException("The member does not exist in this project.")

        try:
            # Check owner with Pessimistic Lock
            is_owner = (
                member.project_role.name.upper() == "OWNER" 
                if member.project_role else False
            )
            if is_owner:
                locked_owners = self.repo.get_owners_with_lock(project_id)
                if len(locked_owners) <= 1:
                    raise BadRequestException(
                        message="The last OWNER of the project cannot be deleted.",
                        error_code="LAST_OWNER_REMOVAL"
                    )

            # Check active task 
            active_tasks = self.repo.count_active_tasks(project_id, user_id_to_remove)
            if active_tasks > 0:
                raise ConflictException(
                    message=f"The member still has {active_tasks} incomplete tasks (TODO/IN_PROGRESS). Please transfer them before deleting the member.",
                    error_code="USER_HAS_ACTIVE_TASKS",
                    details={"active_tasks_count": active_tasks}
                )

            # Delete and commit
            self.repo.delete_member(project_id, user_id_to_remove)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e