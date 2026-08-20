"""
ApplicationTrackerAgent — 投递进度追踪
"""
import uuid
from typing import Optional, List
from sqlalchemy import select
from datetime import datetime
from loguru import logger

from app.db.models import Application, ResumeProfile, Job
from app.db.database import get_db
from app.schemas.models import ApplicationCreate, ApplicationResponse, ApplicationStatus


class ApplicationTrackerAgent:
    """投递追踪 Agent"""

    async def create_application(
        self, user_id, job_id: str, resume_profile_id: Optional[str] = None
    ) -> Optional[ApplicationResponse]:
        """创建投递记录"""
        async for db in get_db():
            # 检查是否已投递
            existing = await db.execute(
                select(Application).where(
                    Application.user_id == int(user_id),
                    Application.job_id == job_id,
                )
            )
            if existing.scalar():
                logger.warning(f"用户 {user_id} 已投递过岗位 {job_id}")
                return None

            app_id = str(uuid.uuid4())
            application = Application(
                id=app_id,
                user_id=int(user_id),
                job_id=job_id,
                resume_profile_id=resume_profile_id,
                status=ApplicationStatus.DRAFT,
                created_at=datetime.utcnow(),
            )
            db.add(application)
            await db.commit()
            await db.refresh(application)
            logger.info(f"投递记录创建: {app_id}")
            return ApplicationResponse.model_validate(application)

    async def update_status(
        self, application_id: str, status: ApplicationStatus, notes: Optional[str] = None
    ) -> Optional[ApplicationResponse]:
        """更新投递状态"""
        async for db in get_db():
            app = await db.get(Application, application_id)
            if not app:
                return None
            app.status = status
            if notes:
                app.notes = notes
            if status == ApplicationStatus.APPLIED:
                app.applied_at = datetime.utcnow()
            await db.commit()
            await db.refresh(app)
            logger.info(f"投递状态更新: {application_id} → {status.value}")
            return ApplicationResponse.model_validate(app)

    async def get_user_applications(self, user_id) -> List[ApplicationResponse]:
        """获取用户所有投递记录"""
        async for db in get_db():
            result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
                .order_by(Application.created_at.desc())
            )
            return [ApplicationResponse.model_validate(r) for r in result.scalars().all()]
        return []

    async def get_application(self, application_id: str) -> Optional[ApplicationResponse]:
        """获取单条投递记录"""
        async for db in get_db():
            app = await db.get(Application, application_id)
            if app:
                return ApplicationResponse.model_validate(app)
        return None
