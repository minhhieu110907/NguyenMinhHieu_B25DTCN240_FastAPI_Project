import os
import sys
import logging
from datetime import datetime, timezone, timedelta

# Append project root to sys.path to allow importing from the 'app' directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.core.config import settings
from app.core.logger import setup_global_logging

from app.models.permissions import Permission
from app.models.role_permissions import RolePermission
from app.models.roles import Role
from app.models.users import User
from app.models.refresh_token import RefreshToken
from app.models.projects import Project
from app.models.project_members import ProjectMember
from app.models.tasks import Task
from app.models.comments import Comment
from app.models.attachments import Attachment
from app.models.activity_logs import ActivityLog

from app.security.password import hash_password
from app.security.scopes import Scope

# Configure logging
setup_global_logging()
logger = logging.getLogger("app.seed")


def seed_database(db: Session):
    try:
        # Check if database is already seeded to prevent duplicate entry errors
        if db.query(Role).first():
            logger.info(
                "Database already seeded. Skipping execution to avoid duplicates."
            )
            return

        # 1. Seed Permissions
        logger.info("Seeding Permissions...")

        perms = [
            Permission(
                id=index,
                code=scope.value
            )
            for index, scope in enumerate(Scope, start=1)
        ]

        db.add_all(perms)
        db.flush()

        # 2. Seed Roles 
        logger.info("Seeding Roles...")

        role_admin = Role(id=1, name="SYSTEM_ADMIN", description="System Administrator")
        role_user = Role(id=2, name="USER", description="Standard User")
        role_owner = Role(id=3, name="OWNER", description="Project Owner")
        role_member = Role(id=4, name="MEMBER", description="Project Member")

        db.add_all([role_admin, role_user, role_owner, role_member])
        db.flush()

        # 3. Assign all Permissions for SYSTEM_ADMIN
        for permission in perms:
            db.add(
                RolePermission(
                    role_id=role_admin.id,
                    permission_id=permission.id
                )
            )

        # 4. Assign business Scope for USER 
        user_allowed_scopes = {
            Scope.USER_UPDATE,
            Scope.PROJECT_READ,
            Scope.PROJECT_CREATE,
            Scope.PROJECT_UPDATE,
            Scope.PROJECT_DELETE,
            Scope.MEMBER_READ,
            Scope.MEMBER_ADD,
            Scope.MEMBER_REMOVE,
            Scope.TASK_READ,
            Scope.TASK_CREATE,
            Scope.TASK_UPDATE,
            Scope.TASK_DELETE,
            Scope.COMMENT_READ,
            Scope.COMMENT_CREATE,
            Scope.COMMENT_DELETE,
            Scope.ATTACHMENT_UPLOAD,
            Scope.ATTACHMENT_DELETE,
        }

        for perm in perms:
            if perm.code in [s.value for s in user_allowed_scopes]:
                db.add(
                    RolePermission(
                        role_id=role_user.id,
                        permission_id=perm.id
                    )
                )

        db.flush()

        # 5. Seed Users 
        logger.info("Seeding Users...")

        default_password = hash_password(
            getattr(settings, "DEFAULT_SEED_PASSWORD", "Password@123")
        )

        admin_user = User(
            id=1,
            email="minhhieu1109@gmail.com",
            password_hash=default_password,
            full_name="Nguyễn Minh Hiếu",
            is_active=True,
            system_role_id=role_admin.id
        )

        dev_user_1 = User(
            id=2,
            email="thang.le@ptit.edu.vn",
            password_hash=default_password,
            full_name="Lê Văn Thắng",
            is_active=True,
            system_role_id=role_user.id
        )

        dev_user_2 = User(
            id=3,
            email="mai.tran@ptit.edu.vn",
            password_hash=default_password,
            full_name="Trần Thị Ngọc Mai",
            is_active=True,
            system_role_id=role_user.id
        )

        dev_user_3 = User(
            id=4,
            email="minhhao@gmail.com",
            password_hash=default_password,
            full_name="Hoang",
            is_active=True,
            system_role_id=role_user.id
        )

        db.add_all([
            admin_user,
            dev_user_1,
            dev_user_2,
            dev_user_3
        ])
        db.flush()

        # 6. Seed Refresh Tokens
        logger.info("Seeding Refresh Tokens...")

        db.add(
            RefreshToken(
                id=1,
                user_id=admin_user.id,
                token="seed_fake_opaque_token_string_86_chars_...",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                is_revoked=False
            )
        )
        db.flush()

        # 7. Seed Projects
        logger.info("Seeding Projects and Members...")

        project = Project(
            id=1,
            name="Microservices Project Management System",
            description="Advanced task management application with strict RBAC",
            created_by=admin_user.id
        )

        db.add(project)
        db.flush()

        # 8. Seed Project Members 
        db.add_all([
            ProjectMember(
                project_id=project.id,
                user_id=admin_user.id,
                project_role_id=role_owner.id
            ),
            ProjectMember(
                project_id=project.id,
                user_id=dev_user_1.id,
                project_role_id=role_member.id
            ),
            ProjectMember(
                project_id=project.id,
                user_id=dev_user_2.id,
                project_role_id=role_member.id
            )
        ])
        db.flush()

        # 9. Seed Tasks
        logger.info("Seeding Tasks...")

        now_utc = datetime.now(timezone.utc)

        task_1 = Task(
            id=1,
            project_id=project.id,
            title="Design 11 Database Tables",
            description="Create schema and normalize foreign keys",
            assignee_id=admin_user.id,
            status="DONE",
            priority="HIGH",
            due_date=now_utc + timedelta(days=2)
        )

        task_2 = Task(
            id=2,
            project_id=project.id,
            title="Implement Auth API and Token Generation",
            description="Use Passlib and Jose to hash passwords and generate JWT",
            assignee_id=dev_user_1.id,
            status="IN_PROGRESS",
            priority="HIGH",
            due_date=now_utc + timedelta(days=3)
        )

        task_3 = Task(
            id=3,
            project_id=project.id,
            title="Fix Kanban board UI bug",
            description="In Progress column layout is broken on mobile devices",
            assignee_id=dev_user_2.id,
            status="TODO",
            priority="MEDIUM",
            due_date=now_utc + timedelta(days=5)
        )

        db.add_all([task_1, task_2, task_3])
        db.flush()

        # 10. Seed Comments
        logger.info("Seeding Comments and Attachments...")

        db.add_all([
            Comment(
                id=1,
                task_id=task_1.id,
                user_id=admin_user.id,
                content="Schema design is finalized. Please review."
            ),
            Comment(
                id=2,
                task_id=task_2.id,
                user_id=dev_user_1.id,
                content="Stuck on Exception Handler bug. Will fix this morning."
            )
        ])
        db.flush()

        # 11. Seed Attachments
        db.add(
            Attachment(
                id=1,
                task_id=task_1.id,
                user_id=admin_user.id,
                file_url="https://www.facebook.com/search/top?q=liverpool%20fc"
            )
        )
        db.flush()

        # 12. Seed Activity Logs
        logger.info("Seeding Activity Logs...")

        db.add(
            ActivityLog(
                id=1,
                user_id=admin_user.id,
                actor_role="SYSTEM_ADMIN",
                action="CREATE",
                entity_type="PROJECT",
                entity_id=project.id,
                payload={
                    "project_name": project.name
                }
            )
        )
        db.flush()
        db.commit()
        logger.info("DATABASE SEEDING COMPLETED SUCCESSFULLY!")

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed, transaction rolled back: {e}")
        raise


def reset_data(db: Session):
    """
    Xóa sạch dữ liệu theo đúng thứ tự ràng buộc khóa ngoại (Foreign Key Constraints).
    """
    try:
        logger.warning("DATABASE RESET STARTED")
        logger.warning("All application data in seeded tables will be deleted.")

        # 1. Activity Logs
        logger.info("Deleting Activity Logs...")
        db.query(ActivityLog).delete(synchronize_session=False)

        # 2. Attachments
        logger.info("Deleting Attachments...")
        db.query(Attachment).delete(synchronize_session=False)

        # 3. Comments
        logger.info("Deleting Comments...")
        db.query(Comment).delete(synchronize_session=False)

        # 4. Tasks
        logger.info("Deleting Tasks...")
        db.query(Task).delete(synchronize_session=False)

        # 5. Project Members
        logger.info("Deleting Project Members...")
        db.query(ProjectMember).delete(synchronize_session=False)

        # 6. Projects
        logger.info("Deleting Projects...")
        db.query(Project).delete(synchronize_session=False)

        # 7. Refresh Tokens
        logger.info("Deleting Refresh Tokens...")
        db.query(RefreshToken).delete(synchronize_session=False)

        # 8. Users
        logger.info("Deleting Users...")
        db.query(User).delete(synchronize_session=False)

        # 9. Role Permissions
        logger.info("Deleting Role Permissions...")
        db.query(RolePermission).delete(synchronize_session=False)

        # 10. Roles
        logger.info("Deleting Roles...")
        db.query(Role).delete(synchronize_session=False)

        # 11. Permissions
        logger.info("Deleting Permissions...")
        db.query(Permission).delete(synchronize_session=False)

        db.commit()
        logger.info("DATABASE RESET COMPLETED SUCCESSFULLY!")

    except Exception as e:
        db.rollback()
        logger.error(f"Database reset failed, transaction rolled back: {e}")
        raise


if __name__ == "__main__":
    db = SessionLocal()

    try:
        if "--reset" in sys.argv:
            logger.warning("--reset argument detected.")
            reset_data(db)
            logger.info("Starting database seeding after reset...")
            seed_database(db)
        else:
            seed_database(db)
    finally:
        db.close()