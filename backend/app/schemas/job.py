from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JobBase(BaseModel):
    agent_id: int
    name: str
    schedule_type: str  # once, interval, cron
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    is_active: bool = True


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    name: Optional[str] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    is_active: Optional[bool] = None


class JobRead(JobBase):
    id: int
    next_run: Optional[datetime] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobExecutionRead(BaseModel):
    id: int
    job_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    output: Optional[str] = None
    error_log: Optional[str] = None
    exit_code: Optional[int] = None

    class Config:
        from_attributes = True