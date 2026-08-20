"""
CompanyResearch API — 公司研究
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import engine
from app.schemas.models import CompanyProfileResponse

router = APIRouter()


@router.get("/{company_id}")
async def get_company(company_id: str):
    """获取公司分析（通过ID）"""
    result = await engine.get_company_by_id(company_id)
    if not result:
        raise HTTPException(status_code=404, detail="公司档案不存在")
    return result


@router.get("/search/{company_name}")
async def search_company(company_name: str):
    """搜索公司分析（通过名称）"""
    result = await engine.get_company_profile(company_name)
    if not result:
        raise HTTPException(status_code=404, detail="公司档案不存在")
    return result
