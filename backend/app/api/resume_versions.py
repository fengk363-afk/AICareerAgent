from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import ResumeVersion
from app.schemas.resume_version import ResumeVersionCreate, ResumeVersionResponse

router = APIRouter()


@router.get("/", response_model=list[ResumeVersionResponse])
async def list_versions(resume_profile_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """获取简历版本列表"""
    query = select(ResumeVersion).order_by(ResumeVersion.created_at.desc())
    if resume_profile_id:
        query = query.where(ResumeVersion.resume_profile_id == resume_profile_id)
    result = await db.execute(query)
    return [ResumeVersionResponse.model_validate(v) for v in result.scalars().all()]


@router.post("/", response_model=ResumeVersionResponse)
async def create_version(data: ResumeVersionCreate, db: AsyncSession = Depends(get_db)):
    """创建新版本"""
    # 检查原简历是否存在
    from app.db.models import ResumeProfile
    result = await db.execute(select(ResumeProfile).where(ResumeProfile.id == data.resume_profile_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="原简历不存在")

    version = ResumeVersion(
        resume_profile_id=data.resume_profile_id,
        version_name=data.version_name,
        original_filename=data.original_filename,
        notes=data.notes,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return ResumeVersionResponse.model_validate(version)


@router.get("/{version_id}", response_model=ResumeVersionResponse)
async def get_version(version_id: str, db: AsyncSession = Depends(get_db)):
    """获取版本详情"""
    result = await db.execute(select(ResumeVersion).where(ResumeVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return ResumeVersionResponse.model_validate(version)


@router.delete("/{version_id}")
async def delete_version(version_id: str, db: AsyncSession = Depends(get_db)):
    """删除版本"""
    result = await db.execute(select(ResumeVersion).where(ResumeVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    await db.delete(version)
    await db.commit()
    return {"message": "删除成功"}
