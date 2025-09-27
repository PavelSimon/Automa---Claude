from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.credential import Credential, ScriptCredential
from ..models.user import User
from ..models.script import Script
from ..schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialRead,
    ScriptCredentialCreate, ScriptCredentialUpdate
)
from .encryption_service import EncryptionService
from ..core.audit import log_action


class CredentialService:
    """Service for managing encrypted credentials"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.encryption_service = EncryptionService()

    async def create_credential(self, credential_data: CredentialCreate, user: User) -> Credential:
        """Create a new encrypted credential"""
        # Validate credential type and data
        if not self.encryption_service.validate_credential_type(
            credential_data.credential_type,
            credential_data.credential_data
        ):
            raise ValueError(f"Invalid credential data for type: {credential_data.credential_type}")

        # Encrypt the credential data
        encrypted_data, key_id = self.encryption_service.encrypt_credential_data(
            credential_data.credential_data,
            credential_data.user_password
        )

        # Create credential record
        credential = Credential(
            name=credential_data.name,
            description=credential_data.description,
            credential_type=credential_data.credential_type,
            encrypted_data=encrypted_data,
            encryption_key_id=key_id,
            tags=credential_data.tags or [],
            expires_at=credential_data.expires_at,
            created_by=user.id
        )

        self.session.add(credential)
        await self.session.commit()
        await self.session.refresh(credential)

        # Log the action
        await log_action(
            session=self.session,
            user_id=user.id,
            action="credential_create",
            resource_type="credential",
            resource_id=credential.id,
            details={"name": credential.name, "type": credential.credential_type}
        )

        return credential

    async def get_credentials(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        credential_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[Credential]:
        """Get user's credentials with filtering"""
        query = select(Credential).where(Credential.created_by == user.id)

        # Add filters
        if credential_type:
            query = query.where(Credential.credential_type == credential_type)

        if search:
            query = query.where(
                or_(
                    Credential.name.ilike(f"%{search}%"),
                    Credential.description.ilike(f"%{search}%")
                )
            )

        # Add tag filtering (JSON array contains)
        if tags:
            for tag in tags:
                query = query.where(Credential.tags.op('@>')([tag]))

        query = query.order_by(Credential.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_credential(self, credential_id: int, user: User) -> Optional[Credential]:
        """Get a specific credential by ID"""
        query = select(Credential).where(
            and_(Credential.id == credential_id, Credential.created_by == user.id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_credential(
        self,
        credential_id: int,
        credential_update: CredentialUpdate,
        user: User
    ) -> Optional[Credential]:
        """Update a credential"""
        credential = await self.get_credential(credential_id, user)
        if not credential:
            return None

        # Update non-encrypted fields
        update_data = credential_update.model_dump(exclude_unset=True, exclude={"credential_data", "user_password"})
        for field, value in update_data.items():
            setattr(credential, field, value)

        # Update encrypted data if provided
        if credential_update.credential_data and credential_update.user_password:
            # Validate new credential data
            if not self.encryption_service.validate_credential_type(
                credential.credential_type,
                credential_update.credential_data
            ):
                raise ValueError(f"Invalid credential data for type: {credential.credential_type}")

            # Re-encrypt with new data
            encrypted_data, key_id = self.encryption_service.encrypt_credential_data(
                credential_update.credential_data,
                credential_update.user_password
            )
            credential.encrypted_data = encrypted_data
            credential.encryption_key_id = key_id

        credential.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(credential)

        # Log the action
        await log_action(
            session=self.session,
            user_id=user.id,
            action="credential_update",
            resource_type="credential",
            resource_id=credential.id,
            details={"name": credential.name, "updated_fields": list(update_data.keys())}
        )

        return credential

    async def delete_credential(self, credential_id: int, user: User) -> bool:
        """Delete a credential"""
        credential = await self.get_credential(credential_id, user)
        if not credential:
            return False

        # Check if credential is used by any scripts
        query = select(ScriptCredential).where(ScriptCredential.credential_id == credential_id)
        result = await self.session.execute(query)
        script_credentials = result.scalars().all()

        if script_credentials:
            raise ValueError("Cannot delete credential: it is used by one or more scripts")

        # Log the action before deletion
        await log_action(
            session=self.session,
            user_id=user.id,
            action="credential_delete",
            resource_type="credential",
            resource_id=credential.id,
            details={"name": credential.name, "type": credential.credential_type}
        )

        await self.session.delete(credential)
        await self.session.commit()
        return True

    async def decrypt_credential(
        self,
        credential_id: int,
        user_password: str,
        user: User
    ) -> Dict[str, Any]:
        """Decrypt credential data"""
        credential = await self.get_credential(credential_id, user)
        if not credential:
            raise ValueError("Credential not found")

        try:
            # Decrypt the data
            decrypted_data = self.encryption_service.decrypt_credential_data(
                credential.encrypted_data,
                user_password
            )

            # Update last used timestamp
            credential.last_used_at = datetime.utcnow()
            await self.session.commit()

            # Log the action
            await log_action(
                session=self.session,
                user_id=user.id,
                action="credential_decrypt",
                resource_type="credential",
                resource_id=credential.id,
                details={"name": credential.name}
            )

            # Return both decrypted and masked data
            masked_data = self.encryption_service.mask_sensitive_data(
                credential.credential_type,
                decrypted_data
            )

            return {
                "credential_data": decrypted_data,
                "masked_data": masked_data
            }

        except Exception as e:
            # Log failed decryption attempt
            await log_action(
                session=self.session,
                user_id=user.id,
                action="credential_decrypt_failed",
                resource_type="credential",
                resource_id=credential.id,
                details={"name": credential.name, "error": str(e)}
            )
            raise ValueError("Failed to decrypt credential. Invalid password or corrupted data.")

    async def test_credential(self, credential_id: int, user_password: str, user: User) -> Dict[str, Any]:
        """Test credential validity (basic validation only)"""
        try:
            decrypted_data = await self.decrypt_credential(credential_id, user_password, user)
            credential = await self.get_credential(credential_id, user)

            # Basic validation based on credential type
            is_valid = self.encryption_service.validate_credential_type(
                credential.credential_type,
                decrypted_data["credential_data"]
            )

            return {
                "success": is_valid,
                "message": "Credential is valid" if is_valid else "Credential validation failed",
                "details": {"type": credential.credential_type}
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Credential test failed: {str(e)}",
                "details": None
            }

    # Script-Credential Association Methods

    async def assign_credential_to_script(
        self,
        script_id: int,
        credential_assignment: ScriptCredentialCreate,
        user: User
    ) -> ScriptCredential:
        """Assign a credential to a script"""
        # Verify script ownership
        script_query = select(Script).where(
            and_(Script.id == script_id, Script.created_by == user.id)
        )
        script_result = await self.session.execute(script_query)
        script = script_result.scalar_one_or_none()
        if not script:
            raise ValueError("Script not found")

        # Verify credential ownership
        credential = await self.get_credential(credential_assignment.credential_id, user)
        if not credential:
            raise ValueError("Credential not found")

        # Check if assignment already exists
        existing_query = select(ScriptCredential).where(
            and_(
                ScriptCredential.script_id == script_id,
                ScriptCredential.credential_id == credential_assignment.credential_id
            )
        )
        existing_result = await self.session.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise ValueError("Credential is already assigned to this script")

        # Create assignment
        assignment = ScriptCredential(
            script_id=script_id,
            credential_id=credential_assignment.credential_id,
            variable_name=credential_assignment.variable_name,
            is_active=credential_assignment.is_active
        )

        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)

        # Log the action
        await log_action(
            session=self.session,
            user_id=user.id,
            action="script_credential_assign",
            resource_type="script_credential",
            resource_id=assignment.id,
            details={
                "script_id": script_id,
                "credential_id": credential_assignment.credential_id,
                "variable_name": credential_assignment.variable_name
            }
        )

        return assignment

    async def get_script_credentials(self, script_id: int, user: User) -> List[ScriptCredential]:
        """Get all credentials assigned to a script"""
        # Verify script ownership
        script_query = select(Script).where(
            and_(Script.id == script_id, Script.created_by == user.id)
        )
        script_result = await self.session.execute(script_query)
        if not script_result.scalar_one_or_none():
            raise ValueError("Script not found")

        query = select(ScriptCredential).where(
            ScriptCredential.script_id == script_id
        ).options(selectinload(ScriptCredential.credential))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def remove_credential_from_script(
        self,
        script_id: int,
        credential_id: int,
        user: User
    ) -> bool:
        """Remove a credential assignment from a script"""
        # Verify script ownership
        script_query = select(Script).where(
            and_(Script.id == script_id, Script.created_by == user.id)
        )
        script_result = await self.session.execute(script_query)
        if not script_result.scalar_one_or_none():
            raise ValueError("Script not found")

        # Find and delete assignment
        assignment_query = select(ScriptCredential).where(
            and_(
                ScriptCredential.script_id == script_id,
                ScriptCredential.credential_id == credential_id
            )
        )
        assignment_result = await self.session.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            return False

        # Log the action before deletion
        await log_action(
            session=self.session,
            user_id=user.id,
            action="script_credential_remove",
            resource_type="script_credential",
            resource_id=assignment.id,
            details={
                "script_id": script_id,
                "credential_id": credential_id,
                "variable_name": assignment.variable_name
            }
        )

        await self.session.delete(assignment)
        await self.session.commit()
        return True