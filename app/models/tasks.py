from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime,Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.database import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.projects import Project
    from app.models.users import User
    from app.models.comments import Comment
    from app.models.attachments import Attachment

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    
    status: Mapped[str] = mapped_column(String(50), default="TODO") 
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
)


    project: Mapped["Project"] = relationship(back_populates="tasks")
    assignee: Mapped["User"] = relationship(back_populates="tasks_assigned")
    comments: Mapped[List["Comment"]] = relationship(back_populates="task", cascade="all, delete")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="task", cascade="all, delete")



