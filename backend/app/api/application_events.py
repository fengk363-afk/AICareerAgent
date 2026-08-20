from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Job, ApplicationEvent
from app.agents.engine import engine

router = APIRouter()


@router.post("/track/{job_id}")
async def track_apply_action(job_id: str, user_id: int = 1, event_type: str = "view_apply", db: AsyncSession = Depends(get_db)):
    """记录用户投递行为"""
    # 验证岗位存在
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 创建事件记录
    event = ApplicationEvent(
        id=f"{event_type}_{job_id}_{user_id}",
        user_id=user_id,
        job_id=job_id,
        event_type=event_type,
        event_data={"timestamp": str(__import__('datetime').datetime.utcnow())},
    )
    db.add(event)
    await db.commit()
    return {"message": f"已记录{event_type}行为", "event_type": event_type}


@router.get("/events/{user_id}")
async def get_user_events(user_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """获取用户投递行为记录"""
    result = await db.execute(
        select(ApplicationEvent)
        .where(ApplicationEvent.user_id == user_id)
        .order_by(ApplicationEvent.created_at.desc())
        .limit(limit)
    )
    return [e.__dict__ for e in result.scalars().all()]
