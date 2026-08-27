from typing import List
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.database import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.roles import Role
    from app.models.refresh_token import RefreshToken
    from app.models.projects import Project
    from app.models.project_members import ProjectMember
    from app.models.tasks import Task
    from app.models.comments import Comment
    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    system_role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    system_role: Mapped["Role"] = relationship(back_populates="users")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete")
    projects_created: Mapped[List["Project"]] = relationship(back_populates="creator")
    project_memberships: Mapped[List["ProjectMember"]] = relationship(back_populates="user", cascade="all, delete")
    tasks_assigned: Mapped[List["Task"]] = relationship(back_populates="assignee")
    comments: Mapped[List["Comment"]] = relationship(back_populates="user")