"""
MatchEngine — AI 简历与 JD 语义匹配
"""
import uuid
from typing import Optional, List
from loguru import logger

from app.db.models import Job, ResumeProfile
from app.db.database import get_db
from app.schemas.models import MatchScoreResponse


class MatchEngine:
    """AI 匹配引擎"""

    async def calculate_match(
        self, profile_id: str, job_id: str
    ) -> Optional[MatchScoreResponse]:
        """计算简历与岗位的匹配度"""
        async for db in get_db():
            profile = await db.get(ResumeProfile, profile_id)
            job = await db.get(Job, job_id)
            if not profile or not job:
                return None

            # 提取技能
            profile_skills = {s["name"].lower() for s in (profile.skills or [])}
            job_skills = {s.lower() for s in (job.preferred_skills or [])}
            profile_text = (profile.parsed_text or "").lower()
            job_text = f"{job.title} {job.description}".lower()

            # ── 技能匹配 ──
            skill_overlap = profile_skills & job_skills
            skill_match = len(skill_overlap) / max(len(job_skills), 1) * 100

            # ── 经验匹配 ──
            exp_keywords = ["实习", "项目", "开发", "算法", "前端", "后端", "产品", "运营"]
            exp_score = sum(1 for kw in exp_keywords if kw in profile_text) / len(exp_keywords) * 100
            experience_match = min(exp_score * 1.2, 100)

            # ── 教育匹配 ──
            education_match = 70.0
            if profile.education:
                edu_text = " ".join(str(e) for e in profile.education)
                if "硕士" in edu_text or "博士" in edu_text:
                    education_match = 90.0
                elif "本科" in edu_text:
                    education_match = 70.0

            # ── 综合评分 ──
            overall = skill_match * 0.5 + experience_match * 0.3 + education_match * 0.2

            # ── 差距分析 ──
            gaps = [s for s in job.preferred_skills if s.lower() not in profile_skills]

            # ── 优势分析 ──
            strengths = []
            if skill_match >= 80:
                strengths.append(f"技能匹配度高，掌握 {len(skill_overlap)} 项岗位核心技能")
            if experience_match >= 70:
                strengths.append("实习/项目经验丰富")
            if education_match >= 80:
                strengths.append("学历背景优秀")
            if not strengths:
                strengths.append("具备基础技术能力，可针对性提升")

            # ── 不足分析 ──
            weaknesses = []
            if skill_match < 50:
                weaknesses.append("技能匹配度较低，需补充核心技术栈")
            if experience_match < 50:
                weaknesses.append("项目/实习经历不足，建议补充实战经验")
            if gaps:
                weaknesses.append(f"缺少 {len(gaps)} 项岗位要求的技能")

            # ── 提升建议 ──
            suggestions = self._generate_suggestions(skill_match, gaps, job.requirements, profile)

            return MatchScoreResponse(
                job_id=job_id,
                job_title=job.title,
                company=job.company,
                overall_score=round(overall, 1),
                skill_match=round(skill_match, 1),
                experience_match=round(experience_match, 1),
                education_match=round(education_match, 1),
                gaps=gaps[:5],
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=suggestions,
            )

    def _generate_suggestions(
        self, skill_match: float, gaps: List[str], requirements: List[str], profile: ResumeProfile
    ) -> List[str]:
        suggestions = []
        if skill_match < 60:
            suggestions.append("技能匹配度较低，建议补充岗位要求的关键技术栈")
        if gaps:
            suggestions.append(f"建议学习/强化以下技能: {', '.join(gaps[:3])}")
        if requirements:
            for req in requirements:
                if "实习" in req:
                    suggestions.append("建议补充实习经历描述，突出项目成果和量化指标")
                if "算法" in req or "数据结构" in req:
                    suggestions.append("建议加强算法和数据结构练习，刷 LeetCode 提升编程能力")
        if not suggestions:
            suggestions.append("简历与岗位匹配度良好，可针对性优化项目描述")
        return suggestions
