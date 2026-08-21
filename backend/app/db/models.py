from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SAEnum, Boolean, UniqueConstraint, Float
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    PREPARING = "preparing"
    APPLIED = "applied"
    VIEWED_APPLY = "viewed_apply"
    SCREENING = "screening"
    WRITTEN_TEST = "written_test"
    INTERVIEW_INVITED = "interview_invited"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    COMPLETED_APPLY = "completed_apply"
    JUMPED_APPLY = "jumped_apply"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class JobSource(str, enum.Enum):
    MOCK = "mock"
    LIEPIN = "liepin"
    BOSS = "boss"
    LAGOU = "lagou"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    COMPANY = "company"
    GDRC = "gdrc"               # 广东人才网
    GD_PUBLIC = "gd_public"      # 广东公共招聘平台


class JobSourceType(str, enum.Enum):
    OFFICIAL = "official"      # 公司官方招聘页
    LINKEDIN = "linkedin"      # LinkedIn
    INDEED = "indeed"          # Indeed
    BOSS = "boss"              # Boss直聘
    LAGOU = "lagou"             # 拉勾
    LIEPIN = "liepin"           # 猎聘
    GLASSDOOR = "glassdoor"    # Glassdoor
    GDRC = "gdrc"              # 广东人才网（政府）
    GD_PUBLIC = "gd_public"    # 广东公共招聘平台（政府）


class JobSeason(str, enum.Enum):
    SPRING = "spring"    # 春招
    AUTUMN = "autumn"    # 秋招
    REGULAR = "regular"  # 日常招聘


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"
    PART_TIME = "part_time"


class CompanyType(str, enum.Enum):
    STATE_ENTERPRISE = "state_enterprise"
    PRIVATE = "private"
    FOREIGN = "foreign"
    STARTUP = "startup"
    GOVERNMENT = "government"


# ── User ──────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Resume Profile ────────────────────────────────────────────

class ResumeProfile(Base):
    __tablename__ = "resume_profiles"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    parsed_text = Column(Text, nullable=True)
    skills = Column(JSONB, nullable=True)
    experience = Column(JSONB, nullable=True)
    project_experience = Column(JSONB, nullable=True)
    education = Column(JSONB, nullable=True)
    certificates = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    strength_analysis = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Resume Version ────────────────────────────────────────────

class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    id = Column(String, primary_key=True, index=True)
    resume_profile_id = Column(String, ForeignKey("resume_profiles.id"), nullable=False, index=True)
    version_name = Column(String(100), nullable=False)
    original_filename = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_optimized = Column(Boolean, default=False)
    target_job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Career Preference ─────────────────────────────────────────

class CareerPreference(Base):
    __tablename__ = "career_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    target_industry = Column(String(100), nullable=True)
    target_role = Column(String(100), nullable=True)
    target_location = Column(String(200), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    preferred_companies = Column(JSONB, nullable=True)
    preferred_company_types = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Job ───────────────────────────────────────────────────────

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    source = Column(String, nullable=False, default="mock")
    source_name = Column(String(100), nullable=True)  # 数据源名称
    source_url = Column(Text, nullable=True)          # 数据源原始链接
    source_type = Column(String(50), nullable=True)   # 数据源类型
    source_job_id = Column(String, nullable=True)
    company = Column(String, nullable=False)
    company_type = Column(String, nullable=True)
    title = Column(String, nullable=False)
    location = Column(String, nullable=False)
    job_type = Column(String, nullable=False, default="full_time")
    salary_range = Column(JSONB, nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(JSONB, nullable=True)
    preferred_skills = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    is_remote = Column(Boolean, default=False)
    is_foreign = Column(Boolean, default=False)
    company_country = Column(String(100), nullable=True)  # 公司所在国家
    visa_support = Column(Boolean, default=False)          # 是否支持签证
    english_required = Column(Boolean, default=False)      # 是否要求英语
    graduate_program = Column(Boolean, default=False)      # 是否校招项目
    campus_recruitment = Column(Boolean, default=False)    # 是否校招
    season = Column(String(20), nullable=True)             # 春招/秋招/日常
    updated_time = Column(DateTime, nullable=True)         # 最后更新时间
    posted_at = Column(DateTime, nullable=True)
    apply_url = Column(Text, nullable=True)
    job_url = Column(Text, nullable=True)  # 岗位来源链接
    apply_source = Column(String, nullable=True)
    company_website = Column(String(255), nullable=True)
    application_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Application ───────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    resume_profile_id = Column(String, ForeignKey("resume_profiles.id"), nullable=True)
    resume_version_id = Column(String, ForeignKey("resume_versions.id"), nullable=True)
    status = Column(SAEnum(ApplicationStatus, values_callable=lambda x: [e.value for e in x]), default=ApplicationStatus.DRAFT)
    application_mode = Column(String(20), nullable=False, default="redirect")  # auto, semi_auto, redirect
    match_score = Column(Float, nullable=True)
    cover_letter = Column(Text, nullable=True)
    jd_keywords_matched = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    submitted_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Saved Job (Bookmark) ──────────────────────────────────────

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job"),)


# ── Target Job (用户主动选择的目标岗位) ───────────────────────

class TargetJob(Base):
    __tablename__ = "target_jobs"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    priority = Column(Integer, default=0)  # 优先级，越高越优先
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_target_job"),)


# ── Interview Session ─────────────────────────────────────────

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    status = Column(SAEnum(InterviewStatus, values_callable=lambda x: [e.value for e in x]), default=InterviewStatus.SCHEDULED)
    questions = Column(JSONB, nullable=True)
    user_answers = Column(JSONB, nullable=True)
    feedback = Column(JSONB, nullable=True)
    overall_score = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Notification ──────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # job_alert, interview_reminder, application_update
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── AI Analysis Record ────────────────────────────────────────

class AIAnalysisRecord(Base):
    __tablename__ = "ai_analysis_records"
    id = Column(String, primary_key=True, index=True)
    profile_id = Column(String, ForeignKey("resume_profiles.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    overall_score = Column(Float, nullable=True)
    skill_match = Column(Float, nullable=True)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)
    industry_match = Column(Float, nullable=True)
    strengths = Column(JSONB, nullable=True)
    weaknesses = Column(JSONB, nullable=True)
    gaps = Column(JSONB, nullable=True)
    suggestions = Column(JSONB, nullable=True)
    match_reason = Column(Text, nullable=True)
    is_llm = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Learning Plan ─────────────────────────────────────────────

class LearningPlan(Base):
    __tablename__ = "learning_plans"
    id = Column(String, primary_key=True, index=True)
    profile_id = Column(String, ForeignKey("resume_profiles.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    plan_data = Column(JSONB, nullable=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Application Event ─────────────────────────────────────────

class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    application_id = Column(String, ForeignKey("applications.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # view_apply, click_apply, jump_apply, complete_apply
    event_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Recommendation Record ─────────────────────────────────────

class RecommendationRecord(Base):
    __tablename__ = "recommendation_records"
    id = Column(String, primary_key=True, index=True)
    profile_id = Column(String, ForeignKey("resume_profiles.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    overall_score = Column(Float, nullable=True)
    match_score = Column(Float, nullable=True)
    potential_score = Column(Float, nullable=True)
    salary_score = Column(Float, nullable=True)
    company_type_score = Column(Float, nullable=True)
    skill_growth_score = Column(Float, nullable=True)
    competition_score = Column(Float, nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    advantages = Column(JSONB, nullable=True)
    risks = Column(JSONB, nullable=True)
    missing_skills = Column(JSONB, nullable=True)
    estimated_competition = Column(String, nullable=True)  # low, medium, high
    should_recommend = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("profile_id", "job_id", name="uq_profile_job_recommend"),)


# ── Company Profile ───────────────────────────────────────────

class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    id = Column(String, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False, index=True)
    company_type = Column(String(50), nullable=True)  # foreign, private, state_enterprise, startup
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)  # small, medium, large
    business_direction = Column(Text, nullable=True)
    hiring_trend = Column(String(100), nullable=True)  # growing, stable, shrinking
    interview_difficulty = Column(String(50), nullable=True)  # easy, medium, hard
    employee_reviews_summary = Column(Text, nullable=True)
    pros = Column(JSONB, nullable=True)
    cons = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("company_name", name="uq_company_name"),)


# ── Job Ranking ───────────────────────────────────────────────

class JobRanking(Base):
    __tablename__ = "job_rankings"
    id = Column(String, primary_key=True, index=True)
    profile_id = Column(String, ForeignKey("resume_profiles.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    overall_score = Column(Float, nullable=True)
    match_score = Column(Float, nullable=True)
    potential_score = Column(Float, nullable=True)
    salary_score = Column(Float, nullable=True)
    company_type_score = Column(Float, nullable=True)
    skill_growth_score = Column(Float, nullable=True)
    competition_score = Column(Float, nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    advantages = Column(JSONB, nullable=True)
    risks = Column(JSONB, nullable=True)
    missing_skills = Column(JSONB, nullable=True)
    estimated_competition = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("profile_id", "job_id", name="uq_profile_job_ranking"),)


# ── Job Source ────────────────────────────────────────────────

class JobSource(Base):
    __tablename__ = "job_sources"
    id = Column(String, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # official, linkedin, indeed, boss, lagou, liepin, glassdoor
    base_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    total_jobs = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Job Sync Record ───────────────────────────────────────────

class JobSyncRecord(Base):
    __tablename__ = "job_sync_records"
    id = Column(String, primary_key=True, index=True)
    source_id = Column(String, ForeignKey("job_sources.id"), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    sync_type = Column(String(20), nullable=False)  # full, incremental
    jobs_added = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    jobs_deleted = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Company Source ─────────────────────────────────────────────

class CompanySource(Base):
    __tablename__ = "company_sources"
    id = Column(String, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False, index=True)
    company_type = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    headquarters = Column(String(200), nullable=True)
    country = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    careers_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    glassdoor_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    hiring_status = Column(String(50), nullable=True)  # hiring, paused, frozen
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("company_name", name="uq_company_source_name"),)


# ── Career Goal ───────────────────────────────────────────────

class CareerGoal(Base):
    __tablename__ = "career_goals"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_position = Column(String(200), nullable=True)
    target_industry = Column(String(100), nullable=True)
    target_company = Column(String(200), nullable=True)
    target_country = Column(String(100), nullable=True)
    target_city = Column(String(100), nullable=True)
    salary_expectation_min = Column(Float, nullable=True)
    salary_expectation_max = Column(Float, nullable=True)
    company_type = Column(String(50), nullable=True)
    remote_preference = Column(String(50), nullable=True)  # remote, hybrid, on_site
    priority_level = Column(Integer, default=0)  # 0-10
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # active, achieved, paused
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Target Company ────────────────────────────────────────────

class TargetCompany(Base):
    __tablename__ = "target_companies"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    company_type = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    target_position = Column(String(200), nullable=True)
    priority = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # active, contacted, applied, offer, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "company_name", name="uq_user_company"),)


# ── User Job Preference ───────────────────────────────────────

class UserJobPreference(Base):
    __tablename__ = "user_job_preferences"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    preferred_locations = Column(JSONB, nullable=True)
    preferred_companies = Column(JSONB, nullable=True)
    preferred_company_types = Column(JSONB, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    is_remote_wanted = Column(Boolean, default=False)
    is_foreign_wanted = Column(Boolean, default=False)
    visa_support_wanted = Column(Boolean, default=False)
    campus_recruitment_wanted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_preference"),)


# ── Career Progress ───────────────────────────────────────────

class CareerProgress(Base):
    __tablename__ = "career_progress"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    career_goal_id = Column(String, ForeignKey("career_goals.id"), nullable=True, index=True)
    skill_progress = Column(JSONB, nullable=True)  # {skill_name: level}
    application_count = Column(Integer, default=0)
    interview_count = Column(Integer, default=0)
    offer_count = Column(Integer, default=0)
    completed_skills = Column(JSONB, nullable=True)
    milestones = Column(JSONB, nullable=True)  # [{title, completed, completed_at}]
    progress_percentage = Column(Float, default=0.0)
    last_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Interview Question ────────────────────────────────────────

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    company = Column(String(200), nullable=True)
    question_type = Column(String(50), nullable=False)  # technical, hr, behavioral, english, situational
    question = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=True)  # easy, medium, hard
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Interview Answer ──────────────────────────────────────────

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(String, ForeignKey("interview_questions.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=True)
    answer = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(JSONB, nullable=True)
    star_optimized = Column(JSONB, nullable=True)  # STAR优化后的回答
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Interview Feedback ────────────────────────────────────────

class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"
    id = Column(String, primary_key=True, index=True)
    answer_id = Column(String, ForeignKey("interview_answers.id"), nullable=False, index=True)
    question_index = Column(Integer, nullable=True)
    score = Column(Float, nullable=True)
    strengths = Column(JSONB, nullable=True)
    improvements = Column(JSONB, nullable=True)
    suggested_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Career Message (Chat History) ─────────────────────────────

class CareerMessage(Base):
    __tablename__ = "career_messages"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String, nullable=True, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    context_type = Column(String(50), nullable=True)  # resume, job, interview, career
    context_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Career Insight ────────────────────────────────────────────

class CareerInsight(Base):
    __tablename__ = "career_insights"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    insight_type = Column(String(50), nullable=False)  # recommendation, warning, tip, achievement
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    related_job_id = Column(String, nullable=True)
    related_goal_id = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Learning Task ─────────────────────────────────────────────

class LearningTask(Base):
    __tablename__ = "learning_tasks"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(String, nullable=True)
    job_id = Column(String, nullable=True)
    skill_name = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)  # learn, practice, project, review
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    estimated_hours = Column(Float, default=1.0)
    completed_hours = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    priority = Column(Integer, default=0)
    due_date = Column(DateTime, nullable=True)
    resources = Column(JSONB, nullable=True)  # [{"type": "video", "url": "..."}]
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Notification (Enhanced) ───────────────────────────────────
