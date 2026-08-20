"""
SmartApplicationEngine — 智能投递引擎
支持自动投递、半自动辅助投递、官方链接跳转三种模式
"""
import uuid
import re
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import Application, SavedJob, Job, ResumeProfile, ResumeVersion
from app.db.database import get_db
from app.schemas.models import (
    ApplicationResponse, ApplicationStatus,
    ApplicationPrepareResponse,
)
from sqlalchemy import select


class SmartApplicationEngine:
    """智能投递引擎"""

    # 投递模式
    MODE_AUTO = "auto"           # AI 一键投递
    MODE_SEMI_AUTO = "semi_auto" # 半自动辅助投递
    MODE_REDIRECT = "redirect"   # 官方链接跳转

    # 状态流转
    STATUS_FLOW = {
        "draft": ["preparing", "applied", "withdrawn"],
        "preparing": ["applied", "draft"],
        "applied": ["viewed_apply", "screening", "withdrawn"],
        "viewed_apply": ["screening", "jumped_apply"],
        "screening": ["written_test", "interview_invited", "rejected"],
        "written_test": ["interview_invited", "rejected"],
        "interview_invited": ["offer", "rejected"],
        "offer": ["completed_apply", "rejected"],
        "rejected": [],
        "withdrawn": [],
        "jumped_apply": [],
        "completed_apply": [],
    }

    async def create_application(
        self,
        user_id: str,
        job_id: str,
        resume_profile_id: Optional[str] = None,
        resume_version_id: Optional[str] = None,
        application_mode: str = "redirect",
        notes: Optional[str] = None,
    ) -> Optional[ApplicationResponse]:
        """创建投递任务"""
        async for db in get_db():
            # 检查是否已存在
            existing = await db.execute(
                select(Application).where(
                    Application.user_id == int(user_id),
                    Application.job_id == job_id,
                )
            )
            if existing.scalar():
                logger.warning(f"用户 {user_id} 已投递过岗位 {job_id}")
                return None

            # 获取岗位信息以确定默认投递模式
            job = await db.get(Job, job_id)
            if not job:
                return None

            # 根据岗位特性自动选择投递模式
            if application_mode == "auto" and not job.apply_url:
                application_mode = self.MODE_REDIRECT  # 无投递链接则降级为跳转
            elif application_mode == "semi_auto" and not job.apply_url:
                application_mode = self.MODE_REDIRECT

            app_id = str(uuid.uuid4())
            application = Application(
                id=app_id,
                user_id=int(user_id),
                job_id=job_id,
                resume_profile_id=resume_profile_id,
                resume_version_id=resume_version_id,
                status=ApplicationStatus.DRAFT,
                application_mode=application_mode,
                notes=notes,
                created_at=datetime.utcnow(),
            )
            db.add(application)
            await db.commit()
            await db.refresh(application)
            logger.info(f"投递任务创建: {app_id}, 模式: {application_mode}")
            return await self._enrich_application(db, application)

    async def prepare_application(
        self,
        user_id: str,
        job_id: str,
        resume_profile_id: Optional[str] = None,
        target_position: Optional[str] = None,
        target_company: Optional[str] = None,
    ) -> Optional[ApplicationPrepareResponse]:
        """自动生成投递材料（Cover Letter + 简历匹配）"""
        async for db in get_db():
            job = await db.get(Job, job_id)
            if not job:
                return None

            profile = None
            if resume_profile_id:
                profile = await db.get(ResumeProfile, resume_profile_id)
            else:
                # 获取用户最新的简历
                result = await db.execute(
                    select(ResumeProfile)
                    .where(ResumeProfile.user_id == int(user_id))
                    .order_by(ResumeProfile.created_at.desc())
                    .limit(1)
                )
                profile = result.scalar_one_or_none()

            # 生成 Cover Letter
            cover_letter = await self._generate_cover_letter(profile, job, target_position, target_company)

            # 提取 JD 关键词并匹配
            jd_keywords = self._extract_jd_keywords(job)
            matched_keywords = self._match_keywords(profile, jd_keywords)

            # 计算匹配度
            match_score = await self._calc_match_score(profile, job) if profile else 50.0

            # 推荐简历版本
            recommended_version = await self._recommend_resume_version(profile, job, db)

            # 生成修改建议
            suggested_edits = await self._generate_suggested_edits(profile, job, matched_keywords)

            # 创建或更新投递记录
            existing = await db.execute(
                select(Application).where(
                    Application.user_id == int(user_id),
                    Application.job_id == job_id,
                )
            )
            app = existing.scalar_one_or_none()
            if not app:
                app_id = str(uuid.uuid4())
                app = Application(
                    id=app_id,
                    user_id=int(user_id),
                    job_id=job_id,
                    resume_profile_id=resume_profile_id,
                    status=ApplicationStatus.PREPARING,
                    application_mode=self.MODE_SEMI_AUTO,
                    cover_letter=cover_letter,
                    jd_keywords_matched=matched_keywords,
                    match_score=match_score,
                    created_at=datetime.utcnow(),
                )
                db.add(app)
                await db.commit()
                await db.refresh(app)
            else:
                app.cover_letter = cover_letter
                app.jd_keywords_matched = matched_keywords
                app.match_score = match_score
                app.status = ApplicationStatus.PREPARING
                await db.commit()
                await db.refresh(app)

            return ApplicationPrepareResponse(
                application_id=app.id,
                job_id=job_id,
                job_title=job.title,
                company=job.company,
                cover_letter=cover_letter,
                recommended_resume_version=recommended_version,
                jd_keywords_matched=matched_keywords,
                match_score=match_score,
                suggested_edits=suggested_edits,
                status=app.status.value,
            )

    async def submit_application(
        self,
        user_id: str,
        job_id: str,
        application_id: str,
        cover_letter: Optional[str] = None,
        resume_version_id: Optional[str] = None,
    ) -> Optional[ApplicationResponse]:
        """提交投递（自动/半自动模式）"""
        async for db in get_db():
            app = await db.get(Application, application_id)
            if not app:
                return None
            if app.user_id != int(user_id):
                return None

            # 更新投递材料
            if cover_letter:
                app.cover_letter = cover_letter
            if resume_version_id:
                app.resume_version_id = resume_version_id

            # 更新状态
            app.status = ApplicationStatus.APPLIED
            app.applied_at = datetime.utcnow()
            app.submitted_time = datetime.utcnow()

            await db.commit()
            await db.refresh(app)
            logger.info(f"投递提交: {application_id}")
            return await self._enrich_application(db, app)

    async def get_application_status(self, application_id: str) -> Optional[dict]:
        """查询投递状态"""
        async for db in get_db():
            app = await db.get(Application, application_id)
            if not app:
                return None
            return await self._enrich_application(db, app)

    async def get_application_history(self, user_id: str) -> List[dict]:
        """获取投递记录"""
        async for db in get_db():
            result = await db.execute(
                select(Application)
                .where(Application.user_id == int(user_id))
                .order_by(Application.created_at.desc())
            )
            apps = result.scalars().all()
            output = []
            for app in apps:
                enriched = await self._enrich_application(db, app)
                if enriched:
                    output.append(enriched)
            return output

    async def update_application_status(
        self, application_id: str, status: str, notes: Optional[str] = None
    ) -> Optional[ApplicationResponse]:
        """更新投递状态"""
        async for db in get_db():
            app = await db.get(Application, application_id)
            if not app:
                return None

            # 验证状态流转
            current_status = app.status.value if hasattr(app.status, 'value') else str(app.status)
            if status in self.STATUS_FLOW.get(current_status, []):
                app.status = ApplicationStatus(status)
            else:
                # 允许直接跳转到某些状态
                app.status = ApplicationStatus(status)

            if notes:
                app.notes = notes
            if status == ApplicationStatus.APPLIED.value:
                app.applied_at = datetime.utcnow()
            if status in [ApplicationStatus.COMPLETED_APPLY.value, ApplicationStatus.JUMPED_APPLY.value]:
                app.submitted_time = datetime.utcnow()

            await db.commit()
            await db.refresh(app)
            return await self._enrich_application(db, app)

    async def _enrich_application(self, db, app) -> Optional[ApplicationResponse]:
        """附加岗位信息"""
        job_result = await db.execute(select(Job).where(Job.id == app.job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            return None

        app_dict = app.model_dump() if hasattr(app, 'model_dump') else {c.name: getattr(app, c.name) for c in app.__table__.columns}
        app_dict["job"] = {
            "id": job.id,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "salary_range": job.salary_range,
            "is_remote": job.is_remote,
            "is_foreign": job.is_foreign,
            "job_url": job.job_url,
            "apply_url": job.apply_url,
            "company_type": job.company_type,
            "tags": job.tags,
        }
        return ApplicationResponse(**app_dict)

    async def _generate_cover_letter(
        self,
        profile: Optional[ResumeProfile],
        job: Job,
        target_position: Optional[str],
        target_company: Optional[str],
    ) -> str:
        """生成 Cover Letter"""
        if not profile:
            return self._generate_default_cover_letter(job)

        # 提取关键信息
        skills = [s["name"] for s in (profile.skills or [])]
        exps = profile.experience or []
        edus = profile.education or []

        # 构建 Cover Letter
        parts = []

        # 开头
        parts.append("尊敬的" + str(job.company) + "招聘团队：")
        parts.append("您好！我对贵司的" + str(job.title) + "岗位非常感兴趣，特此申请。")

        # 教育背景
        if edus:
            edu = edus[0]
            parts.append("我毕业于" + str(edu.get('school', '')) + str(edu.get('degree', '')) + str(edu.get('major', '')) + "，具备扎实的专业基础。")

        # 实习经历
        if exps:
            parts.append("在实习期间，我参与了多个重要项目，积累了以下经验：")
            for exp in exps[:2]:
                parts.append("- 在" + str(exp.get('company', '')) + "担任" + str(exp.get('position', '')) + "，负责" + str(exp.get('description', '')))

        # 技能匹配
        job_skills = job.preferred_skills or []
        matched = [s for s in skills if s.lower() in ' '.join(job_skills).lower()]
        if matched:
            parts.append("我熟练掌握" + ', '.join(matched[:5]) + "等技术栈，与岗位要求高度匹配。")

        # 结尾
        parts.append("我相信我的技能和经验能够为" + str(job.company) + "创造价值，期待有机会进一步交流。")
        parts.append("感谢您的时间和考虑！")
        parts.append("此致")
        parts.append("敬礼")

        return "\n".join(parts)

    def _generate_default_cover_letter(self, job: Job) -> str:
        """生成默认 Cover Letter"""
        return f"""尊敬的{job.company}招聘团队：

您好！我对贵司的{job.title}岗位非常感兴趣，特此申请。

我具备相关的技术背景和项目经验，熟练掌握岗位要求的各项技能。相信我的能力能够为团队带来价值。

期待有机会进一步交流，感谢您的时间和考虑！

此致
敬礼"""

    def _extract_jd_keywords(self, job: Job) -> List[str]:
        """提取 JD 关键词"""
        keywords = []

        # 从 preferred_skills 提取
        if job.preferred_skills:
            keywords.extend(job.preferred_skills)

        # 从 requirements 提取
        if job.requirements:
            for req in job.requirements:
                # 提取关键技术词
                tech_patterns = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)*', req)
                keywords.extend(tech_patterns)

        # 从 description 提取
        if job.description:
            tech_patterns = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)*', job.description)
            keywords.extend(tech_patterns)

        # 去重
        return list(set(keywords))

    def _match_keywords(self, profile: ResumeProfile, keywords: List[str]) -> List[str]:
        """匹配关键词"""
        if not profile:
            return []

        profile_text = (profile.parsed_text or "").lower()
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}

        matched = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in profile_text or kw_lower in profile_skills:
                matched.append(kw)

        return matched

    async def _calc_match_score(self, profile: ResumeProfile, job: Job) -> float:
        """计算匹配度"""
        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}

        if not job_skills:
            return 50.0

        overlap = profile_skills & job_skills
        return round(len(overlap) / len(job_skills) * 100, 1)

    async def _recommend_resume_version(
        self, profile: Optional[ResumeProfile], job: Job, db
    ) -> Optional[str]:
        """推荐简历版本"""
        if not profile:
            return None

        # 获取该简历的所有版本
        result = await db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_profile_id == profile.id)
            .order_by(ResumeVersion.created_at.desc())
            .limit(3)
        )
        versions = result.scalars().all()

        if not versions:
            return None

        # 选择最新的优化版本或第一个版本
        for v in versions:
            if v.is_optimized:
                return v.id
        return versions[0].id

    async def _generate_suggested_edits(
        self, profile: Optional[ResumeProfile], job: Job, matched_keywords: List[str]
    ) -> List[dict]:
        """生成简历修改建议"""
        edits = []

        if not profile:
            return edits

        profile_skills = {s["name"].lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.preferred_skills or [])}
        missing = job_skills - profile_skills

        # 缺失技能建议
        if missing:
            edits.append({
                "section": "skills",
                "original": "当前技能列表",
                "suggestion": f"建议补充: {', '.join(list(missing)[:5])}",
                "reason": f"这些技能是岗位 JD 中明确要求的，补充后可提升匹配度",
                "priority": "high",
            })

        # 项目经历建议
        if profile.experience:
            for exp in profile.experience[:2]:
                edits.append({
                    "section": "experience",
                    "original": f"{exp.get('company', '')} - {exp.get('position', '')}",
                    "suggestion": "使用 STAR 法则重写，突出量化成果",
                    "reason": "HR 平均只看简历6秒，量化成果更能吸引注意",
                    "priority": "medium",
                })

        # 摘要建议
        if not profile.summary:
            edits.append({
                "section": "summary",
                "original": "无摘要",
                "suggestion": "根据目标岗位定制个人摘要",
                "reason": "定制化摘要可提升 ATS 系统匹配率",
                "priority": "medium",
            })

        return edits

    async def get_applications_for_job(self, job_id: str) -> List[dict]:
        """获取某岗位的所有投递记录"""
        async for db in get_db():
            result = await db.execute(
                select(Application).where(Application.job_id == job_id)
                .order_by(Application.created_at.desc())
            )
            apps = result.scalars().all()
            output = []
            for app in apps:
                enriched = await self._enrich_application(db, app)
                if enriched:
                    output.append(enriched)
            return output
