"""
AI Career Agent — AI 职业助手引擎
提供每日任务、技能提升建议、投递计划、面试准备计划
"""
import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger

from app.db.models import (
    CareerGoal, TargetCompany, UserJobPreference, CareerProgress,
    ResumeProfile, Job, Application, InterviewSession,
)
from app.db.database import get_db
from sqlalchemy import select


class AICareerAgentEngine:
    """AI 职业助手引擎"""

    async def get_daily_tasks(self, user_id: str) -> dict:
        """获取每日任务"""
        async for db in get_db():
            # 获取用户目标
            goals_result = await db.execute(
                select(CareerGoal).where(CareerGoal.user_id == int(user_id))
                .where(CareerGoal.status == "active")
                .order_by(CareerGoal.priority_level.desc())
            )
            goals = goals_result.scalars().all()

            # 获取求职偏好
            pref_result = await db.execute(
                select(UserJobPreference).where(UserJobPreference.user_id == int(user_id))
            )
            preference = pref_result.scalar_one_or_none()

            # 获取进度
            progress_result = await db.execute(
                select(CareerProgress).where(CareerProgress.user_id == int(user_id))
            )
            progress = progress_result.scalar_one_or_none()

            # 获取投递记录
            app_result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
            )
            applications = app_result.scalars().all()

            # 获取面试记录
            interview_result = await db.execute(
                select(InterviewSession).where(InterviewSession.user_id == int(user_id))
            )
            interviews = interview_result.scalars().all()

            # 生成每日任务
            tasks = self._generate_daily_tasks(goals, preference, progress, applications, interviews)

            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "tasks": tasks,
                "summary": self._generate_summary(goals, progress, applications, interviews),
            }

    async def get_skill_recommendations(self, user_id: str) -> dict:
        """获取技能提升建议"""
        async for db in get_db():
            # 获取目标
            goals_result = await db.execute(
                select(CareerGoal).where(CareerGoal.user_id == int(user_id))
                .where(CareerGoal.status == "active")
                .order_by(CareerGoal.priority_level.desc())
                .limit(1)
            )
            goal = goals_result.scalar_one_or_none()

            # 获取简历画像
            profile_result = await db.execute(
                select(ResumeProfile)
                .order_by(ResumeProfile.created_at.desc())
                .limit(1)
            )
            profile = profile_result.scalar_one_or_none()

            # 获取进度
            progress_result = await db.execute(
                select(CareerProgress).where(CareerProgress.user_id == int(user_id))
            )
            progress = progress_result.scalar_one_or_none()

            completed_skills = progress.completed_skills if progress else []
            skill_progress = progress.skill_progress if progress else {}

            recommendations = self._generate_skill_recommendations(goal, profile, completed_skills)

            return {
                "goal": self._goal_summary(goal),
                "current_skills": skill_progress,
                "completed_skills": completed_skills,
                "recommendations": recommendations,
            }

    async def get_application_plan(self, user_id: str) -> dict:
        """获取投递计划"""
        async for db in get_db():
            # 获取目标
            goals_result = await db.execute(
                select(CareerGoal).where(CareerGoal.user_id == int(user_id))
                .where(CareerGoal.status == "active")
                .order_by(CareerGoal.priority_level.desc())
            )
            goals = goals_result.scalars().all()

            # 获取投递记录
            app_result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
            )
            applications = app_result.scalars().all()

            # 获取目标公司
            company_result = await db.execute(
                select(TargetCompany).where(TargetCompany.user_id == int(user_id))
            )
            target_companies = company_result.scalars().all()

            plan = self._generate_application_plan(goals, applications, target_companies)

            return {
                "total_applications": len(applications),
                "by_status": self._count_by_status(applications),
                "plan": plan,
                "target_companies": [self._company_summary(c) for c in target_companies],
            }

    async def get_interview_plan(self, user_id: str) -> dict:
        """获取面试准备计划"""
        async for db in get_db():
            # 获取面试记录
            interview_result = await db.execute(
                select(InterviewSession).where(InterviewSession.user_id == int(user_id))
                .order_by(InterviewSession.created_at.desc())
            )
            interviews = interview_result.scalars().all()

            # 获取投递记录
            app_result = await db.execute(
                select(Application).where(Application.user_id == int(user_id))
            )
            applications = app_result.scalars().all()

            plan = self._generate_interview_plan(interviews, applications)

            return {
                "total_interviews": len(interviews),
                "upcoming": plan["upcoming"],
                "completed": plan["completed"],
                "tips": plan["tips"],
            }

    def _generate_daily_tasks(self, goals, preference, progress, applications, interviews) -> List[dict]:
        """生成每日任务"""
        tasks = []

        # 投递任务
        pending_apps = [a for a in applications if a.status.value in ["draft", "applied"]]
        if len(pending_apps) < 3:
            tasks.append({
                "type": "application",
                "title": "投递岗位",
                "description": f"已完成 {len(pending_apps)} 次投递，建议每天投递 3-5 个岗位",
                "priority": "high",
                "icon": "📤",
            })

        # 面试准备
        upcoming_interviews = [i for i in interviews if i.status.value in ["scheduled", "in_progress"]]
        if upcoming_interviews:
            tasks.append({
                "type": "interview",
                "title": "准备面试",
                "description": f"有 {len(upcoming_interviews)} 个面试待准备",
                "priority": "high",
                "icon": "💬",
            })

        # 技能提升
        if progress and progress.skill_progress:
            incomplete_skills = [
                skill for skill, level in progress.skill_progress.items()
                if level not in ["advanced", "expert"]
            ]
            if incomplete_skills:
                tasks.append({
                    "type": "skill",
                    "title": "技能提升",
                    "description": f"还有 {len(incomplete_skills)} 项技能需要提升",
                    "priority": "medium",
                    "icon": "📚",
                })

        # 目标跟进
        if goals:
            tasks.append({
                "type": "goal",
                "title": "职业目标",
                "description": f"当前有 {len(goals)} 个活跃职业目标",
                "priority": "medium",
                "icon": "🎯",
            })

        # 默认任务
        if not tasks:
            tasks.append({
                "type": "general",
                "title": "浏览岗位",
                "description": "查看最新岗位推荐，保持求职活跃度",
                "priority": "low",
                "icon": "🔍",
            })

        return tasks

    def _generate_summary(self, goals, progress, applications, interviews) -> str:
        """生成每日摘要"""
        parts = []
        if goals:
            parts.append(f"有 {len(goals)} 个职业目标")
        if progress:
            parts.append(f"整体进度 {progress.progress_percentage:.0f}%")
        parts.append(f"已投递 {len(applications)} 次")
        parts.append(f"面试 {len(interviews)} 场")
        return " · ".join(parts) if parts else "保持求职节奏，每天进步一点点！"

    def _generate_skill_recommendations(self, goal, profile, completed_skills) -> List[dict]:
        """生成技能提升建议"""
        recommendations = []

        if not goal:
            return [{"skill": "设定职业目标", "reason": "请先设定职业目标以获取个性化建议", "priority": "high"}]

        # 根据目标岗位推荐技能
        position = goal.target_position or ""
        industry = goal.target_industry or ""

        skill_map = {
            "后端": ["Python", "Go", "Java", "数据库", "分布式系统"],
            "前端": ["React", "Vue", "TypeScript", "CSS", "JavaScript"],
            "算法": ["Python", "机器学习", "深度学习", "数学", "算法"],
            "全栈": ["React", "Node.js", "Python", "数据库", "Docker"],
            "移动端": ["Kotlin", "Swift", "React Native", "Flutter"],
        }

        for key, skills in skill_map.items():
            if key in position:
                for skill in skills:
                    if skill not in completed_skills:
                        recommendations.append({
                            "skill": skill,
                            "reason": f"目标岗位 {position} 需要 {skill} 技能",
                            "priority": "medium",
                            "estimated_time": "2-4周",
                        })

        if not recommendations:
            recommendations.append({
                "skill": "通用技术能力",
                "reason": "持续提升技术深度和广度",
                "priority": "low",
                "estimated_time": "持续",
            })

        return recommendations[:5]

    def _generate_application_plan(self, goals, applications, target_companies) -> List[dict]:
        """生成投递计划"""
        plan = []

        # 按目标公司生成计划
        for company in target_companies:
            plan.append({
                "type": "company",
                "title": f"跟进 {company.company_name}",
                "description": f"目标岗位: {company.target_position or '未知'}",
                "status": company.status,
                "priority": company.priority,
            })

        # 按目标岗位生成计划
        for goal in goals:
            if goal.target_position:
                plan.append({
                    "type": "position",
                    "title": f"寻找 {goal.target_position} 岗位",
                    "description": f"目标: {goal.target_city or goal.target_country or '不限'}",
                    "priority": goal.priority_level,
                })

        return plan

    def _generate_interview_plan(self, interviews, applications) -> dict:
        """生成面试准备计划"""
        upcoming = []
        completed = []

        for interview in interviews:
            item = {
                "id": interview.id,
                "job_id": interview.job_id,
                "status": interview.status.value,
                "score": interview.overall_score,
            }
            if interview.status.value in ["scheduled", "in_progress"]:
                upcoming.append(item)
            else:
                completed.append(item)

        tips = [
            "准备 2-3 个 STAR 法则项目故事",
            "复习目标岗位相关的技术栈",
            "研究公司文化和业务方向",
            "准备反问面试官的问题",
        ]

        return {
            "upcoming": upcoming,
            "completed": completed,
            "tips": tips,
        }

    def _goal_summary(self, goal) -> dict:
        if not goal:
            return None
        return {
            "position": goal.target_position,
            "company": goal.target_company,
            "city": goal.target_city,
            "salary_min": goal.salary_expectation_min,
            "salary_max": goal.salary_expectation_max,
        }

    def _company_summary(self, company) -> dict:
        return {
            "name": company.company_name,
            "position": company.target_position,
            "status": company.status,
            "priority": company.priority,
        }

    def _count_by_status(self, applications) -> dict:
        counts = {}
        for app in applications:
            status = app.status.value if hasattr(app.status, "value") else str(app.status)
            counts[status] = counts.get(status, 0) + 1
        return counts
