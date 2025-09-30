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
        ).options(selectinload(Agent.script), selectinload(Agent.jobs))

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

        # Check if agent has a script assigned
        if not agent.script:
            raise ValueError("Agent has no script assigned")

        # Check if agent is already running
        if agent.status == "running":
            return agent

        # Start the agent in Docker sandbox
        from .sandbox_service import SandboxService
        sandbox = SandboxService()

        try:
            # For long-running agents, start container in detached mode
            container_id = await sandbox.start_agent_container(
                script=agent.script,
                agent_id=agent.id,
                config=agent.config_json or {}
            )

            # Update agent status and store container ID
            agent.status = "running"
            agent.config_json = agent.config_json or {}
            agent.config_json["container_id"] = container_id

            await self.session.commit()
            await self.session.refresh(agent)

            await log_action(
                self.session,
                user_id=user.id,
                action="start",
                resource_type="agent",
                resource_id=agent.id,
                details={"name": agent.name, "container_id": container_id}
            )

        except Exception as e:
            agent.status = "error"
            await self.session.commit()
            await self.session.refresh(agent)

            await log_action(
                self.session,
                user_id=user.id,
                action="start_failed",
                resource_type="agent",
                resource_id=agent.id,
                details={"name": agent.name, "error": str(e)}
            )
            raise

        return agent

    async def stop_agent(self, agent_id: int, user: User) -> Optional[Agent]:
        agent = await self.get_agent(agent_id, user)
        if not agent:
            return None

        # Check if agent is already stopped
        if agent.status == "stopped":
            return agent

        # Stop the Docker container if it exists
        container_id = None
        if agent.config_json and "container_id" in agent.config_json:
            container_id = agent.config_json["container_id"]

            from .sandbox_service import SandboxService
            sandbox = SandboxService()

            try:
                await sandbox.stop_agent_container(container_id)

                # Remove container_id from config
                del agent.config_json["container_id"]

            except Exception as e:
                # Log error but continue with status update
                await log_action(
                    self.session,
                    user_id=user.id,
                    action="stop_container_failed",
                    resource_type="agent",
                    resource_id=agent.id,
                    details={"name": agent.name, "container_id": container_id, "error": str(e)}
                )

        agent.status = "stopped"
        await self.session.commit()
        await self.session.refresh(agent)

        await log_action(
            self.session,
            user_id=user.id,
            action="stop",
            resource_type="agent",
            resource_id=agent.id,
            details={"name": agent.name, "container_id": container_id}
        )

        return agent

    async def restart_agent(self, agent_id: int, user: User) -> Optional[Agent]:
        agent = await self.stop_agent(agent_id, user)
        if not agent:
            return None

        return await self.start_agent(agent_id, user)