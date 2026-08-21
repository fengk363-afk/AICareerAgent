"""
广东岗位采集模块 — 第一阶段
支持：广东人才网 (gdrc) + 广东公共招聘平台 (gd_public)
MVP 使用结构化 Mock 数据模拟接口层，后续替换为真实爬虫/API
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from loguru import logger

from app.agents.job_source_adapters import JobSourceAdapter, ADAPTER_REGISTRY


# ── 广东人才网 Mock 数据 ──────────────────────────────────────

_GDRC_JOBS = [
    {
        "source_job_id": "gdrc_001",
        "company": "广东省科学院智能信息研究所",
        "company_type": "state_enterprise",
        "title": "人工智能算法工程师",
        "location": "广州",
        "job_type": "full_time",
        "salary_range": {"min": 18, "max": 30, "unit": "K/月"},
        "description": "负责AI算法研发与落地，参与智能信息处理、自然语言处理等方向的技术攻关。",
        "requirements": ["硕士及以上学历", "熟悉Python/C++", "有NLP或CV项目经验"],
        "preferred_skills": ["Python", "PyTorch", "NLP", "Transformer", "Linux"],
        "tags": ["国企", "科研", "AI", "广州"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=3),
        "apply_url": "https://www.gdrc.com/job/gdrc_001",
        "job_url": "https://www.gdrc.com/job/gdrc_001",
        "company_website": "https://www.gdasi.cn",
        "application_method": "广东人才网投递",
    },
    {
        "source_job_id": "gdrc_002",
        "company": "广州市人民政府办公厅",
        "company_type": "government",
        "title": "信息化管理岗（公务员）",
        "location": "广州",
        "job_type": "full_time",
        "salary_range": {"min": 10, "max": 18, "unit": "K/月"},
        "description": "负责市政府信息化系统建设与运维管理，推进数字政府建设。",
        "requirements": ["本科及以上学历", "计算机相关专业", "熟悉信息系统管理"],
        "preferred_skills": ["Java", "MySQL", "Linux", "网络安全"],
        "tags": ["公务员", "稳定", "广州", "信息化"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": True,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=7),
        "apply_url": "https://www.gdrc.com/job/gdrc_002",
        "job_url": "https://www.gdrc.com/job/gdrc_002",
        "company_website": "https://www.gz.gov.cn",
        "application_method": "广东人才网报名",
    },
    {
        "source_job_id": "gdrc_003",
        "company": "深圳技术大学",
        "company_type": "state_enterprise",
        "title": "前端开发工程师（校招）",
        "location": "深圳",
        "job_type": "full_time",
        "salary_range": {"min": 15, "max": 25, "unit": "K/月"},
        "description": "负责学校智慧校园系统前端开发，使用 Vue/React 技术栈。",
        "requirements": ["2025届本科及以上学历", "熟练掌握 JavaScript", "熟悉 Vue 或 React"],
        "preferred_skills": ["Vue", "TypeScript", "JavaScript", "CSS", "Node.js"],
        "tags": ["高校", "校招", "深圳", "前端"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "spring",
        "posted_at": datetime.utcnow() - timedelta(days=1),
        "apply_url": "https://www.gdrc.com/job/gdrc_003",
        "job_url": "https://www.gdrc.com/job/gdrc_003",
        "company_website": "https://www.gdpu.edu.cn",
        "application_method": "广东人才网投递",
    },
    {
        "source_job_id": "gdrc_004",
        "company": "珠海格力电器股份有限公司",
        "company_type": "state_enterprise",
        "title": "嵌入式软件工程师",
        "location": "珠海",
        "job_type": "full_time",
        "salary_range": {"min": 16, "max": 28, "unit": "K/月"},
        "description": "负责家电产品嵌入式软件开发，参与智能家电控制系统设计。",
        "requirements": ["本科及以上学历", "熟悉 C/C++", "有嵌入式开发经验"],
        "preferred_skills": ["C", "C++", "嵌入式", "ARM", "Linux"],
        "tags": ["国企", "制造业", "珠海", "嵌入式"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": True,
        "season": "autumn",
        "posted_at": datetime.utcnow() - timedelta(days=5),
        "apply_url": "https://www.gdrc.com/job/gdrc_004",
        "job_url": "https://www.gdrc.com/job/gdrc_004",
        "company_website": "https://www.gree.com",
        "application_method": "广东人才网投递",
    },
    {
        "source_job_id": "gdrc_005",
        "company": "东莞松山湖高新技术产业开发区管委会",
        "company_type": "government",
        "title": "产业服务专员（校招）",
        "location": "东莞",
        "job_type": "full_time",
        "salary_range": {"min": 8, "max": 14, "unit": "K/月"},
        "description": "负责园区企业服务工作，协助招商引资、产业政策落地。",
        "requirements": ["本科及以上学历", "经济管理或理工科背景", "良好的沟通能力"],
        "preferred_skills": ["数据分析", "公文写作", "Excel", "PPT"],
        "tags": ["政府", "校招", "东莞", "产业服务"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=10),
        "apply_url": "https://www.gdrc.com/job/gdrc_005",
        "job_url": "https://www.gdrc.com/job/gdrc_005",
        "company_website": "https://www.songshanlake.gov.cn",
        "application_method": "广东人才网报名",
    },
]


# ── 广东公共招聘平台 Mock 数据 ────────────────────────────────

_GDPUBLIC_JOBS = [
    {
        "source_job_id": "gdpub_001",
        "company": "广东省人才交流服务中心",
        "company_type": "government",
        "title": "人力资源助理（劳务派遣）",
        "location": "广州",
        "job_type": "full_time",
        "salary_range": {"min": 6, "max": 10, "unit": "K/月"},
        "description": "协助开展人才招聘、简历筛选、面试安排等人力资源相关工作。",
        "requirements": ["本科及以上学历", "人力资源相关专业优先", "熟练使用 Office 软件"],
        "preferred_skills": ["HR", "招聘", "Excel", "沟通"],
        "tags": ["政府", "人力资源", "广州", "稳定"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=2),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_001",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_001",
        "company_website": "https://gdreclruit.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_002",
        "company": "佛山市人力资源和社会保障局",
        "company_type": "government",
        "title": "就业服务专员（校招）",
        "location": "佛山",
        "job_type": "full_time",
        "salary_range": {"min": 7, "max": 12, "unit": "K/月"},
        "description": "负责就业政策宣传、招聘会组织、失业登记等公共就业服务工作。",
        "requirements": ["2025届本科及以上学历", "公共管理、社会学相关专业优先"],
        "preferred_skills": ["公文写作", "活动策划", "数据分析"],
        "tags": ["政府", "校招", "佛山", "就业服务"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "spring",
        "posted_at": datetime.utcnow() - timedelta(days=4),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_002",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_002",
        "company_website": "https://fslh.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_003",
        "company": "广州市公共就业服务中心",
        "company_type": "government",
        "title": "职业指导师",
        "location": "广州",
        "job_type": "full_time",
        "salary_range": {"min": 8, "max": 15, "unit": "K/月"},
        "description": "为求职者提供职业规划咨询、简历修改、面试指导等公共服务。",
        "requirements": ["本科及以上学历", "有职业规划或HR相关经验优先"],
        "preferred_skills": ["职业规划", "沟通", "简历优化", "面试辅导"],
        "tags": ["政府", "职业指导", "广州", "公共服务"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=6),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_003",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_003",
        "company_website": "https://gzjob.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_004",
        "company": "深圳市公共就业服务平台",
        "company_type": "government",
        "title": "数据分析师（校招）",
        "location": "深圳",
        "job_type": "full_time",
        "salary_range": {"min": 10, "max": 18, "unit": "K/月"},
        "description": "负责就业市场数据分析、招聘趋势研究，支撑公共就业服务决策。",
        "requirements": ["2025届本科及以上学历", "统计学、计算机相关专业", "熟悉 SQL/Python"],
        "preferred_skills": ["Python", "SQL", "数据分析", "Tableau", "Excel"],
        "tags": ["政府", "校招", "深圳", "数据分析"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=1),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_004",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_004",
        "company_website": "https://szjob.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_005",
        "company": "广东省就业服务中心",
        "company_type": "government",
        "title": "信息化运维工程师",
        "location": "广州",
        "job_type": "full_time",
        "salary_range": {"min": 9, "max": 16, "unit": "K/月"},
        "description": "负责省级就业服务平台的日常运维、故障排查和技术支持。",
        "requirements": ["本科及以上学历", "计算机相关专业", "熟悉 Linux/网络"],
        "preferred_skills": ["Linux", "MySQL", "网络运维", "Shell"],
        "tags": ["政府", "运维", "广州", "稳定"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": False,
        "campus_recruitment": False,
        "season": "regular",
        "posted_at": datetime.utcnow() - timedelta(days=8),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_005",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_005",
        "company_website": "https://gdjob.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
    {
        "source_job_id": "gdpub_006",
        "company": "惠州市公共就业和人才服务中心",
        "company_type": "government",
        "title": "招聘专员（校招）",
        "location": "惠州",
        "job_type": "full_time",
        "salary_range": {"min": 6, "max": 10, "unit": "K/月"},
        "description": "组织线上线下招聘会，对接用人单位，服务求职者。",
        "requirements": ["2025届本科及以上学历", "市场营销、人力资源管理优先"],
        "preferred_skills": ["招聘", "沟通", "活动策划", "Office"],
        "tags": ["政府", "校招", "惠州", "招聘"],
        "is_remote": False,
        "is_foreign": False,
        "visa_support": False,
        "english_required": False,
        "graduate_program": True,
        "campus_recruitment": True,
        "season": "spring",
        "posted_at": datetime.utcnow() - timedelta(days=3),
        "apply_url": "https://gdreclruit.gov.cn/job/gdpub_006",
        "job_url": "https://gdreclruit.gov.cn/job/gdpub_006",
        "company_website": "https://hzrss.gov.cn",
        "application_method": "广东公共招聘平台投递",
    },
]


class GuangdongRCSource(JobSourceAdapter):
    """广东人才网适配器 — 广东省人力资源和社会保障厅主办"""

    @property
    def source_name(self) -> str:
        return "gdrc"

    @property
    def source_type(self) -> str:
        return "gdrc"

    @property
    def base_url(self) -> str:
        return "https://www.gdrc.com"

    async def fetch_jobs(
        self, keyword: str = "", location: str = "", limit: int = 20
    ) -> List[Dict[str, Any]]:
        logger.info(f"[广东人才网] 采集岗位: keyword={keyword}, location={location}")
        jobs = []
        for raw in _GDRC_JOBS:
            # 关键词过滤
            if keyword:
                kw = keyword.lower()
                match = (
                    kw in raw["title"].lower()
                    or kw in raw["company"].lower()
                    or kw in raw["description"].lower()
                )
                if not match:
                    continue
            # 地点过滤
            if location and location not in raw["location"]:
                continue
            jobs.append(self.normalize_job(raw))
            if len(jobs) >= limit:
                break
        logger.info(f"[广东人才网] 返回 {len(jobs)} 条岗位")
        return jobs

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[广东人才网] 获取详情: job_id={job_id}")
        for raw in _GDRC_JOBS:
            if raw["source_job_id"] == job_id:
                return self.normalize_job(raw)
        return None


class GuangdongPublicSource(JobSourceAdapter):
    """广东公共招聘平台适配器 — 省级公共就业服务平台"""

    @property
    def source_name(self) -> str:
        return "gd_public"

    @property
    def source_type(self) -> str:
        return "gd_public"

    @property
    def base_url(self) -> str:
        return "https://gdreclruit.gov.cn"

    async def fetch_jobs(
        self, keyword: str = "", location: str = "", limit: int = 20
    ) -> List[Dict[str, Any]]:
        logger.info(f"[广东公共招聘] 采集岗位: keyword={keyword}, location={location}")
        jobs = []
        for raw in _GDPUBLIC_JOBS:
            if keyword:
                kw = keyword.lower()
                match = (
                    kw in raw["title"].lower()
                    or kw in raw["company"].lower()
                    or kw in raw["description"].lower()
                )
                if not match:
                    continue
            if location and location not in raw["location"]:
                continue
            jobs.append(self.normalize_job(raw))
            if len(jobs) >= limit:
                break
        logger.info(f"[广东公共招聘] 返回 {len(jobs)} 条岗位")
        return jobs

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[广东公共招聘] 获取详情: job_id={job_id}")
        for raw in _GDPUBLIC_JOBS:
            if raw["source_job_id"] == job_id:
                return self.normalize_job(raw)
        return None


# 注册到全局适配器表
ADAPTER_REGISTRY["gdrc"] = GuangdongRCSource()
ADAPTER_REGISTRY["gd_public"] = GuangdongPublicSource()
