"""
WebSocket endpoints for real-time updates.

Provides live updates for agent status changes, job executions,
and system metrics to connected clients.
"""

import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Sends messages with the following format:
    {
        "type": "agent_status_change" | "job_execution_complete" | "system_metrics",
        "data": {...}
    }
    """
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "message": "WebSocket connected successfully"
        }, websocket)

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
                continue

            # Echo back for testing (can be removed in production)
            try:
                message = json.loads(data)
                logger.debug(f"Received WebSocket message: {message}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_agent_status_change(agent_id: int, status: str, user_id: int = None):
    """
    Broadcast agent status change to all connected clients.

    Args:
        agent_id: ID of the agent
        status: New status (running, stopped, error)
        user_id: Optional user ID for filtering
    """
    message = {
        "type": "agent_status_change",
        "data": {
            "agent_id": agent_id,
            "status": status,
            "user_id": user_id
        }
    }
    await manager.broadcast(message)


async def broadcast_job_execution_complete(job_id: int, execution_id: int, status: str, user_id: int = None):
    """
    Broadcast job execution completion to all connected clients.

    Args:
        job_id: ID of the job
        execution_id: ID of the execution
        status: Execution status (success, failed, timeout)
        user_id: Optional user ID for filtering
    """
    message = {
        "type": "job_execution_complete",
        "data": {
            "job_id": job_id,
            "execution_id": execution_id,
            "status": status,
            "user_id": user_id
        }
    }
    await manager.broadcast(message)


async def broadcast_system_metrics(metrics: dict):
    """
    Broadcast system metrics to all connected clients.

    Args:
        metrics: Dictionary containing system metrics (CPU, memory, etc.)
    """
    message = {
        "type": "system_metrics",
        "data": metrics
    }
    await manager.broadcast(message)
