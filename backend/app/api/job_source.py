"""
Job Source & Sync API — 岗位数据源管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.db.database import get_db
from app.db.models import Job, JobSource, JobSyncRecord, CompanySource
from app.agents.engine import engine
from app.agents.job_source_adapters import ADAPTER_REGISTRY
from app.schemas.models import (
    JobResponse, JobSourceResponse, JobSyncRecordResponse,
    CompanySourceResponse, AdvancedJobSearchRequest,
)

router = APIRouter()


@router.get("/sources", response_model=list[JobSourceResponse])
async def list_sources():
    """查看数据源列表"""
    return await engine.list_sources()


@router.post("/sync")
async def sync_jobs(source_name: Optional[str] = Query(None)):
    """执行岗位数据同步"""
    result = await engine.sync_jobs(source_name)
    return result


@router.get("/sync/history", response_model=list[JobSyncRecordResponse])
async def get_sync_history(limit: int = Query(20, le=100)):
    """获取同步历史"""
    return await engine.get_sync_history(limit)


@router.get("/search/advanced", response_model=list[JobResponse])
async def advanced_search(
    keyword: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    company_type: Optional[str] = Query(None),
    salary_min: Optional[float] = Query(None),
    salary_max: Optional[float] = Query(None),
    is_foreign: Optional[bool] = Query(None),
    is_remote: Optional[bool] = Query(None),
    visa_support: Optional[bool] = Query(None),
    english_required: Optional[bool] = Query(None),
    graduate_program: Optional[bool] = Query(None),
    campus_recruitment: Optional[bool] = Query(None),
    season: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    company_country: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # comma-separated
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    """高级岗位搜索"""
    tag_list = tags.split(",") if tags else None
    return await engine.search_jobs(
        keyword=keyword,
        location=location,
        company_type=company_type,
        salary_min=salary_min,
        salary_max=salary_max,
        is_foreign=is_foreign,
        is_remote=is_remote,
        visa_support=visa_support,
        english_required=english_required,
        graduate_program=graduate_program,
        campus_recruitment=campus_recruitment,
        season=season,
        source_type=source_type,
        company_country=company_country,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )


@router.get("/foreign", response_model=list[JobResponse])
async def get_foreign_jobs(limit: int = Query(20, le=100)):
    """获取外企岗位"""
    return await engine.get_foreign_jobs(limit)


@router.get("/campus", response_model=list[JobResponse])
async def get_campus_jobs(limit: int = Query(20, le=100)):
    """获取校招岗位"""
    return await engine.get_campus_jobs(limit)


@router.get("/remote", response_model=list[JobResponse])
async def get_remote_jobs(limit: int = Query(20, le=100)):
    """获取远程岗位"""
    return await engine.get_remote_jobs(limit)


@router.get("/overseas", response_model=list[JobResponse])
async def get_overseas_jobs(limit: int = Query(20, le=100)):
    """获取海外岗位"""
    return await engine.get_overseas_jobs(limit)


@router.get("/adapters")
async def list_adapters():
    """列出所有数据源适配器"""
    return [
        {
            "source_name": name,
            "source_type": adapter.source_type,
            "base_url": adapter.base_url,
            "status": "ready" if name in ADAPTER_REGISTRY else "inactive",
        }
        for name, adapter in ADAPTER_REGISTRY.items()
    ]


@router.get("/stats")
async def get_job_stats(db: AsyncSession = Depends(get_db)):
    """获取岗位统计"""
    # 总数
    result = await db.execute(select(Job))
    all_jobs = result.scalars().all()
    total = len(all_jobs)

    # 按来源统计
    source_stats = {}
    for job in all_jobs:
        src = job.source or "unknown"
        if src not in source_stats:
            source_stats[src] = 0
        source_stats[src] += 1

    # 按公司类型统计
    company_type_stats = {}
    for job in all_jobs:
        ct = job.company_type or "unknown"
        if ct not in company_type_stats:
            company_type_stats[ct] = 0
        company_type_stats[ct] += 1

    # 按季节统计
    season_stats = {}
    for job in all_jobs:
        s = job.season or "regular"
        if s not in season_stats:
            season_stats[s] = 0
        season_stats[s] += 1

    # 校招/日常
    campus_count = sum(1 for j in all_jobs if j.campus_recruitment)
    foreign_count = sum(1 for j in all_jobs if j.is_foreign)
    remote_count = sum(1 for j in all_jobs if j.is_remote)
    overseas_count = sum(1 for j in all_jobs if j.is_foreign or j.is_remote or j.visa_support)

    return {
        "total_jobs": total,
        "by_source": source_stats,
        "by_company_type": company_type_stats,
        "by_season": season_stats,
        "campus_jobs": campus_count,
        "foreign_jobs": foreign_count,
        "remote_jobs": remote_count,
        "overseas_jobs": overseas_count,
    }
