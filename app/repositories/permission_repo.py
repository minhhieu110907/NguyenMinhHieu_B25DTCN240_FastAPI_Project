from sqlalchemy.orm import Session
from app.models.role_permissions import RolePermission
from app.models.permissions import Permission

class PermissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_scopes_by_role_id(self, role_id: int) -> set[str]:
        result = (
            self.db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id == role_id)
            .all()
        )
        return {row[0] for row in result}

    