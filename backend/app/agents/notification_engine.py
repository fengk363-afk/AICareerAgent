"""
NotificationEngine — 面试通知 + 岗位状态提醒
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import Notification, Job, Application
from app.db.database import get_db


class NotificationEngine:
    """通知引擎"""

    async def create_notification(
        self, user_id, notif_type: str, title: str, content: str = None, job_id: str = None
    ) -> dict:
        """创建通知"""
        async for db in get_db():
            notif = Notification(
                id=str(uuid.uuid4()),
                user_id=int(user_id),
                type=notif_type,
                title=title,
                content=content,
                job_id=job_id,
                is_read=False,
                created_at=datetime.utcnow(),
            )
            db.add(notif)
            await db.commit()
            await db.refresh(notif)
            logger.info(f"通知创建: {notif.id}, type={notif_type}")
            return {"id": notif.id, "type": notif.type, "title": notif.title, "is_read": notif.is_read}

    async def get_user_notifications(self, user_id, limit: int = 20) -> List[dict]:
        """获取用户通知列表"""
        async for db in get_db():
            from sqlalchemy import select
            result = await db.execute(
                select(Notification)
                .where(Notification.user_id == int(user_id))
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
            return [n.model_dump() for n in result.scalars().all()]
        return []

    async def mark_as_read(self, notification_id: str) -> bool:
        """标记已读"""
        async for db in get_db():
            notif = await db.get(Notification, notification_id)
            if notif:
                notif.is_read = True
                await db.commit()
                return True
            return False

    async def mark_all_read(self, user_id) -> int:
        """全部已读"""
        async for db in get_db():
            from sqlalchemy import update
            result = await db.execute(
                update(Notification)
                .where(Notification.user_id == int(user_id), Notification.is_read == False)
                .values(is_read=True)
            )
            await db.commit()
            return result.rowcount

    async def check_and_notify(self, user_id) -> List[dict]:
        """检查并生成新通知（面试提醒、投递状态变更等）"""
        notifications = []
        async for db in get_db():
            # 检查未读的面试通知
            from sqlalchemy import select
            result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
            )
            applications = result.scalars().all()
            for app in applications:
                if app.status.value == "interview_invited" and not app.notes:
                    # 检查是否已有通知
                    notif_result = await db.execute(
                        select(Notification).where(
                            Notification.user_id == int(user_id),
                            Notification.type == "interview_reminder",
                            Notification.job_id == app.job_id,
                        )
                    )
                    if not notif_result.scalar_one_or_none():
                        job = await db.get(Job, app.job_id)
                        if job:
                            notif = await self.create_notification(
                                user_id, "interview_reminder",
                                f"🎉 {job.company} 面试邀请",
                                f"您投递的 {job.title} 岗位已获得面试邀请，请尽快准备！",
                                job_id=app.job_id,
                            )
                            notifications.append(notif)
        return notifications
