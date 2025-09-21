from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import create_db_and_tables
from .config import settings
from .core.deps import fastapi_users, auth_backend
from .schemas.user import UserRead, UserCreate
from .api import scripts, agents, jobs, monitoring, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    yield
    # Shutdown


app = FastAPI(
    title="Automa - Python Agent Management Platform",
    description="Web application for managing Python applications and automation agents",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
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


@app.get("/")
async def root():
    return {
        "message": "Automa - Python Agent Management Platform",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


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