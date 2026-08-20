"""
Career Agent API — AI 职业顾问
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from app.db.database import get_db
from app.agents.engine import engine

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None


class LearningPlanRequest(BaseModel):
    user_id: str


@router.post("/chat")
async def chat(request: ChatRequest):
    """用户职业咨询对话"""
    result = await engine.career_agent_engine.chat(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
    )
    return result


@router.get("/insights/{user_id}", response_model=list[dict])
async def get_insights(user_id: str):
    """获取职业分析洞察"""
    return await engine.career_agent_engine.get_insights(user_id)


@router.post("/learning/plan/create/{user_id}")
async def create_learning_plan(user_id: str):
    """生成技能提升计划"""
    return await engine.career_agent_engine.create_learning_plan(user_id)


@router.get("/learning/tasks/{user_id}", response_model=list[dict])
async def get_learning_tasks(user_id: str):
    """获取学习任务"""
    return await engine.career_agent_engine.get_learning_tasks(user_id)


@router.get("/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    """获取个人求职仪表盘"""
    return await engine.career_agent_engine.get_dashboard(user_id)


@router.get("/notifications/{user_id}", response_model=list[dict])
async def get_notifications(user_id: str, limit: int = Query(20, le=100)):
    """获取通知列表"""
    return await engine.career_agent_engine.get_notifications(user_id, limit)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """标记通知已读"""
    success = await engine.career_agent_engine.mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"message": "已标记为已读"}


@router.post("/notifications/{user_id}/read-all")
async def mark_all_notifications_read(user_id: str):
    """全部已读"""
    count = await engine.career_agent_engine.mark_all_notifications_read(user_id)
    return {"message": f"已标记 {count} 条通知为已读"}


@router.post("/notifications/check/{user_id}")
async def check_notifications(user_id: str):
    """检查并生成新通知"""
    return await engine.career_agent_engine.check_and_notify(user_id)
