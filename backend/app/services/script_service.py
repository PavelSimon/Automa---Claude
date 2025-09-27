import os
import aiofiles
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import UploadFile, HTTPException
from ..models.script import Script
from ..models.user import User
from ..schemas.script import ScriptCreate, ScriptUpdate
from ..config import settings
from ..core.audit import log_audit_event


def _validate_file_path(file_path: str) -> str:
    """
    Validate and sanitize file paths to prevent path traversal attacks.
    Returns absolute path if valid, raises HTTPException if invalid.
    """
    try:
        # Convert to Path object and resolve
        path = Path(file_path).resolve()

        # Define allowed directories
        scripts_dir = Path(settings.scripts_directory).resolve()
        data_dir = Path(settings.data_directory).resolve()

        # Check if path is within allowed directories
        try:
            # Check if path is under scripts directory
            path.relative_to(scripts_dir)
            return str(path)
        except ValueError:
            try:
                # Check if path is under data directory
                path.relative_to(data_dir)
                return str(path)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"File path must be within allowed directories: {scripts_dir} or {data_dir}"
                )

    except (OSError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file path: {str(e)}"
        )


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent malicious filenames.
    """
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\0']
    sanitized = filename

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')

    # Ensure filename is not empty and has reasonable length
    if not sanitized or len(sanitized) > 255:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    # Ensure it ends with .py
    if not sanitized.endswith('.py'):
        sanitized += '.py'

    return sanitized


class ScriptService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_script(
        self, script_data: ScriptCreate, user: User, file: Optional[UploadFile] = None
    ) -> Script:
        os.makedirs(settings.scripts_directory, exist_ok=True)

        script = Script(
            name=script_data.name,
            description=script_data.description,
            content=script_data.content,
            is_file_based=script_data.is_file_based or False,
            external_file_path=script_data.external_file_path,
            created_by=user.id,
            file_path=""
        )

        if script_data.is_file_based and script_data.external_file_path:
            # File-based script: use external file path with validation
            clean_path = script_data.external_file_path.strip().strip('"').strip("'")
            validated_path = _validate_file_path(clean_path)

            if os.path.exists(validated_path):
                script.file_path = validated_path
                script.external_file_path = validated_path
                # Read content from external file for storage
                async with aiofiles.open(validated_path, 'r', encoding='utf-8') as f:
                    script.content = await f.read()
            else:
                raise FileNotFoundError(f"External script file not found: {validated_path}")
        elif file:
            # Uploaded file with filename sanitization
            sanitized_name = _sanitize_filename(f"{script_data.name}_{user.id}")
            file_path = os.path.join(settings.scripts_directory, sanitized_name)
            validated_path = _validate_file_path(file_path)

            async with aiofiles.open(validated_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            script.file_path = validated_path
            script.is_file_based = True
        elif script_data.content:
            # Inline content: create file in scripts directory with validation
            sanitized_name = _sanitize_filename(f"{script_data.name}_{user.id}")
            file_path = os.path.join(settings.scripts_directory, sanitized_name)
            validated_path = _validate_file_path(file_path)

            async with aiofiles.open(validated_path, 'w', encoding='utf-8') as f:
                await f.write(script_data.content)
            script.file_path = validated_path
            script.is_file_based = False

        self.session.add(script)
        await self.session.commit()
        await self.session.refresh(script)

        await log_audit_event(
            self.session, user, "CREATE", "script", script.id,
            {"script_name": script.name}
        )

        return script

    async def get_scripts(self, user: User, skip: int = 0, limit: int = 100) -> List[Script]:
        query = select(Script).where(Script.created_by == user.id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_script(self, script_id: int, user: User) -> Optional[Script]:
        query = select(Script).where(Script.id == script_id, Script.created_by == user.id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_script(
        self, script_id: int, script_data: ScriptUpdate, user: User
    ) -> Optional[Script]:
        script = await self.get_script(script_id, user)
        if not script:
            return None

        update_data = script_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(script, field, value)

        # Handle file path changes
        if script_data.is_file_based is not None and script_data.external_file_path:
            # Clean the path - remove surrounding quotes if present
            clean_path = script_data.external_file_path.strip().strip('"').strip("'")

            if script_data.is_file_based and os.path.exists(clean_path):
                # Switch to external file
                script.file_path = clean_path
                script.external_file_path = clean_path
                # Read content from external file
                async with aiofiles.open(clean_path, 'r', encoding='utf-8') as f:
                    script.content = await f.read()
            elif not script_data.is_file_based:
                # Switch to inline content - create new file in scripts directory
                if script.file_path and script.external_file_path and script.file_path == script.external_file_path:
                    # Moving from external to internal, create new internal file
                    new_file_path = os.path.join(settings.scripts_directory, f"{script.name}_{user.id}.py")
                    if script_data.content:
                        async with aiofiles.open(new_file_path, 'w', encoding='utf-8') as f:
                            await f.write(script_data.content)
                    script.file_path = new_file_path
                    script.external_file_path = None
        elif script_data.content and script.file_path and not script.is_file_based:
            # Update inline content
            async with aiofiles.open(script.file_path, 'w', encoding='utf-8') as f:
                await f.write(script_data.content)

        await self.session.commit()
        await self.session.refresh(script)

        await log_audit_event(
            self.session, user, "UPDATE", "script", script.id,
            {"updated_fields": list(update_data.keys())}
        )

        return script

    async def delete_script(self, script_id: int, user: User) -> bool:
        script = await self.get_script(script_id, user)
        if not script:
            return False

        if script.file_path and os.path.exists(script.file_path):
            os.remove(script.file_path)

        await self.session.delete(script)
        await self.session.commit()

        await log_audit_event(
            self.session, user, "DELETE", "script", script_id,
            {"script_name": script.name}
        )

        return True