from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_session
from ..models.user import User
from ..schemas.user import UserRead, UserProfileUpdate
from ..core.deps import current_active_user
from ..core.audit import log_action

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserRead)
async def get_my_profile(
    current_user: User = Depends(current_active_user),
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Update current user's profile"""
    try:
        # Update user fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)

        await session.commit()
        await session.refresh(current_user)

        # Log the profile update
        await log_action(
            session,
            user_id=current_user.id,
            action="update_profile",
            resource_type="user",
            resource_id=current_user.id,
            details={"updated_fields": list(update_data.keys())}
        )

        return current_user

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.get("/timezones")
async def get_available_timezones():
    """Get list of available timezones"""
    # Common timezones for users to choose from
    timezones = [
        {"value": "Europe/Bratislava", "label": "Europe/Bratislava (CET/CEST)"},
        {"value": "Europe/Prague", "label": "Europe/Prague (CET/CEST)"},
        {"value": "Europe/Vienna", "label": "Europe/Vienna (CET/CEST)"},
        {"value": "Europe/Budapest", "label": "Europe/Budapest (CET/CEST)"},
        {"value": "Europe/Warsaw", "label": "Europe/Warsaw (CET/CEST)"},
        {"value": "Europe/Berlin", "label": "Europe/Berlin (CET/CEST)"},
        {"value": "Europe/London", "label": "Europe/London (GMT/BST)"},
        {"value": "Europe/Paris", "label": "Europe/Paris (CET/CEST)"},
        {"value": "Europe/Rome", "label": "Europe/Rome (CET/CEST)"},
        {"value": "Europe/Amsterdam", "label": "Europe/Amsterdam (CET/CEST)"},
        {"value": "Europe/Stockholm", "label": "Europe/Stockholm (CET/CEST)"},
        {"value": "Europe/Helsinki", "label": "Europe/Helsinki (EET/EEST)"},
        {"value": "Europe/Moscow", "label": "Europe/Moscow (MSK)"},
        {"value": "US/Eastern", "label": "US/Eastern (EST/EDT)"},
        {"value": "US/Central", "label": "US/Central (CST/CDT)"},
        {"value": "US/Mountain", "label": "US/Mountain (MST/MDT)"},
        {"value": "US/Pacific", "label": "US/Pacific (PST/PDT)"},
        {"value": "UTC", "label": "UTC (Coordinated Universal Time)"},
        {"value": "Asia/Tokyo", "label": "Asia/Tokyo (JST)"},
        {"value": "Asia/Shanghai", "label": "Asia/Shanghai (CST)"},
        {"value": "Australia/Sydney", "label": "Australia/Sydney (AEST/AEDT)"}
    ]

    return {"timezones": timezones}