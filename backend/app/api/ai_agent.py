"""
AI Career Agent API — AI 职业助手
"""
from fastapi import APIRouter, Query
from app.agents.engine import engine

router = APIRouter()


@router.get("/daily-tasks/{user_id}")
async def get_daily_tasks(user_id: str):
    """获取每日任务"""
    return await engine.ai_career_agent_engine.get_daily_tasks(user_id)


@router.get("/skill-recommendations/{user_id}")
async def get_skill_recommendations(user_id: str):
    """获取技能提升建议"""
    return await engine.ai_career_agent_engine.get_skill_recommendations(user_id)


@router.get("/application-plan/{user_id}")
async def get_application_plan(user_id: str):
    """获取投递计划"""
    return await engine.ai_career_agent_engine.get_application_plan(user_id)


@router.get("/interview-plan/{user_id}")
async def get_interview_plan(user_id: str):
    """获取面试准备计划"""
    return await engine.ai_career_agent_engine.get_interview_plan(user_id)
