"""
JobMatchingAgent — 岗位分析 + 简历与 JD 匹配评分
"""
import uuid
from typing import Optional, List
from sqlalchemy import select
from loguru import logger

from app.db.models import Job, Application, ResumeProfile
from app.db.database import get_db
from app.schemas.models import MatchScoreResponse, JobCreate, JobResponse


class JobMatchingAgent:
    """岗位匹配 Agent"""

    # Mock 岗位数据池
    MOCK_JOBS = [
        {
            "source": "mock",
            "company": "字节跳动",
            "title": "后端开发工程师（校招）",
            "location": "北京",
            "job_type": "full_time",
            "salary_range": {"min": 25, "max": 45, "unit": "K/月"},
            "description": "负责推荐系统后端服务开发，使用 Go/Python 构建高并发分布式系统",
            "requirements": ["计算机相关专业", "熟悉 Go 或 Python", "了解数据结构与算法", "有实习经验者优先"],
            "preferred_skills": ["Go", "Python", "Redis", "Kafka", "MySQL", "Docker"],
        },
        {
            "source": "mock",
            "company": "阿里巴巴",
            "title": "前端开发工程师（校招）",
            "location": "杭州",
            "job_type": "full_time",
            "salary_range": {"min": 25, "max": 40, "unit": "K/月"},
            "description": "负责淘宝/天猫前端核心业务开发，使用 React 技术栈",
            "requirements": ["计算机相关专业", "熟练掌握 React", "了解 TypeScript", "有项目经验者优先"],
            "preferred_skills": ["React", "TypeScript", "JavaScript", "CSS", "Webpack", "Node.js"],
        },
        {
            "source": "mock",
            "company": "腾讯",
            "title": "算法工程师（校招）",
            "location": "深圳",
            "job_type": "full_time",
            "salary_range": {"min": 30, "max": 55, "unit": "K/月"},
            "description": "负责搜索/推荐算法优化，提升用户体验和商业化效果",
            "requirements": ["硕士及以上学历", "扎实的数学基础", "熟悉机器学习算法", "有顶会论文优先"],
            "preferred_skills": ["Python", "TensorFlow", "PyTorch", "NLP", "推荐系统", "C++"],
        },
        {
            "source": "mock",
            "company": "美团",
            "title": "全栈开发工程师（校招）",
            "location": "北京",
            "job_type": "full_time",
            "salary_range": {"min": 25, "max": 45, "unit": "K/月"},
            "description": "负责本地生活服务平台全栈开发，覆盖 Web 和移动端",
            "requirements": ["计算机相关专业", "熟悉前后端开发", "了解数据库设计", "有实际项目经验"],
            "preferred_skills": ["Vue", "React", "Node.js", "Python", "PostgreSQL", "Docker"],
        },
        {
            "source": "mock",
            "company": "拼多多",
            "title": "移动端开发工程师（校招）",
            "location": "上海",
            "job_type": "full_time",
            "salary_range": {"min": 30, "max": 50, "unit": "K/月"},
            "description": "负责拼多多 App 核心功能开发，使用 Kotlin/Swift",
            "requirements": ["计算机相关专业", "熟悉 Android 或 iOS 开发", "了解移动端性能优化"],
            "preferred_skills": ["Kotlin", "Swift", "Java", "Objective-C", "React Native", "Flutter"],
        },
    ]

    async def create_job(self, job_data: JobCreate) -> JobResponse:
        job_id = str(uuid.uuid4())
        async for db in get_db():
            job = Job(
                id=job_id,
                source=job_data.source,
                company=job_data.company,
                title=job_data.title,
                location=job_data.location,
                job_type=job_data.job_type,
                salary_range=job_data.salary_range,
                description=job_data.description,
                requirements=job_data.requirements,
                preferred_skills=job_data.preferred_skills,
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            return JobResponse.model_validate(job)

    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        async for db in get_db():
            job = await db.get(Job, job_id)
            if job:
                return JobResponse.model_validate(job)
        return None

    async def list_jobs(self, limit: int = 20, offset: int = 0) -> List[JobResponse]:
        async for db in get_db():
            result = await db.execute(
                select(Job).offset(offset).limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]
        return []

    async def seed_mock_jobs(self):
        """初始化 Mock 岗位数据"""
        async for db in get_db():
            existing = await db.execute(select(Job).limit(1))
            if existing.scalar():
                logger.info("Mock 岗位数据已存在，跳过初始化")
                return []

            jobs = []
            for data in self.MOCK_JOBS:
                job_id = str(uuid.uuid4())
                job = Job(id=job_id, **data)
                jobs.append(job)
            db.add_all(jobs)
            await db.commit()
            logger.info(f"已初始化 {len(jobs)} 条 Mock 岗位数据")
            return [JobResponse.model_validate(j) for j in jobs]

    async def calculate_match(
        self, profile_id: str, job_id: str
    ) -> Optional[MatchScoreResponse]:
        """计算简历与岗位的匹配度"""
        async for db in get_db():
            profile = await db.get(ResumeProfile, profile_id)
            job = await db.get(Job, job_id)
            if not profile or not job:
                return None

            profile_skills = {s["name"].lower() for s in (profile.skills or [])}
            job_skills = {s.lower() for s in (job.preferred_skills or [])}
            job_reqs = " ".join(job.requirements or []).lower()
            profile_text = (profile.parsed_text or "").lower()

            # 技能匹配
            skill_overlap = profile_skills & job_skills
            skill_match = len(skill_overlap) / max(len(job_skills), 1) * 100

            # 经验匹配（简单关键词匹配）
            exp_keywords = ["实习", "项目", "开发", "算法", "前端", "后端"]
            exp_score = sum(1 for kw in exp_keywords if kw in profile_text) / len(exp_keywords) * 100
            experience_match = min(exp_score * 1.2, 100)

            # 教育匹配（简单规则）
            education_match = 70.0  # 默认中等
            if profile.education:
                edu_text = " ".join(str(e) for e in profile.education)
                if "硕士" in edu_text or "博士" in edu_text:
                    education_match = 90.0
                elif "本科" in edu_text:
                    education_match = 70.0

            # 综合评分（加权）
            overall = skill_match * 0.5 + experience_match * 0.3 + education_match * 0.2

            # 识别差距
            gaps = [s for s in job.preferred_skills if s.lower() not in profile_skills]
            suggestions = self._generate_suggestions(skill_match, gaps, job.requirements)

            return MatchScoreResponse(
                job_id=job_id,
                job_title=job.title,
                company=job.company,
                overall_score=round(overall, 1),
                skill_match=round(skill_match, 1),
                experience_match=round(experience_match, 1),
                education_match=round(education_match, 1),
                gaps=gaps[:5],
                suggestions=suggestions,
            )

    def _generate_suggestions(self, skill_match: float, gaps: List[str], requirements: List[str]) -> List[str]:
        suggestions = []
        if skill_match < 60:
            suggestions.append("技能匹配度较低，建议补充岗位要求的关键技术栈")
        if gaps:
            suggestions.append(f"建议学习/强化以下技能: {', '.join(gaps[:3])}")
        if requirements:
            for req in requirements:
                if "实习" in req and not any("实习" in str(e.get("company", "")) for e in []):
                    suggestions.append("建议补充实习经历描述，突出项目成果")
        if not suggestions:
            suggestions.append("简历与岗位匹配度良好，可针对性优化项目描述")
        return suggestions
