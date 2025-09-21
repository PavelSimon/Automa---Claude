from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_session
from ..models.user import User
from ..schemas.job import JobCreate, JobRead, JobUpdate, JobExecutionRead
from ..services.job_service import JobService
from ..core.deps import current_active_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobRead)
async def create_job(
    job: JobCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    return await job_service.create_job(job, current_user)


@router.get("/", response_model=List[JobRead])
async def get_jobs(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    return await job_service.get_jobs(current_user, skip, limit)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    job = await job_service.get_job(job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    job = await job_service.update_job(job_id, job_update, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    success = await job_service.delete_job(job_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/execute")
async def execute_job(
    job_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    execution = await job_service.execute_job(job_id, current_user)
    if not execution:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "message": "Job execution started",
        "execution_id": execution.id,
        "status": execution.status
    }


@router.get("/{job_id}/executions", response_model=List[JobExecutionRead])
async def get_job_executions(
    job_id: int,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    job_service = JobService(session)
    return await job_service.get_job_executions(job_id, current_user, skip, limit)