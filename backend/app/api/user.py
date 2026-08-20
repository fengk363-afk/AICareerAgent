from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.database import get_db
from app.db.models import User, ResumeProfile, ResumeVersion, CareerPreference, Application, InterviewSession
from app.schemas.user import UserProfileResponse

router = APIRouter()


@router.get("/dashboard", response_model=dict)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """获取用户主页数据"""
    # 获取用户信息
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    # 获取简历数量
    result = await db.execute(select(ResumeProfile))
    profiles = result.scalars().all()
    resume_count = len(profiles)

    # 获取版本数量
    result = await db.execute(select(ResumeVersion))
    versions = result.scalars().all()
    version_count = len(versions)

    # 获取投递数量
    result = await db.execute(select(Application))
    applications = result.scalars().all()
    applied_count = len(applications)

    # 获取面试数量
    result = await db.execute(select(InterviewSession))
    interviews = result.scalars().all()
    interview_count = len(interviews)

    # 获取求职偏好
    result = await db.execute(select(CareerPreference).limit(1))
    preference = result.scalar_one_or_none()

    # 统计各状态投递
    stats = {
        "total": applied_count,
        "draft": 0,
        "applied": 0,
        "interview_invited": 0,
        "offer": 0,
        "rejected": 0,
    }
    for app in applications:
        status_val = app.status.value if hasattr(app.status, 'value') else str(app.status)
        if status_val in stats:
            stats[status_val] += 1

    return {
        "user": UserProfileResponse(
            id=str(user.id) if user else "",
            username=user.username if user else "",
            email=user.email if user else "",
            full_name=user.full_name if user else "",
            phone=user.phone if user else "",
            bio=user.bio if user else "",
            created_at=user.created_at if user else datetime.utcnow(),
        ).model_dump() if user else None,
        "preference": {
            "target_industry": preference.target_industry if preference else None,
            "target_role": preference.target_role if preference else None,
            "target_location": preference.target_location if preference else None,
            "salary_min": preference.salary_min if preference else None,
            "salary_max": preference.salary_max if preference else None,
        } if preference else None,
        "stats": {
            "resume_count": resume_count,
            "version_count": version_count,
            "applied_count": applied_count,
            "interview_count": interview_count,
            **stats,
        },
    }
