from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_session
from ..models.user import User
from ..schemas.job import JobExecutionRead
from ..services.job_service import JobService
from ..services.agent_service import AgentService
from ..services.monitoring_service import MonitoringService
from ..core.deps import current_active_user

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/docker")
async def get_docker_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get Docker system status and container information"""
    monitoring_service = MonitoringService(session)
    try:
        return await monitoring_service.get_docker_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Docker status: {str(e)}")


@router.get("/system")
async def get_system_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get system resource usage (CPU, memory, disk)"""
    monitoring_service = MonitoringService(session)
    try:
        return await monitoring_service.get_system_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get comprehensive dashboard data for monitoring view"""
    agent_service = AgentService(session)
    job_service = JobService(session)
    monitoring_service = MonitoringService(session)

    try:
        # Get agents grouped by status
        all_agents = await agent_service.get_agents(current_user, limit=1000)
        agents_by_status = {}
        for agent in all_agents:
            status = agent.status
            if status not in agents_by_status:
                agents_by_status[status] = []
            agents_by_status[status].append({
                "id": agent.id,
                "name": agent.name,
                "status": agent.status,
                "script_id": agent.script_id
            })

        # Get recent job executions
        recent_executions = await job_service.get_recent_executions(current_user, limit=20)
        executions_data = []
        for execution in recent_executions:
            executions_data.append({
                "id": execution.id,
                "job_id": execution.job_id,
                "job_name": execution.job.name if execution.job else "Unknown",
                "status": execution.status,
                "started_at": execution.started_at.isoformat(),
                "finished_at": execution.finished_at.isoformat() if execution.finished_at else None,
                "output": execution.output[:200] if execution.output else None,  # Truncate for dashboard
                "exit_code": execution.exit_code
            })

        # Get system metrics
        system_status = await monitoring_service.get_system_status()

        return {
            "agents": agents_by_status,
            "running_agents": agents_by_status.get("running", []),
            "recent_executions": executions_data,
            "system": system_status,
            "summary": {
                "total_agents": len(all_agents),
                "running_agents": len(agents_by_status.get("running", [])),
                "stopped_agents": len(agents_by_status.get("stopped", [])),
                "error_agents": len(agents_by_status.get("error", [])),
                "recent_executions_count": len(executions_data)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


# Alias endpoint for frontend compatibility
@router.get("/executions/recent", response_model=List[JobExecutionRead])
async def get_recent_executions(
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get recent job executions (alias for frontend compatibility)"""
    job_service = JobService(session)
    return await job_service.get_recent_executions(current_user, limit)