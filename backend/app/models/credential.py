from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    credential_type = Column(String(50), nullable=False, index=True)  # api_key, user_pass, oauth, ssh_key, db_connection, custom
    encrypted_data = Column(LargeBinary, nullable=False)  # Encrypted JSON data
    encryption_key_id = Column(String(100), nullable=False)  # Key version for rotation
    tags = Column(JSON)  # For categorization ["aws", "production", "email"]
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))

    # Relationships
    creator = relationship("User", backref="credentials")
    script_credentials = relationship("ScriptCredential", back_populates="credential")


class ScriptCredential(Base):
    __tablename__ = "script_credentials"

    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False, index=True)
    credential_id = Column(Integer, ForeignKey("credentials.id"), nullable=False, index=True)
    variable_name = Column(String(100), nullable=False)  # Environment variable name
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    script = relationship("Script", backref="script_credentials")
    credential = relationship("Credential", back_populates="script_credentials")