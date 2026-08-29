"""
Ashby 招聘数据源适配器
支持 Ashby API（需要认证）
"""
import os
import re
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.agents.job_source_adapters import JobSourceAdapter


class AshbySource(JobSourceAdapter):
    """Ashby 招聘数据源适配器"""

    @property
    def source_name(self) -> str:
        return "ashby"

    @property
    def source_type(self) -> str:
        return "api"

    @property
    def base_url(self) -> str:
        return "https://api.ashbyhq.com"

    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取 API 密钥"""
        return os.environ.get("ASHBY_API_KEY")

    def _get_board_name(self) -> Optional[str]:
        """从环境变量获取 Board 名称"""
        return os.environ.get("ASHBY_BOARD")

    def _get_company_name(self) -> Optional[str]:
        """从环境变量获取公司名"""
        return os.environ.get("ASHBY_COMPANY_NAME")

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """从 Ashby API 获取岗位列表"""
        api_key = self._get_api_key()
        board = self._get_board_name()
        if not api_key:
            logger.warning("[Ashby] 未配置 ASHBY_API_KEY")
            return []
        if not board:
            logger.warning("[Ashby] 未配置 ASHBY_BOARD")
            return []

        try:
            import aiohttp
            url = f"{self.base_url}/v1/jobPosting/list"
            headers = {
                "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
                "Content-Type": "application/json"
            }
            payload = {
                "board": board,
                "limit": limit
            }
            if keyword:
                payload["search"] = keyword

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        jobs = data.get("jobPostings", [])
                        logger.info(f"[Ashby] 获取到 {len(jobs)} 个岗位")
                        return jobs
                    else:
                        logger.error(f"[Ashby] API 请求失败: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"[Ashby] 获取岗位失败: {e}")
            return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """从 Ashby API 获取岗位详情"""
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("[Ashby] 未配置 ASHBY_API_KEY")
            return None

        try:
            import aiohttp
            url = f"{self.base_url}/v1/jobPosting/get"
            headers = {
                "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
                "Content-Type": "application/json"
            }
            payload = {"id": job_id}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"[Ashby] 获取岗位详情: {job_id}")
                        return data.get("jobPosting")
                    else:
                        logger.error(f"[Ashby] 获取岗位详情失败: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"[Ashby] 获取岗位详情失败: {e}")
            return None

    def normalize_ashby_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """将 Ashby API 响应标准化为统一格式"""
        # 提取基本信息
        title = raw_job.get("title", "")
        job_id = str(raw_job.get("id", ""))

        # 提取公司名
        company_name = self._get_company_name() or "Unknown"

        # 提取部门/团队
        department = raw_job.get("department", "")
        team = raw_job.get("team", "")
        dept_name = department or team

        # 提取地点信息
        locations = []
        location_str = ""
        is_remote = False

        # Ashby 的 locations 字段
        ashby_locations = raw_job.get("locations", [])
        if ashby_locations:
            for loc in ashby_locations:
                name = loc.get("name", "") or loc.get("city", "")
                if name:
                    locations.append(name)
            location_str = ", ".join(locations[:3])

        # 检查是否远程
        employment_type = raw_job.get("employmentType", "")
        if employment_type and "remote" in employment_type.lower():
            is_remote = True
        if raw_job.get("isRemote", False):
            is_remote = True

        # 提取描述
        description = ""
        content = raw_job.get("content", "") or raw_job.get("description", "")
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
        url = raw_job.get("url", "") or raw_job.get("applyUrl", "")

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
                normalized = self.normalize_ashby_job(raw_job)
                normalized_jobs.append(normalized)
            except Exception as e:
                logger.warning(f"[Ashby] 标准化岗位失败: {e}")
                continue
        return normalized_jobs[:limit]
