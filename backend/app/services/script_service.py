import os
import aiofiles
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import UploadFile
from ..models.script import Script
from ..models.user import User
from ..schemas.script import ScriptCreate, ScriptUpdate
from ..config import settings
from ..core.audit import log_audit_event


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
            created_by=user.id,
            file_path=""
        )

        if file:
            file_path = os.path.join(settings.scripts_directory, f"{script_data.name}_{user.id}.py")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            script.file_path = file_path
        elif script_data.content:
            file_path = os.path.join(settings.scripts_directory, f"{script_data.name}_{user.id}.py")
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(script_data.content)
            script.file_path = file_path

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

        if script_data.content and script.file_path:
            async with aiofiles.open(script.file_path, 'w') as f:
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