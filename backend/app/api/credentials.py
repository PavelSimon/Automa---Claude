from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_async_session
from ..core.deps import current_active_user
from ..models.user import User
from ..services.credential_service import CredentialService
from ..schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialRead,
    CredentialDecryptRequest, CredentialDecryptResponse,
    CredentialTestResponse, CredentialType, SUPPORTED_CREDENTIAL_TYPES,
    ScriptCredentialCreate, ScriptCredentialRead, ScriptCredentialUpdate
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/credentials/", response_model=CredentialRead)
@limiter.limit("10/minute")
async def create_credential(
    request: Request,
    credential: CredentialCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Create a new encrypted credential"""
    try:
        service = CredentialService(session)
        db_credential = await service.create_credential(credential, current_user)
        return db_credential
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create credential: {str(e)}")


@router.get("/credentials/", response_model=List[CredentialRead])
async def list_credentials(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    credential_type: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """List user's credentials with filtering options"""
    try:
        service = CredentialService(session)
        credentials = await service.get_credentials(
            current_user,
            skip=skip,
            limit=limit,
            credential_type=credential_type,
            tags=tags,
            search=search
        )
        return credentials
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list credentials: {str(e)}")


@router.get("/credentials/{credential_id}", response_model=CredentialRead)
async def get_credential(
    credential_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get a specific credential by ID (metadata only)"""
    service = CredentialService(session)
    credential = await service.get_credential(credential_id, current_user)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    return credential


@router.put("/credentials/{credential_id}", response_model=CredentialRead)
async def update_credential(
    credential_id: int,
    credential_update: CredentialUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Update a credential"""
    try:
        service = CredentialService(session)
        credential = await service.update_credential(credential_id, credential_update, current_user)
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
        return credential
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update credential: {str(e)}")


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Delete a credential"""
    try:
        service = CredentialService(session)
        success = await service.delete_credential(credential_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Credential not found")
        return {"message": "Credential deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete credential: {str(e)}")


@router.post("/credentials/{credential_id}/decrypt", response_model=CredentialDecryptResponse)
@limiter.limit("5/minute")
async def decrypt_credential(
    request: Request,
    credential_id: int,
    decrypt_request: CredentialDecryptRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Decrypt credential data (requires user password)"""
    try:
        service = CredentialService(session)
        result = await service.decrypt_credential(credential_id, decrypt_request.user_password, current_user)
        return CredentialDecryptResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt credential: {str(e)}")


@router.post("/credentials/{credential_id}/test", response_model=CredentialTestResponse)
@limiter.limit("5/minute")
async def test_credential(
    request: Request,
    credential_id: int,
    test_request: CredentialDecryptRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Test credential validity"""
    try:
        service = CredentialService(session)
        result = await service.test_credential(credential_id, test_request.user_password, current_user)
        return CredentialTestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test credential: {str(e)}")


@router.get("/credentials/types/", response_model=List[CredentialType])
async def get_credential_types():
    """Get supported credential types"""
    return SUPPORTED_CREDENTIAL_TYPES


# Script-Credential Association Endpoints

@router.get("/scripts/{script_id}/credentials/", response_model=List[ScriptCredentialRead])
async def get_script_credentials(
    script_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get all credentials assigned to a script"""
    try:
        service = CredentialService(session)
        assignments = await service.get_script_credentials(script_id, current_user)
        return assignments
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get script credentials: {str(e)}")


@router.post("/scripts/{script_id}/credentials/", response_model=ScriptCredentialRead)
async def assign_credential_to_script(
    script_id: int,
    assignment: ScriptCredentialCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Assign a credential to a script"""
    try:
        service = CredentialService(session)
        result = await service.assign_credential_to_script(script_id, assignment, current_user)

        # Reload with relationships for response
        await session.refresh(result, ["credential"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign credential to script: {str(e)}")


@router.delete("/scripts/{script_id}/credentials/{credential_id}")
async def remove_credential_from_script(
    script_id: int,
    credential_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Remove a credential assignment from a script"""
    try:
        service = CredentialService(session)
        success = await service.remove_credential_from_script(script_id, credential_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Credential assignment not found")
        return {"message": "Credential removed from script successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove credential from script: {str(e)}")