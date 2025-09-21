from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_session
from ..models.user import User
from ..schemas.agent import AgentCreate, AgentRead, AgentUpdate
from ..services.agent_service import AgentService
from ..core.deps import current_active_user

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=AgentRead)
async def create_agent(
    agent: AgentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    return await agent_service.create_agent(agent, current_user)


@router.get("/", response_model=List[AgentRead])
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    return await agent_service.get_agents(current_user, skip, limit, status)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    agent = await agent_service.get_agent(agent_id, current_user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    agent = await agent_service.update_agent(agent_id, agent_update, current_user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    success = await agent_service.delete_agent(agent_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    agent = await agent_service.start_agent(agent_id, current_user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": f"Agent {agent.name} started successfully", "status": agent.status}


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    agent = await agent_service.stop_agent(agent_id, current_user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": f"Agent {agent.name} stopped successfully", "status": agent.status}


@router.post("/{agent_id}/restart")
async def restart_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    agent_service = AgentService(session)
    agent = await agent_service.restart_agent(agent_id, current_user)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": f"Agent {agent.name} restarted successfully", "status": agent.status}