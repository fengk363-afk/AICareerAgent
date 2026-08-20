from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import InterviewSession
from app.agents.engine import engine
from app.schemas.models import InterviewSessionCreate, InterviewSessionResponse, UserAnswer

router = APIRouter()


@router.post("/sessions", response_model=InterviewSessionResponse)
async def create_session(data: InterviewSessionCreate):
    """创建模拟面试会话"""
    result = await engine.create_interview(data.user_id, data.job_id)
    if not result:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return result


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取面试会话详情"""
    session = await db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    return InterviewSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/submit")
async def submit_answers(session_id: str, answers: list[UserAnswer]):
    """提交面试答案，获取反馈"""
    result = await engine.submit_interview_answers(session_id, answers)
    if not result:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    return result
