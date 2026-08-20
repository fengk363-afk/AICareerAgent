"""
CompanyResearchEngine — 公司研究引擎
分析公司信息，包括公司类型、行业、规模、业务方向、招聘趋势、面试难度、员工评价
"""
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import CompanyProfile
from app.db.database import get_db
from app.schemas.models import CompanyProfileResponse
from sqlalchemy import select


class CompanyResearchEngine:
    """公司研究引擎"""

    # 公司研究数据池
    COMPANY_DATA = {
        "字节跳动": {
            "company_type": "foreign" if False else "private",
            "industry": "互联网/人工智能",
            "company_size": "large",
            "business_direction": "短视频、社交、AI、云计算",
            "hiring_trend": "growing",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "技术氛围好，成长快，但工作强度大，996常见",
            "pros": ["技术栈先进", "成长空间大", "薪资竞争力强", "扁平化管理"],
            "cons": ["工作强度大", "加班文化", "竞争激烈", "稳定性一般"],
        },
        "阿里巴巴": {
            "company_type": "private",
            "industry": "互联网/电商",
            "company_size": "large",
            "business_direction": "电商、云计算、物流、文娱",
            "hiring_trend": "stable",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "大厂平台好，技术积累深，但层级较多，晋升竞争激烈",
            "pros": ["平台大资源多", "技术积累深厚", "品牌认可度高", "培训体系完善"],
            "cons": ["层级较多", "晋升竞争激烈", "工作强度大", "内卷严重"],
        },
        "腾讯": {
            "company_type": "private",
            "industry": "互联网/社交游戏",
            "company_size": "large",
            "business_direction": "社交、游戏、云计算、金融科技",
            "hiring_trend": "stable",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "产品文化强，工作生活平衡相对较好，但晋升周期长",
            "pros": ["产品文化强", "工作生活平衡较好", "福利好", "技术实力强"],
            "cons": ["晋升周期长", "部门壁垒", "创新压力大", "加班存在"],
        },
        "Microsoft": {
            "company_type": "foreign",
            "industry": "科技/云计算",
            "company_size": "large",
            "business_direction": "云计算、AI、办公软件、游戏",
            "hiring_trend": "growing",
            "interview_difficulty": "medium",
            "employee_reviews_summary": "WLB优秀，技术氛围好，国际化环境，但晋升较慢",
            "pros": ["工作生活平衡好", "技术氛围优秀", "国际化环境", "福利完善"],
            "cons": ["晋升较慢", "决策流程长", "国内团队边缘化", "薪资涨幅有限"],
        },
        "Google": {
            "company_type": "foreign",
            "industry": "科技/互联网",
            "company_size": "large",
            "business_direction": "搜索、云计算、AI、广告",
            "hiring_trend": "stable",
            "interview_difficulty": "hard",
            "employee_reviews_summary": "技术天花板高，创新氛围好，但面试难度极大，HC 有限",
            "pros": ["技术天花板高", "创新氛围好", "薪资顶级", "技术分享文化"],
            "cons": ["面试难度极大", "HC 有限", "晋升慢", "国内业务边缘"],
        },
        "美团": {
            "company_type": "private",
            "industry": "互联网/本地生活",
            "company_size": "large",
            "business_direction": "外卖、到店、酒店旅游、买菜",
            "hiring_trend": "growing",
            "interview_difficulty": "medium",
            "employee_reviews_summary": "业务增长快，技术挑战多，但工作强度大，竞争激烈",
            "pros": ["业务增长快", "技术挑战多", "薪资有竞争力", "成长空间大"],
            "cons": ["工作强度大", "竞争激烈", "加班文化", "稳定性一般"],
        },
        "拼多多": {
            "company_type": "private",
            "industry": "互联网/电商",
            "company_size": "large",
            "business_direction": "电商、农业、Temu",
            "hiring_trend": "growing",
            "interview_difficulty": "medium",
            "employee_reviews_summary": "薪资顶级，但工作强度极大，管理风格独特",
            "pros": ["薪资顶级", "成长快", "扁平管理", "技术挑战大"],
            "cons": ["工作强度极大", "管理风格独特", "稳定性差", "压力巨大"],
        },
        "某AI创业公司": {
            "company_type": "startup",
            "industry": "人工智能",
            "company_size": "small",
            "business_direction": "大模型应用、AI 工具、企业级 AI 服务",
            "hiring_trend": "growing",
            "interview_difficulty": "easy",
            "employee_reviews_summary": "AI 赛道热门，成长空间大，但风险高，稳定性差",
            "pros": ["AI 赛道热门", "成长空间大", "技术前沿", "扁平管理"],
            "cons": ["风险高", "稳定性差", "薪资可能不如大厂", "工作强度大"],
        },
        "某国企": {
            "company_type": "state_enterprise",
            "industry": "信息技术",
            "company_size": "medium",
            "business_direction": "企业信息系统、数字化转型",
            "hiring_trend": "stable",
            "interview_difficulty": "easy",
            "employee_reviews_summary": "稳定，WLB 好，但技术成长慢，薪资涨幅有限",
            "pros": ["稳定", "WLB 好", "压力小", "福利完善"],
            "cons": ["技术成长慢", "薪资涨幅有限", "层级多", "创新少"],
        },
        "某远程公司": {
            "company_type": "startup",
            "industry": "SaaS/互联网",
            "company_size": "small",
            "business_direction": "SaaS 产品、远程协作工具",
            "hiring_trend": "growing",
            "interview_difficulty": "easy",
            "employee_reviews_summary": "远程工作灵活，国际化团队，但薪资可能不如国内大厂",
            "pros": ["远程灵活", "国际化团队", "WLB 好", "技术栈先进"],
            "cons": ["薪资可能较低", "沟通成本高", "职业发展受限", "稳定性一般"],
        },
    }

    async def get_or_create_company_profile(self, company_name: str) -> Optional[CompanyProfileResponse]:
        """获取或创建公司档案"""
        async for db in get_db():
            # 检查是否已存在
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.company_name == company_name)
            )
            profile = result.scalar_one_or_none()

            if profile:
                return CompanyProfileResponse.model_validate(profile)

            # 创建新档案
            company_data = self.COMPANY_DATA.get(company_name, {})
            if not company_data:
                # 使用默认数据
                company_data = {
                    "company_type": "private",
                    "industry": "互联网",
                    "company_size": "medium",
                    "business_direction": "未知",
                    "hiring_trend": "stable",
                    "interview_difficulty": "medium",
                    "employee_reviews_summary": "暂无评价数据",
                    "pros": [],
                    "cons": [],
                }

            profile_id = f"company_{company_name[:20]}"
            company_profile = CompanyProfile(
                id=profile_id,
                company_name=company_name,
                **company_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(company_profile)
            await db.commit()
            await db.refresh(company_profile)
            return CompanyProfileResponse.model_validate(company_profile)

    async def get_company_profile(self, company_id: str) -> Optional[CompanyProfileResponse]:
        """获取公司档案"""
        async for db in get_db():
            result = await db.execute(select(CompanyProfile).where(CompanyProfile.id == company_id))
            profile = result.scalar_one_or_none()
            if profile:
                return CompanyProfileResponse.model_validate(profile)
        return None

    async def get_company_by_name(self, company_name: str) -> Optional[dict]:
        """通过公司名称获取公司分析"""
        profile = await self.get_or_create_company_profile(company_name)
        if profile:
            return profile.model_dump()
        return None
