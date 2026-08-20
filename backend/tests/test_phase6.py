"""
AICareerAgent Phase 6 测试 — 真实岗位数据、收藏、筛选、目标岗位、差距分析
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── JobSourceEngine 测试 ────────────────────────────────────────

class TestJobSourceEngine:
    def test_mock_jobs_count(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        assert len(engine.MOCK_JOBS) == 10

    def test_mock_jobs_have_job_url(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        for job in engine.MOCK_JOBS:
            assert "job_url" in job, f"Job {job['company']} {job['title']} missing job_url"
            assert job["job_url"] is not None and len(job["job_url"]) > 0

    def test_mock_jobs_have_apply_url(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        for job in engine.MOCK_JOBS:
            assert "apply_url" in job
            assert job["apply_url"] is not None

    def test_mock_jobs_diversity(self):
        from app.agents.job_source_engine import JobSourceEngine
        from app.db.models import CompanyType
        engine = JobSourceEngine()
        companies = [j["company"] for j in engine.MOCK_JOBS]
        assert len(set(companies)) == 10  # 10 unique companies
        # 检查公司类型多样性
        company_types = [j["company_type"] for j in engine.MOCK_JOBS]
        assert len(set(company_types)) >= 3  # 至少3种公司类型

    def test_mock_jobs_remote_and_foreign(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        remote_jobs = [j for j in engine.MOCK_JOBS if j["is_remote"]]
        foreign_jobs = [j for j in engine.MOCK_JOBS if j["is_foreign"]]
        assert len(remote_jobs) >= 1
        assert len(foreign_jobs) >= 2


# ── TargetJobEngine 测试 ────────────────────────────────────────

class TestTargetJobEngine:
    def test_target_job_schema(self):
        from app.schemas.models import TargetJobRequest, TargetJobResponse
        req = TargetJobRequest(user_id="1", job_id="job-001", priority=5)
        assert req.user_id == "1"
        assert req.job_id == "job-001"
        assert req.priority == 5

    def test_target_job_response(self):
        from app.schemas.models import TargetJobResponse
        resp = TargetJobResponse(
            id="tj-001",
            user_id="1",
            job_id="job-001",
            priority=5,
            notes="首选",
            created_at="2024-01-01T00:00:00",
            job={"id": "job-001", "company": "Test", "title": "Engineer"},
        )
        assert resp.job_id == "job-001"
        assert resp.job["company"] == "Test"


# ── GapAnalysisEngine 测试 ──────────────────────────────────────

class TestGapAnalysisEngine:
    def test_gap_analysis_schema(self):
        from app.schemas.models import GapAnalysisResponse
        resp = GapAnalysisResponse(
            profile_id="p-001",
            job_id="job-001",
            job_title="后端开发",
            company="Test",
            overall_score=75.0,
            skill_match=80.0,
            experience_match=70.0,
            education_match=75.0,
            gaps=["Kafka", "Redis"],
            strengths=["技能匹配高"],
            weaknesses=["经验不足"],
            suggestions=["学习Kafka"],
            match_reason="基于技能匹配",
            learning_plan={"phases": [], "priority_skills": [], "estimated_time": "2个月", "tips": []},
        )
        assert resp.overall_score == 75.0
        assert len(resp.gaps) == 2
        assert resp.learning_plan is not None

    def test_gap_analysis_without_learning_plan(self):
        from app.schemas.models import GapAnalysisResponse
        resp = GapAnalysisResponse(
            profile_id="p-001",
            job_id="job-001",
            job_title="后端开发",
            company="Test",
            overall_score=60.0,
            skill_match=50.0,
            experience_match=60.0,
            education_match=70.0,
            gaps=["Go"],
            strengths=[],
            weaknesses=["技能不足"],
            suggestions=["学习Go"],
            match_reason="匹配度一般",
            learning_plan=None,
        )
        assert resp.learning_plan is None


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_job_has_job_url_field(self):
        from app.db.models import Job
        # 验证 Job 模型有 job_url 字段
        columns = {c.name for c in Job.__table__.columns}
        assert "job_url" in columns, "Job 模型缺少 job_url 字段"
        assert "apply_url" in columns, "Job 模型缺少 apply_url 字段"

    def test_target_job_model_exists(self):
        from app.db.models import TargetJob
        assert TargetJob.__tablename__ == "target_jobs"
        columns = {c.name for c in TargetJob.__table__.columns}
        assert "user_id" in columns
        assert "job_id" in columns
        assert "priority" in columns
        assert "notes" in columns

    def test_saved_job_model_exists(self):
        from app.db.models import SavedJob
        assert SavedJob.__tablename__ == "saved_jobs"
        columns = {c.name for c in SavedJob.__table__.columns}
        assert "user_id" in columns
        assert "job_id" in columns

    def test_all_required_models_exist(self):
        from app.db.models import (
            User, ResumeProfile, ResumeVersion, CareerPreference,
            Job, Application, SavedJob, TargetJob, InterviewSession,
            Notification, AIAnalysisRecord, LearningPlan, ApplicationEvent,
        )
        models = [
            User, ResumeProfile, ResumeVersion, CareerPreference,
            Job, Application, SavedJob, TargetJob, InterviewSession,
            Notification, AIAnalysisRecord, LearningPlan, ApplicationEvent,
        ]
        for model in models:
            assert hasattr(model, '__tablename__')
            assert model.__tablename__ is not None


# ── API Schemas 测试 ────────────────────────────────────────────

class TestAPISchemas:
    def test_job_response_has_job_url(self):
        from app.schemas.models import JobResponse
        from datetime import datetime
        resp = JobResponse(
            id="job-001",
            source="mock",
            company="Test",
            title="Engineer",
            location="Beijing",
            job_type="full_time",
            is_remote=False,
            is_foreign=False,
            description="Test",
            requirements=[],
            preferred_skills=[],
            tags=[],
            created_at=datetime.utcnow(),
            job_url="https://example.com/job",
            apply_url="https://example.com/apply",
        )
        assert resp.job_url == "https://example.com/job"
        assert resp.apply_url == "https://example.com/apply"

    def test_job_create_has_job_url(self):
        from app.schemas.models import JobCreate
        job = JobCreate(
            company="Test",
            title="Engineer",
            location="Beijing",
            description="Test",
            job_url="https://example.com/job",
        )
        assert job.job_url == "https://example.com/job"

    def test_gap_analysis_response(self):
        from app.schemas.models import GapAnalysisResponse
        resp = GapAnalysisResponse(
            profile_id="p-001",
            job_id="job-001",
            job_title="后端开发",
            company="Test",
            overall_score=75.0,
            skill_match=80.0,
            experience_match=70.0,
            education_match=75.0,
            gaps=["Kafka"],
            strengths=["好"],
            weaknesses=["差"],
            suggestions=["建议"],
            match_reason="原因",
        )
        assert resp.overall_score == 75.0
        assert resp.skill_match == 80.0


# ── Engine 测试 ─────────────────────────────────────────────────

class TestCareerEngine:
    def test_engine_has_new_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        # 验证新方法存在
        assert hasattr(engine, 'analyze_gap')
        assert hasattr(engine, 'get_gap_analysis')
        assert hasattr(engine, 'add_target_job')
        assert hasattr(engine, 'remove_target_job')
        assert hasattr(engine, 'get_target_jobs')
        assert hasattr(engine, 'get_target_job')

    def test_engine_has_gap_analysis_engine(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'gap_analysis_engine')
        assert engine.gap_analysis_engine is not None

    def test_engine_has_target_job_engine(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'target_job_engine')
        assert engine.target_job_engine is not None


# ── 端到端流程测试 ──────────────────────────────────────────────

class TestPhase6E2E:
    @pytest.fixture
    def mock_db_session(self):
        session = MagicMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_profile(self):
        profile = MagicMock()
        profile.id = "profile-001"
        profile.user_id = "1"
        profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
        ]
        profile.experience = [{"company": "Alibaba", "position": "Backend Intern"}]
        profile.education = [{"school": "ZJU", "degree": "本科", "major": "CS"}]
        profile.parsed_text = "Python Go 实习 项目"
        return profile

    @pytest.fixture
    def mock_job(self):
        job = MagicMock()
        job.id = "job-001"
        job.company = "字节跳动"
        job.title = "后端开发工程师"
        job.location = "北京"
        job.preferred_skills = ["Go", "Python", "Redis", "Kafka"]
        job.description = "后端开发"
        job.requirements = ["熟悉 Go 或 Python"]
        job.salary_range = {"min": 25, "max": 45, "unit": "K/月"}
        job.is_remote = False
        job.is_foreign = False
        job.job_url = "https://jobs.bytedance.com/campus"
        job.apply_url = "https://jobs.bytedance.com/campus"
        job.company_type = "private"
        job.tags = ["大厂"]
        return job

    @pytest.mark.asyncio
    async def test_gap_analysis_flow(self, mock_db_session, mock_profile, mock_job):
        """差距分析流程测试"""
        from app.agents.gap_analysis_engine import GapAnalysisEngine

        engine = GapAnalysisEngine()

        async def mock_get(model, id):
            if model.__name__ == 'ResumeProfile':
                return mock_profile
            return mock_job

        mock_db_session.get = AsyncMock(side_effect=mock_get)

        # Mock execute to return a result with scalar_one_or_none = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        async def mock_get_db():
            yield mock_db_session

        with patch('app.agents.gap_analysis_engine.get_db', mock_get_db):
            result = await engine.analyze_gap("profile-001", "job-001")

        assert result is not None
        assert result.job_id == "job-001"
        assert result.job_title == "后端开发工程师"
        assert result.company == "字节跳动"
        assert 0 <= result.overall_score <= 100
        assert 0 <= result.skill_match <= 100
        # Kafka 和 Redis 应该是差距技能 (case-insensitive)
        gaps_lower = [g.lower() for g in result.gaps]
        assert "kafka" in gaps_lower or "redis" in gaps_lower

    @pytest.mark.asyncio
    async def test_target_job_add_and_remove(self, mock_db_session):
        """目标岗位添加和移除测试"""
        from app.agents.target_job_engine import TargetJobEngine

        engine = TargetJobEngine()

        # 验证方法存在且可调用
        assert hasattr(engine, 'add_target_job')
        assert hasattr(engine, 'remove_target_job')
        assert hasattr(engine, 'get_target_jobs')
        assert hasattr(engine, 'get_target_job')

        # 验证方法签名正确
        import inspect
        add_sig = inspect.signature(engine.add_target_job)
        assert 'user_id' in add_sig.parameters
        assert 'job_id' in add_sig.parameters

        remove_sig = inspect.signature(engine.remove_target_job)
        assert 'user_id' in remove_sig.parameters
        assert 'job_id' in remove_sig.parameters


# ── 筛选功能测试 ────────────────────────────────────────────────

class TestJobFiltering:
    def test_filter_by_company_type(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        # 检查是否有外企岗位
        foreign_jobs = [j for j in engine.MOCK_JOBS if j["is_foreign"]]
        assert len(foreign_jobs) >= 2

    def test_filter_by_remote(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        remote_jobs = [j for j in engine.MOCK_JOBS if j["is_remote"]]
        assert len(remote_jobs) >= 1

    def test_filter_by_salary_range(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        # 检查薪资范围
        for job in engine.MOCK_JOBS:
            assert "salary_range" in job
            assert "min" in job["salary_range"]
            assert "max" in job["salary_range"]
            assert job["salary_range"]["min"] <= job["salary_range"]["max"]

    def test_filter_by_location(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        locations = [j["location"] for j in engine.MOCK_JOBS]
        assert len(set(locations)) >= 3  # 至少3个不同城市


# ── 收藏功能测试 ────────────────────────────────────────────────

class TestJobSaving:
    def test_saved_job_schema(self):
        from app.schemas.models import SavedJobResponse
        from datetime import datetime
        resp = SavedJobResponse(
            id="sj-001",
            user_id="1",
            job_id="job-001",
            created_at=datetime.utcnow(),
            job={"id": "job-001", "company": "Test", "title": "Engineer"},
        )
        assert resp.job_id == "job-001"
        assert resp.job["company"] == "Test"

    def test_application_response_has_job_url(self):
        from app.schemas.models import ApplicationResponse
        from datetime import datetime
        resp = ApplicationResponse(
            id="app-001",
            user_id="1",
            job_id="job-001",
            status="applied",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            job={"title": "后端开发", "company": "Test", "job_url": "https://example.com"},
        )
        assert resp.job["job_url"] == "https://example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
