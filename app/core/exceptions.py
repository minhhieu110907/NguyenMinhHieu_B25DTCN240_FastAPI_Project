from typing import Any, Optional

# CORE EXCEPTION
class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

# HTTP EXCEPTIONS
class BadRequestException(AppException):
    def __init__(self, message: str = "Invalid data", error_code: str = "BAD_REQUEST", details: Optional[Any] = None):
        super().__init__(message, status_code=400, error_code=error_code, details=details)

class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message, status_code=404, error_code="NOT_FOUND", details=details)

# AUTH EXCEPTION
class AuthError(AppException):
    def __init__(self, message: str, status_code: int = 401, error_code: str = "AUTH_ERROR", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=status_code, error_code=error_code, details=details)

class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password", status_code=401, error_code="INVALID_CREDENTIALS")

class AccountInactiveError(AuthError):
    def __init__(self) -> None:
        super().__init__("Account is inactive", status_code=403, error_code="ACCOUNT_INACTIVE")

class AccountLockedError(AuthError):
    def __init__(self, locked_until: str) -> None:
        super().__init__(
            message=f"Account is locked until {locked_until}", 
            status_code=423, 
            error_code="ACCOUNT_LOCKED",
            details={"locked_until": locked_until} # Help UI
        )

class TokenInvalidError(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid or expired token", status_code=401, error_code="TOKEN_INVALID")

class TokenRevokedError(AuthError):
    def __init__(self) -> None:
        super().__init__("Token has been revoked", status_code=401, error_code="TOKEN_REVOKED")


# CONFLICT EXCEPTION
class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            details=details,
        )

class UserAlreadyExistsError(ConflictException):
    def __init__(self) -> None:
        super().__init__(
            message="Email already registered",
            error_code="USER_ALREADY_EXISTS",
        )


class ForbiddenError(AuthError):
    def __init__(
        self, 
        message: str = "You do not have permission to access this resource", 
        details: Optional[Any] = None
    ) -> None:
        super().__init__(
            message=message, 
            status_code=403, 
            error_code="FORBIDDEN", 
            details=details
        )



# RATE LIMIT EXCEPTIONS
class RateLimitError(AppException):
    """Base exception for rate limiting errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details,
        )


class RateLimitExceededError(RateLimitError):
    """Raised when a client exceeds the configured rate limit."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            message="Too many requests",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "retry_after": retry_after,
            },
        )
        self.retry_after = retry_after


class RateLimitServiceUnavailableError(RateLimitError):
    """Raised when Redis is unavailable and rate limiting cannot be checked."""

    def __init__(self) -> None:
        super().__init__(
            message="Rate limit service temporarily unavailable",
            status_code=503,
            error_code="RATE_LIMIT_SERVICE_UNAVAILABLE",
        )