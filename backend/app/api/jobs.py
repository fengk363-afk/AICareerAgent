from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.db.database import get_db
from app.db.models import Job, ApplicationEvent
from app.agents.engine import engine
from app.schemas.models import JobResponse, MatchScoreResponse

router = APIRouter()


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    keyword: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    company_type: Optional[str] = Query(None),
    salary_min: Optional[float] = Query(None),
    salary_max: Optional[float] = Query(None),
    is_foreign: Optional[bool] = Query(None),
    is_remote: Optional[bool] = Query(None),
    has_apply_url: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    """搜索岗位（支持多维度筛选）"""
    return await engine.search_jobs(
        keyword=keyword, location=location, job_type=job_type,
        company_type=company_type, salary_min=salary_min, salary_max=salary_max,
        is_foreign=is_foreign, is_remote=is_remote, has_apply_url=has_apply_url,
        limit=limit, offset=offset,
    )


@router.post("/seed", response_model=list[JobResponse])
async def seed_jobs():
    """初始化 Mock 岗位数据"""
    return await engine.seed_jobs()


@router.get("/match", response_model=MatchScoreResponse)
async def calculate_match(profile_id: str, job_id: str):
    """计算简历与岗位的匹配度"""
    result = await engine.get_match(profile_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="简历画像或岗位不存在")
    return result


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """获取岗位详情"""
    result = await engine.get_job(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return result


@router.get("/{job_id}/apply-info")
async def get_apply_info(job_id: str, db: AsyncSession = Depends(get_db)):
    """获取岗位投递入口信息"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        "apply_url": job.apply_url,
        "apply_source": job.apply_source,
        "company_website": job.company_website,
        "application_method": job.application_method,
        "is_remote": job.is_remote,
        "is_foreign": job.is_foreign,
    }
