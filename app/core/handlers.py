from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException
from app.schemas.api_response import APIErrorResponse

def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppException):
        raise exc

    error_response = APIErrorResponse(
        success=False,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json") 
    )


def general_exception_handler(request: Request,exc: Exception) -> JSONResponse:
    error_response = APIErrorResponse(
        success=False,
        message="Internal server error",
        error_code="INTERNAL_SERVER_ERROR",
        details=None,
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )