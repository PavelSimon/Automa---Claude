from sqlalchemy.ext.asyncio import AsyncSession
from ..models.audit import AuditLog
from ..models.user import User
from fastapi import Request
from typing import Optional, Dict, Any


async def log_action(
    session: AsyncSession,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    session.add(audit_log)
    await session.commit()


async def log_audit_event(
    session: AsyncSession,
    user: Optional[User],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    return await log_action(
        session=session,
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )