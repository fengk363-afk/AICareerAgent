"""
GapAnalysisEngine — 能力差距分析引擎
用于分析用户与目标岗位之间的差距，生成学习路线和简历优化建议
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import ResumeProfile, Job, LearningPlan, AIAnalysisRecord
from app.db.database import get_db
from app.schemas.models import GapAnalysisResponse


class GapAnalysisEngine:
    """能力差距分析引擎"""

    async def analyze_gap(
        self, profile_id: str, job_id: str
    ) -> Optional[GapAnalysisResponse]:
        """分析简历与目标岗位的差距"""
        async for db in get_db():
            profile = await db.get(ResumeProfile, profile_id)
            job = await db.get(Job, job_id)
            if not profile or not job:
                return None

            # 计算技能差距
            profile_skills = {s["name"].lower() for s in (profile.skills or [])}
            job_skills = {s.lower() for s in (job.preferred_skills or [])}
            gaps = list(job_skills - profile_skills)
            overlaps = profile_skills & job_skills

            # 技能匹配度
            skill_match = len(overlaps) / max(len(job_skills), 1) * 100

            # 经验匹配度
            profile_text = (profile.parsed_text or "").lower()
            exp_keywords = ["实习", "项目", "开发", "算法", "前端", "后端", "产品", "运营"]
            exp_score = sum(1 for kw in exp_keywords if kw in profile_text) / len(exp_keywords) * 100
            experience_match = min(exp_score * 1.2, 100)

            # 教育匹配度
            education_match = 70.0
            if profile.education:
                edu_text = " ".join(str(e) for e in profile.education)
                if "硕士" in edu_text or "博士" in edu_text:
                    education_match = 90.0
                elif "本科" in edu_text:
                    education_match = 70.0

            # 综合评分
            overall_score = skill_match * 0.5 + experience_match * 0.3 + education_match * 0.2

            # 优势分析
            strengths = []
            if skill_match >= 80:
                strengths.append(f"技能匹配度高，掌握 {len(overlaps)} 项岗位核心技能")
            if experience_match >= 70:
                strengths.append("实习/项目经验丰富")
            if education_match >= 80:
                strengths.append("学历背景优秀")
            if not strengths:
                strengths.append("具备基础技术能力，可针对性提升")

            # 不足分析
            weaknesses = []
            if skill_match < 50:
                weaknesses.append("技能匹配度较低，需补充核心技术栈")
            if experience_match < 50:
                weaknesses.append("项目/实习经历不足，建议补充实战经验")
            if gaps:
                weaknesses.append(f"缺少 {len(gaps)} 项岗位要求的技能")

            # 提升建议
            suggestions = []
            if gaps:
                suggestions.append(f"建议学习/强化以下技能: {', '.join(gaps[:3])}")
            if job.requirements:
                for req in job.requirements:
                    if "实习" in str(req):
                        suggestions.append("建议补充实习经历描述，突出项目成果和量化指标")
                    if "算法" in str(req) or "数据结构" in str(req):
                        suggestions.append("建议加强算法和数据结构练习")
            if not suggestions:
                suggestions.append("简历与岗位匹配度良好，可针对性优化项目描述")

            # 生成学习路线
            learning_plan = await self._generate_learning_plan(
                profile_id, job_id, gaps, list(profile_skills),
                f"拥有{len(profile.experience or [])}段实习经历" if profile.experience else ""
            )

            # 保存分析记录
            analysis_id = str(uuid.uuid4())
            record = AIAnalysisRecord(
                id=analysis_id,
                profile_id=profile_id,
                job_id=job_id,
                overall_score=round(overall_score, 1),
                skill_match=round(skill_match, 1),
                experience_match=round(experience_match, 1),
                education_match=round(education_match, 1),
                strengths=strengths,
                weaknesses=weaknesses,
                gaps=gaps[:5],
                suggestions=suggestions,
                match_reason=f"基于技能匹配({skill_match:.0f}%)、经验匹配({experience_match:.0f}%)、教育匹配({education_match:.0f}%)综合评估",
                is_llm=False,
                created_at=datetime.utcnow(),
            )
            db.add(record)
            await db.commit()

            return GapAnalysisResponse(
                profile_id=profile_id,
                job_id=job_id,
                job_title=job.title,
                company=job.company,
                overall_score=round(overall_score, 1),
                skill_match=round(skill_match, 1),
                experience_match=round(experience_match, 1),
                education_match=round(education_match, 1),
                gaps=gaps[:5],
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=suggestions,
                match_reason=record.match_reason,
                learning_plan=learning_plan,
            )

    async def _generate_learning_plan(
        self, profile_id: str, job_id: str, missing_skills: List[str],
        existing_skills: List[str], experience_summary: str
    ) -> Optional[dict]:
        """生成学习路线"""
        async for db in get_db():
            # 检查是否已有学习路线
            from sqlalchemy import select
            result = await db.execute(
                select(LearningPlan).where(
                    LearningPlan.profile_id == profile_id,
                    LearningPlan.job_id == job_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing.plan_data

            # 生成新学习路线
            phases = []
            priority_skills = missing_skills[:3] if missing_skills else []

            if missing_skills:
                phases.append({
                    "phase": "基础补强",
                    "duration": "2-4周",
                    "topics": missing_skills[:3],
                    "resources": ["官方文档", "在线教程", "技术博客"],
                    "tasks": [f"学习 {skill} 基础概念" for skill in missing_skills[:3]] + [f"完成 {skill} 小项目" for skill in missing_skills[:2]],
                })

            phases.append({
                "phase": "项目实践",
                "duration": "4-8周",
                "topics": ["综合项目", "技术深度"],
                "resources": ["GitHub开源项目", "技术社区", "在线课程"],
                "tasks": [
                    "参与开源项目贡献",
                    "独立完成一个完整项目",
                    "撰写技术博客总结",
                ],
            })

            phases.append({
                "phase": "面试准备",
                "duration": "2-4周",
                "topics": ["算法刷题", "行为面试", "系统设计"],
                "resources": ["LeetCode", "《剑指Offer》", "系统设计入门"],
                "tasks": [
                    "每天刷2道LeetCode",
                    "准备3个STAR法则项目故事",
                    "学习系统设计基础",
                ],
            })

            plan = {
                "phases": phases,
                "priority_skills": priority_skills,
                "estimated_time": "2-4个月",
                "tips": [
                    "保持每天学习2-3小时",
                    "理论与实践结合",
                    "定期复盘总结",
                    "加入技术社区交流",
                ],
            }

            # 保存学习路线
            plan_id = str(uuid.uuid4())
            learning_plan = LearningPlan(
                id=plan_id,
                profile_id=profile_id,
                job_id=job_id,
                plan_data=plan,
                status="active",
                created_at=datetime.utcnow(),
            )
            db.add(learning_plan)
            await db.commit()

            return plan

    async def get_gap_analysis(self, profile_id: str, job_id: str) -> Optional[dict]:
        """获取差距分析结果"""
        async for db in get_db():
            result = await db.execute(
                select(AIAnalysisRecord).where(
                    AIAnalysisRecord.profile_id == profile_id,
                    AIAnalysisRecord.job_id == job_id,
                ).order_by(AIAnalysisRecord.created_at.desc()).limit(1)
            )
            record = result.scalar_one_or_none()
            if record:
                return record.model_dump()
        return None
