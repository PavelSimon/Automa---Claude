from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_session
from ..models.user import User
from ..schemas.script import ScriptCreate, ScriptRead, ScriptUpdate
from ..services.script_service import ScriptService
from ..core.deps import current_active_user

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.post("/", response_model=ScriptRead)
async def create_script(
    script: ScriptCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
    file: UploadFile = File(None)
):
    script_service = ScriptService(session)
    return await script_service.create_script(script, current_user, file)


@router.get("/", response_model=List[ScriptRead])
async def get_scripts(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    script_service = ScriptService(session)
    return await script_service.get_scripts(current_user, skip, limit)


@router.get("/{script_id}", response_model=ScriptRead)
async def get_script(
    script_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    script_service = ScriptService(session)
    script = await script_service.get_script(script_id, current_user)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.put("/{script_id}", response_model=ScriptRead)
async def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    script_service = ScriptService(session)
    script = await script_service.update_script(script_id, script_update, current_user)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    script_service = ScriptService(session)
    success = await script_service.delete_script(script_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"message": "Script deleted successfully"}