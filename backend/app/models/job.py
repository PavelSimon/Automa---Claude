from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    schedule_type = Column(String(50), nullable=False, index=True)  # once, interval, cron
    cron_expression = Column(String(100))
    interval_seconds = Column(Integer)
    next_run = Column(DateTime(timezone=True), index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="jobs")
    creator = relationship("User", backref="jobs")
    executions = relationship("JobExecution", back_populates="job")


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False, index=True)  # running, success, failed, timeout
    output = Column(Text)
    error_log = Column(Text)
    exit_code = Column(Integer)

    # Relationships
    job = relationship("Job", back_populates="executions")