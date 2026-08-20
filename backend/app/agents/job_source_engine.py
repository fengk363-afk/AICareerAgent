"""
JobSourceEngine — 统一岗位数据源系统
支持多种招聘平台，MVP 使用 Mock 数据
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import Job, JobType, CompanyType, JobSourceType
from app.db.models import JobSource as JobSourceModel
# Import enum separately to avoid shadowing
import enum
class _JobSourceEnum(str, enum.Enum):
    MOCK = "mock"
    LIEPIN = "liepin"
    BOSS = "boss"
    LAGOU = "lagou"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    COMPANY = "company"
from sqlalchemy import select
from app.db.database import get_db
from app.schemas.models import JobResponse
from app.agents.job_source_adapters import ADAPTER_REGISTRY, get_adapter


class JobSourceEngine:
    """统一岗位数据源引擎"""

    # Mock 岗位数据池（模拟多来源）
    MOCK_JOBS = [
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://jobs.bytedance.com/campus",
            "company": "字节跳动",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "后端开发工程师（校招）",
            "location": "北京",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 25, "max": 45, "unit": "K/月"},
            "description": "负责推荐系统后端服务开发，使用 Go/Python 构建高并发分布式系统",
            "requirements": ["计算机相关专业", "熟悉 Go 或 Python", "了解数据结构与算法", "有实习经验者优先"],
            "preferred_skills": ["Go", "Python", "Redis", "Kafka", "MySQL", "Docker"],
            "tags": ["大厂", "核心技术", "成长快", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "apply_url": "https://jobs.bytedance.com/campus",
            "job_url": "https://jobs.bytedance.com/campus",
            "apply_source": "company",
            "company_website": "https://www.bytedance.com",
            "application_method": "在线申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://careers.alibaba.com/campus",
            "company": "阿里巴巴",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "前端开发工程师（校招）",
            "location": "杭州",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 25, "max": 40, "unit": "K/月"},
            "description": "负责淘宝/天猫前端核心业务开发，使用 React 技术栈",
            "requirements": ["计算机相关专业", "熟练掌握 React", "了解 TypeScript", "有项目经验者优先"],
            "preferred_skills": ["React", "TypeScript", "JavaScript", "CSS", "Webpack", "Node.js"],
            "tags": ["大厂", "核心业务", "技术栈先进", "校招", "春招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "spring",
            "apply_url": "https://careers.alibaba.com/campus",
            "job_url": "https://careers.alibaba.com/campus",
            "apply_source": "boss",
            "company_website": "https://www.alibaba.com",
            "application_method": "内推/网申",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://careers.tencent.com/campus",
            "company": "腾讯",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "算法工程师（校招）",
            "location": "深圳",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 30, "max": 55, "unit": "K/月"},
            "description": "负责搜索/推荐算法优化，提升用户体验和商业化效果",
            "requirements": ["硕士及以上学历", "扎实的数学基础", "熟悉机器学习算法", "有顶会论文优先"],
            "preferred_skills": ["Python", "TensorFlow", "PyTorch", "NLP", "推荐系统", "C++"],
            "tags": ["大厂", "算法", "高薪资", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "apply_url": "https://careers.tencent.com/campus",
            "job_url": "https://careers.tencent.com/campus",
            "apply_source": "company",
            "company_website": "https://www.tencent.com",
            "application_method": "在线申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://zhaopin.meituan.com/campus",
            "company": "美团",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "全栈开发工程师（校招）",
            "location": "北京",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 25, "max": 45, "unit": "K/月"},
            "description": "负责本地生活服务平台全栈开发，覆盖 Web 和移动端",
            "requirements": ["计算机相关专业", "熟悉前后端开发", "了解数据库设计", "有实际项目经验"],
            "preferred_skills": ["Vue", "React", "Node.js", "Python", "PostgreSQL", "Docker"],
            "tags": ["大厂", "全栈", "业务丰富", "校招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "regular",
            "apply_url": "https://zhaopin.meituan.com/campus",
            "job_url": "https://zhaopin.meituan.com/campus",
            "apply_source": "boss",
            "company_website": "https://www.meituan.com",
            "application_method": "内推/网申",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "company",
            "source_type": JobSourceType.OFFICIAL.value,
            "source_url": "https://careers.pinduoduo.com/campus",
            "company": "拼多多",
            "company_type": CompanyType.PRIVATE.value,
            "company_country": "中国",
            "title": "移动端开发工程师（校招）",
            "location": "上海",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 30, "max": 50, "unit": "K/月"},
            "description": "负责拼多多 App 核心功能开发，使用 Kotlin/Swift",
            "requirements": ["计算机相关专业", "熟悉 Android 或 iOS 开发", "了解移动端性能优化"],
            "preferred_skills": ["Kotlin", "Swift", "Java", "Objective-C", "React Native", "Flutter"],
            "tags": ["大厂", "移动端", "高并发", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "apply_url": "https://careers.pinduoduo.com/campus",
            "job_url": "https://careers.pinduoduo.com/campus",
            "apply_source": "company",
            "company_website": "https://www.pinduoduo.com",
            "application_method": "在线申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "linkedin",
            "source_type": JobSourceType.LINKEDIN.value,
            "source_url": "https://careers.microsoft.com/campus",
            "company": "Microsoft",
            "company_type": CompanyType.FOREIGN.value,
            "company_country": "美国",
            "title": "Software Engineer I (校招)",
            "location": "北京",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 40, "max": 70, "unit": "K/月"},
            "description": "参与 Azure 云服务开发，使用 C#/Go 构建分布式系统",
            "requirements": ["计算机相关专业", "熟练掌握至少一门编程语言", "良好的英语能力"],
            "preferred_skills": ["C#", "Go", "Python", "Azure", "Kubernetes", "SQL"],
            "tags": ["外企", "WLB", "技术栈先进", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": True,
            "visa_support": True,
            "english_required": True,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "apply_url": "https://careers.microsoft.com/campus",
            "job_url": "https://careers.microsoft.com/campus",
            "apply_source": "linkedin",
            "company_website": "https://www.microsoft.com",
            "application_method": "LinkedIn/官网",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "linkedin",
            "source_type": JobSourceType.LINKEDIN.value,
            "source_url": "https://careers.google.com/jobs",
            "company": "Google",
            "company_type": CompanyType.FOREIGN.value,
            "company_country": "美国",
            "title": "Software Engineer - New Grad",
            "location": "上海",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 50, "max": 80, "unit": "K/月"},
            "description": "参与 Google Cloud 产品开发，使用 C++/Java 构建大规模分布式系统",
            "requirements": ["本科及以上学历", "扎实的算法基础", "良好的英语沟通能力"],
            "preferred_skills": ["C++", "Java", "Python", "Go", "Distributed Systems", "Cloud"],
            "tags": ["外企", "顶级薪资", "技术挑战", "校招", "秋招"],
            "is_remote": False,
            "is_foreign": True,
            "visa_support": True,
            "english_required": True,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "autumn",
            "apply_url": "https://careers.google.com/jobs",
            "job_url": "https://careers.google.com/jobs",
            "apply_source": "linkedin",
            "company_website": "https://www.google.com",
            "application_method": "官网申请",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "lagou",
            "source_type": JobSourceType.LAGOU.value,
            "source_url": "https://www.lagou.com/jobs/ai-startup",
            "company": "某AI创业公司",
            "company_type": CompanyType.STARTUP.value,
            "company_country": "中国",
            "title": "后端开发工程师（校招）",
            "location": "北京",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 20, "max": 35, "unit": "K/月"},
            "description": "参与 AI 产品后端开发，使用 Python/Go 构建大模型应用服务",
            "requirements": ["计算机相关专业", "熟悉 Python", "对 AI/LLM 有兴趣"],
            "preferred_skills": ["Python", "FastAPI", "LangChain", "Redis", "PostgreSQL", "Docker"],
            "tags": ["创业公司", "AI", "成长空间大", "校招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "regular",
            "apply_url": "https://www.lagou.com/jobs/ai-startup",
            "job_url": "https://www.lagou.com/jobs/ai-startup",
            "apply_source": "lagou",
            "company_website": "https://www.ai-startup.com",
            "application_method": "拉勾网",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "liepin",
            "source_type": JobSourceType.LIEPIN.value,
            "source_url": "https://www.liepin.com/state-enterprise",
            "company": "某国企",
            "company_type": CompanyType.STATE_ENTERPRISE.value,
            "company_country": "中国",
            "title": "信息技术岗（校招）",
            "location": "北京",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 15, "max": 25, "unit": "K/月"},
            "description": "负责企业内部信息系统开发与维护",
            "requirements": ["计算机相关专业", "熟悉 Java/Python", "稳定性要求高"],
            "preferred_skills": ["Java", "Spring Boot", "MySQL", "Vue", "Linux"],
            "tags": ["国企", "稳定", "WLB好", "校招"],
            "is_remote": False,
            "is_foreign": False,
            "visa_support": False,
            "english_required": False,
            "graduate_program": True,
            "campus_recruitment": True,
            "season": "regular",
            "apply_url": "https://www.liepin.com/state-enterprise",
            "job_url": "https://www.liepin.com/state-enterprise",
            "apply_source": "liepin",
            "company_website": "https://www.state-enterprise.com",
            "application_method": "猎聘/官网",
        },
        {
            "source": _JobSourceEnum.MOCK.value,
            "source_name": "boss",
            "source_type": JobSourceType.BOSS.value,
            "source_url": "https://www.wechatjobs.com/remote",
            "company": "某远程公司",
            "company_type": CompanyType.STARTUP.value,
            "company_country": "美国",
            "title": "前端开发工程师（远程）",
            "location": "远程",
            "job_type": JobType.FULL_TIME.value,
            "salary_range": {"min": 20, "max": 40, "unit": "K/月"},
            "description": "远程开发 SaaS 产品前端，使用 React/TypeScript",
            "requirements": ["熟练掌握 React", "有独立开发能力", "良好的沟通能力"],
            "preferred_skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "GraphQL"],
            "tags": ["远程", "灵活", "国际化", "海外机会"],
            "is_remote": True,
            "is_foreign": False,
            "visa_support": False,
            "english_required": True,
            "graduate_program": False,
            "campus_recruitment": False,
            "season": "regular",
            "apply_url": "https://www.wechatjobs.com/remote",
            "job_url": "https://www.wechatjobs.com/remote",
            "apply_source": "boss",
            "company_website": "https://www.remote-company.com",
            "application_method": "微信/官网",
        },
    ]

    async def seed_mock_jobs(self) -> List[JobResponse]:
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

    async def search_jobs(
        self,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        company_type: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        is_foreign: Optional[bool] = None,
        is_remote: Optional[str] = None,
        has_apply_url: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        company_country: Optional[str] = None,
        visa_support: Optional[bool] = None,
        english_required: Optional[bool] = None,
        graduate_program: Optional[bool] = None,
        campus_recruitment: Optional[bool] = None,
        season: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[JobResponse]:
        """搜索岗位（支持多维度筛选）"""
        async for db in get_db():
            query = select(Job)

            if keyword:
                kw = keyword.lower()
                query = query.where(
                    (Job.title.ilike(f"%{kw}%")) |
                    (Job.company.ilike(f"%{kw}%")) |
                    (Job.description.ilike(f"%{kw}%"))
                )
            if location:
                query = query.where(Job.location.ilike(f"%{location}%"))
            if job_type:
                query = query.where(Job.job_type == job_type)
            if company_type:
                query = query.where(Job.company_type == company_type)
            if is_foreign is not None:
                query = query.where(Job.is_foreign == is_foreign)
            if is_remote is not None:
                query = query.where(Job.is_remote == is_remote)
            if has_apply_url is not None:
                if has_apply_url:
                    query = query.where(Job.apply_url.isnot(None))
                else:
                    query = query.where(Job.apply_url.is_(None))
            if salary_min is not None:
                query = query.where(Job.salary_range["min"].as_integer() >= salary_min)
            if salary_max is not None:
                query = query.where(Job.salary_range["max"].as_integer() <= salary_max)
            if tags:
                for tag in tags:
                    query = query.where(Job.tags.contains([tag]))
            if source_type:
                query = query.where(Job.source_type == source_type)
            if company_country:
                query = query.where(Job.company_country.ilike(f"%{company_country}%"))
            if visa_support is not None:
                query = query.where(Job.visa_support == visa_support)
            if english_required is not None:
                query = query.where(Job.english_required == english_required)
            if graduate_program is not None:
                query = query.where(Job.graduate_program == graduate_program)
            if campus_recruitment is not None:
                query = query.where(Job.campus_recruitment == campus_recruitment)
            if season:
                query = query.where(Job.season == season)

            result = await db.execute(query.offset(offset).limit(limit))
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        async for db in get_db():
            job = await db.get(Job, job_id)
            if job:
                return JobResponse.model_validate(job)
        return None

    async def get_foreign_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取外企岗位"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(Job.is_foreign == True)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_campus_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取校招岗位"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(Job.campus_recruitment == True)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_remote_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取远程岗位"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(Job.is_remote == True)
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]

    async def get_overseas_jobs(self, limit: int = 20) -> List[JobResponse]:
        """获取海外岗位（外企+远程+签证支持）"""
        async for db in get_db():
            result = await db.execute(
                select(Job)
                .where(
                    (Job.is_foreign == True) |
                    (Job.is_remote == True) |
                    (Job.visa_support == True)
                )
                .order_by(Job.created_at.desc())
                .limit(limit)
            )
            return [JobResponse.model_validate(r) for r in result.scalars().all()]
