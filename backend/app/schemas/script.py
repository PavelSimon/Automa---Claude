from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ScriptBase(BaseModel):
    name: str
    description: Optional[str] = None
    content: Optional[str] = None


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None


class ScriptRead(ScriptBase):
    id: int
    file_path: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True