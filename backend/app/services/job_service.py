from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.job import Job, JobExecution
from ..models.user import User
from ..schemas.job import JobCreate, JobUpdate
from ..core.audit import log_action
from croniter import croniter


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
        elif job_data.schedule_type == "cron" and job_data.cron_expression:
            # Parse cron expression and get next run time
            try:
                cron = croniter(job_data.cron_expression, datetime.now(timezone.utc))
                next_run = cron.get_next(datetime)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {job_data.cron_expression}") from e

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

        # Schedule job if active
        if job.is_active:
            from .scheduler_service import get_scheduler
            try:
                scheduler = get_scheduler()
                await scheduler.schedule_job(job)
            except Exception as e:
                # Log but don't fail if scheduler not available
                pass

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
        ).options(selectinload(Job.agent), selectinload(Job.executions))

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
        if "schedule_type" in update_data or "interval_seconds" in update_data or "cron_expression" in update_data:
            if job.schedule_type == "interval" and job.interval_seconds:
                job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)
            elif job.schedule_type == "cron" and job.cron_expression:
                try:
                    cron = croniter(job.cron_expression, datetime.now(timezone.utc))
                    job.next_run = cron.get_next(datetime)
                except Exception as e:
                    raise ValueError(f"Invalid cron expression: {job.cron_expression}") from e

        await self.session.commit()
        await self.session.refresh(job)

        # Reschedule job
        from .scheduler_service import get_scheduler
        try:
            scheduler = get_scheduler()
            if job.is_active:
                await scheduler.schedule_job(job)
            else:
                await scheduler.unschedule_job(job.id)
        except Exception as e:
            # Log but don't fail if scheduler not available
            pass

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

        # Unschedule job first
        from .scheduler_service import get_scheduler
        try:
            scheduler = get_scheduler()
            await scheduler.unschedule_job(job.id)
        except Exception as e:
            # Log but don't fail if scheduler not available
            pass

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

        # Check if job has an agent with a script
        if not job.agent or not job.agent.script:
            raise ValueError("Job's agent has no script assigned")

        execution = JobExecution(
            job_id=job.id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )

        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)

        # Execute the job's script in sandbox
        from .sandbox_service import SandboxService
        sandbox = SandboxService()

        try:
            result = await sandbox.execute_script(
                script=job.agent.script,
                config=job.agent.config_json
            )

            # Update execution with results
            execution.status = result["status"]
            execution.finished_at = datetime.now(timezone.utc)
            execution.output = result["output"]
            execution.exit_code = result["exit_code"]

            if result["error"]:
                execution.error_message = result["error"]

        except Exception as e:
            execution.status = "failed"
            execution.finished_at = datetime.now(timezone.utc)
            execution.error_message = str(e)
            execution.exit_code = -1

        await self.session.commit()
        await self.session.refresh(execution)

        # Update next_run time for recurring jobs
        if job.schedule_type == "interval" and job.interval_seconds:
            job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)
            await self.session.commit()

        await log_action(
            self.session,
            user_id=user.id,
            action="execute",
            resource_type="job",
            resource_id=job.id,
            details={"execution_id": execution.id, "status": execution.status}
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

    async def get_recent_executions(self, user: User, limit: int = 1000) -> List[JobExecution]:
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