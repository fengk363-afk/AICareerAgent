from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine

router = APIRouter()


@router.get("/notifications/{user_id}")
async def get_notifications(user_id: int, limit: int = 20):
    """获取用户通知列表"""
    return await engine.get_notifications(user_id, limit)


@router.post("/notifications/{notification_id}/read")
async def mark_read(notification_id: str):
    """标记通知已读"""
    success = await engine.mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"message": "已标记为已读"}


@router.post("/notifications/{user_id}/read-all")
async def mark_all_read(user_id: int):
    """全部已读"""
    count = await engine.mark_all_notifications_read(user_id)
    return {"message": f"已标记 {count} 条通知为已读"}


@router.post("/notifications/check/{user_id}")
async def check_notifications(user_id: int):
    """检查并生成新通知"""
    notifications = await engine.check_notifications(user_id)
    return {"new_notifications": notifications}
