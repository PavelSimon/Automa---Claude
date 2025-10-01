"""
Graceful shutdown utilities for application cleanup.
Handles proper cleanup of running agents and resources.
"""
import logging
from sqlalchemy import select
from ..database import AsyncSessionLocal
from ..models.agent import Agent
from ..services.sandbox_service import SandboxService

logger = logging.getLogger(__name__)


async def graceful_shutdown_agents():
    """
    Gracefully shutdown all running agents on application shutdown.
    Stops all Docker containers associated with running agents.
    """
    logger.info("Starting graceful shutdown of agents...")

    try:
        async with AsyncSessionLocal() as session:
            # Get all running agents
            result = await session.execute(
                select(Agent).where(Agent.status == "running")
            )
            running_agents = result.scalars().all()

            if not running_agents:
                logger.info("No running agents to shutdown")
                return

            logger.info(f"Found {len(running_agents)} running agents to shutdown")

            sandbox = SandboxService()
            shutdown_count = 0
            error_count = 0

            for agent in running_agents:
                try:
                    # Get container ID from agent config
                    container_id = None
                    if agent.config_json and "container_id" in agent.config_json:
                        container_id = agent.config_json["container_id"]

                    if container_id:
                        logger.info(f"Stopping agent {agent.id} (container: {container_id})")
                        await sandbox.stop_agent_container(container_id, timeout=10)

                        # Update agent status
                        agent.status = "stopped"
                        if agent.config_json and "container_id" in agent.config_json:
                            del agent.config_json["container_id"]

                        shutdown_count += 1
                    else:
                        # Agent marked as running but has no container ID
                        logger.warning(f"Agent {agent.id} marked as running but has no container_id")
                        agent.status = "stopped"
                        error_count += 1

                except Exception as e:
                    logger.error(f"Error stopping agent {agent.id}: {str(e)}")
                    # Mark as stopped anyway to prevent orphaned status
                    agent.status = "error"
                    error_count += 1

            # Commit all status updates
            await session.commit()

            logger.info(
                f"Graceful shutdown complete: {shutdown_count} agents stopped, "
                f"{error_count} errors"
            )

    except Exception as e:
        logger.error(f"Error during graceful shutdown: {str(e)}")
        # Don't raise - we want the application to shutdown even if cleanup fails


async def cleanup_orphaned_containers():
    """
    Cleanup orphaned Docker containers that are running but have no associated agent.
    This is a maintenance function that should be called periodically.
    """
    logger.info("Checking for orphaned containers...")

    try:
        sandbox = SandboxService()

        # Get all automa containers
        all_containers = await sandbox.list_agent_containers()

        async with AsyncSessionLocal() as session:
            # Get all running agents with container IDs
            result = await session.execute(
                select(Agent).where(Agent.status == "running")
            )
            running_agents = result.scalars().all()

            active_container_ids = set()
            for agent in running_agents:
                if agent.config_json and "container_id" in agent.config_json:
                    active_container_ids.add(agent.config_json["container_id"])

            # Find orphaned containers
            orphaned_count = 0
            for container in all_containers:
                if container["id"] not in active_container_ids:
                    logger.warning(f"Found orphaned container: {container['id']}")
                    try:
                        await sandbox.stop_agent_container(container["id"])
                        orphaned_count += 1
                    except Exception as e:
                        logger.error(f"Error stopping orphaned container {container['id']}: {str(e)}")

            if orphaned_count > 0:
                logger.info(f"Cleaned up {orphaned_count} orphaned containers")
            else:
                logger.info("No orphaned containers found")

    except Exception as e:
        logger.error(f"Error during orphaned container cleanup: {str(e)}")


async def emergency_stop_all_agents():
    """
    Emergency stop for all agents - forcefully stops all containers.
    Use only in emergency situations.
    """
    logger.warning("EMERGENCY STOP: Forcefully stopping all agent containers")

    try:
        sandbox = SandboxService()
        all_containers = await sandbox.list_agent_containers()

        stopped_count = 0
        for container in all_containers:
            try:
                await sandbox.stop_agent_container(container["id"], timeout=5)
                stopped_count += 1
            except Exception as e:
                logger.error(f"Error in emergency stop of container {container['id']}: {str(e)}")

        logger.warning(f"Emergency stop complete: {stopped_count} containers stopped")

        # Update all agents to stopped status
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Agent))
            all_agents = result.scalars().all()

            for agent in all_agents:
                if agent.status == "running":
                    agent.status = "stopped"
                    if agent.config_json and "container_id" in agent.config_json:
                        del agent.config_json["container_id"]

            await session.commit()

    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
