from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.job import Job, JobExecution
from ..models.user import User
from ..schemas.job import JobCreate, JobUpdate
from ..core.audit import log_action


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(self, job_data: JobCreate, user: User) -> Job:
        # Calculate next_run based on schedule_type
        next_run = None
        if job_data.schedule_type == "once":
            next_run = datetime.now(timezone.utc) + timedelta(minutes=1)  # Run in 1 minute
        elif job_data.schedule_type == "interval" and job_data.interval_seconds:
            next_run = datetime.now(timezone.utc) + timedelta(seconds=job_data.interval_seconds)
        # TODO: Add cron parsing for cron_expression

        job = Job(
            agent_id=job_data.agent_id,
            name=job_data.name,
            schedule_type=job_data.schedule_type,
            cron_expression=job_data.cron_expression,
            interval_seconds=job_data.interval_seconds,
            next_run=next_run,
            is_active=job_data.is_active,
            created_by=user.id
        )

        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        await log_action(
            self.session,
            user_id=user.id,
            action="create",
            resource_type="job",
            resource_id=job.id,
            details={"name": job.name, "agent_id": job.agent_id, "schedule_type": job.schedule_type}
        )

        return job

    async def get_jobs(self, user: User, skip: int = 0, limit: int = 100) -> List[Job]:
        query = select(Job).where(Job.created_by == user.id)\
            .offset(skip).limit(limit)\
            .options(selectinload(Job.agent))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_job(self, job_id: int, user: User) -> Optional[Job]:
        query = select(Job).where(
            and_(Job.id == job_id, Job.created_by == user.id)
        ).options(selectinload(Job.agent))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_job(self, job_id: int, job_update: JobUpdate, user: User) -> Optional[Job]:
        job = await self.get_job(job_id, user)
        if not job:
            return None

        update_data = job_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        # Recalculate next_run if schedule changed
        if "schedule_type" in update_data or "interval_seconds" in update_data:
            if job.schedule_type == "interval" and job.interval_seconds:
                job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)

        await self.session.commit()
        await self.session.refresh(job)

        await log_action(
            self.session,
            user_id=user.id,
            action="update",
            resource_type="job",
            resource_id=job.id,
            details=update_data
        )

        return job

    async def delete_job(self, job_id: int, user: User) -> bool:
        job = await self.get_job(job_id, user)
        if not job:
            return False

        await log_action(
            self.session,
            user_id=user.id,
            action="delete",
            resource_type="job",
            resource_id=job.id,
            details={"name": job.name}
        )

        await self.session.delete(job)
        await self.session.commit()
        return True

    async def execute_job(self, job_id: int, user: User) -> Optional[JobExecution]:
        job = await self.get_job(job_id, user)
        if not job:
            return None

        execution = JobExecution(
            job_id=job.id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )

        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)

        # TODO: Implement actual job execution logic
        # For now, simulate immediate completion
        execution.status = "success"
        execution.finished_at = datetime.now(timezone.utc)
        execution.output = f"Job {job.name} executed successfully"
        execution.exit_code = 0

        await self.session.commit()
        await self.session.refresh(execution)

        await log_action(
            self.session,
            user_id=user.id,
            action="execute",
            resource_type="job",
            resource_id=job.id,
            details={"execution_id": execution.id}
        )

        return execution

    async def get_job_executions(
        self,
        job_id: int,
        user: User,
        skip: int = 0,
        limit: int = 50
    ) -> List[JobExecution]:
        # Verify user owns the job
        job = await self.get_job(job_id, user)
        if not job:
            return []

        query = select(JobExecution).where(JobExecution.job_id == job_id)\
            .order_by(JobExecution.started_at.desc())\
            .offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_executions(self, user: User, limit: int = 10) -> List[JobExecution]:
        """Get recent job executions for monitoring dashboard"""
        query = select(JobExecution)\
            .join(Job)\
            .where(Job.created_by == user.id)\
            .order_by(JobExecution.started_at.desc())\
            .limit(limit)\
            .options(
                selectinload(JobExecution.job).selectinload(Job.agent)
            )

        result = await self.session.execute(query)
        return result.scalars().all()