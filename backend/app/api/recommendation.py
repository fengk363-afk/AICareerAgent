"""
Recommendation API — AI 求职推荐
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine
from app.schemas.models import RecommendationResponse

router = APIRouter()


@router.post("/generate/{profile_id}")
async def generate_recommendations(
    profile_id: str,
    user_id: str = Query("1", description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
):
    """生成个性化岗位推荐"""
    result = await engine.generate_recommendations(profile_id, user_id, limit)
    if not result:
        raise HTTPException(status_code=404, detail="简历画像不存在或推荐生成失败")
    return result


@router.get("/{profile_id}", response_model=list[RecommendationResponse])
async def get_recommendations(profile_id: str):
    """获取推荐列表"""
    result = await engine.get_recommendations(profile_id)
    return result or []
