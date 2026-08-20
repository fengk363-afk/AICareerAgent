"""
GapAnalysis API — 能力差距分析
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine
from app.schemas.models import GapAnalysisResponse

router = APIRouter()


@router.get("/analyze/{profile_id}/{job_id}", response_model=GapAnalysisResponse)
async def analyze_gap(profile_id: str, job_id: str):
    """分析简历与目标岗位的差距"""
    result = await engine.analyze_gap(profile_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="简历画像或岗位不存在")
    return result


@router.get("/history/{profile_id}/{job_id}")
async def get_gap_history(profile_id: str, job_id: str):
    """获取差距分析历史"""
    result = await engine.get_gap_analysis(profile_id, job_id)
    return result or {}
