from typing import List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.users import User
    from app.models.permissions import Permission
    from app.models.project_members import ProjectMember
    

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(back_populates="system_role")
    project_members: Mapped[List["ProjectMember"]] = relationship(
        back_populates="project_role"
    )
