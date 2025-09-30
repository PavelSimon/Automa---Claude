from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import Optional
import logging

from ..models.job import Job
from ..database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                'coalesce': False,  # Run all missed executions
                'max_instances': 3,  # Allow max 3 concurrent instances per job
                'misfire_grace_time': 300  # 5 minutes grace period
            }
        )
        self.scheduler.add_listener(self._job_error_listener, mask=0b111)

    def _job_error_listener(self, event):
        """Listen for scheduler errors"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")

    async def start(self):
        """Start the scheduler and load all active jobs"""
        self.scheduler.start()
        await self._load_all_jobs()
        logger.info("Scheduler started successfully")

    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")

    async def _load_all_jobs(self):
        """Load all active jobs from database"""
        async with AsyncSessionLocal() as session:
            query = select(Job).where(Job.is_active == True).options(
                selectinload(Job.agent).selectinload(Job.agent.script)
            )
            result = await session.execute(query)
            jobs = result.scalars().all()

            for job in jobs:
                try:
                    await self.schedule_job(job)
                    logger.info(f"Loaded job: {job.name} (ID: {job.id})")
                except Exception as e:
                    logger.error(f"Failed to load job {job.name} (ID: {job.id}): {e}")

    async def schedule_job(self, job: Job):
        """Schedule a job based on its configuration"""
        job_id = f"job_{job.id}"

        # Remove existing job if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Determine trigger type
        trigger = None
        if job.schedule_type == "cron" and job.cron_expression:
            try:
                trigger = CronTrigger.from_crontab(job.cron_expression, timezone="UTC")
            except Exception as e:
                logger.error(f"Invalid cron expression for job {job.id}: {e}")
                raise ValueError(f"Invalid cron expression: {job.cron_expression}")

        elif job.schedule_type == "interval" and job.interval_seconds:
            trigger = IntervalTrigger(seconds=job.interval_seconds, timezone="UTC")

        elif job.schedule_type == "once" and job.next_run:
            trigger = DateTrigger(run_date=job.next_run, timezone="UTC")

        else:
            raise ValueError(f"Invalid schedule configuration for job {job.id}")

        # Schedule the job
        self.scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            id=job_id,
            args=[job.id],
            replace_existing=True,
            name=f"{job.name} (ID: {job.id})"
        )

        logger.info(f"Scheduled job: {job.name} (ID: {job.id}, Type: {job.schedule_type})")

    async def unschedule_job(self, job_id: int):
        """Remove a job from the scheduler"""
        scheduler_job_id = f"job_{job_id}"
        if self.scheduler.get_job(scheduler_job_id):
            self.scheduler.remove_job(scheduler_job_id)
            logger.info(f"Unscheduled job ID: {job_id}")

    async def _execute_job(self, job_id: int):
        """Execute a job (called by scheduler)"""
        async with AsyncSessionLocal() as session:
            try:
                # Load job with relationships
                query = select(Job).where(Job.id == job_id).options(
                    selectinload(Job.agent).selectinload(Job.agent.script)
                )
                result = await session.execute(query)
                job = result.scalar_one_or_none()

                if not job:
                    logger.error(f"Job {job_id} not found")
                    return

                if not job.is_active:
                    logger.info(f"Job {job_id} is inactive, skipping execution")
                    return

                # Execute the job via JobService
                from .job_service import JobService
                from ..models.user import User

                # Get job owner
                owner_query = select(User).where(User.id == job.created_by)
                owner_result = await session.execute(owner_query)
                owner = owner_result.scalar_one_or_none()

                if not owner:
                    logger.error(f"Job owner not found for job {job_id}")
                    return

                job_service = JobService(session)
                execution = await job_service.execute_job(job_id, owner)

                if execution:
                    logger.info(f"Job {job_id} executed successfully (Execution ID: {execution.id})")
                else:
                    logger.error(f"Failed to execute job {job_id}")

                # For "once" jobs, deactivate after execution
                if job.schedule_type == "once":
                    job.is_active = False
                    await session.commit()
                    await self.unschedule_job(job_id)
                    logger.info(f"Job {job_id} completed (once), deactivated")

            except Exception as e:
                logger.error(f"Error executing job {job_id}: {e}", exc_info=True)
                await session.rollback()

    def get_scheduled_jobs(self):
        """Get list of all currently scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs


# Global scheduler instance
scheduler_service: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get global scheduler instance"""
    global scheduler_service
    if scheduler_service is None:
        raise RuntimeError("Scheduler not initialized")
    return scheduler_service


async def init_scheduler():
    """Initialize global scheduler"""
    global scheduler_service
    scheduler_service = SchedulerService()
    await scheduler_service.start()


def shutdown_scheduler():
    """Shutdown global scheduler"""
    global scheduler_service
    if scheduler_service:
        scheduler_service.shutdown()
        scheduler_service = None
