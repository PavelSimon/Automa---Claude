from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from fastapi_users.db import SQLAlchemyBaseUserTable
from ..database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile fields
    first_name = Column(String(100))
    last_name = Column(String(100))
    timezone = Column(String(50), default="Europe/Bratislava")
    dark_mode = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())