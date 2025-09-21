from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Union
from datetime import datetime, timezone

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomaException(Exception):
    """Base exception for Automa application"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AutomaException):
    """Validation error exception"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 400, details)

class NotFoundError(AutomaException):
    """Resource not found exception"""
    def __init__(self, resource: str, identifier: Union[str, int], details: dict = None):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, 404, details)

class PermissionError(AutomaException):
    """Permission denied exception"""
    def __init__(self, message: str = "Permission denied", details: dict = None):
        super().__init__(message, 403, details)

class ServiceUnavailableError(AutomaException):
    """Service unavailable exception"""
    def __init__(self, service: str, details: dict = None):
        message = f"Service '{service}' is currently unavailable"
        super().__init__(message, 503, details)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with structured error response"""
    error_id = f"err_{int(datetime.now(timezone.utc).timestamp())}"

    # Log the error
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "error_id": error_id,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "client_ip": request.client.host if request.client else None
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url)
            }
        }
    )

async def automa_exception_handler(request: Request, exc: AutomaException):
    """Handle custom Automa exceptions"""
    error_id = f"err_{int(datetime.now(timezone.utc).timestamp())}"

    # Log the error
    logger.error(
        f"Automa Exception: {exc.status_code} - {exc.message}",
        extra={
            "error_id": error_id,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "details": exc.details,
            "client_ip": request.client.host if request.client else None
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url),
                "details": exc.details
            }
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database exceptions"""
    error_id = f"err_{int(datetime.now(timezone.utc).timestamp())}"

    # Log the error
    logger.error(
        f"Database Exception: {str(exc)}",
        extra={
            "error_id": error_id,
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else None
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Database error occurred",
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url)
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    error_id = f"err_{int(datetime.now(timezone.utc).timestamp())}"

    # Log the error
    logger.error(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "error_id": error_id,
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else None
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url)
            }
        }
    )