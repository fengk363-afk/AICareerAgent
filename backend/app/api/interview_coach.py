"""
Interview Coach API — AI 面试教练
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.db.database import get_db
from app.db.models import InterviewSession, InterviewQuestion, InterviewAnswer
from app.agents.engine import engine
from app.schemas.models import (
    InterviewSessionCreate, InterviewSessionResponse, UserAnswer,
)

router = APIRouter()


@router.post("/generate/{job_id}")
async def generate_questions(
    job_id: str,
    question_types: str = Query(None, description="逗号分隔的问题类型: technical,behavioral,situational,hr,english"),
):
    """根据岗位JD生成面试题"""
    types = question_types.split(",") if question_types else None
    result = await engine.interview_coach_engine.generate_questions(job_id, types)
    if not result:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return result


@router.get("/questions/{job_id}", response_model=list[dict])
async def get_questions(job_id: str):
    """获取岗位题库"""
    return await engine.interview_coach_engine.get_questions(job_id)


@router.post("/session/create", response_model=dict)
async def create_session(data: InterviewSessionCreate):
    """创建模拟面试会话"""
    result = await engine.interview_coach_engine.create_session(data.user_id, data.job_id)
    if not result:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return result


@router.post("/session/{session_id}/answer")
async def submit_answer(session_id: str, answer_data: dict):
    """提交面试答案"""
    result = await engine.interview_coach_engine.submit_answer(session_id, answer_data)
    if not result:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    return result


@router.post("/evaluate/{answer_id}")
async def evaluate_answer(answer_id: str):
    """AI 评分反馈"""
    result = await engine.interview_coach_engine.evaluate_answer(answer_id)
    if not result:
        raise HTTPException(status_code=404, detail="答案不存在")
    return result


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取面试会话详情"""
    result = await engine.interview_coach_engine.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    return result


@router.get("/history/{user_id}", response_model=list[dict])
async def get_history(user_id: str):
    """获取面试历史记录"""
    return await engine.interview_coach_engine.get_history(user_id)


@router.get("/stats/{user_id}")
async def get_stats(user_id: str, db: AsyncSession = Depends(get_db)):
    """获取面试统计"""
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.user_id == int(user_id))
    )
    sessions = result.scalars().all()

    result2 = await db.execute(
        select(InterviewAnswer).where(InterviewAnswer.user_id == int(user_id))
    )
    answers = result2.scalars().all()

    total_sessions = len(sessions)
    total_answers = len(answers)
    avg_score = sum(a.score or 0 for a in answers) / total_answers if total_answers > 0 else 0

    return {
        "total_sessions": total_sessions,
        "total_answers": total_answers,
        "average_score": round(avg_score, 1),
        "sessions": [
            {
                "id": s.id,
                "job_id": s.job_id,
                "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
                "question_count": len(s.questions or []),
                "overall_score": s.overall_score,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in sessions
        ],
    }
