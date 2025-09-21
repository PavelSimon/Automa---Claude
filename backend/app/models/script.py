from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    content = Column(Text)
    is_file_based = Column(Boolean, default=False)  # True if script uses external file, False if inline content
    external_file_path = Column(String(500))  # Path to external .py file if is_file_based=True
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", backref="scripts")
    agents = relationship("Agent", back_populates="script")