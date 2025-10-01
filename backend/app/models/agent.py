from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    config_json = Column(JSON)
    is_active = Column(Boolean, default=True, index=True)
    status = Column(String(50), default="stopped", index=True)  # stopped, running, error
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Relationships
    script = relationship("Script", back_populates="agents")
    creator = relationship("User", backref="agents")
    jobs = relationship("Job", back_populates="agent", cascade="all, delete-orphan")

    @property
    def is_deleted(self):
        """Check if agent is soft deleted"""
        return self.deleted_at is not None