"""
JobFilter API — 岗位筛选配置接口
提供行业、岗位分类等筛选选项
"""
from fastapi import APIRouter
from typing import List, Dict, Any

from app.services.job_filter_config import JobFilterConfigService

router = APIRouter()


@router.get("/filter-options")
async def get_filter_options():
    """获取所有筛选选项（行业、岗位分类）"""
    return JobFilterConfigService.get_all_filter_options([])


@router.get("/industries")
async def get_industries():
    """获取所有行业列表"""
    return JobFilterConfigService.get_industries()


@router.get("/job-categories")
async def get_job_categories():
    """获取所有岗位分类列表"""
    return JobFilterConfigService.get_job_categories()


@router.get("/job-categories/by-industry/{industry}")
async def get_categories_by_industry(industry: str):
    """根据行业获取对应的岗位分类"""
    return JobFilterConfigService.get_categories_by_industry(industry)
