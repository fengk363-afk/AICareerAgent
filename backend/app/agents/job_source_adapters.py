"""
JobSourceAdapters — 多来源岗位数据适配器
支持多种招聘平台，MVP 使用 Mock 数据模拟接口层
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger


class JobSourceAdapter(ABC):
    """岗位数据源适配器基类"""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称"""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """数据源类型"""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """基础 URL"""
        pass

    @abstractmethod
    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """获取岗位列表"""
        pass

    @abstractmethod
    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取岗位详情"""
        pass

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """标准化岗位数据"""
        return {
            "source": self.source_name,
            "source_type": self.source_type,
            "source_url": raw_job.get("url", ""),
            "company": raw_job.get("company", ""),
            "company_type": raw_job.get("company_type", None),
            "title": raw_job.get("title", ""),
            "location": raw_job.get("location", ""),
            "job_type": raw_job.get("job_type", "full_time"),
            "salary_range": raw_job.get("salary_range", None),
            "description": raw_job.get("description", ""),
            "requirements": raw_job.get("requirements", []),
            "preferred_skills": raw_job.get("preferred_skills", []),
            "tags": raw_job.get("tags", []),
            "is_remote": raw_job.get("is_remote", False),
            "is_foreign": raw_job.get("is_foreign", False),
            "company_country": raw_job.get("company_country", None),
            "visa_support": raw_job.get("visa_support", False),
            "english_required": raw_job.get("english_required", False),
            "graduate_program": raw_job.get("graduate_program", False),
            "campus_recruitment": raw_job.get("campus_recruitment", False),
            "season": raw_job.get("season", "regular"),
            "posted_at": raw_job.get("posted_at", None),
            "apply_url": raw_job.get("apply_url", raw_job.get("url", "")),
            "job_url": raw_job.get("url", ""),
            "apply_source": self.source_name,
            "company_website": raw_job.get("company_website", None),
            "application_method": raw_job.get("application_method", None),
        }


class CompanyOfficialSource(JobSourceAdapter):
    """公司官方招聘页适配器"""

    @property
    def source_name(self) -> str:
        return "company"

    @property
    def source_type(self) -> str:
        return "official"

    @property
    def base_url(self) -> str:
        return "https://careers.example.com"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """模拟从公司官方招聘页获取岗位"""
        logger.info(f"[CompanyOfficial] 获取岗位: keyword={keyword}, location={location}")
        # MVP: 返回空列表，实际接入时替换为真实 API 调用
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """模拟获取岗位详情"""
        logger.info(f"[CompanyOfficial] 获取岗位详情: job_id={job_id}")
        return None


class LinkedInSource(JobSourceAdapter):
    """LinkedIn 适配器"""

    @property
    def source_name(self) -> str:
        return "linkedin"

    @property
    def source_type(self) -> str:
        return "linkedin"

    @property
    def base_url(self) -> str:
        return "https://www.linkedin.com/jobs"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """模拟从 LinkedIn 获取岗位"""
        logger.info(f"[LinkedIn] 获取岗位: keyword={keyword}, location={location}")
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[LinkedIn] 获取岗位详情: job_id={job_id}")
        return None


class IndeedSource(JobSourceAdapter):
    """Indeed 适配器"""

    @property
    def source_name(self) -> str:
        return "indeed"

    @property
    def source_type(self) -> str:
        return "indeed"

    @property
    def base_url(self) -> str:
        return "https://www.indeed.com"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        logger.info(f"[Indeed] 获取岗位: keyword={keyword}, location={location}")
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[Indeed] 获取岗位详情: job_id={job_id}")
        return None


class BossSource(JobSourceAdapter):
    """Boss直聘适配器"""

    @property
    def source_name(self) -> str:
        return "boss"

    @property
    def source_type(self) -> str:
        return "boss"

    @property
    def base_url(self) -> str:
        return "https://www.zhipin.com"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        logger.info(f"[Boss] 获取岗位: keyword={keyword}, location={location}")
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[Boss] 获取岗位详情: job_id={job_id}")
        return None


class LagouSource(JobSourceAdapter):
    """拉勾网适配器"""

    @property
    def source_name(self) -> str:
        return "lagou"

    @property
    def source_type(self) -> str:
        return "lagou"

    @property
    def base_url(self) -> str:
        return "https://www.lagou.com"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        logger.info(f"[Lagou] 获取岗位: keyword={keyword}, location={location}")
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[Lagou] 获取岗位详情: job_id={job_id}")
        return None


class LiepinSource(JobSourceAdapter):
    """猎聘适配器"""

    @property
    def source_name(self) -> str:
        return "liepin"

    @property
    def source_type(self) -> str:
        return "liepin"

    @property
    def base_url(self) -> str:
        return "https://www.liepin.com"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        logger.info(f"[Liepin] 获取岗位: keyword={keyword}, location={location}")
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[Liepin] 获取岗位详情: job_id={job_id}")
        return None


class GlassdoorSource(JobSourceAdapter):
    """Glassdoor 适配器"""

    @property
    def source_name(self) -> str:
        return "glassdoor"

    @property
    def source_type(self) -> str:
        return "glassdoor"

    @property
    def base_url(self) -> str:
        return "https://www.glassdoor.com"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        logger.info(f"[Glassdoor] 获取岗位: keyword={keyword}, location={location}")
        return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        logger.info(f"[Glassdoor] 获取岗位详情: job_id={job_id}")
        return None


# 适配器注册表
ADAPTER_REGISTRY: Dict[str, JobSourceAdapter] = {
    "company": CompanyOfficialSource(),
    "linkedin": LinkedInSource(),
    "indeed": IndeedSource(),
    "boss": BossSource(),
    "lagou": LagouSource(),
    "liepin": LiepinSource(),
    "glassdoor": GlassdoorSource(),
}


def get_adapter(source_name: str) -> Optional[JobSourceAdapter]:
    """获取适配器"""
    return ADAPTER_REGISTRY.get(source_name)


def list_adapters() -> List[Dict[str, str]]:
    """列出所有适配器"""
    return [
        {"source_name": name, "source_type": adapter.source_type, "base_url": adapter.base_url}
        for name, adapter in ADAPTER_REGISTRY.items()
    ]
