from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import resume, jobs, applications, interview, tracker, auth, resume_versions, career_preference, user, notifications, match, learning, application_events, target_jobs, gap_analysis, recommendation, company_research, job_ranking, job_source, career_goal, ai_agent, application_center, interview_coach, career_agent, job_filters
from app.core.config import get_settings
from app.db.database import init_db
from loguru import logger

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 求职助手 — 简历解析 · 岗位匹配 · 模拟面试 · 投递追踪",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["Interview"])
app.include_router(tracker.router, prefix="/api/v1/tracker", tags=["Tracker"])
app.include_router(resume_versions.router, prefix="/api/v1/resume-versions", tags=["ResumeVersions"])
app.include_router(career_preference.router, prefix="/api/v1/career-preference", tags=["CareerPreference"])
app.include_router(user.router, prefix="/api/v1/user", tags=["User"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(match.router, prefix="/api/v1/match", tags=["Match"])
app.include_router(learning.router, prefix="/api/v1/learning", tags=["Learning"])
app.include_router(application_events.router, prefix="/api/v1/application-events", tags=["ApplicationEvents"])
app.include_router(target_jobs.router, prefix="/api/v1/target-jobs", tags=["TargetJobs"])
app.include_router(gap_analysis.router, prefix="/api/v1/gap-analysis", tags=["GapAnalysis"])
app.include_router(recommendation.router, prefix="/api/v1/recommend", tags=["Recommendation"])
app.include_router(company_research.router, prefix="/api/v1/company", tags=["CompanyResearch"])
app.include_router(job_ranking.router, prefix="/api/v1/jobs/rank", tags=["JobRanking"])
app.include_router(job_source.router, prefix="/api/v1/jobs/source", tags=["JobSource"])
app.include_router(career_goal.router, prefix="/api/v1", tags=["CareerGoal"])
app.include_router(ai_agent.router, prefix="/api/v1", tags=["AICareerAgent"])
app.include_router(application_center.router, prefix="/api/v1/apply", tags=["ApplicationCenter"])
app.include_router(interview_coach.router, prefix="/api/v1/interview", tags=["InterviewCoach"])
app.include_router(career_agent.router, prefix="/api/v1/agent", tags=["CareerAgent"])
app.include_router(job_filters.router, prefix="/api/v1/jobs/filters", tags=["JobFilters"])


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("数据库初始化完成")


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
