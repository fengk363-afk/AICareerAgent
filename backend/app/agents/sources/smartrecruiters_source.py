"""
SmartRecruiters 招聘数据源适配器
支持 SmartRecruiters API（需要认证）
"""
import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.agents.job_source_adapters import JobSourceAdapter


class SmartRecruitersSource(JobSourceAdapter):
    """SmartRecruiters 招聘数据源适配器"""

    @property
    def source_name(self) -> str:
        return "smartrecruiters"

    @property
    def source_type(self) -> str:
        return "api"

    @property
    def base_url(self) -> str:
        return "https://api.smartrecruiters.com"

    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取 API 密钥"""
        return os.environ.get("SMARTRECRUITERS_API_KEY")

    def _get_tenant(self) -> Optional[str]:
        """从环境变量获取 Tenant 名称"""
        return os.environ.get("SMARTRECRUITERS_TENANT")

    def _get_company_name(self) -> Optional[str]:
        """从环境变量获取公司名"""
        return os.environ.get("SMARTRECRUITERS_COMPANY_NAME")

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """从 SmartRecruiters API 获取岗位列表"""
        api_key = self._get_api_key()
        tenant = self._get_tenant()
        if not api_key:
            logger.warning("[SmartRecruiters] 未配置 SMARTRECRUITERS_API_KEY")
            return []
        if not tenant:
            logger.warning("[SmartRecruiters] 未配置 SMARTRECRUITERS_TENANT")
            return []

        try:
            import aiohttp
            url = f"{self.base_url}/jobs/v4/{tenant}/jobs"
            params = {"limit": limit}
            if keyword:
                params["keyword"] = keyword
            if location:
                params["location"] = location

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        jobs = data.get("jobs", [])
                        logger.info(f"[SmartRecruiters] 获取到 {len(jobs)} 个岗位")
                        return jobs
                    else:
                        logger.error(f"[SmartRecruiters] API 请求失败: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"[SmartRecruiters] 获取岗位失败: {e}")
            return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """从 SmartRecruiters API 获取岗位详情"""
        api_key = self._get_api_key()
        tenant = self._get_tenant()
        if not api_key or not tenant:
            logger.warning("[SmartRecruiters] 未配置 API 密钥或 Tenant")
            return None

        try:
            import aiohttp
            url = f"{self.base_url}/jobs/v4/{tenant}/jobs/{job_id}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"[SmartRecruiters] 获取岗位详情: {job_id}")
                        return data.get("job")
                    else:
                        logger.error(f"[SmartRecruiters] 获取岗位详情失败: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"[SmartRecruiters] 获取岗位详情失败: {e}")
            return None

    def normalize_smartrecruiters_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """将 SmartRecruiters API 响应标准化为统一格式"""
        # 提取基本信息
        title = raw_job.get("title", "")
        job_id = str(raw_job.get("id", "") or raw_job.get("refNumber", ""))

        # 提取公司名
        company_name = self._get_company_name() or "Unknown"

        # 提取部门
        department = raw_job.get("department", "")
        industry = raw_job.get("industry", "")
        dept_name = department or industry

        # 提取地点信息
        locations = []
        location_str = ""
        is_remote = False

        # SmartRecruiters 的 location 字段
        location_data = raw_job.get("location", {})
        if location_data:
            city = location_data.get("city", "")
            state = location_data.get("state", "")
            country = location_data.get("country", "")
            if city:
                locations.append(city)
            if state:
                locations.append(state)
            if country:
                locations.append(country)
            location_str = ", ".join(locations)

        # 检查是否远程
        employment_type = raw_job.get("employmentType", "")
        if employment_type and "remote" in employment_type.lower():
            is_remote = True
        if raw_job.get("isRemote", False):
            is_remote = True

        # 提取描述
        description = ""
        content = raw_job.get("jobAd", "") or raw_job.get("description", "")
        if content:
            description = re.sub(r'<[^>]+>', '', content)
            description = re.sub(r'\s+', ' ', description).strip()

        # 提取要求
        requirements = []
        qualifications = raw_job.get("qualifications", "")
        if qualifications:
            req_text = re.sub(r'<[^>]+>', '', qualifications)
            req_text = re.sub(r'\s+', ' ', req_text).strip()
            if req_text:
                requirements.append(req_text)

        # 提取技能关键词
        preferred_skills = []
        text_for_matching = (title + " " + description).lower()
        tech_keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
            "React", "Vue", "Angular", "Node.js", "Express", "Django", "Flask",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "K8s",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
            "REST", "GraphQL", "API", "Microservices",
            "Machine Learning", "AI", "Deep Learning", "NLP",
            "Git", "Linux", "Agile", "Scrum",
        ]
        for keyword in tech_keywords:
            if keyword.lower() in text_for_matching:
                preferred_skills.append(keyword)

        # 提取标签
        tags = []
        if dept_name:
            tags.append(dept_name)
        if location_str:
            tags.append(location_str)

        # 判断是否外企
        is_foreign = False
        foreign_companies = [
            "google", "microsoft", "amazon", "apple", "facebook", "meta",
            "netflix", "linkedin", "twitter", "stripe", "shopify",
            "uber", "lyft", "airbnb", "spotify", "adobe", "oracle",
            "salesforce", "ibm", "intel", "nvidia", "qualcomm",
        ]
        if any(c in company_name.lower() for c in foreign_companies):
            is_foreign = True

        # 构建 URL
        url = raw_job.get("applyUrl", "") or raw_job.get("url", "")

        # 构建发布时间
        posted_at = None
        created_at = raw_job.get("createdAt", "") or raw_job.get("publishedAt", "")
        if created_at:
            try:
                posted_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
            except:
                pass

        # 构建更新时间
        updated_at = raw_job.get("updatedAt", "")

        return {
            "source_job_id": job_id,
            "source": self.source_name,
            "source_type": self.source_type,
            "source_url": url,
            "company": company_name,
            "company_type": None,
            "title": title,
            "location": location_str,
            "locations": locations if locations else None,
            "job_type": "full_time",
            "salary_range": None,
            "description": description,
            "requirements": requirements,
            "preferred_skills": preferred_skills[:10],
            "tags": tags,
            "is_remote": is_remote,
            "is_foreign": is_foreign,
            "company_country": None,
            "visa_support": False,
            "english_required": is_foreign,
            "graduate_program": False,
            "campus_recruitment": False,
            "season": "regular",
            "industry": dept_name,
            "job_category": dept_name,
            "posted_at": posted_at,
            "apply_url": url,
            "job_url": url,
            "apply_source": self.source_name,
            "company_website": None,
            "application_method": None,
        }

    async def fetch_jobs_normalized(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """获取并标准化岗位列表"""
        raw_jobs = await self.fetch_jobs(keyword, location, limit)
        normalized_jobs = []
        for raw_job in raw_jobs:
            try:
                normalized = self.normalize_smartrecruiters_job(raw_job)
                normalized_jobs.append(normalized)
            except Exception as e:
                logger.warning(f"[SmartRecruiters] 标准化岗位失败: {e}")
                continue
        return normalized_jobs[:limit]
