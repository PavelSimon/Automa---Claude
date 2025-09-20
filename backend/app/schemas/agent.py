from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    script_id: int
    config_json: Optional[Dict[str, Any]] = None
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentRead(AgentBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True