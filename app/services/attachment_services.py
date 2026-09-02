import os
import uuid
import logging
from typing import List
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.tasks import Task
from app.models.users import User
from app.models.attachments import Attachment
from app.repositories.attachment_repo import TaskAttachmentRepository
from app.repositories.project_repo import ProjectRepository
from app.core.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "application/zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
UPLOAD_DIR = "uploads/attachments"


class TaskAttachmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.attachment_repo = TaskAttachmentRepository(db)
        self.project_repo = ProjectRepository(db)

    def upload_attachment(
        self, 
        task: Task, 
        file: UploadFile, 
        current_user: User
    ) -> Attachment:
        # 1. Check MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise BadRequestException(
                f"Unsupported file type: '{file.content_type}'. Allowed types: Images, PDF, Docs, Zip."
            )

        # 2. Read bytes and enforce size limits
        file_content = file.file.read()
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            raise BadRequestException(
                f"File size exceeds maximum threshold of {MAX_FILE_SIZE // (1024 * 1024)}MB."
            )
        if file_size == 0:
            raise BadRequestException("Uploaded file cannot be empty.")

        # 3. Create sanitized storage path
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_ext = os.path.splitext(file.filename or "")[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        saved_file_path = os.path.join(UPLOAD_DIR, unique_filename).replace("\\", "/")

        # 4. Save file to disk
        with open(saved_file_path, "wb") as buffer:
            buffer.write(file_content)

        try:
            # 5. DB Persistence (Assign to file_url column)
            attachment = self.attachment_repo.create(
                task_id=task.id,
                user_id=current_user.id,
                file_url=saved_file_path
            )

            # 6. Dual-Logging (ActivityLog)
            self.project_repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="ATTACHMENT_UPLOAD",
                entity_type="TASK",
                entity_id=task.id,
                payload={
                    "task_id": task.id,
                    "attachment_id": attachment.id,
                    "file_url": saved_file_path,
                    "file_size": file_size,
                },
            )

            self.db.commit()
            self.db.refresh(attachment)

            # 7. Console logging
            logger.info(
                f"AUDIT | User [ID: {current_user.id}] attached file [ID: {attachment.id}] "
                f"to Task [ID: {task.id}] at path '{saved_file_path}'"
            )
            return attachment

        except Exception as e:
            self.db.rollback()
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
            logger.error(f"ERROR | Failed to attach file to Task [ID: {task.id}]: {str(e)}")
            raise e

    def list_attachments(self, task_id: int) -> List[Attachment]:
        return self.attachment_repo.get_by_task_id(task_id)

    def delete_attachment(self, attachment_id: int, current_user: User) -> None:
        attachment = self.attachment_repo.get_by_id(attachment_id)
        if not attachment:
            raise NotFoundException("Attachment does not exist.")

        stored_file_path = attachment.file_url
        task_id = attachment.task_id

        try:
            self.attachment_repo.delete(attachment)
            self.project_repo.add_activity_log(
                user_id=current_user.id,
                actor_role=getattr(current_user, "role", "USER"),
                action="ATTACHMENT_DELETE",
                entity_type="TASK",
                entity_id=task_id,
                payload={"attachment_id": attachment_id, "file_url": stored_file_path},
            )
            self.db.commit()

            # Purge physical file from disk
            if os.path.exists(stored_file_path):
                os.remove(stored_file_path)

            logger.info(
                f"AUDIT | User [ID: {current_user.id}] deleted Attachment [ID: {attachment_id}] "
                f"from Task [ID: {task_id}]"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"ERROR | Failed to delete Attachment [ID: {attachment_id}]: {str(e)}")
            raise e