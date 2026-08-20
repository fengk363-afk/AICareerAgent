from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ResumeProfile, Job
from app.agents.engine import engine

router = APIRouter()


@router.post("/generate/{profile_id}/{job_id}")
async def generate_plan(profile_id: str, job_id: str, db: AsyncSession = Depends(get_db)):
    """生成能力提升路线"""
    # 从数据库获取技能和缺失信息
    profile = await db.get(ResumeProfile, profile_id)
    job = await db.get(Job, job_id)
    if not profile or not job:
        raise HTTPException(status_code=404, detail="简历或岗位不存在")

    # 计算缺失技能
    profile_skills = {s["name"] for s in (profile.skills or [])}
    job_skills = set(job.preferred_skills or [])
    missing_skills = list(job_skills - profile_skills)
    existing_skills = list(profile_skills)

    result = await engine.generate_learning_plan(profile_id, job_id, missing_skills=missing_skills, existing_skills=existing_skills)
    if not result:
        raise HTTPException(status_code=404, detail="生成学习路线失败")
    return result


@router.get("/plans/{profile_id}", response_model=list[dict])
async def list_plans(profile_id: str):
    """获取学习路线列表"""
    return await engine.get_learning_plans(profile_id)
