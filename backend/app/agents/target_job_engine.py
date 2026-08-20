"""
TargetJobEngine — 用户目标岗位管理引擎
支持用户主动选择目标岗位，并生成差距分析
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import TargetJob, Job, ResumeProfile
from app.db.database import get_db
from app.schemas.models import TargetJobResponse


class TargetJobEngine:
    """用户目标岗位管理引擎"""

    async def add_target_job(
        self, user_id: str, job_id: str, priority: int = 0, notes: Optional[str] = None
    ) -> Optional[TargetJobResponse]:
        """添加目标岗位"""
        async for db in get_db():
            # 检查是否已存在
            from sqlalchemy import select
            result = await db.execute(
                select(TargetJob).where(
                    TargetJob.user_id == int(user_id),
                    TargetJob.job_id == job_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                # 更新
                existing.priority = priority
                existing.notes = notes
                await db.commit()
                await db.refresh(existing)
                return TargetJobResponse.model_validate(existing)

            target_id = str(uuid.uuid4())
            target_job = TargetJob(
                id=target_id,
                user_id=int(user_id),
                job_id=job_id,
                priority=priority,
                notes=notes,
                created_at=datetime.utcnow(),
            )
            db.add(target_job)
            await db.commit()
            await db.refresh(target_job)
            logger.info(f"用户 {user_id} 添加目标岗位 {job_id}")
            return TargetJobResponse.model_validate(target_job)

    async def remove_target_job(self, user_id: str, job_id: str) -> bool:
        """移除目标岗位"""
        async for db in get_db():
            result = await db.execute(
                select(TargetJob).where(
                    TargetJob.user_id == int(user_id),
                    TargetJob.job_id == job_id,
                )
            )
            target = result.scalar_one_or_none()
            if target:
                await db.delete(target)
                await db.commit()
                return True
            return False

    async def get_target_jobs(self, user_id: str) -> List[dict]:
        """获取用户目标岗位列表"""
        async for db in get_db():
            result = await db.execute(
                select(TargetJob)
                .where(TargetJob.user_id == int(user_id))
                .order_by(TargetJob.priority.desc(), TargetJob.created_at.desc())
            )
            targets = result.scalars().all()
            output = []
            for t in targets:
                job_result = await db.execute(select(Job).where(Job.id == t.job_id))
                job = job_result.scalar_one_or_none()
                target_dict = t.model_dump()
                if job:
                    target_dict["job"] = {
                        "id": job.id,
                        "company": job.company,
                        "title": job.title,
                        "location": job.location,
                        "salary_range": job.salary_range,
                        "is_remote": job.is_remote,
                        "is_foreign": job.is_foreign,
                        "job_url": job.job_url,
                    }
                output.append(target_dict)
            return output

    async def get_target_job(self, user_id: str, job_id: str) -> Optional[dict]:
        """获取单个目标岗位"""
        async for db in get_db():
            result = await db.execute(
                select(TargetJob).where(
                    TargetJob.user_id == int(user_id),
                    TargetJob.job_id == job_id,
                )
            )
            target = result.scalar_one_or_none()
            if target:
                job_result = await db.execute(select(Job).where(Job.id == job_id))
                job = job_result.scalar_one_or_none()
                output = target.model_dump()
                if job:
                    output["job"] = {
                        "id": job.id,
                        "company": job.company,
                        "title": job.title,
                        "location": job.location,
                        "salary_range": job.salary_range,
                        "is_remote": job.is_remote,
                        "is_foreign": job.is_foreign,
                        "job_url": job.job_url,
                    }
                return output
        return None
