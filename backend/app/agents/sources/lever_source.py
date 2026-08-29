"""
Lever 招聘数据源适配器
支持 Lever 公开 Job Board API（无需认证）
"""
import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.agents.job_source_adapters import JobSourceAdapter


class LeverSource(JobSourceAdapter):
    """Lever 招聘数据源适配器"""

    @property
    def source_name(self) -> str:
        return "lever"

    @property
    def source_type(self) -> str:
        return "api"

    @property
    def base_url(self) -> str:
        return "https://api.lever.co/v0"

    def _get_company_slug(self) -> Optional[str]:
        """从环境变量获取公司 slug"""
        return os.environ.get("LEVER_COMPANY")

    async def fetch_jobs(self, keyword: str = "", location: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """从 Lever 公开 API 获取岗位列表"""
        company = self._get_company_slug()
        if not company:
            logger.warning("[Lever] 未配置 LEVER_COMPANY")
            return []

        try:
            import aiohttp
            url = f"{self.base_url}/postings/{company}"
            params = {"state": "published", "mode": "json", "limit": limit}
            if keyword:
                params["search"] = keyword
            if location:
                params["location"] = location

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        jobs = data if isinstance(data, list) else []
                        logger.info(f"[Lever] 获取到 {len(jobs)} 个岗位")
                        return jobs
                    else:
                        logger.error(f"[Lever] API 请求失败: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"[Lever] 获取岗位失败: {e}")
            return []

    async def fetch_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """从 Lever API 获取岗位详情"""
        company = self._get_company_slug()
        if not company:
            logger.warning("[Lever] 未配置 LEVER_COMPANY")
            return None

        try:
            import aiohttp
            url = f"{self.base_url}/{company}/jobs/{job_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"[Lever] 获取岗位详情: {job_id}")
                        return data
                    else:
                        logger.error(f"[Lever] 获取岗位详情失败: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"[Lever] 获取岗位详情失败: {e}")
            return None

    def normalize_lever_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """将 Lever API 响应标准化为统一格式"""
        import html as html_module

        # 提取基本信息
        # Lever API 正确字段：
        # - text: 岗位标题（简短职位名称）
        # - description / descriptionBody: 岗位描述（HTML）
        # - descriptionPlain / descriptionBodyPlain: 纯文本描述
        # - opening / openingPlain: 岗位介绍开头（不是标题！）
        title = raw_job.get("text", "") or ""
        title = html_module.unescape(title).strip()
        # 确保标题不包含 HTML 标签
        title = re.sub(r'<[^>]+>', '', title).strip()
        job_id = str(raw_job.get("id", ""))

        # 提取公司名（Lever 公开 API 不返回公司名，需要从配置获取）
        company_name = os.environ.get("LEVER_COMPANY_NAME", "Unknown")

        # 提取部门/团队（Lever API 使用 categories 字段）
        categories = raw_job.get("categories", {})
        department = categories.get("department", "")
        team = categories.get("team", "")
        dept_name = department or team

        # 提取地点信息
        locations = []
        location_str = ""
        is_remote = False

        # Lever 的 locations 字段（可能是字符串或列表）
        lever_locations = raw_job.get("locations", [])
        if isinstance(lever_locations, str):
            locations = [lever_locations]
        elif isinstance(lever_locations, list):
            for loc in lever_locations:
                if isinstance(loc, dict):
                    name = loc.get("name", "") or loc.get("city", "")
                else:
                    name = str(loc)
                if name:
                    locations.append(name)
        # 也从 categories 中提取地点
        category_location = categories.get("location", "")
        if category_location and category_location not in locations:
            locations.append(category_location)
        location_str = ", ".join(locations[:3])

        # 检查是否远程
        workplace_type = raw_job.get("workplaceType", "")
        if workplace_type and "remote" in workplace_type.lower():
            is_remote = True
        if raw_job.get("isRemote", False):
            is_remote = True

        # 提取描述（优先使用 descriptionPlain，其次 descriptionBodyPlain）
        description = ""
        # 优先使用纯文本版本
        plain_desc = raw_job.get("descriptionPlain", "") or raw_job.get("descriptionBodyPlain", "")
        if plain_desc:
            description = plain_desc.strip()
        else:
            # 如果没有纯文本，从 HTML 清洗
            html_desc = raw_job.get("description", "") or raw_job.get("descriptionBody", "")
            if html_desc:
                description = re.sub(r'<[^>]+>', '', html_desc)
                description = html_module.unescape(description)
                description = re.sub(r'\s+', ' ', description).strip()

        # 提取要求（从 lists 字段）
        requirements = []
        lists = raw_job.get("lists", [])
        if isinstance(lists, list):
            for item in lists:
                if isinstance(item, dict):
                    item_text = item.get("text", "")
                    item_content = item.get("content", "")
                    # 如果是要求/职责部分，提取内容
                    if item_text and item_content:
                        # 清理 HTML
                        content_clean = re.sub(r'<[^>]+>', '', item_content)
                        content_clean = html_module.unescape(content_clean)
                        content_clean = re.sub(r'\s+', ' ', content_clean).strip()
                        if content_clean:
                            requirements.append(f"{item_text}\n{content_clean}")

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
        commitment = categories.get("commitment", "")
        if commitment:
            tags.append(commitment)

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

        # 构建 URL（Lever API 使用 hostedUrl 或 applyUrl）
        url = raw_job.get("hostedUrl", "") or raw_job.get("applyUrl", "") or ""

        # 构建发布时间
        posted_at = None
        created_at = raw_job.get("createdAt", "")
        if created_at:
            try:
                # Lever 返回的是 Unix timestamp（毫秒）
                if isinstance(created_at, (int, float)):
                    # 如果是毫秒时间戳，转换为秒
                    if created_at > 9999999999:
                        created_at = created_at / 1000
                    posted_at = datetime.fromtimestamp(created_at)
                else:
                    posted_at = datetime.fromisoformat(str(created_at).replace("Z", "+00:00")).replace(tzinfo=None)
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
                normalized = self.normalize_lever_job(raw_job)
                normalized_jobs.append(normalized)
            except Exception as e:
                logger.warning(f"[Lever] 标准化岗位失败: {e}")
                continue
        return normalized_jobs[:limit]
