"""
ResumeOptimizerAgent — 根据目标岗位自动优化简历内容
"""
from typing import Optional, List
from loguru import logger

from app.db.models import ResumeProfile, Job
from app.db.database import get_db
from app.schemas.models import ResumeOptimizationResponse


class ResumeOptimizerAgent:
    """简历优化 Agent"""

    async def optimize(
        self, resume_profile_id: str, job_id: str
    ) -> Optional[ResumeOptimizationResponse]:
        """生成简历优化建议"""
        async for db in get_db():
            profile = await db.get(ResumeProfile, resume_profile_id)
            job = await db.get(Job, job_id)
            if not profile or not job:
                return None

            # 分析差距
            profile_skills = {s["name"].lower() for s in (profile.skills or [])}
            job_skills = {s.lower() for s in (job.preferred_skills or [])}
            missing_skills = job_skills - profile_skills

            # 生成优化建议
            optimized_summary = await self._optimize_summary(profile, job)
            suggested_edits = await self._generate_edits(profile, job, missing_skills)
            improvement_score = await self._calc_improvement_score(profile, job, missing_skills)

            return ResumeOptimizationResponse(
                resume_profile_id=resume_profile_id,
                job_id=job_id,
                optimized_summary=optimized_summary,
                optimized_skills=list(job_skills),
                suggested_edits=suggested_edits,
                improvement_score=improvement_score,
            )

    async def _optimize_summary(self, profile: ResumeProfile, job: Job) -> str:
        """生成优化后的个人摘要（不含时间信息）"""
        skills = [s["name"] for s in (profile.skills or [])]
        exps = profile.experience or []
        edus = profile.education or []
        projects = profile.project_experience or []

        # 根据岗位调整摘要重点
        job_title_lower = job.title.lower()
        focus_area = ""
        if "前端" in job_title_lower:
            focus_area = "前端开发"
        elif "后端" in job_title_lower:
            focus_area = "后端开发"
        elif "算法" in job_title_lower:
            focus_area = "算法工程"
        elif "全栈" in job_title_lower:
            focus_area = "全栈开发"
        elif "移动端" in job_title_lower:
            focus_area = "移动端开发"

        parts = []
        # 教育背景（不含年份）
        if edus:
            edu = edus[0]
            school = edu.get("school", "")
            degree = edu.get("degree", "")
            major = edu.get("major", "")
            edu_info = school
            if degree:
                edu_info += degree
            if major:
                edu_info += major
            parts.append(f"{edu_info}毕业生")
        if focus_area:
            parts.append(f"专注于{focus_area}方向")
        # 实习经历
        if exps:
            exp_count = len(exps)
            parts.append(f"拥有{exp_count}段技术实习经历")
        # 项目经历
        if projects:
            pe_count = len(projects)
            parts.append(f"主导{pe_count}个项目")
        # 核心技能
        if skills:
            top_skills = skills[:5]
            parts.append(f"熟练掌握{', '.join(top_skills)}")

        return "。".join(parts) + "。" if parts else "待完善"

    async def _generate_edits(
        self, profile: ResumeProfile, job: Job, missing_skills: set[str]
    ) -> List[dict]:
        """生成具体修改建议"""
        edits = []

        # 技能建议
        if missing_skills:
            edits.append({
                "section": "skills",
                "original": "当前技能列表",
                "suggestion": f"建议补充: {', '.join(list(missing_skills)[:5])}",
                "reason": f"这些技能是岗位 JD 中明确要求的",
            })

        # 项目经历建议
        if profile.experience:
            for exp in profile.experience[:2]:
                edits.append({
                    "section": "experience",
                    "original": f"{exp.get('company', '')} - {exp.get('position', '')}",
                    "suggestion": "使用 STAR 法则重写，突出量化成果（如性能提升X%、处理X万级请求）",
                    "reason": "HR 平均只看简历6秒，量化成果更能吸引注意",
                })

        # 摘要建议
        edits.append({
            "section": "summary",
            "original": profile.summary or "无摘要",
            "suggestion": "根据目标岗位定制个人摘要，突出与岗位最相关的技能和经历",
            "reason": "定制化摘要可提升 ATS 系统匹配率",
        })

        return edits

    async def _calc_improvement_score(
        self, profile: ResumeProfile, job: Job, missing_skills: set[str]
    ) -> float:
        """计算优化后预期提升分数"""
        job_skills = set(s.lower() for s in (job.preferred_skills or []))
        current_match = len(job_skills - missing_skills) / max(len(job_skills), 1)
        # 优化后可达匹配度
        potential_match = min(current_match + 0.25, 1.0)
        return round(potential_match * 100, 1)
