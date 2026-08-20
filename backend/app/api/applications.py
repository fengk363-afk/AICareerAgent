from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Application, SavedJob, Job
from app.agents.engine import engine
from app.schemas.models import ApplicationResponse

router = APIRouter()


@router.post("/", response_model=ApplicationResponse)
async def create_application(data: dict):
    """创建投递记录"""
    result = await engine.apply_job(data["user_id"], data["job_id"], data.get("resume_profile_id"))
    if not result:
        raise HTTPException(status_code=400, detail="投递记录已存在或数据无效")
    return result


@router.get("/user/{user_id}", response_model=list[ApplicationResponse])
async def get_user_applications(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取用户投递列表"""
    result = await db.execute(
        select(Application).where(Application.user_id == user_id)
        .order_by(Application.created_at.desc())
    )
    apps = result.scalars().all()
    # 附加岗位信息
    output = []
    for app in apps:
        job_result = await db.execute(select(Job).where(Job.id == app.job_id))
        job = job_result.scalar_one_or_none()
        app_dict = app.model_dump() if hasattr(app, 'model_dump') else {c.name: getattr(app, c.name) for c in app.__table__.columns}
        if job:
            app_dict["job"] = {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url,
                "apply_url": job.apply_url,
            }
        output.append(app_dict)
    return output


@router.patch("/{application_id}/status")
async def update_status(application_id: str, status: str, notes: str = None):
    """更新投递状态"""
    result = await engine.update_application_status(application_id, status, notes)
    if not result:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return result


@router.post("/optimize")
async def optimize_resume(resume_profile_id: str, job_id: str):
    """生成简历优化建议"""
    result = await engine.optimize_resume(resume_profile_id, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="简历或岗位不存在")
    return result


@router.post("/save/{job_id}")
async def save_job(job_id: str, user_id: int = 1):
    """收藏岗位"""
    success = await engine.save_job(user_id, job_id)
    if not success:
        raise HTTPException(status_code=400, detail="已收藏该岗位")
    return {"message": "收藏成功"}


@router.delete("/save/{job_id}")
async def remove_saved_job(job_id: str, user_id: int = 1):
    """取消收藏"""
    success = await engine.remove_saved_job(user_id, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="未找到收藏记录")
    return {"message": "已取消收藏"}


@router.get("/saved/{user_id}", response_model=list[dict])
async def get_saved_jobs(user_id: int):
    """获取收藏的岗位"""
    return await engine.get_saved_jobs(user_id)
