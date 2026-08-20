from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.db.database import get_db
from app.db.models import AIAnalysisRecord
from app.agents.engine import engine
from app.schemas.models import MatchScoreResponse, AIAnalysisRecordResponse

router = APIRouter()


@router.get("/match", response_model=MatchScoreResponse)
async def calculate_match(profile_id: str, job_id: str):
    """计算简历与岗位的匹配度（AI增强）"""
    result = await engine.get_match(profile_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="简历画像或岗位不存在")
    return result


@router.get("/analysis/{profile_id}/{job_id}", response_model=AIAnalysisRecordResponse)
async def get_analysis(profile_id: str, job_id: str, db: AsyncSession = Depends(get_db)):
    """获取AI匹配分析详情"""
    result = await engine.get_ai_analysis(profile_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")

    # 从数据库获取详细记录
    from app.db.models import AIAnalysisRecord
    record_result = await db.execute(
        select(AIAnalysisRecord)
        .where(AIAnalysisRecord.profile_id == profile_id, AIAnalysisRecord.job_id == job_id)
        .order_by(AIAnalysisRecord.created_at.desc())
        .limit(1)
    )
    record = record_result.scalar_one_or_none()
    if record:
        return AIAnalysisRecordResponse.model_validate(record)
    return result


@router.get("/history/{profile_id}", response_model=list[AIAnalysisRecordResponse])
async def get_history(profile_id: str, limit: int = Query(10, le=50)):
    """获取匹配分析历史"""
    result = await engine.get_analysis_history(profile_id)
    return result
