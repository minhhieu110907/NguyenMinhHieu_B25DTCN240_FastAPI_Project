from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.database import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.project_members import ProjectMember
    from app.models.users import User
    from app.models.tasks import Task


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )

    # Relationships
    creator: Mapped["User"] = relationship(back_populates="projects_created")
    members: Mapped[List["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="project", cascade="all, delete"
    )
