from fastapi_users import schemas
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserRead(schemas.BaseUser[int]):
    id: int
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: str = "Europe/Bratislava"
    created_at: datetime


class UserCreate(schemas.BaseUserCreate):
    email: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = "Europe/Bratislava"


class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information only"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = None