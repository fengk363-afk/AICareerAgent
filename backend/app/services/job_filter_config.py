"""
JobFilterConfig — 岗位筛选配置服务
提供行业、岗位分类的枚举和统计信息
"""
from typing import List, Dict, Any, Optional
from loguru import logger


# 行业分类配置
INDUSTRY_CONFIG: Dict[str, Dict[str, Any]] = {
    "互联网": {
        "name": "互联网",
        "icon": "🌐",
        "description": "互联网、电子商务、社交媒体等",
    },
    "科技": {
        "name": "科技",
        "icon": "💻",
        "description": "硬件、软件、云计算、AI 等",
    },
    "金融": {
        "name": "金融",
        "icon": "💰",
        "description": "银行、证券、保险、金融科技等",
    },
    "人工智能": {
        "name": "人工智能",
        "icon": "🤖",
        "description": "AI、机器学习、深度学习等",
    },
    "远程工作": {
        "name": "远程工作",
        "icon": "🏠",
        "description": "支持远程办公的岗位",
    },
    "制造业": {
        "name": "制造业",
        "icon": "🏭",
        "description": "汽车、电子、机械等制造业",
    },
    "医疗": {
        "name": "医疗",
        "icon": "🏥",
        "description": "医疗、健康、生物医药等",
    },
    "教育": {
        "name": "教育",
        "icon": "📚",
        "description": "教育、培训、知识服务等",
    },
    "零售": {
        "name": "零售",
        "icon": "🛒",
        "description": "零售、电商、物流等",
    },
    "咨询": {
        "name": "咨询",
        "icon": "💼",
        "description": "管理咨询、技术咨询等",
    },
}


# 岗位分类配置
JOB_CATEGORY_CONFIG: Dict[str, Dict[str, Any]] = {
    "后端开发": {
        "name": "后端开发",
        "icon": "⚙️",
        "description": "服务端开发、API、数据库等",
        "parent_industry": "互联网",
    },
    "前端开发": {
        "name": "前端开发",
        "icon": "🎨",
        "description": "Web 前端、移动端 UI 等",
        "parent_industry": "互联网",
    },
    "算法工程": {
        "name": "算法工程",
        "icon": "🧮",
        "description": "机器学习、推荐系统、NLP 等",
        "parent_industry": "人工智能",
    },
    "移动端开发": {
        "name": "移动端开发",
        "icon": "📱",
        "description": "iOS、Android、小程序等",
        "parent_industry": "互联网",
    },
    "产品运营": {
        "name": "产品运营",
        "icon": "📊",
        "description": "产品管理、用户运营、增长等",
        "parent_industry": "互联网",
    },
    "全栈开发": {
        "name": "全栈开发",
        "icon": "🔧",
        "description": "前后端全栈开发",
        "parent_industry": "互联网",
    },
    "数据分析": {
        "name": "数据分析",
        "icon": "📈",
        "description": "数据分析师、商业智能等",
        "parent_industry": "金融",
    },
    "测试开发": {
        "name": "测试开发",
        "icon": "🧪",
        "description": "质量保证、自动化测试等",
        "parent_industry": "互联网",
    },
    "运维开发": {
        "name": "运维开发",
        "icon": "🚀",
        "description": "DevOps、SRE、基础设施等",
        "parent_industry": "科技",
    },
    "UI/UX 设计": {
        "name": "UI/UX 设计",
        "icon": "✏️",
        "description": "用户界面设计、用户体验设计等",
        "parent_industry": "互联网",
    },
}


class JobFilterConfigService:
    """岗位筛选配置服务"""

    @staticmethod
    def get_industries() -> List[Dict[str, Any]]:
        """获取所有行业列表"""
        return [
            {
                "value": key,
                "label": f"{config['icon']} {config['name']}",
                "description": config["description"],
            }
            for key, config in INDUSTRY_CONFIG.items()
        ]

    @staticmethod
    def get_job_categories() -> List[Dict[str, Any]]:
        """获取所有岗位分类列表"""
        return [
            {
                "value": key,
                "label": f"{config['icon']} {config['name']}",
                "description": config["description"],
                "parent_industry": config.get("parent_industry"),
            }
            for key, config in JOB_CATEGORY_CONFIG.items()
        ]

    @staticmethod
    def get_categories_by_industry(industry: str) -> List[Dict[str, Any]]:
        """根据行业获取对应的岗位分类"""
        return [
            {
                "value": key,
                "label": f"{config['icon']} {config['name']}",
                "description": config["description"],
                "parent_industry": config.get("parent_industry"),
            }
            for key, config in JOB_CATEGORY_CONFIG.items()
            if config.get("parent_industry") == industry
        ]

    @staticmethod
    def get_industry_stats(jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计各行业的岗位数量"""
        stats = {}
        for job in jobs:
            industry = job.get("industry")
            if industry:
                stats[industry] = stats.get(industry, 0) + 1
        return stats

    @staticmethod
    def get_category_stats(jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计各岗位分类的岗位数量"""
        stats = {}
        for job in jobs:
            category = job.get("job_category")
            if category:
                stats[category] = stats.get(category, 0) + 1
        return stats

    @staticmethod
    def get_all_filter_options(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取所有筛选选项（含统计数据）"""
        industry_stats = JobFilterConfigService.get_industry_stats(jobs)
        category_stats = JobFilterConfigService.get_category_stats(jobs)

        return {
            "industries": [
                {
                    **item,
                    "count": industry_stats.get(item["value"], 0),
                }
                for item in JobFilterConfigService.get_industries()
            ],
            "job_categories": [
                {
                    **item,
                    "count": category_stats.get(item["value"], 0),
                }
                for item in JobFilterConfigService.get_job_categories()
            ],
        }
