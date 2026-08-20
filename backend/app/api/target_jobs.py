"""
TargetJob API — 用户目标岗位管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.db.database import get_db
from app.db.models import TargetJob, Job
from app.agents.engine import engine
from app.schemas.models import TargetJobRequest, TargetJobResponse

router = APIRouter()


@router.get("/my", response_model=list[TargetJobResponse])
async def get_my_target_jobs(
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取用户目标岗位列表"""
    return await engine.get_target_jobs(user_id)


@router.post("/add", response_model=TargetJobResponse)
async def add_target_job(data: TargetJobRequest, db: AsyncSession = Depends(get_db)):
    """添加目标岗位"""
    # 验证岗位是否存在
    job_result = await db.execute(select(Job).where(Job.id == data.job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="岗位不存在")

    result = await engine.add_target_job(data.user_id, data.job_id, data.priority, data.notes)
    if not result:
        raise HTTPException(status_code=400, detail="添加目标岗位失败")
    return result


@router.delete("/remove/{job_id}")
async def remove_target_job(
    job_id: str,
    user_id: str = Query(..., description="用户ID"),
):
    """移除目标岗位"""
    success = await engine.remove_target_job(user_id, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="未找到目标岗位记录")
    return {"message": "已移除目标岗位"}


@router.get("/gap-analysis/{job_id}")
async def get_gap_analysis(
    job_id: str,
    profile_id: str = Query(..., description="简历画像ID"),
    user_id: str = Query(..., description="用户ID"),
):
    """获取目标岗位的差距分析"""
    # 验证是否是用户的目标岗位
    target_result = await engine.get_target_job(user_id, job_id)
    if not target_result:
        raise HTTPException(status_code=404, detail="该岗位不是你的目标岗位")

    result = await engine.get_gap_analysis(profile_id, job_id)
    if not result:
        # 如果没有分析记录，实时生成
        result = await engine.analyze_gap(profile_id, job_id)
        if result:
            return result.model_dump()
        raise HTTPException(status_code=404, detail="差距分析生成失败")
    return result
