"""
JobSyncEngine — 岗位数据同步引擎
管理多来源岗位数据的同步和更新
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import Job, JobSource, JobSyncRecord
from app.db.database import get_db
from sqlalchemy import select
from app.agents.job_source_adapters import ADAPTER_REGISTRY, get_adapter


def _model_to_dict(obj):
    """将 SQLAlchemy 模型序列化为 dict"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


class JobSyncEngine:
    """岗位数据同步引擎"""

    # 预配置的数据源
    DEFAULT_SOURCES = [
        {
            "id": "src_company",
            "source_name": "company",
            "source_type": "official",
            "base_url": "https://careers.example.com",
            "description": "公司官方招聘页",
            "is_active": True,
        },
        {
            "id": "src_linkedin",
            "source_name": "linkedin",
            "source_type": "linkedin",
            "base_url": "https://www.linkedin.com/jobs",
            "description": "LinkedIn 招聘",
            "is_active": True,
        },
        {
            "id": "src_indeed",
            "source_name": "indeed",
            "source_type": "indeed",
            "base_url": "https://www.indeed.com",
            "description": "Indeed 招聘",
            "is_active": True,
        },
        {
            "id": "src_boss",
            "source_name": "boss",
            "source_type": "boss",
            "base_url": "https://www.zhipin.com",
            "description": "Boss直聘",
            "is_active": True,
        },
        {
            "id": "src_lagou",
            "source_name": "lagou",
            "source_type": "lagou",
            "base_url": "https://www.lagou.com",
            "description": "拉勾网",
            "is_active": True,
        },
        {
            "id": "src_liepin",
            "source_name": "liepin",
            "source_type": "liepin",
            "base_url": "https://www.liepin.com",
            "description": "猎聘",
            "is_active": True,
        },
        {
            "id": "src_glassdoor",
            "source_name": "glassdoor",
            "source_type": "glassdoor",
            "base_url": "https://www.glassdoor.com",
            "description": "Glassdoor",
            "is_active": True,
        },
        {
            "id": "src_gdrc",
            "source_name": "gdrc",
            "source_type": "gdrc",
            "base_url": "https://www.gdrc.com",
            "description": "广东人才网（广东省人社厅）",
            "is_active": True,
        },
        {
            "id": "src_gd_public",
            "source_name": "gd_public",
            "source_type": "gd_public",
            "base_url": "https://gdreclruit.gov.cn",
            "description": "广东公共招聘平台（省级公共就业服务）",
            "is_active": True,
        },
    ]

    async def init_sources(self) -> List[dict]:
        """初始化/更新数据源配置（upsert 新数据源）"""
        async for db in get_db():
            # 加载已有数据源名称集合
            result = await db.execute(select(JobSource))
            existing = result.scalars().all()
            existing_names = {s.source_name for s in existing}

            added = 0
            for data in self.DEFAULT_SOURCES:
                if data["source_name"] not in existing_names:
                    source = JobSource(**data)
                    db.add(source)
                    added += 1

            if added:
                await db.commit()
                logger.info(f"已新增 {added} 个数据源")
            else:
                logger.info("数据源配置已是最新，无需初始化")

            result = await db.execute(select(JobSource))
            return [_model_to_dict(s) for s in result.scalars().all()]

    async def list_sources(self) -> List[dict]:
        """列出所有数据源"""
        async for db in get_db():
            result = await db.execute(
                select(JobSource).order_by(JobSource.created_at.desc())
            )
            return [_model_to_dict(s) for s in result.scalars().all()]

    async def sync_jobs(self, source_name: Optional[str] = None) -> dict:
        """执行岗位数据同步"""
        async for db in get_db():
            # 查找数据源记录，获取真实 source_id
            src_result = await db.execute(
                select(JobSource).where(JobSource.source_name == (source_name or "all"))
            )
            src_record = src_result.scalar_one_or_none()
            db_source_id = src_record.id if src_record else (source_name or "all")

            # 创建同步记录
            sync_id = str(uuid.uuid4())
            sync_record = JobSyncRecord(
                id=sync_id,
                source_id=db_source_id,
                source_name=source_name or "all",
                sync_type="incremental",
                status="running",
                started_at=datetime.utcnow(),
            )
            db.add(sync_record)
            await db.commit()
            await db.refresh(sync_record)

            jobs_added = 0
            jobs_updated = 0
            jobs_deleted = 0
            errors = []

            try:
                # 获取适配器
                if source_name and source_name != "all":
                    adapter = get_adapter(source_name)
                    if adapter:
                        try:
                            jobs = await adapter.fetch_jobs()
                            jobs_added = await self._upsert_jobs(db, jobs, source_name)
                        except Exception as e:
                            errors.append(f"{source_name}: {str(e)}")
                else:
                    # 同步所有活跃数据源
                    for name, adapter in ADAPTER_REGISTRY.items():
                        try:
                            jobs = await adapter.fetch_jobs()
                            added = await self._upsert_jobs(db, jobs, name)
                            jobs_added += added
                        except Exception as e:
                            errors.append(f"{name}: {str(e)}")
                            logger.warning(f"数据源 {name} 同步失败: {e}")

                # 更新同步记录
                sync_record.status = "completed"
                sync_record.jobs_added = jobs_added
                sync_record.jobs_updated = jobs_updated
                sync_record.jobs_deleted = jobs_deleted
                sync_record.completed_at = datetime.utcnow()
                if errors:
                    sync_record.error_message = "; ".join(errors)

                # 更新数据源最后同步时间
                if source_name and source_name != "all":
                    src_result = await db.execute(
                        select(JobSource).where(JobSource.source_name == source_name)
                    )
                    src = src_result.scalar_one_or_none()
                    if src:
                        src.last_sync_at = datetime.utcnow()
                        src.total_jobs = jobs_added
                else:
                    for name in ADAPTER_REGISTRY:
                        src_result = await db.execute(
                            select(JobSource).where(JobSource.source_name == name)
                        )
                        src = src_result.scalar_one_or_none()
                        if src:
                            src.last_sync_at = datetime.utcnow()

                await db.commit()

                return {
                    "sync_id": sync_id,
                    "status": "completed",
                    "jobs_added": jobs_added,
                    "jobs_updated": jobs_updated,
                    "jobs_deleted": jobs_deleted,
                    "errors": errors,
                    "started_at": sync_record.started_at.isoformat() if sync_record.started_at else None,
                    "completed_at": sync_record.completed_at.isoformat() if sync_record.completed_at else None,
                }

            except Exception as e:
                sync_record.status = "failed"
                sync_record.error_message = str(e)
                await db.commit()
                return {
                    "sync_id": sync_id,
                    "status": "failed",
                    "error": str(e),
                }

    async def _upsert_jobs(self, db, jobs: List[dict], source_name: str) -> int:
        """插入或更新岗位"""
        added = 0
        for job_data in jobs:
            # 检查是否已存在
            existing = await db.execute(
                select(Job).where(
                    Job.source == source_name,
                    Job.source_job_id == job_data.get("source_job_id", ""),
                )
            )
            existing_job = existing.scalar_one_or_none()

            if existing_job:
                # 更新
                for key, value in job_data.items():
                    if value is not None and hasattr(existing_job, key):
                        setattr(existing_job, key, value)
                jobs_updated = True
            else:
                # 插入
                job_id = str(uuid.uuid4())
                job = Job(id=job_id, **job_data)
                db.add(job)
                added += 1

            # 调试输出：打印岗位关键信息
            desc_len = len(job_data.get("description", ""))
            req_len = len(job_data.get("requirements", []))
            logger.info(
                f"[{source_name}] {'新增' if not existing_job else '更新'}: "
                f"title={job_data.get('title', '')}, "
                f"description_len={desc_len}, "
                f"requirements_count={req_len}"
            )

        await db.commit()
        return added

    async def get_sync_history(self, limit: int = 20) -> List[dict]:
        """获取同步历史"""
        async for db in get_db():
            result = await db.execute(
                select(JobSyncRecord)
                .order_by(JobSyncRecord.created_at.desc())
                .limit(limit)
            )
            return [r.model_dump() for r in result.scalars().all()]
        return []
