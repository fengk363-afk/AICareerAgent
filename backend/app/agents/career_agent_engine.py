"""
CareerAgentEngine — AI 职业顾问引擎
基于用户简历、岗位、投递记录、面试记录提供智能职业咨询
"""
import uuid
import json
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger

from app.db.models import (
    CareerMessage, CareerInsight, LearningTask, Notification,
    ResumeProfile, Job, Application, InterviewSession, InterviewAnswer,
    CareerGoal, TargetCompany, CareerProgress,
)
from app.db.database import get_db
from sqlalchemy import select


class CareerAgentEngine:
    """AI 职业顾问引擎"""

    # AI 回复模板
    RESPONSE_TEMPLATES = {
        "greeting": "你好！我是你的 AI 求职顾问。我可以帮你分析简历、推荐岗位、准备面试、规划职业路径。请告诉我你的需求？",
        "resume_analysis": "基于你的简历分析，我发现以下亮点：\n1. 技能匹配度良好\n2. 项目经验丰富\n3. 建议补充 {missing_skills} 技能\n\n整体匹配度：{score}%",
        "job_recommendation": "根据你的职业目标，我推荐以下岗位：\n\n{jobs}\n\n建议优先投递：{top_job}",
        "interview_prep": "针对这个岗位，建议你重点准备：\n1. {tech_questions}\n2. {behavioral_questions}\n3. 公司背景调研：{company_info}",
        "career_advice": "基于你的情况，我建议：\n1. 短期：补充 {skills} 技能\n2. 中期：积累 {experience} 经验\n3. 长期：向 {direction} 方向发展",
        "salary_advice": "根据市场行情，{position} 岗位的薪资范围是 {salary_range}。你的期望薪资 {expectation} 属于{level}水平。",
        "motivation": "求职是一个系统工程，保持积极心态很重要！你已经完成了 {progress}% 的目标，继续加油！"
    }

    async def chat(self, user_id: str, message: str, session_id: Optional[str] = None) -> dict:
        """处理用户职业咨询对话"""
        async for db in get_db():
            # 获取用户上下文
            context = await self._build_context(db, user_id)

            # 生成回复
            response = await self._generate_response(message, context)

            # 保存消息
            msg_id = str(uuid.uuid4())
            if not session_id:
                session_id = f"session_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"

            # 保存用户消息
            user_msg = CareerMessage(
                id=str(uuid.uuid4()),
                user_id=int(user_id),
                session_id=session_id,
                role="user",
                content=message,
                created_at=datetime.utcnow(),
            )
            db.add(user_msg)

            # 保存AI回复
            ai_msg = CareerMessage(
                id=msg_id,
                user_id=int(user_id),
                session_id=session_id,
                role="assistant",
                content=response["text"],
                context_type=response.get("context_type"),
                created_at=datetime.utcnow(),
            )
            db.add(ai_msg)

            # 清理过期历史：保留最近 MAX_HISTORY 轮对话，防止 token 累积超限
            await self._prune_history(db, session_id)

            # 生成洞察
            if response.get("generate_insight"):
                await self._create_insight(db, user_id, response)

            await db.commit()

            return {
                "session_id": session_id,
                "message_id": msg_id,
                "response": response["text"],
                "suggestions": response.get("suggestions", []),
                "context": response.get("context", {}),
            }

    async def _prune_history(self, db, session_id: str):
        """清理对话历史，保留最近 MAX_HISTORY 轮，防止 token 累积超限"""
        MAX_HISTORY = 20  # 保留最近 20 条消息（10 轮对话）
        result = await db.execute(
            select(CareerMessage)
            .where(CareerMessage.session_id == session_id)
            .order_by(CareerMessage.created_at.desc())
        )
        all_msgs = result.scalars().all()
        if len(all_msgs) > MAX_HISTORY:
            to_delete = all_msgs[MAX_HISTORY:]
            for msg in to_delete:
                await db.delete(msg)
            logger.info(f"清理对话历史：session={session_id}, 删除 {len(to_delete)} 条旧消息，保留最近 {MAX_HISTORY} 条")

    async def get_insights(self, user_id: str) -> List[dict]:
        """获取职业分析洞察"""
        async for db in get_db():
            result = await db.execute(
                select(CareerInsight)
                .where(CareerInsight.user_id == int(user_id))
                .order_by(CareerInsight.created_at.desc())
                .limit(20)
            )
            insights = result.scalars().all()
            return [
                {
                    "id": i.id,
                    "insight_type": i.insight_type,
                    "title": i.title,
                    "content": i.content,
                    "is_read": i.is_read,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in insights
            ]

    async def create_learning_plan(self, user_id: str) -> dict:
        """生成技能提升计划"""
        async for db in get_db():
            # 获取用户上下文
            context = await self._build_context(db, user_id)

            # 生成学习任务
            tasks = self._generate_learning_tasks(context)

            # 保存到数据库
            saved_tasks = []
            for task_data in tasks:
                task = LearningTask(
                    id=str(uuid.uuid4()),
                    user_id=int(user_id),
                    skill_name=task_data["skill"],
                    task_type=task_data["type"],
                    title=task_data["title"],
                    description=task_data["description"],
                    estimated_hours=task_data.get("estimated_hours", 10),
                    priority=task_data.get("priority", 0),
                    resources=task_data.get("resources"),
                    status="pending",
                    created_at=datetime.utcnow(),
                )
                db.add(task)
                saved_tasks.append({
                    "id": task.id,
                    "skill_name": task_data["skill"],
                    "type": task_data["type"],
                    "title": task_data["title"],
                    "estimated_hours": task_data.get("estimated_hours", 10),
                    "priority": task_data.get("priority", 0),
                    "status": "pending",
                })

            await db.commit()

            return {
                "total_tasks": len(saved_tasks),
                "estimated_total_hours": sum(t["estimated_hours"] for t in saved_tasks),
                "tasks": saved_tasks,
                "summary": f"为你生成了 {len(saved_tasks)} 个学习任务，预计需要 {sum(t['estimated_hours'] for t in saved_tasks):.0f} 小时",
            }

    async def get_learning_tasks(self, user_id: str) -> List[dict]:
        """获取学习任务列表"""
        async for db in get_db():
            result = await db.execute(
                select(LearningTask)
                .where(LearningTask.user_id == int(user_id))
                .order_by(LearningTask.priority.desc(), LearningTask.created_at.desc())
            )
            tasks = result.scalars().all()
            return [
                {
                    "id": t.id,
                    "skill_name": t.skill_name,
                    "task_type": t.task_type,
                    "title": t.title,
                    "description": t.description,
                    "estimated_hours": t.estimated_hours,
                    "completed_hours": t.completed_hours,
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                }
                for t in tasks
            ]

    async def get_dashboard(self, user_id: str) -> dict:
        """获取个人求职仪表盘"""
        async for db in get_db():
            # 统计投递记录
            app_result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
            )
            applications = app_result.scalars().all()

            # 统计面试记录
            interview_result = await db.execute(
                select(InterviewSession).where(InterviewSession.user_id == int(user_id))
            )
            interviews = interview_result.scalars().all()

            # 统计进度
            progress_result = await db.execute(
                select(CareerProgress).where(CareerProgress.user_id == int(user_id))
            )
            progress = progress_result.scalar_one_or_none()

            # 统计目标
            goal_result = await db.execute(
                select(CareerGoal).where(CareerGoal.user_id == int(user_id))
                .where(CareerGoal.status == "active")
            )
            goals = goal_result.scalars().all()

            # 统计公司
            company_result = await db.execute(
                select(TargetCompany).where(TargetCompany.user_id == int(user_id))
            )
            companies = company_result.scalars().all()

            # 统计通知
            notif_result = await db.execute(
                select(Notification).where(Notification.user_id == int(user_id))
                .where(Notification.is_read == False)
            )
            unread_notifs = len(list(notif_result.scalars().all()))

            # 统计洞察
            insight_result = await db.execute(
                select(CareerInsight).where(CareerInsight.user_id == int(user_id))
                .where(CareerInsight.is_read == False)
            )
            unread_insights = len(list(insight_result.scalars().all()))

            # 计算统计
            stats = {
                "total_applications": len(applications),
                "by_status": {},
                "total_interviews": len(interviews),
                "completed_interviews": len([i for i in interviews if (i.status.value == "completed" if hasattr(i.status, 'value') else i.status == "completed")]),
                "total_goals": len(goals),
                "total_companies": len(companies),
                "unread_notifications": unread_notifs,
                "unread_insights": unread_insights,
            }

            for app in applications:
                status = app.status.value if hasattr(app.status, 'value') else str(app.status)
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # 获取最新洞察
            latest_insights = []
            if insights := await self.get_insights(user_id):
                latest_insights = insights[:3]

            return {
                "stats": stats,
                "progress": {
                    "percentage": progress.progress_percentage if progress else 0,
                    "milestones": progress.milestones if progress else [],
                } if progress else {"percentage": 0, "milestones": []},
                "latest_insights": latest_insights,
                "recommendations": self._generate_dashboard_recommendations(stats, goals),
            }

    async def get_notifications(self, user_id: str, limit: int = 20) -> List[dict]:
        """获取通知列表"""
        async for db in get_db():
            result = await db.execute(
                select(Notification)
                .where(Notification.user_id == int(user_id))
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
            notifications = result.scalars().all()
            return [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "content": n.content,
                    "is_read": n.is_read,
                    "link": n.link,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notifications
            ]

    async def mark_notification_read(self, notification_id: str) -> bool:
        """标记通知已读"""
        async for db in get_db():
            notif = await db.get(Notification, notification_id)
            if notif:
                notif.is_read = True
                await db.commit()
                return True
            return False

    async def mark_all_notifications_read(self, user_id: str) -> int:
        """全部已读"""
        async for db in get_db():
            result = await db.execute(
                select(Notification).where(
                    Notification.user_id == int(user_id),
                    Notification.is_read == False,
                )
            )
            notifications = result.scalars().all()
            for n in notifications:
                n.is_read = True
            await db.commit()
            return len(notifications)

    async def check_and_notify(self, user_id: str) -> List[dict]:
        """检查并生成新通知"""
        async for db in get_db():
            new_notifications = []

            # 检查投递状态变化
            app_result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
            )
            applications = app_result.scalars().all()

            for app in applications:
                # 检查是否有新的状态更新
                if app.status.value in ["interview_invited", "offer"]:
                    # 生成通知
                    notif_id = str(uuid.uuid4())
                    notif = Notification(
                        id=notif_id,
                        user_id=int(user_id),
                        type="application_update",
                        title=f"{'面试邀请' if app.status.value == 'interview_invited' else 'Offer!'}",
                        content=f"你的投递已获得{app.status.value.replace('_', ' ')}状态",
                        application_id=app.id,
                        created_at=datetime.utcnow(),
                    )
                    db.add(notif)
                    new_notifications.append(notif_id)

            await db.commit()
            return [{"id": nid, "created": True} for nid in new_notifications]

    async def _build_context(self, db, user_id: str) -> dict:
        """构建用户上下文"""
        context = {
            "user_id": user_id,
            "resume": None,
            "goals": [],
            "applications": [],
            "interviews": [],
            "progress": None,
        }

        # 获取简历
        profile_result = await db.execute(
            select(ResumeProfile)
            .order_by(ResumeProfile.created_at.desc())
            .limit(1)
        )
        context["resume"] = profile_result.scalar_one_or_none()

        # 获取目标
        goals_result = await db.execute(
            select(CareerGoal)
            .where(CareerGoal.user_id == int(user_id))
            .where(CareerGoal.status == "active")
        )
        context["goals"] = goals_result.scalars().all()

        # 获取投递记录
        app_result = await db.execute(
            select(Application).where(Application.user_id == int(user_id))
        )
        context["applications"] = app_result.scalars().all()

        # 获取面试记录
        interview_result = await db.execute(
            select(InterviewSession).where(InterviewSession.user_id == int(user_id))
        )
        context["interviews"] = interview_result.scalars().all()

        # 获取进度
        progress_result = await db.execute(
            select(CareerProgress).where(CareerProgress.user_id == int(user_id))
        )
        context["progress"] = progress_result.scalar_one_or_none()

        return context

    async def _generate_response(self, message: str, context: dict) -> dict:
        """生成 AI 回复"""
        message_lower = message.lower()

        #  greeting
        if any(kw in message_lower for kw in ["你好", "hello", "hi", "hey"]):
            return {
                "text": self.RESPONSE_TEMPLATES["greeting"],
                "context_type": "greeting",
                "generate_insight": False,
                "suggestions": ["分析我的简历", "推荐岗位", "准备面试"],
            }

        # 简历分析
        if any(kw in message_lower for kw in ["简历", "resume", "分析", "分析我的"]):
            if context["resume"]:
                skills = [s["name"] for s in (context["resume"].skills or [])]
                return {
                    "text": self.RESPONSE_TEMPLATES["resume_analysis"].format(
                        missing_skills="Kafka, Docker" if len(skills) < 5 else "暂无",
                        score=75 if len(skills) >= 5 else 60
                    ),
                    "context_type": "resume",
                    "generate_insight": True,
                    "suggestions": ["优化简历", "补充技能"],
                }
            return {
                "text": "你还没有上传简历，请先上传简历以便我为你分析。",
                "context_type": "resume",
                "generate_insight": False,
                "suggestions": ["上传简历"],
            }

        # 岗位推荐
        if any(kw in message_lower for kw in ["推荐", "岗位", "job", "工作"]):
            goals_text = "\n".join([f"- {g.target_position} @ {g.target_company or '不限'}" for g in context["goals"][:3]])
            return {
                "text": f"根据你的职业目标，我为你推荐以下方向的岗位：\n\n{goals_text or '暂无明确目标，建议先设定职业目标'}\n\n你可以在【岗位市场】页面查看更多机会。",
                "context_type": "recommendation",
                "generate_insight": True,
                "suggestions": ["查看岗位市场", "设定职业目标"],
            }

        # 面试准备
        if any(kw in message_lower for kw in ["面试", "interview", "准备"]):
            return {
                "text": self.RESPONSE_TEMPLATES["interview_prep"].format(
                    tech_questions="数据结构与算法、系统设计基础",
                    behavioral_questions="项目经历、团队合作、问题解决",
                    company_info="了解公司背景、技术栈、业务方向"
                ),
                "context_type": "interview",
                "generate_insight": True,
                "suggestions": ["开始模拟面试", "查看面试题库"],
            }

        # 职业规划
        if any(kw in message_lower for kw in ["规划", "career", "发展", "方向"]):
            return {
                "text": self.RESPONSE_TEMPLATES["career_advice"].format(
                    skills="目标岗位相关技术",
                    experience="完整项目经验",
                    direction="技术专家或技术管理"
                ),
                "context_type": "career",
                "generate_insight": True,
                "suggestions": ["生成学习路线", "设定职业目标"],
            }

        # 薪资咨询
        if any(kw in message_lower for kw in ["薪资", "salary", "待遇"]):
            return {
                "text": self.RESPONSE_TEMPLATES["salary_advice"].format(
                    position="后端开发工程师",
                    salary_range="25-45K/月",
                    expectation="市场中等水平",
                    level="中等"
                ),
                "context_type": "salary",
                "generate_insight": False,
                "suggestions": ["查看岗位薪资", "谈判技巧"],
            }

        # 鼓励
        if any(kw in message_lower for kw in ["鼓励", "加油", "坚持"]):
            progress_pct = context["progress"].progress_percentage if context["progress"] else 0
            return {
                "text": self.RESPONSE_TEMPLATES["motivation"].format(progress=progress_pct),
                "context_type": "motivation",
                "generate_insight": False,
                "suggestions": ["查看进度", "设定新目标"],
            }

        # 默认回复
        return {
            "text": "我理解你的问题。作为 AI 求职顾问，我可以帮你：\n1. 分析简历和岗位匹配度\n2. 推荐合适的岗位\n3. 准备面试\n4. 规划职业路径\n\n请告诉我你的具体需求？",
            "context_type": "general",
            "generate_insight": False,
            "suggestions": ["分析简历", "推荐岗位", "准备面试"],
        }

    async def _create_insight(self, db, user_id: str, response: dict):
        """创建职业洞察"""
        insight_types = {
            "resume": "tip",
            "recommendation": "recommendation",
            "interview": "tip",
            "career": "tip",
            "salary": "tip",
        }
        insight_type = insight_types.get(response.get("context_type"), "tip")

        insight = CareerInsight(
            id=str(uuid.uuid4()),
            user_id=int(user_id),
            insight_type=insight_type,
            title=f"AI 建议：{response.get('context_type', 'general')}",
            content=response.get("text", "")[:500],
            created_at=datetime.utcnow(),
        )
        db.add(insight)
        await db.commit()

    def _generate_learning_tasks(self, context: dict) -> List[dict]:
        """生成学习任务"""
        tasks = []

        # 基于目标岗位生成技能学习任务
        for goal in context.get("goals", [])[:2]:
            if goal.target_position:
                tasks.append({
                    "skill": f"{goal.target_position}核心技能",
                    "type": "learn",
                    "title": f"学习 {goal.target_position} 核心技术栈",
                    "description": f"针对 {goal.target_position} 岗位，系统学习核心技术栈",
                    "estimated_hours": 40,
                    "priority": 10,
                    "resources": [{"type": "course", "title": "技术栈系统课程"}],
                })

        # 基于简历缺失技能生成任务
        if context.get("resume"):
            # 这里简化处理，实际应该对比岗位要求的技能
            tasks.append({
                "skill": "项目经验",
                "type": "practice",
                "title": "完成一个完整的项目实践",
                "description": "选择一个技术方向，完成从设计到部署的完整项目",
                "estimated_hours": 80,
                "priority": 8,
            })

        # 通用任务
        tasks.append({
            "skill": "算法",
            "type": "practice",
            "title": "LeetCode 刷题训练",
            "description": "每天坚持刷 2-3 道算法题，保持手感",
            "estimated_hours": 60,
            "priority": 7,
        })

        tasks.append({
            "skill": "面试技巧",
            "type": "review",
            "title": "模拟面试练习",
            "description": "进行至少 3 次完整的模拟面试",
            "estimated_hours": 10,
            "priority": 6,
        })

        return tasks

    def _generate_dashboard_recommendations(self, stats: dict, goals: List) -> List[dict]:
        """生成仪表盘推荐"""
        recommendations = []

        if stats["total_applications"] < 3:
            recommendations.append({
                "type": "action",
                "title": "增加投递",
                "description": "建议每天投递 3-5 个岗位",
                "priority": "high",
            })

        if stats["total_interviews"] == 0 and stats["total_applications"] > 0:
            recommendations.append({
                "type": "tip",
                "title": "准备面试",
                "description": "你的投递已获得响应，建议开始准备面试",
                "priority": "medium",
            })

        if not goals:
            recommendations.append({
                "type": "action",
                "title": "设定职业目标",
                "description": "设定明确的职业目标可以获得更精准的推荐",
                "priority": "high",
            })

        return recommendations
