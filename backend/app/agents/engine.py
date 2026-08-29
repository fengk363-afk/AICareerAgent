"""
Engine — 统一编排所有 Engine，提供端到端流程
"""
from loguru import logger

from app.agents.resume_engine import ResumeEngine
from app.agents.job_source_engine import JobSourceEngine
from app.agents.match_engine import MatchEngine
from app.agents.ai_analysis_engine import AIAnalysisEngine
from app.agents.resume_optimizer_agent import ResumeOptimizerAgent
from app.agents.interview_engine import InterviewEngine
from app.agents.application_engine import ApplicationEngine
from app.agents.notification_engine import NotificationEngine
from app.agents.learning_engine import LearningEngine
from app.agents.gap_analysis_engine import GapAnalysisEngine
from app.agents.target_job_engine import TargetJobEngine
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.company_research_engine import CompanyResearchEngine
from app.agents.job_ranking_engine import JobRankingEngine
from app.agents.job_source_adapters import ADAPTER_REGISTRY, get_adapter, list_adapters
import app.agents.job_source_guangdong  # 注册广东数据源适配器
from app.agents.job_sync_engine import JobSyncEngine
from app.agents.career_goal_engine import CareerGoalEngine
from app.agents.ai_career_agent_engine import AICareerAgentEngine
from app.agents.smart_application_engine import SmartApplicationEngine
from app.agents.interview_coach_engine import InterviewCoachEngine
from app.agents.career_agent_engine import CareerAgentEngine
from app.schemas.models import (
    MatchScoreResponse,
    ResumeOptimizationResponse,
    InterviewSessionResponse,
    ApplicationResponse,
)


class CareerEngine:
    """求职助手核心引擎，编排各 Engine 完成端到端流程"""

    def __init__(self):
        self.resume_engine = ResumeEngine()
        self.job_source_engine = JobSourceEngine()
        self.match_engine = MatchEngine()
        self.ai_analysis_engine = AIAnalysisEngine()
        self.resume_optimizer_agent = ResumeOptimizerAgent()
        self.interview_engine = InterviewEngine()
        self.application_engine = ApplicationEngine()
        self.notification_engine = NotificationEngine()
        self.learning_engine = LearningEngine()
        self.gap_analysis_engine = GapAnalysisEngine()
        self.target_job_engine = TargetJobEngine()
        self.recommendation_engine = RecommendationEngine()
        self.company_research_engine = CompanyResearchEngine()
        self.job_ranking_engine = JobRankingEngine()
        self.job_sync_engine = JobSyncEngine()
        self.career_goal_engine = CareerGoalEngine()
        self.ai_career_agent_engine = AICareerAgentEngine()
        self.smart_application_engine = SmartApplicationEngine()
        self.interview_coach_engine = InterviewCoachEngine()
        self.career_agent_engine = CareerAgentEngine()

    # ── 完整流程 ─────────────────────────────────────────────────

    async def full_pipeline(self, user_id: str, file_bytes: bytes, filename: str) -> dict:
        """端到端流程：上传简历 → 解析 → 画像 → 推荐岗位 → 匹配评分"""
        logger.info(f"[Pipeline] 开始处理用户 {user_id} 的简历: {filename}")

        profile = await self.resume_engine.parse_and_create(user_id, file_bytes, filename)
        jobs = await self.job_source_engine.search_jobs()
        jobs_list = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
        matches = []
        for job in jobs_list:
            match = await self.match_engine.calculate_match(profile.id, job.id)
            if match:
                matches.append(match)
        matches.sort(key=lambda x: x.overall_score, reverse=True)

        return {"profile": profile, "jobs": jobs, "matches": matches}

    # ── Resume ───────────────────────────────────────────────────

    async def upload_resume(self, user_id: str, file_bytes: bytes, filename: str):
        return await self.resume_engine.parse_and_create(user_id, file_bytes, filename)

    async def get_profile(self, profile_id: str):
        return await self.resume_engine.get_profile(profile_id)

    async def list_profiles(self, user_id: str):
        return await self.resume_engine.list_profiles(user_id)

    async def optimize_resume(self, resume_profile_id: str, job_id: str):
        return await self.resume_engine.optimize_for_job(resume_profile_id, job_id)

    # ── Jobs ─────────────────────────────────────────────────────

    async def get_jobs(self, limit: int = 50, offset: int = 0):
        result = await self.job_source_engine.search_jobs(limit=limit, offset=offset)
        if isinstance(result, list):
            return {"jobs": result, "total": len(result), "limit": limit, "offset": offset, "has_more": False}
        return result

    async def search_jobs(self, **kwargs):
        result = await self.job_source_engine.search_jobs(**kwargs)
        if isinstance(result, list):
            return {"jobs": result, "total": len(result), "limit": kwargs.get("limit", 50), "offset": kwargs.get("offset", 0), "has_more": False}
        return result

    async def seed_jobs(self):
        return await self.job_source_engine.seed_mock_jobs()

    async def get_job(self, job_id: str):
        return await self.job_source_engine.get_job(job_id)

    # ── Match ────────────────────────────────────────────────────

    async def get_match(self, profile_id: str, job_id: str):
        return await self.ai_analysis_engine.calculate_match(profile_id, job_id)

    async def get_ai_analysis(self, profile_id: str, job_id: str):
        return await self.ai_analysis_engine.calculate_match(profile_id, job_id)

    async def get_analysis_history(self, profile_id: str, job_id: str = None):
        return await self.ai_analysis_engine.get_analysis_history(profile_id, job_id)

    async def generate_learning_plan(self, profile_id: str, job_id: str, **kwargs):
        # 从 profile 和 job 提取技能信息
        from app.db.models import ResumeProfile, Job
        from app.db.database import get_db
        missing_skills = kwargs.get('missing_skills', [])
        existing_skills = kwargs.get('existing_skills', [])
        experience_summary = kwargs.get('experience_summary', '')

        async for db in get_db():
            profile = await db.get(ResumeProfile, profile_id)
            job = await db.get(Job, job_id)
            if not profile or not job:
                return None
            if not missing_skills:
                profile_skills = {s["name"] for s in (profile.skills or [])}
                job_skills = set(job.preferred_skills or [])
                missing_skills = list(job_skills - profile_skills)
            if not existing_skills:
                existing_skills = [s["name"] for s in (profile.skills or [])]
            if not experience_summary:
                exps = profile.experience or []
                experience_summary = f"拥有{len(exps)}段实习经历" if exps else ""
            return await self.learning_engine.generate_learning_plan(profile_id, job_id, missing_skills, existing_skills, experience_summary)

    async def get_learning_plans(self, profile_id: str):
        return await self.learning_engine.get_learning_plans(profile_id)

    # ── Interview ────────────────────────────────────────────────

    async def create_interview(self, user_id: str, job_id: str):
        return await self.interview_engine.create_session(user_id, job_id)

    async def submit_interview_answers(self, session_id: str, answers: list):
        return await self.interview_engine.submit_answers(session_id, answers)

    # ── Application ──────────────────────────────────────────────

    async def apply_job(self, user_id: str, job_id: str, resume_profile_id: str = None):
        return await self.application_engine.apply_job(user_id, job_id, resume_profile_id)

    async def get_applications(self, user_id: str):
        return await self.application_engine.get_user_applications(user_id)

    async def update_application_status(self, application_id: str, status: str, notes: str = None):
        return await self.application_engine.update_status(application_id, status, notes)

    async def save_job(self, user_id: str, job_id: str):
        return await self.application_engine.save_job(user_id, job_id)

    async def remove_saved_job(self, user_id: str, job_id: str):
        return await self.application_engine.remove_saved_job(user_id, job_id)

    async def get_saved_jobs(self, user_id: str):
        return await self.application_engine.get_saved_jobs(user_id)

    # ── Notification ─────────────────────────────────────────────

    async def get_notifications(self, user_id: str, limit: int = 20):
        return await self.notification_engine.get_user_notifications(user_id, limit)

    async def mark_notification_read(self, notification_id: str):
        return await self.notification_engine.mark_as_read(notification_id)

    async def mark_all_notifications_read(self, user_id: str):
        return await self.notification_engine.mark_all_read(user_id)

    async def check_notifications(self, user_id: str):
        return await self.notification_engine.check_and_notify(user_id)

    # ── Gap Analysis ─────────────────────────────────────────────

    async def analyze_gap(self, profile_id: str, job_id: str):
        return await self.gap_analysis_engine.analyze_gap(profile_id, job_id)

    async def get_gap_analysis(self, profile_id: str, job_id: str):
        return await self.gap_analysis_engine.get_gap_analysis(profile_id, job_id)

    # ── Target Jobs ──────────────────────────────────────────────

    async def add_target_job(self, user_id: str, job_id: str, priority: int = 0, notes: str = None):
        return await self.target_job_engine.add_target_job(user_id, job_id, priority, notes)

    async def remove_target_job(self, user_id: str, job_id: str):
        return await self.target_job_engine.remove_target_job(user_id, job_id)

    async def get_target_jobs(self, user_id: str):
        return await self.target_job_engine.get_target_jobs(user_id)

    async def get_target_job(self, user_id: str, job_id: str):
        return await self.target_job_engine.get_target_job(user_id, job_id)

    # ── Recommendation ───────────────────────────────────────────

    async def generate_recommendations(self, profile_id: str, user_id: str = "1", limit: int = 10):
        return await self.recommendation_engine.generate_recommendations(profile_id, user_id, limit)

    async def get_recommendations(self, profile_id: str):
        return await self.recommendation_engine.get_recommendations(profile_id)

    # ── Company Research ─────────────────────────────────────────

    async def get_company_profile(self, company_name: str):
        return await self.company_research_engine.get_or_create_company_profile(company_name)

    async def get_company_by_id(self, company_id: str):
        return await self.company_research_engine.get_company_profile(company_id)

    # ── Job Ranking ──────────────────────────────────────────────

    async def rank_jobs(self, profile_id: str, user_id: str = "1", limit: int = 20):
        return await self.job_ranking_engine.rank_jobs(profile_id, user_id, limit)

    async def get_rankings(self, profile_id: str):
        return await self.job_ranking_engine.get_rankings(profile_id)

    # ── Job Sync ─────────────────────────────────────────────────

    async def init_sources(self):
        return await self.job_sync_engine.init_sources()

    async def list_sources(self):
        return await self.job_sync_engine.list_sources()

    async def sync_jobs(self, source_name: str = None):
        return await self.job_sync_engine.sync_jobs(source_name)

    async def get_sync_history(self, limit: int = 20):
        return await self.job_sync_engine.get_sync_history(limit)

    # ── Job Source Adapters ──────────────────────────────────────

    async def list_adapters(self):
        return list_adapters()

    # ── Career Goal ──────────────────────────────────────────────

    async def create_goal(self, **kwargs):
        return await self.career_goal_engine.create_goal(**kwargs)

    async def get_goals(self, user_id: str):
        return await self.career_goal_engine.get_goals(user_id)

    async def get_goal(self, goal_id: str):
        return await self.career_goal_engine.get_goal(goal_id)

    async def update_goal(self, goal_id: str, **kwargs):
        return await self.career_goal_engine.update_goal(goal_id, **kwargs)

    async def delete_goal(self, goal_id: str):
        return await self.career_goal_engine.delete_goal(goal_id)

    async def create_target_company(self, **kwargs):
        return await self.career_goal_engine.create_target_company(**kwargs)

    async def get_target_companies(self, user_id: str):
        return await self.career_goal_engine.get_target_companies(user_id)

    async def delete_target_company(self, company_id: str):
        return await self.career_goal_engine.delete_target_company(company_id)

    async def get_or_create_preference(self, user_id: str):
        return await self.career_goal_engine.get_or_create_preference(user_id)

    async def update_preference(self, user_id: str, **kwargs):
        return await self.career_goal_engine.update_preference(user_id, **kwargs)

    async def get_or_create_progress(self, user_id: str):
        return await self.career_goal_engine.get_or_create_progress(user_id)

    async def update_progress(self, user_id: str, **kwargs):
        return await self.career_goal_engine.update_progress(user_id, **kwargs)

    # ── AI Career Agent ──────────────────────────────────────────

    async def get_daily_tasks(self, user_id: str):
        return await self.ai_career_agent_engine.get_daily_tasks(user_id)

    async def get_skill_recommendations(self, user_id: str):
        return await self.ai_career_agent_engine.get_skill_recommendations(user_id)

    async def get_application_plan(self, user_id: str):
        return await self.ai_career_agent_engine.get_application_plan(user_id)

    async def get_interview_plan(self, user_id: str):
        return await self.ai_career_agent_engine.get_interview_plan(user_id)

    # ── Smart Application ────────────────────────────────────────

    async def create_application(self, **kwargs):
        return await self.smart_application_engine.create_application(**kwargs)

    async def prepare_application(self, **kwargs):
        return await self.smart_application_engine.prepare_application(**kwargs)

    async def submit_application(self, **kwargs):
        return await self.smart_application_engine.submit_application(**kwargs)

    async def get_application_status(self, application_id: str):
        return await self.smart_application_engine.get_application_status(application_id)

    async def get_application_history(self, user_id: str):
        return await self.smart_application_engine.get_application_history(user_id)

    async def update_application_status(self, application_id: str, status: str, notes: str = None):
        return await self.smart_application_engine.update_application_status(application_id, status, notes)

    # ── Interview Coach ──────────────────────────────────────────

    async def generate_questions(self, job_id: str, question_types: list = None):
        return await self.interview_coach_engine.generate_questions(job_id, question_types)

    async def get_questions(self, job_id: str):
        return await self.interview_coach_engine.get_questions(job_id)

    async def create_interview_session(self, user_id: str, job_id: str):
        return await self.interview_coach_engine.create_session(user_id, job_id)

    async def submit_interview_answer(self, session_id: str, answer_data: dict):
        return await self.interview_coach_engine.submit_answer(session_id, answer_data)

    async def evaluate_interview_answer(self, answer_id: str):
        return await self.interview_coach_engine.evaluate_answer(answer_id)

    async def get_interview_session(self, session_id: str):
        return await self.interview_coach_engine.get_session(session_id)

    async def get_interview_history(self, user_id: str):
        return await self.interview_coach_engine.get_history(user_id)


# 全局引擎实例
engine = CareerEngine()
