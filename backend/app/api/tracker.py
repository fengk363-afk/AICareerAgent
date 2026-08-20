from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine
from app.schemas.models import ApplicationResponse

router = APIRouter()


@router.get("/dashboard/{user_id}", response_model=dict)
async def get_dashboard(user_id: int, db: AsyncSession = Depends(__import__('app.db.database', fromlist=['get_db']).get_db)):
    """获取用户投递总览"""
    applications = await engine.get_applications(user_id)

    stats = {
        "total": len(applications),
        "draft": 0, "applied": 0, "screening": 0, "written_test": 0,
        "interview_invited": 0, "offer": 0, "rejected": 0,
    }
    for app in applications:
        key = app.status.value if hasattr(app.status, "value") else str(app.status)
        if key in stats:
            stats[key] += 1

    recent = applications[:5] if applications else []

    return {
        "user_id": user_id,
        "stats": stats,
        "recent_applications": recent,
    }


@router.get("/applications/{user_id}", response_model=list[ApplicationResponse])
async def list_applications(user_id: int):
    """获取用户投递列表"""
    return await engine.get_applications(user_id)
