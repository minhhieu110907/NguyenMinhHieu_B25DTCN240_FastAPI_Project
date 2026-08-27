from enum import Enum

class Scope(str, Enum):
    # SYSTEM (Admin)
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    ROLE_MANAGE = "role:manage"

    # PROJECT
    PROJECT_READ = "project:read"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # PROJECT MEMBER
    MEMBER_READ = "member:read"
    MEMBER_ADD = "member:add"
    MEMBER_REMOVE = "member:remove"

    # TASK (Công việc)
    TASK_READ = "task:read"
    TASK_CREATE = "task:create"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"

    # COMMENT & ATTACHMENT
    COMMENT_CREATE = "comment:create"
    COMMENT_DELETE = "comment:delete"
    COMMENT_READ = "comment:read"
    ATTACHMENT_UPLOAD = "attachment:upload"
    ATTACHMENT_DELETE = "attachment:delete"

def scopes_to_string(scopes: set[Scope] | set[str]) -> str:
    return " ".join(
        sorted(
            scope.value if isinstance(scope, Scope) else scope 
            for scope in scopes
        )
    )

def parse_scopes(scope_string: str) -> set[str]:
    if not scope_string:
        return set()
    return set(scope_string.split())

def has_required_scopes(user_scopes: set[str], required: set[Scope]) -> bool:
    return {scope.value for scope in required}.issubset(user_scopes)

