from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class ResolveAIException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(ResolveAIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(ResolveAIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class PolicyDeniedError(ResolveAIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="POLICY_DENIED",
            details=details,
        )


class ApprovalRequiredError(ResolveAIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="APPROVAL_REQUIRED",
            details=details,
        )


async def resolveai_exception_handler(request: Request, exc: ResolveAIException) -> JSONResponse:
    origin = request.headers.get("origin", "http://localhost:3000")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
        headers={
            "X-Request-ID": getattr(request.state, "request_id", ""),
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
            "Access-Control-Allow-Credentials": "true",
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    origin = request.headers.get("origin", "http://localhost:3000")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
        headers={
            "X-Request-ID": getattr(request.state, "request_id", ""),
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
            "Access-Control-Allow-Credentials": "true",
        },
    )