"""
Greenhouse 招聘数据源适配器
支持 Greenhouse API v2 获取岗位数据
"""
import os
import re
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.agents.job_source_adapters import JobSourceAdapter


class GreenhouseSource(JobSourceAdapter):
    """Greenhouse 招聘数据源适配器"""

    @property
    def source_name(self) -> str:
        return "greenhouse"

    @property
    def source_type(self) -> str:
        return "api"

    @property
    def base_url(self) -> str:
        return "https://boards-api.greenhouse.io/v1"

    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取 API 密钥"""
        return os.environ.get("GREENHOUSE_API_KEY")

    def _get_board_name(self) -> Optional[str]:
        """从环境变量获取 Board 名称"""
        return os.environ.get("GREENHOUSE_BOARD")

    def _build_api_url(self, endpoint: str = "boards") -> str:
        """构建 API URL"""
        board = self._get_board_name()
        if not board:
            return ""
        return f"{self.base_url}/{endpoint}/{board}"

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """从 Greenhouse API 获取岗位列表"""
        board = self._get_board_name()
        if not board:
            logger.warning("[Greenhouse] 未配置 GREENHOUSE_BOARD")
            return []

        try:
            import aiohttp
            url = f"{self.base_url}/boards/{board}/jobs"
            params = {"content": "true"}
            if keyword:
                params["search"] = keyword
            if location:
                params["location"] = location

            headers = {"Accept": "application/json"}
            api_key = self._get_api_key()
            if api_key:
                headers["Authorization"] = f"Basic {api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        jobs = data.get("jobs", [])
                        logger.info(f"[Greenhouse] 获取到 {len(jobs)} 个岗位")
                        return jobs
                    else:
                        logger.error(f"[Greenhouse] API 请求失败: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"[Greenhouse] 获取岗位失败: {e}")
            return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """从 Greenhouse API 获取岗位详情"""
        board = self._get_board_name()
        if not board:
            logger.warning("[Greenhouse] 未配置 GREENHOUSE_BOARD")
            return None

        try:
            import aiohttp
            url = f"{self.base_url}/boards/{board}/jobs/{job_id}"
            headers = {"Accept": "application/json"}
            api_key = self._get_api_key()
            if api_key:
                headers["Authorization"] = f"Basic {api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"[Greenhouse] 获取岗位详情: {job_id}")
                        return data
                    else:
                        logger.error(f"[Greenhouse] 获取岗位详情失败: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"[Greenhouse] 获取岗位详情失败: {e}")
            return None

    def normalize_greenhouse_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """将 Greenhouse API 响应标准化为统一格式"""
        # 提取基本信息
        title = raw_job.get("title", "")

        # 提取公司名（Greenhouse API 返回 company_name 在顶层）
        company_name = raw_job.get("company_name", "") or "Unknown"

        # 提取部门名称
        departments = raw_job.get("departments", [])
        dept_name = departments[0].get("name", "") if departments else ""

        # 提取地点信息
        location = raw_job.get("location", {})
        location_name = location.get("name", "") if location else ""

        # 提取地点列表（从 offices 数组）
        locations = []
        offices = raw_job.get("offices", [])
        for office in offices:
            name = office.get("name", "")
            if name and name not in locations:
                locations.append(name)

        # 构建地点字符串
        location_str = location_name or ", ".join(locations[:3])

        # 提取描述（Greenhouse 使用 content 字段，包含 HTML）
        description = ""
        content = raw_job.get("content", "")
        if content:
            # 清理 HTML 标签
            description = re.sub(r'<[^>]+>', '', content)
            description = re.sub(r'\s+', ' ', description).strip()

        # 提取要求（从 content 中解析）
        requirements = []
        if content:
            # 尝试从 content 中提取 "Minimum requirements" 部分
            min_req_match = re.search(r'Minimum requirements\s*(?:<[^>]+>\s*)*(.*?)(?=\n\s*<h[23]|$)', content, re.DOTALL)
            if min_req_match:
                req_text = re.sub(r'<[^>]+>', '', min_req_match.group(1))
                req_text = re.sub(r'\s+', ' ', req_text).strip()
                if req_text:
                    requirements.append(req_text)

        # 提取责任（从 content 中解析）
        responsibilities = []
        if content:
            resp_match = re.search(r'What you\'ll do\s*(?:<[^>]+>\s*)*(.*?)(?=\n\s*<h[23]|Minimum requirements)', content, re.DOTALL)
            if resp_match:
                resp_text = re.sub(r'<[^>]+>', '', resp_match.group(1))
                resp_text = re.sub(r'\s+', ' ', resp_text).strip()
                if resp_text:
                    responsibilities.append(resp_text)

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

        # 判断是否远程
        is_remote = False
        work_type = raw_job.get("work_type", "")
        if work_type and "remote" in work_type.lower():
            is_remote = True
        if "remote" in description.lower() or "work from home" in description.lower():
            is_remote = True

        # 判断是否外企
        is_foreign = False
        if company_name:
            foreign_companies = [
                "google", "microsoft", "amazon", "apple", "facebook", "meta",
                "netflix", "linkedin", "twitter", "stripe", "shopify",
                "uber", "lyft", "airbnb", "spotify", "adobe", "oracle",
                "salesforce", "ibm", "intel", "nvidia", "qualcomm",
            ]
            if any(c in company_name.lower() for c in foreign_companies):
                is_foreign = True

        # 判断是否海外
        company_country = None
        if offices:
            # 从 office 信息推断国家
            for office in offices:
                loc = office.get("location", "")
                if loc and loc != "United States":
                    company_country = loc
                    break
            if not company_country and offices:
                # 默认美国
                company_country = "United States"

        # 构建发布时间（转换为 naive datetime）
        posted_at = None
        first_published = raw_job.get("first_published", "")
        if first_published:
            try:
                dt = datetime.fromisoformat(first_published.replace("Z", "+00:00"))
                # 转换为 naive datetime（去掉时区信息）
                posted_at = dt.replace(tzinfo=None)
            except:
                pass

        # 构建更新时间
        updated_at = raw_job.get("updated_at", "")

        # 构建 URL
        url = raw_job.get("absolute_url", "") or raw_job.get("url", "")

        return {
            "source_job_id": str(raw_job.get("id", "")),
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
            "company_country": company_country,
            "visa_support": False,
            "english_required": is_foreign,
            "graduate_program": False,
            "campus_recruitment": False,
            "season": "regular",
            "industry": dept_name,
            "job_category": dept_name,
            "posted_at": posted_at if posted_at else None,
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
                normalized = self.normalize_greenhouse_job(raw_job)
                normalized_jobs.append(normalized)
            except Exception as e:
                logger.warning(f"[Greenhouse] 标准化岗位失败: {e}")
                continue
        return normalized_jobs[:limit]
