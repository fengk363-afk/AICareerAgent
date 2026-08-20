"""
JobRanking API — 岗位排序
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine
from app.schemas.models import JobRankingResponse

router = APIRouter()


@router.post("/rank/{profile_id}")
async def rank_jobs(
    profile_id: str,
    user_id: str = Query("1", description="用户ID"),
    limit: int = Query(20, ge=1, le=50, description="排名数量"),
):
    """对岗位进行综合排序"""
    result = await engine.rank_jobs(profile_id, user_id, limit)
    if not result:
        raise HTTPException(status_code=404, detail="简历画像不存在或排序失败")
    return result


@router.get("/{profile_id}", response_model=list[JobRankingResponse])
async def get_rankings(profile_id: str):
    """获取排名列表"""
    result = await engine.get_rankings(profile_id)
    return result or []
