"""
AIAnalysisEngine — AI 语义匹配分析引擎
"""
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.db.models import Job, ResumeProfile, AIAnalysisRecord
from app.db.database import get_db
from app.schemas.models import MatchScoreResponse
from app.services.llm_service import llm_service
from app.core.ai_config import ai_config


class AIAnalysisEngine:
    """AI 语义匹配引擎"""

    MATCH_PROMPT = """你是一个专业的求职顾问，负责分析简历与岗位的匹配度。

## 候选人简历
{resume_text}

## 岗位描述
{job_text}

## 岗位要求
{requirements}

## 候选人技能
{skills}

## 候选人经历
{experience}

请分析匹配度并输出 JSON：
{{
  "overall_score": 综合匹配分数(0-100),
  "skill_match": 技能匹配度(0-100),
  "experience_match": 经验匹配度(0-100),
  "education_match": 教育匹配度(0-100),
  "industry_match": 行业匹配度(0-100),
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "gaps": ["缺失技能1", "缺失技能2"],
  "suggestions": ["建议1", "建议2"],
  "match_reason": "匹配理由分析"
}}"""

    RESUME_OPTIMIZE_PROMPT = """你是一个专业的简历优化顾问。请根据目标岗位优化简历。

## 当前简历
{resume_text}

## 目标岗位
{job_title}
{job_company}
{job_description}
{job_requirements}
{job_skills}

请输出优化后的简历摘要和修改建议（JSON格式）：
{{
  "optimized_summary": "优化后的个人摘要（不含任何时间信息，只包含教育背景、实习经历、项目经历、核心技能的概括）",
  "optimized_skills": ["补充技能1", "补充技能2"],
  "suggested_edits": [
    {{"section": "模块名", "original": "原文", "suggestion": "建议修改", "reason": "修改原因"}}
  ],
  "improvement_score": 优化后预期分数(0-100),
  "missing_skills": ["缺失技能1"]
}}"""

    INTERVIEW_QUESTION_PROMPT = """你是一个专业的面试官，请根据岗位信息生成面试问题。

## 岗位信息
公司: {company}
岗位: {title}
描述: {description}
要求: {requirements}
技能: {skills}

请生成5个面试问题（JSON格式）：
{{
  "questions": [
    {{"question": "问题内容", "category": "technical|behavioral|situational", "difficulty": "easy|medium|hard"}}
  ]
}}"""

    async def calculate_match(
        self, profile_id: str, job_id: str
    ) -> Optional[MatchScoreResponse]:
        """AI 语义匹配分析"""
        async for db in get_db():
            profile = await db.get(ResumeProfile, profile_id)
            job = await db.get(Job, job_id)
            if not profile or not job:
                return None

            # 构建分析文本
            resume_text = profile.parsed_text or ""
            job_text = f"{job.title} {job.description}"
            skills_text = ", ".join([s["name"] for s in (profile.skills or [])])
            exp_text = "\n".join([
                f"- {e.get('company', '')} {e.get('position', '')} ({e.get('start_date', '')}-{e.get('end_date', '至今')})"
                for e in (profile.experience or [])
            ])

            # 尝试 LLM 分析
            use_llm = ai_config.is_llm_enabled() and ai_config.get("match", "enable_llm_analysis", default=False)

            if use_llm:
                result = await self._llm_analyze(resume_text, job_text, job.requirements, skills_text, exp_text)
            else:
                result = await self._rule_analyze(profile, job)

            # 保存分析记录
            analysis_id = str(uuid.uuid4())
            record = AIAnalysisRecord(
                id=analysis_id,
                profile_id=profile_id,
                job_id=job_id,
                overall_score=result.get("overall_score", 0),
                skill_match=result.get("skill_match", 0),
                experience_match=result.get("experience_match", 0),
                education_match=result.get("education_match", 0),
                industry_match=result.get("industry_match", 0),
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                gaps=result.get("gaps", []),
                suggestions=result.get("suggestions", []),
                match_reason=result.get("match_reason", ""),
                is_llm=result.get("is_llm", False),
                created_at=datetime.utcnow(),
            )
            db.add(record)
            await db.commit()

            return MatchScoreResponse(
                job_id=job_id,
                job_title=job.title,
                company=job.company,
                overall_score=result.get("overall_score", 0),
                skill_match=result.get("skill_match", 0),
                experience_match=result.get("experience_match", 0),
                education_match=result.get("education_match", 0),
                gaps=result.get("gaps", [])[:5],
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                suggestions=result.get("suggestions", []),
            )

    async def _llm_analyze(
        self, resume_text: str, job_text: str, requirements, skills_text: str, exp_text: str
    ) -> dict:
        """LLM 语义分析"""
        prompt = self.MATCH_PROMPT.format(
            resume_text=resume_text[:2000],
            job_text=job_text[:1000],
            requirements=str(requirements)[:500],
            skills=skills_text[:500],
            experience=exp_text[:1000],
        )
        text = await llm_service.chat_completion([
            {"role": "system", "content": "你是专业的求职顾问，请分析简历与岗位的匹配度。"},
            {"role": "user", "content": prompt},
        ])
        if text:
            try:
                result = json.loads(text)
                result["is_llm"] = True
                return result
            except json.JSONDecodeError:
                pass
        return await self._rule_analyze_mock()

    async def _rule_analyze(self, profile: ResumeProfile, job: Job) -> dict:
        """规则分析（备用）"""
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        profile_text = (profile.parsed_text or "").lower()
        job_text = f"{job.title} {job.description}".lower()

        # 技能匹配
        skill_overlap = profile_skills & job_skills
        skill_match = len(skill_overlap) / max(len(job_skills), 1) * 100

        # 经验匹配
        exp_keywords = ["实习", "项目", "开发", "算法", "前端", "后端", "产品", "运营"]
        exp_score = sum(1 for kw in exp_keywords if kw in profile_text) / len(exp_keywords) * 100
        experience_match = min(exp_score * 1.2, 100)

        # 教育匹配
        education_match = 70.0
        if profile.education:
            edu_text = " ".join(str(e) for e in profile.education)
            if "硕士" in edu_text or "博士" in edu_text:
                education_match = 90.0
            elif "本科" in edu_text:
                education_match = 70.0

        # 行业匹配（简单关键词）
        industry_match = 60.0
        industry_keywords = ["互联网", "AI", "金融", "电商", "游戏", "社交"]
        for kw in industry_keywords:
            if kw in job_text and kw in profile_text:
                industry_match = 85.0
                break

        # 综合评分
        cfg = ai_config.get("match")
        overall = (
            skill_match * cfg.get("weight_skill", 0.4) +
            experience_match * cfg.get("weight_experience", 0.3) +
            education_match * cfg.get("weight_education", 0.15) +
            industry_match * cfg.get("weight_industry", 0.15)
        )

        gaps = [s for s in job.preferred_skills if s.lower() not in profile_skills]
        job_requirements = job.requirements or []
        strengths = []
        weaknesses = []
        suggestions = []

        if skill_match >= 80:
            strengths.append(f"技能匹配度高，掌握 {len(skill_overlap)} 项岗位核心技能")
        if experience_match >= 70:
            strengths.append("实习/项目经验丰富")
        if education_match >= 80:
            strengths.append("学历背景优秀")
        if not strengths:
            strengths.append("具备基础技术能力，可针对性提升")

        if skill_match < 50:
            weaknesses.append("技能匹配度较低，需补充核心技术栈")
        if experience_match < 50:
            weaknesses.append("项目/实习经历不足，建议补充实战经验")
        if gaps:
            weaknesses.append(f"缺少 {len(gaps)} 项岗位要求的技能")

        if gaps:
            suggestions.append(f"建议学习/强化以下技能: {', '.join(gaps[:3])}")
        if job_requirements:
            for req in job_requirements:
                if "实习" in str(req):
                    suggestions.append("建议补充实习经历描述，突出项目成果和量化指标")
                if "算法" in str(req) or "数据结构" in str(req):
                    suggestions.append("建议加强算法和数据结构练习")
        if not suggestions:
            suggestions.append("简历与岗位匹配度良好，可针对性优化项目描述")

        return {
            "overall_score": round(overall, 1),
            "skill_match": round(skill_match, 1),
            "experience_match": round(experience_match, 1),
            "education_match": round(education_match, 1),
            "industry_match": round(industry_match, 1),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "gaps": gaps[:5],
            "suggestions": suggestions,
            "match_reason": f"基于技能匹配({skill_match:.0f}%)、经验匹配({experience_match:.0f}%)、教育匹配({education_match:.0f}%)综合评估",
            "is_llm": False,
        }

    async def _rule_analyze_mock(self) -> dict:
        """Mock 分析结果"""
        return {
            "overall_score": 75.0,
            "skill_match": 70.0,
            "experience_match": 80.0,
            "education_match": 75.0,
            "industry_match": 60.0,
            "strengths": ["技术栈匹配良好", "有相关实习经验"],
            "weaknesses": ["缺少分布式系统经验"],
            "gaps": ["Kafka", "Kubernetes"],
            "suggestions": ["建议学习 Kafka 消息队列", "补充分布式系统项目经验"],
            "match_reason": "基于规则分析，匹配度良好",
            "is_llm": False,
        }

    async def get_analysis_history(self, profile_id: str, job_id: str) -> List[dict]:
        """获取匹配分析历史"""
        async for db in get_db():
            from sqlalchemy import select
            result = await db.execute(
                select(AIAnalysisRecord)
                .where(AIAnalysisRecord.profile_id == profile_id)
                .order_by(AIAnalysisRecord.created_at.desc())
                .limit(10)
            )
            return [r.model_dump() for r in result.scalars().all()]
        return []
