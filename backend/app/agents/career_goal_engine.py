"""
CareerGoalEngine — 职业目标管理引擎
管理用户的职业目标、目标公司、求职偏好和进度追踪
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import (
    CareerGoal, TargetCompany, UserJobPreference, CareerProgress,
    ResumeProfile, Job,
)
from app.db.database import get_db
from sqlalchemy import select


class CareerGoalEngine:
    """职业目标管理引擎"""

    async def create_goal(
        self,
        user_id: str,
        target_position: Optional[str] = None,
        target_industry: Optional[str] = None,
        target_company: Optional[str] = None,
        target_country: Optional[str] = None,
        target_city: Optional[str] = None,
        salary_expectation_min: Optional[float] = None,
        salary_expectation_max: Optional[float] = None,
        company_type: Optional[str] = None,
        remote_preference: Optional[str] = None,
        priority_level: int = 0,
        notes: Optional[str] = None,
    ) -> dict:
        """创建职业目标"""
        async for db in get_db():
            goal_id = str(uuid.uuid4())
            goal = CareerGoal(
                id=goal_id,
                user_id=int(user_id),
                target_position=target_position,
                target_industry=target_industry,
                target_company=target_company,
                target_country=target_country,
                target_city=target_city,
                salary_expectation_min=salary_expectation_min,
                salary_expectation_max=salary_expectation_max,
                company_type=company_type,
                remote_preference=remote_preference,
                priority_level=priority_level,
                notes=notes,
                status="active",
                created_at=datetime.utcnow(),
            )
            db.add(goal)
            await db.commit()
            await db.refresh(goal)
            logger.info(f"用户 {user_id} 创建职业目标: {goal_id}")
            return self._goal_to_dict(goal)

    async def get_goals(self, user_id: str) -> List[dict]:
        """获取用户职业目标列表"""
        async for db in get_db():
            result = await db.execute(
                select(CareerGoal)
                .where(CareerGoal.user_id == int(user_id))
                .order_by(CareerGoal.priority_level.desc(), CareerGoal.created_at.desc())
            )
            goals = result.scalars().all()
            return [self._goal_to_dict(g) for g in goals]

    async def get_goal(self, goal_id: str) -> Optional[dict]:
        """获取单个职业目标"""
        async for db in get_db():
            goal = await db.get(CareerGoal, goal_id)
            if goal:
                return self._goal_to_dict(goal)
        return None

    async def update_goal(
        self, goal_id: str, **kwargs
    ) -> Optional[dict]:
        """更新职业目标"""
        async for db in get_db():
            goal = await db.get(CareerGoal, goal_id)
            if not goal:
                return None
            for key, value in kwargs.items():
                if hasattr(goal, key) and value is not None:
                    setattr(goal, key, value)
            goal.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(goal)
            return self._goal_to_dict(goal)

    async def delete_goal(self, goal_id: str) -> bool:
        """删除职业目标"""
        async for db in get_db():
            goal = await db.get(CareerGoal, goal_id)
            if goal:
                await db.delete(goal)
                await db.commit()
                return True
            return False

    async def create_target_company(
        self, user_id: str, company_name: str,
        company_type: Optional[str] = None,
        industry: Optional[str] = None,
        target_position: Optional[str] = None,
        priority: int = 0,
        notes: Optional[str] = None,
    ) -> dict:
        """添加目标公司"""
        async for db in get_db():
            # 检查是否已存在
            result = await db.execute(
                select(TargetCompany).where(
                    TargetCompany.user_id == int(user_id),
                    TargetCompany.company_name == company_name,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.priority = priority
                existing.notes = notes
                existing.company_type = company_type or existing.company_type
                existing.industry = industry or existing.industry
                existing.target_position = target_position or existing.target_position
                await db.commit()
                return self._company_to_dict(existing)

            company_id = str(uuid.uuid4())
            company = TargetCompany(
                id=company_id,
                user_id=int(user_id),
                company_name=company_name,
                company_type=company_type,
                industry=industry,
                target_position=target_position,
                priority=priority,
                notes=notes,
                status="active",
                created_at=datetime.utcnow(),
            )
            db.add(company)
            await db.commit()
            await db.refresh(company)
            return self._company_to_dict(company)

    async def get_target_companies(self, user_id: str) -> List[dict]:
        """获取目标公司列表"""
        async for db in get_db():
            result = await db.execute(
                select(TargetCompany)
                .where(TargetCompany.user_id == int(user_id))
                .order_by(TargetCompany.priority.desc())
            )
            return [self._company_to_dict(c) for c in result.scalars().all()]

    async def delete_target_company(self, company_id: str) -> bool:
        """删除目标公司"""
        async for db in get_db():
            company = await db.get(TargetCompany, company_id)
            if company:
                await db.delete(company)
                await db.commit()
                return True
            return False

    async def get_or_create_preference(self, user_id: str) -> dict:
        """获取或创建用户求职偏好"""
        async for db in get_db():
            result = await db.execute(
                select(UserJobPreference).where(UserJobPreference.user_id == int(user_id))
            )
            pref = result.scalar_one_or_none()
            if pref:
                return self._preference_to_dict(pref)

            pref = UserJobPreference(
                id=str(uuid.uuid4()),
                user_id=int(user_id),
                created_at=datetime.utcnow(),
            )
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
            return self._preference_to_dict(pref)

    async def update_preference(self, user_id: str, **kwargs) -> dict:
        """更新用户求职偏好"""
        async for db in get_db():
            result = await db.execute(
                select(UserJobPreference).where(UserJobPreference.user_id == int(user_id))
            )
            pref = result.scalar_one_or_none()
            if not pref:
                pref = UserJobPreference(
                    id=str(uuid.uuid4()),
                    user_id=int(user_id),
                )
                db.add(pref)

            for key, value in kwargs.items():
                if hasattr(pref, key) and value is not None:
                    setattr(pref, key, value)
            pref.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(pref)
            return self._preference_to_dict(pref)

    async def get_or_create_progress(self, user_id: str) -> dict:
        """获取或创建职业进度"""
        async for db in get_db():
            result = await db.execute(
                select(CareerProgress).where(CareerProgress.user_id == int(user_id))
            )
            progress = result.scalar_one_or_none()
            if progress:
                return self._progress_to_dict(progress)

            progress = CareerProgress(
                id=str(uuid.uuid4()),
                user_id=int(user_id),
                skill_progress={},
                milestones=[],
                created_at=datetime.utcnow(),
            )
            db.add(progress)
            await db.commit()
            await db.refresh(progress)
            return self._progress_to_dict(progress)

    async def update_progress(
        self, user_id: str,
        skill_progress: Optional[dict] = None,
        application_count: Optional[int] = None,
        interview_count: Optional[int] = None,
        offer_count: Optional[int] = None,
        completed_skills: Optional[List[str]] = None,
        milestones: Optional[List[dict]] = None,
    ) -> dict:
        """更新职业进度"""
        async for db in get_db():
            result = await db.execute(
                select(CareerProgress).where(CareerProgress.user_id == int(user_id))
            )
            progress = result.scalar_one_or_none()
            if not progress:
                progress = CareerProgress(
                    id=str(uuid.uuid4()),
                    user_id=int(user_id),
                )
                db.add(progress)

            if skill_progress is not None:
                progress.skill_progress = skill_progress
            if application_count is not None:
                progress.application_count = application_count
            if interview_count is not None:
                progress.interview_count = interview_count
            if offer_count is not None:
                progress.offer_count = offer_count
            if completed_skills is not None:
                progress.completed_skills = completed_skills
            if milestones is not None:
                progress.milestones = milestones
            progress.last_updated = datetime.utcnow()
            progress.updated_at = datetime.utcnow()

            # 计算完成度
            progress.progress_percentage = self._calc_progress(progress)

            await db.commit()
            await db.refresh(progress)
            return self._progress_to_dict(progress)

    def _calc_progress(self, progress: CareerProgress) -> float:
        """计算职业目标完成度"""
        if not progress.milestones:
            return 0.0
        completed = sum(1 for m in progress.milestones if m.get("completed"))
        return round(completed / len(progress.milestones) * 100, 1)

    def _goal_to_dict(self, goal: CareerGoal) -> dict:
        return {
            "id": goal.id,
            "user_id": str(goal.user_id),
            "target_position": goal.target_position,
            "target_industry": goal.target_industry,
            "target_company": goal.target_company,
            "target_country": goal.target_country,
            "target_city": goal.target_city,
            "salary_expectation_min": goal.salary_expectation_min,
            "salary_expectation_max": goal.salary_expectation_max,
            "company_type": goal.company_type,
            "remote_preference": goal.remote_preference,
            "priority_level": goal.priority_level,
            "notes": goal.notes,
            "status": goal.status,
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
            "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
        }

    def _company_to_dict(self, company: TargetCompany) -> dict:
        return {
            "id": company.id,
            "user_id": str(company.user_id),
            "company_name": company.company_name,
            "company_type": company.company_type,
            "industry": company.industry,
            "target_position": company.target_position,
            "priority": company.priority,
            "notes": company.notes,
            "status": company.status,
            "created_at": company.created_at.isoformat() if company.created_at else None,
        }

    def _preference_to_dict(self, pref: UserJobPreference) -> dict:
        return {
            "id": pref.id,
            "user_id": str(pref.user_id),
            "preferred_locations": pref.preferred_locations,
            "preferred_companies": pref.preferred_companies,
            "preferred_company_types": pref.preferred_company_types,
            "salary_min": pref.salary_min,
            "salary_max": pref.salary_max,
            "is_remote_wanted": pref.is_remote_wanted,
            "is_foreign_wanted": pref.is_foreign_wanted,
            "visa_support_wanted": pref.visa_support_wanted,
            "campus_recruitment_wanted": pref.campus_recruitment_wanted,
            "created_at": pref.created_at.isoformat() if pref.created_at else None,
            "updated_at": pref.updated_at.isoformat() if pref.updated_at else None,
        }

    def _progress_to_dict(self, progress: CareerProgress) -> dict:
        return {
            "id": progress.id,
            "user_id": str(progress.user_id),
            "career_goal_id": progress.career_goal_id,
            "skill_progress": progress.skill_progress or {},
            "application_count": progress.application_count,
            "interview_count": progress.interview_count,
            "offer_count": progress.offer_count,
            "completed_skills": progress.completed_skills or [],
            "milestones": progress.milestones or [],
            "progress_percentage": progress.progress_percentage,
            "last_updated": progress.last_updated.isoformat() if progress.last_updated else None,
            "created_at": progress.created_at.isoformat() if progress.created_at else None,
        }
