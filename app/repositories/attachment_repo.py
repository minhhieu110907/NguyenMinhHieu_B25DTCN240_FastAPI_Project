from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.attachments import Attachment

class TaskAttachmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        task_id: int,
        user_id: int,
        file_url: str
    ) -> Attachment:
        """Stage a new attachment record into the database session."""
        attachment = Attachment(
            task_id=task_id,
            user_id=user_id,
            file_url=file_url
        )
        self.db.add(attachment)
        self.db.flush()
        return attachment

    def get_by_id(self, attachment_id: int) -> Optional[Attachment]:
        return self.db.query(Attachment).filter(Attachment.id == attachment_id).first()

    def get_by_task_id(self, task_id: int) -> List[Attachment]:
        return (
            self.db.query(Attachment)
            .filter(Attachment.task_id == task_id)
            .order_by(Attachment.created_at.desc())
            .all()
        )

    def delete(self, attachment: Attachment) -> None:
        self.db.delete(attachment)
        self.db.flush()