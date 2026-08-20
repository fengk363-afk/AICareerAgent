"""
Application Center API — 智能投递中心
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.db.database import get_db
from app.db.models import Application, Job
from app.agents.engine import engine
from app.schemas.models import (
    ApplicationCreateRequest,
    ApplicationPrepareRequest,
    ApplicationPrepareResponse,
    ApplicationSubmitRequest,
    ApplicationStatusResponse,
    ApplicationHistoryResponse,
)

router = APIRouter()


@router.post("/create", response_model=ApplicationStatusResponse)
async def create_application(data: ApplicationCreateRequest):
    """创建投递任务"""
    result = await engine.smart_application_engine.create_application(
        user_id=data.user_id,
        job_id=data.job_id,
        resume_profile_id=data.resume_profile_id,
        resume_version_id=data.resume_version_id,
        application_mode=data.application_mode,
        notes=data.notes,
    )
    if not result:
        raise HTTPException(status_code=400, detail="投递任务创建失败")
    return result


@router.post("/prepare", response_model=ApplicationPrepareResponse)
async def prepare_application(data: ApplicationPrepareRequest):
    """自动生成投递材料"""
    result = await engine.smart_application_engine.prepare_application(
        user_id=data.user_id,
        job_id=data.job_id,
        resume_profile_id=data.resume_profile_id,
        target_position=data.target_position,
        target_company=data.target_company,
    )
    if not result:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return result


@router.post("/submit")
async def submit_application(data: ApplicationSubmitRequest):
    """提交投递"""
    result = await engine.smart_application_engine.submit_application(
        user_id=data.user_id,
        job_id=data.job_id,
        application_id=data.application_id,
        cover_letter=data.cover_letter,
        resume_version_id=data.resume_version_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {"message": "投递已提交", "application_id": data.application_id}


@router.get("/status/{application_id}", response_model=ApplicationStatusResponse)
async def get_application_status(application_id: str):
    """查询投递状态"""
    result = await engine.smart_application_engine.get_application_status(application_id)
    if not result:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return result


@router.get("/history/{user_id}", response_model=list[ApplicationHistoryResponse])
async def get_application_history(user_id: str):
    """获取投递记录"""
    return await engine.smart_application_engine.get_application_history(user_id)


@router.get("/job/{job_id}", response_model=list[ApplicationHistoryResponse])
async def get_applications_for_job(job_id: str):
    """获取某岗位的所有投递记录"""
    return await engine.smart_application_engine.get_applications_for_job(job_id)


@router.patch("/status/{application_id}")
async def update_application_status(
    application_id: str,
    status: str = Query(..., description="新状态"),
    notes: str = Query(None, description="备注"),
):
    """更新投递状态"""
    result = await engine.smart_application_engine.update_application_status(
        application_id, status, notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return result


@router.get("/stats/{user_id}")
async def get_application_stats(user_id: str, db: AsyncSession = Depends(get_db)):
    """获取投递统计"""
    result = await db.execute(
        select(Application).where(Application.user_id == int(user_id))
    )
    applications = result.scalars().all()

    stats = {
        "total": len(applications),
        "by_status": {},
        "by_mode": {},
    }

    for app in applications:
        status = app.status.value if hasattr(app.status, 'value') else str(app.status)
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        mode = app.application_mode or "redirect"
        stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1

    return stats
