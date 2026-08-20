import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import ResumeProfile, ResumeVersion
from app.agents.engine import engine
from app.schemas.models import ResumeProfileResponse
from app.api.auth import get_token
from app.core.auth_utils import decode_access_token

router = APIRouter()


@router.post("/upload", response_model=ResumeProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    version_name: Optional[str] = None,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF 简历，创建新版本"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式")

    content = await file.read()

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    user_id = int(payload.get("sub"))

    result = await engine.upload_resume(user_id, content, file.filename)

    version = ResumeVersion(
        id=str(uuid.uuid4()),
        resume_profile_id=result.id,
        version_name=version_name or f"v{len(result.skills or [])}skills",
        original_filename=file.filename,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return result


@router.get("/profiles", response_model=list[ResumeProfileResponse])
async def list_profiles(db: AsyncSession = Depends(get_db)):
    """列出所有简历画像"""
    result = await db.execute(
        select(ResumeProfile).order_by(ResumeProfile.created_at.desc())
    )
    return [ResumeProfileResponse.model_validate(p) for p in result.scalars().all()]


@router.get("/profiles/{profile_id}", response_model=ResumeProfileResponse)
async def get_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """查询简历画像"""
    result = await db.execute(select(ResumeProfile).where(ResumeProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="简历画像不存在")
    return ResumeProfileResponse.model_validate(profile)


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """删除简历画像"""
    result = await db.execute(select(ResumeProfile).where(ResumeProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="简历画像不存在")
    await db.delete(profile)
    await db.commit()
    return {"message": "删除成功"}
