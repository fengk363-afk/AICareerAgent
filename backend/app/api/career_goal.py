"""
CareerGoal API — 职业目标管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine
from app.schemas.models import (
    RecommendationResponse, JobRankingResponse,
)

router = APIRouter()


# ── Career Goals ──────────────────────────────────────────────

@router.post("/goals/create")
async def create_goal(
    user_id: str = Query(..., description="用户ID"),
    target_position: str = Query(None),
    target_industry: str = Query(None),
    target_company: str = Query(None),
    target_country: str = Query(None),
    target_city: str = Query(None),
    salary_expectation_min: float = Query(None),
    salary_expectation_max: float = Query(None),
    company_type: str = Query(None),
    remote_preference: str = Query(None),
    priority_level: int = Query(0),
    notes: str = Query(None),
):
    """创建职业目标"""
    result = await engine.career_goal_engine.create_goal(
        user_id=user_id,
        target_position=target_position,
        target_industry=target_industry,
        target_company=target_company,
        target_country=target_country,
        target_city=target_city,
        salary_expectation_min=salary_expectation_min,
        salary_expectation_max=salary_expectation_max,
        company_type=company_type,
        remote_preference=remote_preference,
        priority_level=priority_level,
        notes=notes,
    )
    return result


@router.get("/goals/{user_id}", response_model=list[dict])
async def get_goals(user_id: str):
    """获取用户职业目标列表"""
    return await engine.career_goal_engine.get_goals(user_id)


@router.get("/goals/detail/{goal_id}")
async def get_goal(goal_id: str):
    """获取单个职业目标"""
    result = await engine.career_goal_engine.get_goal(goal_id)
    if not result:
        raise HTTPException(status_code=404, detail="目标不存在")
    return result


@router.put("/goals/{goal_id}")
async def update_goal(goal_id: str, **kwargs):
    """更新职业目标"""
    result = await engine.career_goal_engine.update_goal(goal_id, **kwargs)
    if not result:
        raise HTTPException(status_code=404, detail="目标不存在")
    return result


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str):
    """删除职业目标"""
    success = await engine.career_goal_engine.delete_goal(goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="目标不存在")
    return {"message": "已删除"}


# ── Target Companies ──────────────────────────────────────────

@router.post("/companies")
async def create_target_company(
    user_id: str = Query(...),
    company_name: str = Query(...),
    company_type: str = Query(None),
    industry: str = Query(None),
    target_position: str = Query(None),
    priority: int = Query(0),
    notes: str = Query(None),
):
    """添加目标公司"""
    return await engine.career_goal_engine.create_target_company(
        user_id=user_id,
        company_name=company_name,
        company_type=company_type,
        industry=industry,
        target_position=target_position,
        priority=priority,
        notes=notes,
    )


@router.get("/companies/{user_id}", response_model=list[dict])
async def get_target_companies(user_id: str):
    """获取目标公司列表"""
    return await engine.career_goal_engine.get_target_companies(user_id)


@router.delete("/companies/{company_id}")
async def delete_target_company(company_id: str):
    """删除目标公司"""
    success = await engine.career_goal_engine.delete_target_company(company_id)
    if not success:
        raise HTTPException(status_code=404, detail="公司不存在")
    return {"message": "已删除"}


# ── User Preferences ──────────────────────────────────────────

@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """获取用户求职偏好"""
    return await engine.career_goal_engine.get_or_create_preference(user_id)


@router.put("/preferences/{user_id}")
async def update_preferences(user_id: str, **kwargs):
    """更新用户求职偏好"""
    return await engine.career_goal_engine.update_preference(user_id, **kwargs)


# ── Career Progress ───────────────────────────────────────────

@router.get("/progress/{user_id}")
async def get_progress(user_id: str):
    """获取职业进度"""
    return await engine.career_goal_engine.get_or_create_progress(user_id)


@router.put("/progress/{user_id}")
async def update_progress(user_id: str, **kwargs):
    """更新职业进度"""
    return await engine.career_goal_engine.update_progress(user_id, **kwargs)
