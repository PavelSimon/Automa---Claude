from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from .database import create_db_and_tables
from .config import settings
from .core.deps import fastapi_users, auth_backend
from .schemas.user import UserRead, UserCreate
from .api import scripts, agents, jobs, monitoring, profile, health, credentials, websocket
from .core.exceptions import (
    AutomaException,
    http_exception_handler,
    automa_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from .services.scheduler_service import init_scheduler, shutdown_scheduler
from .core.cache import close_redis
from .core.shutdown import graceful_shutdown_agents

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    await init_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()
    await graceful_shutdown_agents()
    await close_redis()


app = FastAPI(
    title="Automa - Python Agent Management Platform",
    description="Web application for managing Python applications and automation agents",
    version="0.1.0",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(AutomaException, automa_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes with rate limiting
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"],
)

# API routes
app.include_router(scripts.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(credentials.router, prefix="/api/v1")

# Health and monitoring routes (no auth required)
app.include_router(health.router, tags=["health"])

# WebSocket route (no auth required - handles connection internally)
app.include_router(websocket.router, tags=["websocket"])


@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    return {
        "message": "Automa - Python Agent Management Platform",
        "version": "0.1.0",
        "docs": "/docs"
    }


# Basic health check is now handled by health router


def main():
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()