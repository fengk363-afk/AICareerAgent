"""
JobSyncEngine — 岗位数据同步引擎
管理多来源岗位数据的同步和更新
支持岗位生命周期状态管理（ACTIVE/CLOSED/EXPIRED/REMOVED/UNKNOWN）
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.db.models import Job, JobSource, JobSyncRecord
from app.db.database import get_db
from sqlalchemy import select, update
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
            "id": "src_greenhouse",
            "source_name": "greenhouse",
            "source_type": "api",
            "base_url": "https://boards-api.greenhouse.io/v1",
            "description": "Greenhouse 招聘平台（API）",
            "is_active": True,
        },
        {
            "id": "src_lever",
            "source_name": "lever",
            "source_type": "api",
            "base_url": "https://boards-api.lever.co/v1",
            "description": "Lever 招聘平台（公开 API）",
            "is_active": True,
        },
        {
            "id": "src_ashby",
            "source_name": "ashby",
            "source_type": "api",
            "base_url": "https://api.ashbyhq.com",
            "description": "Ashby 招聘平台（API）",
            "is_active": True,
        },
        {
            "id": "src_smartrecruiters",
            "source_name": "smartrecruiters",
            "source_type": "api",
            "base_url": "https://api.smartrecruiters.com",
            "description": "SmartRecruiters 招聘平台（API）",
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

    # 支持岗位消失检测的数据源（有 external_id 且能可靠判断 OPEN/CLOSED）
    CLOSABLE_SOURCES = {"greenhouse", "lever", "ashby", "smartrecruiters"}

    # 岗位消失后标记为 CLOSED 前的等待天数
    CLOSED_AFTER_DAYS = 7

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
            jobs_closed = 0
            jobs_reactivated = 0
            failed_count = 0
            errors = []

            try:
                # 获取适配器
                if source_name and source_name != "all":
                    adapter = get_adapter(source_name)
                    if adapter:
                        try:
                            # 优先使用 normalize 后的数据（包含 source_job_id）
                            # 使用大 limit 确保获取所有岗位
                            if hasattr(adapter, 'fetch_jobs_normalized'):
                                jobs = await adapter.fetch_jobs_normalized(limit=1000)
                            else:
                                jobs = await adapter.fetch_jobs(limit=1000)
                            # 同步成功，执行 upsert + 消失检测
                            result = await self._sync_source(db, jobs, source_name)
                            jobs_added = result["added"]
                            jobs_updated = result["updated"]
                            jobs_closed = result["closed"]
                            jobs_reactivated = result["reactivated"]
                        except Exception as e:
                            failed_count += 1
                            errors.append(f"{source_name}: {str(e)}")
                            logger.error(f"[JobSync] 数据源 {source_name} 同步失败: {e}")
                    else:
                        errors.append(f"{source_name}: 适配器不存在")
                else:
                    # 同步所有活跃数据源
                    for name, adapter in ADAPTER_REGISTRY.items():
                        try:
                            # 优先使用 normalize 后的数据
                            if hasattr(adapter, 'fetch_jobs_normalized'):
                                jobs = await adapter.fetch_jobs_normalized(limit=1000)
                            else:
                                jobs = await adapter.fetch_jobs(limit=1000)
                            result = await self._sync_source(db, jobs, name)
                            jobs_added += result["added"]
                            jobs_updated += result["updated"]
                            jobs_closed += result["closed"]
                            jobs_reactivated += result["reactivated"]
                        except Exception as e:
                            failed_count += 1
                            errors.append(f"{name}: {str(e)}")
                            logger.warning(f"数据源 {name} 同步失败: {e}")

                # 更新同步记录
                sync_record.status = "completed"
                sync_record.jobs_added = jobs_added
                sync_record.jobs_updated = jobs_updated
                sync_record.jobs_deleted = jobs_closed  # 复用 jobs_deleted 字段记录关闭数
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
                    "source": source_name or "all",
                    "status": "completed",
                    "success": failed_count == 0,
                    "fetched_count": jobs_added + jobs_updated,
                    "created_count": jobs_added,
                    "updated_count": jobs_updated,
                    "closed_count": jobs_closed,
                    "reactivated_count": jobs_reactivated,
                    "failed_count": failed_count,
                    "errors": errors,
                    "started_at": sync_record.started_at.isoformat() if sync_record.started_at else None,
                    "completed_at": sync_record.completed_at.isoformat() if sync_record.completed_at else None,
                }

            except Exception as e:
                sync_record.status = "failed"
                sync_record.error_message = str(e)
                await db.commit()
                logger.error(f"[JobSync] 同步任务异常: {e}")
                return {
                    "sync_id": sync_id,
                    "source": source_name or "all",
                    "status": "failed",
                    "success": False,
                    "error": str(e),
                }

    async def _sync_source(self, db, jobs: List[dict], source_name: str) -> Dict[str, int]:
        """同步单个数据源的岗位，返回统计结果"""
        result = {"added": 0, "updated": 0, "closed": 0, "reactivated": 0}
        now = datetime.utcnow()

        # 空列表视为异常：API 可能返回 200 但无数据（配置错误、权限问题等）
        # 此时不应执行消失检测，避免误下架所有岗位
        if not jobs:
            logger.warning(f"[{source_name}] 同步返回空列表，跳过 upsert 和消失检测")
            return result

        # 1. 先查询所有现有岗位，建立查找表（避免 autoflush 问题）
        existing_map = {}
        existing_result = await db.execute(
            select(Job).where(Job.source == source_name)
        )
        for job in existing_result.scalars().all():
            if job.source_job_id:
                existing_map[job.source_job_id] = job

        # 2. 处理本次同步的岗位
        current_ids = set()
        for job_data in jobs:
            source_job_id = job_data.get("source_job_id", "")
            if not source_job_id:
                continue
            current_ids.add(source_job_id)

            if source_job_id in existing_map:
                # 更新现有岗位
                existing_job = existing_map[source_job_id]
                for key, value in job_data.items():
                    if value is not None and hasattr(existing_job, key):
                        setattr(existing_job, key, value)
                existing_job.last_seen_at = now
                existing_job.last_synced_at = now
                # 如果岗位之前是 CLOSED/UNKNOWN，重新激活
                if existing_job.status in ("closed", "unknown"):
                    existing_job.status = "active"
                    existing_job.status_changed_at = now
                    result["reactivated"] += 1
                    logger.info(f"[{source_name}] 重新激活岗位: {job_data.get('title', '')}")
                elif existing_job.status != "active":
                    existing_job.status = "active"
                    existing_job.status_changed_at = now
                    result["reactivated"] += 1
                result["updated"] += 1
                logger.info(
                    f"[{source_name}] 更新: title={job_data.get('title', '')}, "
                    f"status={existing_job.status}"
                )
            else:
                # 新增岗位
                job_id = str(uuid.uuid4())
                job_data["id"] = job_id
                job_data["created_at"] = now
                job_data["last_seen_at"] = now
                job_data["last_synced_at"] = now
                job_data["status"] = "active"
                job_data["status_changed_at"] = now
                try:
                    job = Job(**job_data)
                    db.add(job)
                    result["added"] += 1
                    logger.info(f"[{source_name}] 新增: title={job_data.get('title', '')}")
                except Exception as e:
                    logger.error(f"[{source_name}] 岗位创建失败: {e}, data={job_data}")
                    continue

        # 3. 检测消失的岗位（仅对有 external_id 的数据源）
        if source_name in self.CLOSABLE_SOURCES:
            for job_id, existing_job in existing_map.items():
                if job_id not in current_ids:
                    # 计算距离上次 seen 的时间
                    if existing_job.last_seen_at:
                        days_since_seen = (now - existing_job.last_seen_at).days
                        if days_since_seen >= self.CLOSED_AFTER_DAYS:
                            # 超过阈值，标记为 CLOSED
                            existing_job.status = "closed"
                            existing_job.status_changed_at = now
                            result["closed"] += 1
                            logger.info(
                                f"[{source_name}] 岗位已关闭: {existing_job.title} "
                                f"(last_seen={existing_job.last_seen_at}, {days_since_seen}天前)"
                            )
                        else:
                            # 未超过阈值，标记为 UNKNOWN
                            existing_job.status = "unknown"
                            existing_job.status_changed_at = now
                            logger.warning(
                                f"[{source_name}] 岗位状态未知: {existing_job.title} "
                                f"(last_seen={existing_job.last_seen_at}, {days_since_seen}天前)"
                            )
                    else:
                        # 没有 last_seen_at，保守标记为 UNKNOWN
                        existing_job.status = "unknown"
                        existing_job.status_changed_at = now
                        logger.warning(
                            f"[{source_name}] 岗位状态未知（无 last_seen_at）: {existing_job.title}"
                        )

            if result["closed"] > 0 or result["reactivated"] > 0:
                logger.info(
                    f"[{source_name}] 消失检测完成: closed={result['closed']}, "
                    f"reactivated={result['reactivated']}"
                )

        await db.commit()
        return result

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
