from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index('ix_job_active_nextrun', 'is_active', 'next_run'),
        Index('ix_job_user_active', 'created_by', 'is_active'),
        Index('ix_job_agent_active', 'agent_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    schedule_type = Column(String(50), nullable=False, index=True)  # once, interval, cron
    cron_expression = Column(String(100))
    interval_seconds = Column(Integer)
    next_run = Column(DateTime(timezone=True), index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Relationships
    agent = relationship("Agent", back_populates="jobs")
    creator = relationship("User", backref="jobs")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")

    @property
    def is_deleted(self):
        """Check if job is soft deleted"""
        return self.deleted_at is not None


class JobExecution(Base):
    __tablename__ = "job_executions"
    __table_args__ = (
        Index('ix_execution_job_started', 'job_id', 'started_at'),
        Index('ix_execution_status_started', 'status', 'started_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False, index=True)  # running, success, failed, timeout
    output = Column(Text)
    error_log = Column(Text)
    exit_code = Column(Integer)

    # Relationships
    job = relationship("Job", back_populates="executions")