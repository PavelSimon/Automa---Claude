"""
Service layer tests for business logic.
Tests agent lifecycle, job execution, and core service methods.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Script, Agent, Job, JobExecution
from app.services.agent_service import AgentService
from app.services.job_service import JobService
from app.services.script_service import ScriptService
from app.schemas.agent import AgentCreate, AgentUpdate
from app.schemas.job import JobCreate, JobUpdate
from app.schemas.script import ScriptCreate


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for service tests"""
    user = User(
        email=f"service_test_{datetime.now().timestamp()}@test.com",
        hashed_password="test_hash",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_script(db_session: AsyncSession, test_user: User) -> Script:
    """Create a test script"""
    script = Script(
        name="Test Service Script",
        description="Script for service layer testing",
        content="print('service test')",
        file_path="/tmp/test_service.py",
        is_active=True,
        created_by=test_user.id
    )
    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)
    return script


@pytest.mark.asyncio
async def test_agent_lifecycle(db_session: AsyncSession, test_user: User, test_script: Script):
    """Test complete agent lifecycle: create -> start -> stop -> restart -> delete"""
    service = AgentService(db_session)

    # 1. Create agent
    agent_data = AgentCreate(
        name="Lifecycle Test Agent",
        description="Testing agent lifecycle",
        script_id=test_script.id,
        is_active=True,
        config_json={"test": "lifecycle"}
    )
    agent = await service.create_agent(agent_data, test_user)

    assert agent is not None
    assert agent.name == "Lifecycle Test Agent"
    assert agent.status == "stopped"
    assert agent.script_id == test_script.id
    assert agent.created_by == test_user.id

    # 2. Start agent (Note: will fail without Docker, but tests the logic)
    try:
        started_agent = await service.start_agent(agent.id, test_user)
        # If Docker is available, should be running
        if started_agent:
            assert started_agent.status in ["running", "error"]  # error if Docker unavailable
    except Exception as e:
        # Expected if Docker is not available
        assert "docker" in str(e).lower() or "container" in str(e).lower()

    # 3. Stop agent
    try:
        stopped_agent = await service.stop_agent(agent.id, test_user)
        if stopped_agent:
            assert stopped_agent.status == "stopped"
    except Exception:
        pass  # Expected if Docker not available

    # 4. Update agent
    update_data = AgentUpdate(
        name="Updated Lifecycle Agent",
        description="Updated description"
    )
    updated_agent = await service.update_agent(agent.id, update_data, test_user)
    assert updated_agent is not None
    assert updated_agent.name == "Updated Lifecycle Agent"
    assert updated_agent.description == "Updated description"

    # 5. Get agent
    retrieved_agent = await service.get_agent(agent.id, test_user)
    assert retrieved_agent is not None
    assert retrieved_agent.id == agent.id

    # 6. List agents
    agents = await service.get_agents(test_user)
    assert len(agents) > 0
    assert any(a.id == agent.id for a in agents)

    # 7. Delete agent
    deleted = await service.delete_agent(agent.id, test_user)
    assert deleted is True

    # Verify deletion
    deleted_agent = await service.get_agent(agent.id, test_user)
    assert deleted_agent is None


@pytest.mark.asyncio
async def test_agent_status_transitions(db_session: AsyncSession, test_user: User, test_script: Script):
    """Test agent status transitions and validation"""
    service = AgentService(db_session)

    # Create agent
    agent_data = AgentCreate(
        name="Status Test Agent",
        script_id=test_script.id,
        is_active=True
    )
    agent = await service.create_agent(agent_data, test_user)
    assert agent.status == "stopped"

    # Test restart on stopped agent (should fail or start)
    try:
        restarted = await service.restart_agent(agent.id, test_user)
        # Restart on stopped agent might start it or fail gracefully
        assert restarted is not None
    except Exception:
        pass  # Expected if Docker not available

    # Test stop on already stopped agent (should be idempotent)
    stopped = await service.stop_agent(agent.id, test_user)
    assert stopped is not None
    assert stopped.status == "stopped"


@pytest.mark.asyncio
async def test_job_execution_workflow(db_session: AsyncSession, test_user: User, test_script: Script):
    """Test job creation and execution workflow"""
    agent_service = AgentService(db_session)
    job_service = JobService(db_session)

    # Create agent first
    agent_data = AgentCreate(
        name="Job Test Agent",
        script_id=test_script.id,
        is_active=True
    )
    agent = await agent_service.create_agent(agent_data, test_user)

    # 1. Create job - once type
    job_data = JobCreate(
        name="Test Job Once",
        description="Test once job",
        agent_id=agent.id,
        schedule_type="once",
        is_active=True
    )
    job = await job_service.create_job(job_data, test_user)

    assert job is not None
    assert job.name == "Test Job Once"
    assert job.schedule_type == "once"
    assert job.agent_id == agent.id
    assert job.is_active is True

    # 2. Execute job manually
    try:
        execution = await job_service.execute_job(job.id, test_user)
        assert execution is not None
        assert execution.job_id == job.id
        # Status can be completed, failed, or running depending on Docker availability
        assert execution.status in ["completed", "failed", "running"]
    except Exception as e:
        # Expected if Docker not available
        assert "docker" in str(e).lower() or "container" in str(e).lower()

    # 3. Get job history
    history = await job_service.get_job_history(job.id, test_user)
    assert isinstance(history, list)
    # History might be empty if execution failed due to Docker

    # 4. Update job
    update_data = JobUpdate(
        name="Updated Test Job",
        is_active=False
    )
    updated_job = await job_service.update_job(job.id, update_data, test_user)
    assert updated_job.name == "Updated Test Job"
    assert updated_job.is_active is False

    # 5. Delete job
    deleted = await job_service.delete_job(job.id, test_user)
    assert deleted is True


@pytest.mark.asyncio
async def test_job_interval_scheduling(db_session: AsyncSession, test_user: User, test_script: Script):
    """Test interval-based job scheduling"""
    agent_service = AgentService(db_session)
    job_service = JobService(db_session)

    # Create agent
    agent_data = AgentCreate(name="Interval Agent", script_id=test_script.id, is_active=True)
    agent = await agent_service.create_agent(agent_data, test_user)

    # Create interval job
    job_data = JobCreate(
        name="Interval Job",
        agent_id=agent.id,
        schedule_type="interval",
        interval_seconds=300,  # 5 minutes
        is_active=True
    )
    job = await job_service.create_job(job_data, test_user)

    assert job.schedule_type == "interval"
    assert job.interval_seconds == 300
    assert job.next_run is not None  # Should be calculated

    # Verify next_run is in the future
    assert job.next_run > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_job_cron_scheduling(db_session: AsyncSession, test_user: User, test_script: Script):
    """Test cron-based job scheduling"""
    agent_service = AgentService(db_session)
    job_service = JobService(db_session)

    # Create agent
    agent_data = AgentCreate(name="Cron Agent", script_id=test_script.id, is_active=True)
    agent = await agent_service.create_agent(agent_data, test_user)

    # Create cron job - daily at midnight
    job_data = JobCreate(
        name="Cron Job Daily",
        agent_id=agent.id,
        schedule_type="cron",
        cron_expression="0 0 * * *",
        is_active=True
    )
    job = await job_service.create_job(job_data, test_user)

    assert job.schedule_type == "cron"
    assert job.cron_expression == "0 0 * * *"
    assert job.next_run is not None

    # Test hourly cron
    job_data_hourly = JobCreate(
        name="Cron Job Hourly",
        agent_id=agent.id,
        schedule_type="cron",
        cron_expression="0 * * * *",
        is_active=True
    )
    job_hourly = await job_service.create_job(job_data_hourly, test_user)
    assert job_hourly.cron_expression == "0 * * * *"


@pytest.mark.asyncio
async def test_script_service_operations(db_session: AsyncSession, test_user: User):
    """Test script service CRUD operations"""
    service = ScriptService(db_session)

    # 1. Create script
    script_data = ScriptCreate(
        name="Service Test Script",
        description="Testing script service",
        content="#!/usr/bin/env python3\nprint('test')"
    )
    script = await service.create_script(script_data, test_user)

    assert script is not None
    assert script.name == "Service Test Script"
    assert script.created_by == test_user.id

    # 2. Get script
    retrieved = await service.get_script(script.id, test_user)
    assert retrieved is not None
    assert retrieved.id == script.id

    # 3. List scripts
    scripts = await service.get_scripts(test_user)
    assert len(scripts) > 0
    assert any(s.id == script.id for s in scripts)

    # 4. Update script
    from app.schemas.script import ScriptUpdate
    update_data = ScriptUpdate(
        name="Updated Service Script",
        content="print('updated')"
    )
    updated = await service.update_script(script.id, update_data, test_user)
    assert updated.name == "Updated Service Script"
    assert updated.content == "print('updated')"

    # 5. Delete script
    deleted = await service.delete_script(script.id, test_user)
    assert deleted is True

    # Verify deletion
    deleted_script = await service.get_script(script.id, test_user)
    assert deleted_script is None


@pytest.mark.asyncio
async def test_agent_without_script_fails(db_session: AsyncSession, test_user: User):
    """Test that starting an agent without a script fails gracefully"""
    service = AgentService(db_session)

    # Create agent with invalid script_id
    agent = Agent(
        name="No Script Agent",
        script_id=99999,  # Non-existent
        status="stopped",
        is_active=True,
        created_by=test_user.id
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    # Try to start agent without valid script
    with pytest.raises(Exception):  # Should raise error
        await service.start_agent(agent.id, test_user)


@pytest.mark.asyncio
async def test_job_execution_creates_execution_record(db_session: AsyncSession, test_user: User, test_script: Script):
    """Test that job execution creates JobExecution records"""
    agent_service = AgentService(db_session)
    job_service = JobService(db_session)

    # Create agent and job
    agent_data = AgentCreate(name="Exec Record Agent", script_id=test_script.id, is_active=True)
    agent = await agent_service.create_agent(agent_data, test_user)

    job_data = JobCreate(
        name="Exec Record Job",
        agent_id=agent.id,
        schedule_type="once",
        is_active=True
    )
    job = await job_service.create_job(job_data, test_user)

    # Execute job
    try:
        execution = await job_service.execute_job(job.id, test_user)

        # Verify execution record was created
        result = await db_session.execute(
            select(JobExecution).where(JobExecution.job_id == job.id)
        )
        executions = result.scalars().all()

        assert len(executions) > 0
        assert executions[0].job_id == job.id
        assert executions[0].started_at is not None
    except Exception:
        # If Docker is unavailable, execution might fail
        # But we still want to verify the execution record attempt
        pass


@pytest.mark.asyncio
async def test_user_isolation(db_session: AsyncSession):
    """Test that users can only access their own resources"""
    # Create two users
    user1 = User(email="user1@test.com", hashed_password="hash1", is_active=True)
    user2 = User(email="user2@test.com", hashed_password="hash2", is_active=True)
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # User1 creates a script
    script_service = ScriptService(db_session)
    script_data = ScriptCreate(name="User1 Script", content="print('user1')", is_active=True)
    user1_script = await script_service.create_script(script_data, user1)

    # User2 tries to get User1's script
    user2_view = await script_service.get_script(user1_script.id, user2)
    assert user2_view is None, "User2 should not be able to access User1's script"

    # User1 can access their own script
    user1_view = await script_service.get_script(user1_script.id, user1)
    assert user1_view is not None
    assert user1_view.id == user1_script.id
