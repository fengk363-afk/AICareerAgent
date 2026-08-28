import json
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class InterviewStatus(str):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ApplicationStatus(str):
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    WRITTEN_TEST = "written_test"
    INTERVIEW_INVITED = "interview_invited"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    VIEWED_APPLY = "viewed_apply"
    PREPARING = "preparing"
    JUMPED_APPLY = "jumped_apply"
    COMPLETED_APPLY = "completed_apply"


class SkillItem(BaseModel):
    name: str
    description: str = ""
    level: str = "intermediate"
    category: str = "technical_skills"  # technical_skills, business_skills, tools_skills, content_skills


class EducationItem(BaseModel):
    school: str
    degree: str
    major: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class ExperienceItem(BaseModel):
    company: str
    position: str
    employment_type: str = "full_time"  # full_time, internship, contract, part_time
    start_date: str
    end_date: Optional[str] = None
    description: str


class ProjectExperienceItem(BaseModel):
    project_name: str
    date: str
    role: str
    description: str
    achievement: str = ""
    technologies: str = ""


class CertificateItem(BaseModel):
    name: str
    issuing_organization: str = ""
    issue_date: str = ""
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class ResumeProfileCreate(BaseModel):
    user_id: int
    original_filename: str
    parsed_text: Optional[str] = None
    skills: Optional[list] = None
    experience: Optional[list] = None
    project_experience: Optional[list] = None
    education: Optional[list] = None
    certificates: Optional[list] = None
    summary: Optional[str] = None


class ResumeProfileResponse(ResumeProfileCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    strength_analysis: Optional[list] = None
    file_path: Optional[str] = None

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    source: str = "mock"
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    source_job_id: Optional[str] = None
    company: str
    company_type: Optional[str] = None
    title: str
    location: str
    job_type: str = "full_time"
    salary_range: Optional[dict] = None
    description: str
    requirements: Optional[list] = None
    preferred_skills: Optional[list] = None
    tags: Optional[list] = None
    is_remote: bool = False
    is_foreign: bool = False
    apply_url: Optional[str] = None
    job_url: Optional[str] = None  # 岗位来源链接
    apply_source: Optional[str] = None
    company_website: Optional[str] = None
    application_method: Optional[str] = None
    status: Optional[str] = "active"
    last_seen_at: Optional[datetime] = None
    status_changed_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None


class JobResponse(BaseModel):
    id: str
    source: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    source_job_id: Optional[str] = None
    company: str
    company_type: Optional[str] = None
    company_country: Optional[str] = None
    title: str
    location: str
    locations: Optional[List[str]] = None  # 标准化地点列表
    job_type: str
    salary_range: Optional[dict] = None
    description: str
    requirements: Optional[list] = None
    preferred_skills: Optional[list] = None
    tags: Optional[list] = None
    is_remote: bool
    is_foreign: bool
    visa_support: bool
    english_required: bool
    graduate_program: bool
    campus_recruitment: bool
    season: Optional[str] = None
    industry: Optional[str] = None  # 行业
    job_category: Optional[str] = None  # 岗位分类
    updated_time: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    apply_url: Optional[str] = None
    job_url: Optional[str] = None
    apply_source: Optional[str] = None
    company_website: Optional[str] = None
    application_method: Optional[str] = None
    created_at: datetime
    status: Optional[str] = "active"  # active/closed/expired/removed/unknown
    last_seen_at: Optional[datetime] = None
    status_changed_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchScoreResponse(BaseModel):
    job_id: str
    job_title: str
    company: str
    overall_score: float
    skill_match: float
    experience_match: float
    education_match: float
    industry_match: Optional[float] = None
    gaps: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    match_reason: Optional[str] = None


class ApplicationCreate(BaseModel):
    user_id: str
    job_id: str
    resume_profile_id: Optional[str] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    resume_profile_id: Optional[str] = None
    status: str
    match_score: Optional[float] = None
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    applied_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    job: Optional[dict] = None

    class Config:
        from_attributes = True


class ResumeOptimizationRequest(BaseModel):
    resume_profile_id: str
    job_id: str


class ResumeOptimizationResponse(BaseModel):
    resume_profile_id: str
    job_id: str
    optimized_summary: str
    optimized_skills: List[str]
    suggested_edits: List[dict]
    improvement_score: float
    missing_skills: Optional[List[str]] = None
    version_id: Optional[str] = None


class InterviewSessionCreate(BaseModel):
    user_id: str
    job_id: str


class InterviewQuestion(BaseModel):
    question: str
    category: str
    difficulty: str


class UserAnswer(BaseModel):
    question_index: int
    answer: str


class InterviewFeedback(BaseModel):
    question_index: int
    score: float
    strengths: List[str]
    improvements: List[str]
    suggested_answer: str


class InterviewSessionResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    status: str
    questions: Optional[List[dict]] = None
    user_answers: Optional[List[dict]] = None
    feedback: Optional[List[dict]] = None
    overall_score: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AIAnalysisRecordResponse(BaseModel):
    id: str
    profile_id: str
    job_id: str
    overall_score: float
    skill_match: float
    experience_match: float
    education_match: float
    industry_match: Optional[float] = None
    strengths: List[str]
    weaknesses: List[str]
    gaps: List[str]
    suggestions: List[str]
    match_reason: Optional[str] = None
    is_llm: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LearningPlanResponse(BaseModel):
    id: str
    profile_id: str
    job_id: str
    job_title: str
    company: str
    phases: List[dict]
    priority_skills: List[str]
    estimated_time: str
    tips: List[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SavedJobResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    created_at: datetime
    job: Optional[dict] = None

    class Config:
        from_attributes = True


class TargetJobRequest(BaseModel):
    user_id: str
    job_id: str
    priority: int = 0  # 优先级，越高越优先
    notes: Optional[str] = None


class TargetJobResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    priority: int
    notes: Optional[str] = None
    created_at: datetime
    job: Optional[dict] = None

    class Config:
        from_attributes = True


class GapAnalysisResponse(BaseModel):
    profile_id: str
    job_id: str
    job_title: str
    company: str
    overall_score: float
    skill_match: float
    experience_match: float
    education_match: float
    gaps: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    match_reason: str
    learning_plan: Optional[dict] = None

    class Config:
        from_attributes = True


# ── Phase 7: Recommendation & Company Research ────────────────

class RecommendationResponse(BaseModel):
    id: str
    profile_id: str
    job_id: str
    overall_score: float
    match_score: float
    potential_score: float
    salary_score: float
    company_type_score: float
    skill_growth_score: float
    competition_score: float
    recommendation_reason: str
    advantages: List[str]
    risks: List[str]
    missing_skills: List[str]
    estimated_competition: str
    should_recommend: bool
    job: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyProfileResponse(BaseModel):
    id: str
    company_name: str
    company_type: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    business_direction: Optional[str] = None
    hiring_trend: Optional[str] = None
    interview_difficulty: Optional[str] = None
    employee_reviews_summary: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobRankingResponse(BaseModel):
    id: str
    profile_id: str
    job_id: str
    rank: int
    overall_score: float
    match_score: float
    potential_score: float
    salary_score: float
    company_type_score: float
    skill_growth_score: float
    competition_score: float
    recommendation_reason: str
    advantages: List[str]
    risks: List[str]
    missing_skills: List[str]
    estimated_competition: str
    job: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRecommendationRequest(BaseModel):
    profile_id: str
    user_id: Optional[str] = None
    limit: int = 10


# ── Phase 8: Job Source & Sync ────────────────────────────────

class JobSourceResponse(BaseModel):
    id: str
    source_name: str
    source_type: str
    base_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    last_sync_at: Optional[datetime] = None
    total_jobs: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobSyncRecordResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    sync_type: str
    jobs_added: int
    jobs_updated: int
    jobs_deleted: int
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanySourceResponse(BaseModel):
    id: str
    company_name: str
    company_type: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    careers_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    glassdoor_url: Optional[str] = None
    description: Optional[str] = None
    hiring_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdvancedJobSearchRequest(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None
    company_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    is_foreign: Optional[bool] = None
    is_remote: Optional[bool] = None
    visa_support: Optional[bool] = None
    english_required: Optional[bool] = None
    graduate_program: Optional[bool] = None
    campus_recruitment: Optional[bool] = None
    season: Optional[str] = None
    source_type: Optional[str] = None
    company_country: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 20
    offset: int = 0


class SyncJobsRequest(BaseModel):
    source_name: Optional[str] = None


# ── Phase Application Center ──────────────────────────────────

class ApplicationCreateRequest(BaseModel):
    user_id: str
    job_id: str
    resume_profile_id: Optional[str] = None
    resume_version_id: Optional[str] = None
    application_mode: str = "redirect"  # auto, semi_auto, redirect
    notes: Optional[str] = None


class ApplicationPrepareRequest(BaseModel):
    user_id: str
    job_id: str
    resume_profile_id: Optional[str] = None
    target_position: Optional[str] = None
    target_company: Optional[str] = None


class ApplicationPrepareResponse(BaseModel):
    application_id: str
    job_id: str
    job_title: str
    company: str
    cover_letter: str
    recommended_resume_version: Optional[str] = None
    jd_keywords_matched: List[str]
    match_score: float
    suggested_edits: List[dict]
    status: str


class ApplicationSubmitRequest(BaseModel):
    user_id: str
    job_id: str
    application_id: str
    cover_letter: Optional[str] = None
    resume_version_id: Optional[str] = None


class ApplicationStatusResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    resume_profile_id: Optional[str] = None
    resume_version_id: Optional[str] = None
    status: str
    application_mode: str
    match_score: Optional[float] = None
    cover_letter: Optional[str] = None
    jd_keywords_matched: Optional[List[str]] = None
    notes: Optional[str] = None
    applied_at: Optional[str] = None
    submitted_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    job: Optional[dict] = None

    class Config:
        from_attributes = True


class ApplicationHistoryResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    resume_profile_id: Optional[str] = None
    resume_version_id: Optional[str] = None
    status: str
    application_mode: str
    match_score: Optional[float] = None
    cover_letter: Optional[str] = None
    jd_keywords_matched: Optional[List[str]] = None
    notes: Optional[str] = None
    applied_at: Optional[str] = None
    submitted_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    job: Optional[dict] = None

    class Config:
        from_attributes = True
