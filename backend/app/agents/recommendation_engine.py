"""
RecommendationEngine — AI 求职推荐核心引擎
根据用户简历、职业偏好、目标岗位、技能差距、薪资要求、城市要求生成个性化岗位推荐列表
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import (
    ResumeProfile, Job, CareerPreference, TargetJob,
    RecommendationRecord, CompanyProfile, CareerGoal,
)
from app.db.database import get_db
from app.schemas.models import RecommendationResponse
from sqlalchemy import select


class RecommendationEngine:
    """AI 求职推荐引擎"""

    # 公司研究数据池（Mock 数据，实际可接入外部 API）
    COMPANY_RESEARCH_DATA = {
        "字节跳动": {
            "company_type": "private",
            "industry": "互联网/人工智能",
            "company_size": "large",
            "business_direction": "短视频、社交、AI、云计算",
            "hiring_trend": "growing",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "技术氛围好，成长快，但工作强度大，996常见",
            "pros": ["技术栈先进", "成长空间大", "薪资竞争力强", "扁平化管理"],
            "cons": ["工作强度大", "加班文化", "竞争激烈", "稳定性一般"],
        },
        "阿里巴巴": {
            "company_type": "private",
            "industry": "互联网/电商",
            "company_size": "large",
            "business_direction": "电商、云计算、物流、文娱",
            "hiring_trend": "stable",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "大厂平台好，技术积累深，但层级较多，晋升竞争激烈",
            "pros": ["平台大资源多", "技术积累深厚", "品牌认可度高", "培训体系完善"],
            "cons": ["层级较多", "晋升竞争激烈", "工作强度大", "内卷严重"],
        },
        "腾讯": {
            "company_type": "private",
            "industry": "互联网/社交游戏",
            "company_size": "large",
            "business_direction": "社交、游戏、云计算、金融科技",
            "hiring_trend": "stable",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "产品文化强，工作生活平衡相对较好，但晋升周期长",
            "pros": ["产品文化强", "工作生活平衡较好", "福利好", "技术实力强"],
            "cons": ["晋升周期长", "部门壁垒", "创新压力大", "加班存在"],
        },
        "Microsoft": {
            "company_type": "foreign",
            "industry": "科技/云计算",
            "company_size": "large",
            "business_direction": "云计算、AI、办公软件、游戏",
            "hiring_trend": "growing",
            "interview_difficulty": "medium",
            "employee_reviews_summary": "WLB优秀，技术氛围好，国际化环境，但晋升较慢",
            "pros": ["工作生活平衡好", "技术氛围优秀", "国际化环境", "福利完善"],
            "cons": ["晋升较慢", "决策流程长", "国内团队边缘化", "薪资涨幅有限"],
        },
        "Google": {
            "company_type": "foreign",
            "industry": "科技/互联网",
            "company_size": "large",
            "business_direction": "搜索、云计算、AI、广告",
            "hiring_trend": "stable",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "技术天花板高，创新氛围好，但面试难度极大，HC 有限",
            "pros": ["技术天花板高", "创新氛围好", "薪资顶级", "技术分享文化"],
            "cons": ["面试难度极大", "HC 有限", "晋升慢", "国内业务边缘"],
        },
        "美团": {
            "company_type": "private",
            "industry": "互联网/本地生活",
            "company_size": "large",
            "business_direction": "外卖、到店、酒店旅游、买菜",
            "hiring_trend": "growing",
            "interview_difficulty": "medium",
            "employee_reviews_summary": "业务增长快，技术挑战多，但工作强度大，竞争激烈",
            "pros": ["业务增长快", "技术挑战多", "薪资有竞争力", "成长空间大"],
            "cons": ["工作强度大", "竞争激烈", "加班文化", "稳定性一般"],
        },
        "拼多多": {
            "company_type": "private",
            "industry": "互联网/电商",
            "company_size": "large",
            "business_direction": "电商、农业、Temu",
            "hiring_trend": "growing",
            "interview_difficulty": "medium",
            "employee_reviews_summary": "薪资顶级，但工作强度极大，管理风格独特",
            "pros": ["薪资顶级", "成长快", "扁平管理", "技术挑战大"],
            "cons": ["工作强度极大", "管理风格独特", "稳定性差", "压力巨大"],
        },
        "某AI创业公司": {
            "company_type": "startup",
            "industry": "人工智能",
            "company_size": "small",
            "business_direction": "大模型应用、AI 工具、企业级 AI 服务",
            "hiring_trend": "growing",
            "interview_difficulty": "easy",
            "employee_reviews_summary": "AI 赛道热门，成长空间大，但风险高，稳定性差",
            "pros": ["AI 赛道热门", "成长空间大", "技术前沿", "扁平管理"],
            "cons": ["风险高", "稳定性差", "薪资可能不如大厂", "工作强度大"],
        },
        "某国企": {
            "company_type": "state_enterprise",
            "industry": "信息技术",
            "company_size": "medium",
            "business_direction": "企业信息系统、数字化转型",
            "hiring_trend": "stable",
            "interview_difficulty": "easy",
            "employee_reviews_summary": "稳定，WLB 好，但技术成长慢，薪资涨幅有限",
            "pros": ["稳定", "WLB 好", "压力小", "福利完善"],
            "cons": ["技术成长慢", "薪资涨幅有限", "层级多", "创新少"],
        },
        "某远程公司": {
            "company_type": "startup",
            "industry": "SaaS/互联网",
            "company_size": "small",
            "business_direction": "SaaS 产品、远程协作工具",
            "hiring_trend": "growing",
            "interview_difficulty": "easy",
            "employee_reviews_summary": "远程工作灵活，国际化团队，但薪资可能不如国内大厂",
            "pros": ["远程灵活", "国际化团队", "WLB 好", "技术栈先进"],
            "cons": ["薪资可能较低", "沟通成本高", "职业发展受限", "稳定性一般"],
        },
    }

    async def generate_recommendations(
        self, profile_id: str, user_id: str = "1", limit: int = 10
    ) -> List[RecommendationResponse]:
        """生成个性化岗位推荐（用户目标驱动）"""
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

            # 获取职业目标（Phase 9: 用户目标驱动）
            goals_result = await db.execute(
                select(CareerGoal).where(CareerGoal.user_id == int(user_id))
                .where(CareerGoal.status == "active")
                .order_by(CareerGoal.priority_level.desc())
            )
            goals = goals_result.scalars().all()

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

            # 获取已有推荐记录
            rec_result = await db.execute(
                select(RecommendationRecord).where(
                    RecommendationRecord.profile_id == profile_id
                )
            )
            existing_recs = {r.job_id: r for r in rec_result.scalars().all()}

            recommendations = []
            for job in all_jobs:
                rec = existing_recs.get(job.id)
                if rec:
                    recommendations.append(RecommendationResponse.model_validate(rec))
                    continue

                # 计算推荐分数（Phase 9: 用户目标权重 40%）
                score_data = await self._calculate_recommendation(
                    profile, job, preference, goals, target_job_ids
                )

                # 保存推荐记录
                rec_id = str(uuid.uuid4())
                record = RecommendationRecord(
                    id=rec_id,
                    profile_id=profile_id,
                    job_id=job.id,
                    **score_data,
                    created_at=datetime.utcnow(),
                )
                db.add(record)

                recommendations.append(RecommendationResponse(
                    id=rec_id,
                    profile_id=profile_id,
                    job_id=job.id,
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

            await db.commit()

            # 按综合评分排序，返回前 limit 个
            recommendations.sort(key=lambda x: x.overall_score, reverse=True)
            return recommendations[:limit]

        return []

    async def _calculate_recommendation(
        self,
        profile: ResumeProfile,
        job: Job,
        preference: Optional[CareerPreference],
        goals: List,
        target_job_ids: set,
    ) -> dict:
        """计算推荐分数（Phase 9: 用户目标驱动，目标权重40%）"""
        # 1. 用户目标匹配度 (40%) — Phase 9 新增
        goal_score = await self._calc_goal_score(job, goals, preference)

        # 2. 简历匹配度 (30%)
        match_score = await self._calc_match_score(profile, job)

        # 3. 发展潜力 (20%)
        potential_score = await self._calc_potential_score(job, preference, goals)

        # 4. 薪资水平 (10%)
        salary_score = await self._calc_salary_score(job, preference)

        # 综合评分（Phase 9 新权重）
        overall_score = (
            goal_score * 0.40 +
            match_score * 0.30 +
            potential_score * 0.20 +
            salary_score * 0.10
        )

        # 生成推荐理由（包含目标差距分析）
        recommendation_reason = await self._generate_reason(
            profile, job, match_score, potential_score, salary_score, goals
        )

        # 分析优势和风险
        advantages, risks = await self._analyze_advantages_risks(profile, job, goals)

        # 缺失技能
        missing_skills = await self._get_missing_skills(profile, job)

        # 竞争程度
        estimated_competition = await self._estimate_competition(job)

        return {
            "overall_score": round(overall_score, 1),
            "match_score": round(match_score, 1),
            "potential_score": round(potential_score, 1),
            "salary_score": round(salary_score, 1),
            "company_type_score": round(goal_score, 1),  # 复用 goal_score 作为公司类型分
            "skill_growth_score": round(match_score, 1),  # 复用 match_score 作为技能提升分
            "competition_score": round(self._estimate_competition_score(estimated_competition), 1),
            "recommendation_reason": recommendation_reason,
            "advantages": advantages,
            "risks": risks,
            "missing_skills": missing_skills,
            "estimated_competition": estimated_competition,
            "should_recommend": overall_score >= 50,
        }

    async def _calc_match_score(self, profile: ResumeProfile, job: Job) -> float:
        """计算简历匹配度"""
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        if not job_skills:
            return 50.0
        overlap = profile_skills & job_skills
        return len(overlap) / len(job_skills) * 100

    async def _calc_potential_score(self, job: Job, preference, goals: List = None) -> float:
        """计算发展潜力"""
        score = 50.0
        # 行业匹配
        if preference and preference.target_industry:
            if preference.target_industry in job.description:
                score += 15
        # 岗位匹配
        if preference and preference.target_role:
            if preference.target_role in job.title:
                score += 15
        # 公司类型偏好
        if preference and preference.preferred_company_types:
            if job.company_type in preference.preferred_company_types:
                score += 10

        # 目标匹配潜力
        if goals:
            for goal in goals[:1]:
                if goal.target_industry and goal.target_industry in job.description:
                    score += 10
                if goal.target_position and goal.target_position in job.title:
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
        # 缺失技能适中最好（既有挑战又能学到东西）
        if len(missing) == 0:
            return 40.0  # 太简单，学不到新东西
        elif len(missing) <= 2:
            return 90.0  # 刚好可以挑战
        elif len(missing) <= 4:
            return 70.0
        else:
            return 50.0  # 差距太大，难以提升

    async def _calc_competition_score(self, job: Job) -> float:
        """计算竞争难度（分数越高表示竞争越小，越容易投递）"""
        score = 50.0
        # 外企竞争相对小
        if job.is_foreign:
            score += 15
        # 远程工作竞争小
        if job.is_remote:
            score += 10
        # 创业公司竞争小
        if job.company_type == "startup":
            score += 10
        # 国企竞争小
        if job.company_type == "state_enterprise":
            score += 5
        # 大厂竞争大
        if job.company_type == "private" and job.is_foreign is False:
            score -= 10
        return max(0, min(100, score))

    async def _generate_reason(
        self, profile: ResumeProfile, job: Job,
        match_score: float, potential_score: float, salary_score: float,
        goals: List = None
    ) -> str:
        """生成推荐理由（含目标差距分析）"""
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

        # 目标差距分析
        if goals:
            for goal in goals[:1]:  # 只显示最高优先级目标
                gaps = []
                if goal.target_position and goal.target_position not in job.title:
                    gaps.append(f"目标岗位: {goal.target_position}")
                if goal.target_company and goal.target_company not in job.company:
                    gaps.append(f"目标公司: {goal.target_company}")
                if goal.target_city and goal.target_city not in job.location:
                    gaps.append(f"目标城市: {goal.target_city}")
                if gaps:
                    reasons.append(f"与目标有差距: {'、'.join(gaps)}")

        return "；".join(reasons) if reasons else "综合评估后推荐"

    async def _analyze_advantages_risks(
        self, profile: ResumeProfile, job: Job, goals: List = None
    ) -> tuple:
        """分析优势和风险（含目标分析）"""
        advantages = []
        risks = []

        # 优势
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

        # 目标匹配优势
        if goals:
            for goal in goals[:1]:
                if goal.target_company and goal.target_company in job.company:
                    advantages.append(f"匹配目标公司: {goal.target_company}")
                if goal.target_city and goal.target_city in job.location:
                    advantages.append(f"匹配目标城市: {goal.target_city}")

        # 风险
        missing = job_skills - profile_skills
        if len(missing) > 3:
            risks.append(f"缺少 {len(missing)} 项关键技能")
        if job.company_type == "private" and not job.is_foreign:
            risks.append("国内大厂工作强度大")
        if job.company_type == "startup":
            risks.append("创业公司稳定性风险")

        # 目标差距风险
        if goals:
            for goal in goals[:1]:
                if goal.salary_expectation_max:
                    job_max = job.salary_range.get("max", 0) if job.salary_range else 0
                    if job_max < goal.salary_expectation_max * 0.7:
                        risks.append(f"薪资低于目标预期")

        return advantages, risks

    async def _calc_goal_score(self, job: Job, goals: List, preference) -> float:
        """计算用户目标匹配度（Phase 9: 权重40%）"""
        if not goals:
            return 50.0  # 无目标时给中等分数

        score = 50.0
        goal = goals[0]  # 使用最高优先级目标

        # 岗位匹配
        if goal.target_position:
            if goal.target_position in job.title or goal.target_position in job.description:
                score += 20
            else:
                score -= 10

        # 公司匹配
        if goal.target_company:
            if goal.target_company in job.company:
                score += 15
            else:
                score -= 5

        # 城市匹配
        if goal.target_city:
            if goal.target_city in job.location:
                score += 10
            else:
                score -= 5

        # 国家匹配
        if goal.target_country:
            if goal.target_country in job.company_country or goal.target_country in job.location:
                score += 10
            elif goal.is_foreign or job.is_foreign:
                score += 5

        # 公司类型匹配
        if goal.company_type:
            if goal.company_type == job.company_type:
                score += 10
            else:
                score -= 5

        # 远程偏好
        if goal.remote_preference:
            if goal.remote_preference == "remote" and job.is_remote:
                score += 10
            elif goal.remote_preference == "on_site" and not job.is_remote:
                score += 5

        # 薪资匹配
        if goal.salary_expectation_min and job.salary_range:
            job_min = job.salary_range.get("min", 0)
            if job_min >= goal.salary_expectation_min:
                score += 10
            elif job_min < goal.salary_expectation_min * 0.7:
                score -= 15

        return max(0, min(100, score))

    def _estimate_competition_score(self, competition: str) -> float:
        """将竞争程度转换为分数"""
        if competition == "low":
            return 80.0
        elif competition == "medium":
            return 50.0
        else:
            return 30.0

    async def get_recommendations(self, profile_id: str) -> List[dict]:
        """获取推荐列表"""
        async for db in get_db():
            result = await db.execute(
                select(RecommendationRecord)
                .where(RecommendationRecord.profile_id == profile_id)
                .order_by(RecommendationRecord.overall_score.desc())
            )
            return [r.model_dump() for r in result.scalars().all()]
        return []

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

    async def get_recommendations(self, profile_id: str) -> List[dict]:
        """获取推荐列表"""
        async for db in get_db():
            result = await db.execute(
                select(RecommendationRecord)
                .where(RecommendationRecord.profile_id == profile_id)
                .order_by(RecommendationRecord.overall_score.desc())
            )
            return [r.model_dump() for r in result.scalars().all()]
        return []
