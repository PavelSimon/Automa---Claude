from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.agent import Agent
from ..models.user import User
from ..schemas.agent import AgentCreate, AgentUpdate
from ..core.audit import log_action


class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent(self, agent_data: AgentCreate, user: User) -> Agent:
        agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            script_id=agent_data.script_id,
            config_json=agent_data.config_json,
            is_active=agent_data.is_active,
            created_by=user.id,
            status="stopped"
        )

        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)

        await log_action(
            self.session,
            user_id=user.id,
            action="create",
            resource_type="agent",
            resource_id=agent.id,
            details={"name": agent.name, "script_id": agent.script_id}
        )

        return agent

    async def get_agents(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Agent]:
        query = select(Agent).where(Agent.created_by == user.id)

        if status:
            query = query.where(Agent.status == status)

        query = query.offset(skip).limit(limit).options(selectinload(Agent.script))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_agent(self, agent_id: int, user: User) -> Optional[Agent]:
        query = select(Agent).where(
            and_(Agent.id == agent_id, Agent.created_by == user.id)
        ).options(selectinload(Agent.script))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_agent(self, agent_id: int, agent_update: AgentUpdate, user: User) -> Optional[Agent]:
        agent = await self.get_agent(agent_id, user)
        if not agent:
            return None

        update_data = agent_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        await self.session.commit()
        await self.session.refresh(agent)

        await log_action(
            self.session,
            user_id=user.id,
            action="update",
            resource_type="agent",
            resource_id=agent.id,
            details=update_data
        )

        return agent

    async def delete_agent(self, agent_id: int, user: User) -> bool:
        agent = await self.get_agent(agent_id, user)
        if not agent:
            return False

        await log_action(
            self.session,
            user_id=user.id,
            action="delete",
            resource_type="agent",
            resource_id=agent.id,
            details={"name": agent.name}
        )

        await self.session.delete(agent)
        await self.session.commit()
        return True

    async def start_agent(self, agent_id: int, user: User) -> Optional[Agent]:
        agent = await self.get_agent(agent_id, user)
        if not agent:
            return None

        # TODO: Implement actual agent starting logic with Docker/sandbox
        agent.status = "running"

        await self.session.commit()
        await self.session.refresh(agent)

        await log_action(
            self.session,
            user_id=user.id,
            action="start",
            resource_type="agent",
            resource_id=agent.id,
            details={"name": agent.name}
        )

        return agent

    async def stop_agent(self, agent_id: int, user: User) -> Optional[Agent]:
        agent = await self.get_agent(agent_id, user)
        if not agent:
            return None

        # TODO: Implement actual agent stopping logic
        agent.status = "stopped"

        await self.session.commit()
        await self.session.refresh(agent)

        await log_action(
            self.session,
            user_id=user.id,
            action="stop",
            resource_type="agent",
            resource_id=agent.id,
            details={"name": agent.name}
        )

        return agent

    async def restart_agent(self, agent_id: int, user: User) -> Optional[Agent]:
        agent = await self.stop_agent(agent_id, user)
        if not agent:
            return None

        return await self.start_agent(agent_id, user)