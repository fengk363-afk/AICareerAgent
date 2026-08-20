"""
ApplicationEngine — 岗位收藏 + 投递追踪 + 状态管理
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger
from sqlalchemy import select

from app.db.models import Application, SavedJob, Job, ResumeProfile
from app.db.database import get_db
from app.schemas.models import ApplicationResponse, ApplicationStatus


class ApplicationEngine:
    """投递追踪引擎"""

    async def apply_job(
        self, user_id, job_id: str, resume_profile_id: Optional[str] = None
    ) -> Optional[ApplicationResponse]:
        """创建投递记录"""
        async for db in get_db():
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
        self, application_id: str, status: str, notes: Optional[str] = None
    ) -> Optional[ApplicationResponse]:
        """更新投递状态"""
        async for db in get_db():
            app = await db.get(Application, application_id)
            if not app:
                return None
            app.status = ApplicationStatus(status)
            if notes:
                app.notes = notes
            if status == ApplicationStatus.APPLIED.value:
                app.applied_at = datetime.utcnow()
            await db.commit()
            await db.refresh(app)
            logger.info(f"投递状态更新: {application_id} → {status}")
            return ApplicationResponse.model_validate(app)

    async def get_user_applications(self, user_id) -> List[ApplicationResponse]:
        """获取用户所有投递记录"""
        async for db in get_db():
            result = await db.execute(
                select(Application)
                .where(Application.user_id == int(user_id))
                .order_by(Application.created_at.desc())
            )
            return [ApplicationResponse.model_validate(r) for r in result.scalars().all()]
        return []

    async def save_job(self, user_id, job_id: str) -> bool:
        """收藏岗位"""
        async for db in get_db():
            existing = await db.execute(
                select(SavedJob).where(
                    SavedJob.user_id == int(user_id),
                    SavedJob.job_id == job_id,
                )
            )
            if existing.scalar():
                return False
            saved = SavedJob(id=str(uuid.uuid4()), user_id=int(user_id), job_id=job_id)
            db.add(saved)
            await db.commit()
            return True

    async def remove_saved_job(self, user_id, job_id: str) -> bool:
        """取消收藏"""
        async for db in get_db():
            result = await db.execute(
                select(SavedJob).where(
                    SavedJob.user_id == int(user_id),
                    SavedJob.job_id == job_id,
                )
            )
            saved = result.scalar_one_or_none()
            if saved:
                await db.delete(saved)
                await db.commit()
                return True
            return False

    async def get_saved_jobs(self, user_id) -> List[dict]:
        """获取收藏的岗位"""
        async for db in get_db():
            result = await db.execute(
                select(SavedJob)
                .where(SavedJob.user_id == int(user_id))
                .order_by(SavedJob.created_at.desc())
            )
            return [r.model_dump() for r in result.scalars().all()]
        return []
