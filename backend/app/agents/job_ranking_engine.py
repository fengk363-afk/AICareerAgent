"""
JobRankingEngine — 岗位排序引擎
对岗位进行综合排序，生成推荐理由
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import ResumeProfile, Job, CareerPreference, TargetJob, JobRanking
from app.db.database import get_db
from app.schemas.models import JobRankingResponse
from sqlalchemy import select


class JobRankingEngine:
    """岗位排序引擎"""

    # 评分权重配置
    WEIGHTS = {
        "match_score": 0.30,       # 简历匹配度
        "potential_score": 0.15,   # 发展潜力
        "salary_score": 0.15,      # 薪资水平
        "company_type_score": 0.10, # 公司类型
        "skill_growth_score": 0.15, # 技能提升价值
        "competition_score": 0.15,  # 竞争难度（分数越高越容易投递）
    }

    async def rank_jobs(
        self, profile_id: str, user_id: str = "1", limit: int = 20
    ) -> List[JobRankingResponse]:
        """对岗位进行综合排序"""
        async for db in get_db():
            # 获取简历画像
            profile = await db.get(ResumeProfile, profile_id)
            if not profile:
                return []

            # 获取求职偏好
            pref_result = await db.execute(
                select(CareerPreference).where(CareerPreference.user_id == int(user_id)).limit(1)
            )
            preference = pref_result.scalar_one_or_none()

            # 获取目标岗位
            target_result = await db.execute(
                select(TargetJob).where(TargetJob.user_id == int(user_id))
                .order_by(TargetJob.priority.desc())
            )
            target_jobs = target_result.scalars().all()
            target_job_ids = {t.job_id for t in target_jobs}

            # 获取所有岗位
            jobs_result = await db.execute(select(Job).order_by(Job.created_at.desc()))
            all_jobs = jobs_result.scalars().all()

            # 获取已有排名记录
            ranking_result = await db.execute(
                select(JobRanking).where(JobRanking.profile_id == profile_id)
            )
            existing_rankings = {r.job_id: r for r in ranking_result.scalars().all()}

            rankings = []
            for idx, job in enumerate(all_jobs):
                existing = existing_rankings.get(job.id)
                if existing:
                    rankings.append(JobRankingResponse.model_validate(existing))
                    continue

                # 计算排名分数
                score_data = await self._calculate_ranking(profile, job, preference, target_job_ids)

                # 保存排名记录
                ranking_id = str(uuid.uuid4())
                ranking = JobRanking(
                    id=ranking_id,
                    profile_id=profile_id,
                    job_id=job.id,
                    rank=0,  # 稍后设置
                    **score_data,
                    created_at=datetime.utcnow(),
                )
                db.add(ranking)

                rankings.append(JobRankingResponse(
                    id=ranking_id,
                    profile_id=profile_id,
                    job_id=job.id,
                    rank=0,
                    **score_data,
                    job={
                        "id": job.id,
                        "company": job.company,
                        "title": job.title,
                        "location": job.location,
                        "salary_range": job.salary_range,
                        "is_remote": job.is_remote,
                        "is_foreign": job.is_foreign,
                        "job_url": job.job_url,
                        "apply_url": job.apply_url,
                        "company_type": job.company_type,
                        "tags": job.tags,
                    },
                    created_at=datetime.utcnow(),
                ))

            # 设置排名
            rankings.sort(key=lambda x: x.overall_score, reverse=True)
            for i, r in enumerate(rankings):
                r.rank = i + 1

            await db.commit()
            return rankings[:limit]

        return []

    async def _calculate_ranking(
        self,
        profile: ResumeProfile,
        job: Job,
        preference: Optional[CareerPreference],
        target_job_ids: set,
    ) -> dict:
        """计算排名分数"""
        # 1. 简历匹配度
        match_score = await self._calc_match_score(profile, job)

        # 2. 发展潜力
        potential_score = await self._calc_potential_score(job, preference)

        # 3. 薪资水平
        salary_score = await self._calc_salary_score(job, preference)

        # 4. 公司类型
        company_type_score = await self._calc_company_type_score(job, preference)

        # 5. 技能提升价值
        skill_growth_score = await self._calc_skill_growth_score(profile, job)

        # 6. 竞争难度
        competition_score = await self._calc_competition_score(job)

        # 综合评分
        weights = self.WEIGHTS
        overall_score = (
            match_score * weights["match_score"] +
            potential_score * weights["potential_score"] +
            salary_score * weights["salary_score"] +
            company_type_score * weights["company_type_score"] +
            skill_growth_score * weights["skill_growth_score"] +
            competition_score * weights["competition_score"]
        )

        # 生成推荐理由
        recommendation_reason = await self._generate_reason(
            profile, job, match_score, potential_score, salary_score
        )

        # 分析优势和风险
        advantages, risks = await self._analyze_advantages_risks(profile, job)

        # 缺失技能
        missing_skills = await self._get_missing_skills(profile, job)

        # 竞争程度
        estimated_competition = await self._estimate_competition(job)

        return {
            "overall_score": round(overall_score, 1),
            "match_score": round(match_score, 1),
            "potential_score": round(potential_score, 1),
            "salary_score": round(salary_score, 1),
            "company_type_score": round(company_type_score, 1),
            "skill_growth_score": round(skill_growth_score, 1),
            "competition_score": round(competition_score, 1),
            "recommendation_reason": recommendation_reason,
            "advantages": advantages,
            "risks": risks,
            "missing_skills": missing_skills,
            "estimated_competition": estimated_competition,
        }

    async def _calc_match_score(self, profile: ResumeProfile, job: Job) -> float:
        """计算简历匹配度"""
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        if not job_skills:
            return 50.0
        overlap = profile_skills & job_skills
        return len(overlap) / len(job_skills) * 100

    async def _calc_potential_score(self, job: Job, preference: Optional[CareerPreference]) -> float:
        """计算发展潜力"""
        score = 50.0
        if preference and preference.target_industry:
            if preference.target_industry in job.description:
                score += 15
        if preference and preference.target_role:
            if preference.target_role in job.title:
                score += 15
        if preference and preference.preferred_company_types:
            if job.company_type in preference.preferred_company_types:
                score += 10
        return min(score, 100)

    async def _calc_salary_score(self, job: Job, preference: Optional[CareerPreference]) -> float:
        """计算薪资匹配度"""
        if not preference or not preference.salary_min:
            return 60.0
        salary_min = job.salary_range.get("min", 0) if job.salary_range else 0
        salary_max = job.salary_range.get("max", 0) if job.salary_range else 0
        pref_min = preference.salary_min
        pref_max = preference.salary_max or float('inf')

        if salary_max < pref_min:
            return 20.0
        elif salary_min >= pref_max:
            return 90.0
        elif salary_min >= pref_min and salary_max <= pref_max:
            return 80.0
        else:
            return 60.0

    async def _calc_company_type_score(self, job: Job, preference: Optional[CareerPreference]) -> float:
        """计算公司类型偏好匹配"""
        if not preference or not preference.preferred_company_types:
            return 50.0
        if job.company_type in preference.preferred_company_types:
            return 90.0
        return 30.0

    async def _calc_skill_growth_score(self, profile: ResumeProfile, job: Job) -> float:
        """计算技能提升价值"""
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        missing = job_skills - profile_skills
        if len(missing) == 0:
            return 40.0
        elif len(missing) <= 2:
            return 90.0
        elif len(missing) <= 4:
            return 70.0
        else:
            return 50.0

    async def _calc_competition_score(self, job: Job) -> float:
        """计算竞争难度"""
        score = 50.0
        if job.is_foreign:
            score += 15
        if job.is_remote:
            score += 10
        if job.company_type == "startup":
            score += 10
        if job.company_type == "state_enterprise":
            score += 5
        if job.company_type == "private" and not job.is_foreign:
            score -= 10
        return max(0, min(100, score))

    async def _generate_reason(
        self, profile: ResumeProfile, job: Job,
        match_score: float, potential_score: float, salary_score: float
    ) -> str:
        """生成推荐理由"""
        reasons = []
        if match_score >= 70:
            reasons.append(f"技能匹配度高({match_score:.0f}%)，与岗位要求高度契合")
        elif match_score >= 50:
            reasons.append(f"技能匹配度中等({match_score:.0f}%)，有一定基础可快速上手")
        else:
            reasons.append(f"技能匹配度较低({match_score:.0f}%)，需要补充技能后可考虑")

        if potential_score >= 70:
            reasons.append("发展潜力大，符合职业方向")
        if salary_score >= 70:
            reasons.append("薪资符合预期")

        return "；".join(reasons) if reasons else "综合评估后推荐"

    async def _analyze_advantages_risks(
        self, profile: ResumeProfile, job: Job
    ) -> tuple:
        """分析优势和风险"""
        advantages = []
        risks = []

        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        overlap = profile_skills & job_skills
        if len(overlap) >= 3:
            advantages.append(f"掌握 {len(overlap)} 项岗位核心技能")
        if job.is_foreign:
            advantages.append("外企背景，国际化环境")
        if job.is_remote:
            advantages.append("支持远程工作，灵活性高")
        if job.company_type == "startup":
            advantages.append("创业公司成长空间大")

        missing = job_skills - profile_skills
        if len(missing) > 3:
            risks.append(f"缺少 {len(missing)} 项关键技能")
        if job.company_type == "private" and not job.is_foreign:
            risks.append("国内大厂工作强度大")
        if job.company_type == "startup":
            risks.append("创业公司稳定性风险")

        return advantages, risks

    async def _get_missing_skills(self, profile: ResumeProfile, job: Job) -> List[str]:
        """获取缺失技能"""
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        return list(job_skills - profile_skills)

    async def _estimate_competition(self, job: Job) -> str:
        """估算竞争程度"""
        if job.is_foreign:
            return "medium"
        elif job.is_remote:
            return "low"
        elif job.company_type == "startup":
            return "low"
        elif job.company_type == "state_enterprise":
            return "medium"
        else:
            return "high"

    async def get_rankings(self, profile_id: str) -> List[dict]:
        """获取排名列表"""
        async for db in get_db():
            result = await db.execute(
                select(JobRanking)
                .where(JobRanking.profile_id == profile_id)
                .order_by(JobRanking.rank.asc())
            )
            return [r.model_dump() for r in result.scalars().all()]
        return []
