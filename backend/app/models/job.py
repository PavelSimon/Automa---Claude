from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    name = Column(String(255), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # once, interval, cron
    cron_expression = Column(String(100))
    interval_seconds = Column(Integer)
    next_run = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="jobs")
    creator = relationship("User", backref="jobs")
    executions = relationship("JobExecution", back_populates="job")


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False)  # running, success, failed, timeout
    output = Column(Text)
    error_log = Column(Text)
    exit_code = Column(Integer)

    # Relationships
    job = relationship("Job", back_populates="executions")