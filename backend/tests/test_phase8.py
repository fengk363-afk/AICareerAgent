"""
AICareerAgent Phase 8 测试 — 岗位数据源、同步、高级搜索
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── JobSourceAdapters 测试 ─────────────────────────────────────

class TestJobSourceAdapters:
    def test_adapter_registry(self):
        from app.agents.job_source_adapters import ADAPTER_REGISTRY, list_adapters
        assert len(ADAPTER_REGISTRY) >= 7
        adapters = list_adapters()
        assert len(adapters) >= 7
        for adapter in adapters:
            assert "source_name" in adapter
            assert "source_type" in adapter
            assert "base_url" in adapter

    def test_all_adapters_exist(self):
        from app.agents.job_source_adapters import (
            CompanyOfficialSource, LinkedInSource, IndeedSource,
            BossSource, LagouSource, LiepinSource, GlassdoorSource,
        )
        adapters = [
            CompanyOfficialSource, LinkedInSource, IndeedSource,
            BossSource, LagouSource, LiepinSource, GlassdoorSource,
        ]
        for adapter_cls in adapters:
            adapter = adapter_cls()
            assert adapter.source_name
            assert adapter.source_type
            assert adapter.base_url

    def test_get_adapter(self):
        from app.agents.job_source_adapters import get_adapter
        adapter = get_adapter("linkedin")
        assert adapter is not None
        assert adapter.source_name == "linkedin"

        adapter = get_adapter("nonexistent")
        assert adapter is None


# ── JobSourceEngine 测试 ───────────────────────────────────────

class TestJobSourceEngine:
    def test_mock_jobs_have_new_fields(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        for job in engine.MOCK_JOBS:
            assert "source_name" in job
            assert "source_type" in job
            assert "source_url" in job
            assert "company_country" in job
            assert "visa_support" in job
            assert "english_required" in job
            assert "graduate_program" in job
            assert "campus_recruitment" in job
            assert "season" in job

    def test_mock_jobs_tags(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        all_tags = set()
        for job in engine.MOCK_JOBS:
            tags = job.get("tags", [])
            all_tags.update(tags)
        # 检查标签覆盖
        assert "校招" in all_tags or "秋招" in all_tags
        assert "外企" in all_tags or "远程" in all_tags

    def test_mock_jobs_diversity(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        # 检查来源多样性
        sources = [j["source_name"] for j in engine.MOCK_JOBS]
        assert len(set(sources)) >= 4  # 至少4种不同来源

        # 检查季节多样性
        seasons = [j["season"] for j in engine.MOCK_JOBS]
        assert len(set(seasons)) >= 2

        # 检查校招/日常
        campus_jobs = [j for j in engine.MOCK_JOBS if j["campus_recruitment"]]
        regular_jobs = [j for j in engine.MOCK_JOBS if not j["campus_recruitment"]]
        assert len(campus_jobs) >= 5
        assert len(regular_jobs) >= 1


# ── JobSyncEngine 测试 ─────────────────────────────────────────

class TestJobSyncEngine:
    def test_engine_has_sync_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'job_sync_engine')
        assert hasattr(engine, 'init_sources')
        assert hasattr(engine, 'list_sources')
        assert hasattr(engine, 'sync_jobs')
        assert hasattr(engine, 'get_sync_history')
        assert hasattr(engine, 'list_adapters')

    def test_default_sources_configured(self):
        from app.agents.job_sync_engine import JobSyncEngine
        engine = JobSyncEngine()
        assert len(engine.DEFAULT_SOURCES) >= 7
        source_names = {s["source_name"] for s in engine.DEFAULT_SOURCES}
        expected = {"company", "linkedin", "indeed", "boss", "lagou", "liepin", "glassdoor"}
        assert expected.issubset(source_names)


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_job_has_new_fields(self):
        from app.db.models import Job
        columns = {c.name for c in Job.__table__.columns}
        new_fields = [
            "source_name", "source_url", "source_type",
            "company_country", "visa_support", "english_required",
            "graduate_program", "campus_recruitment", "updated_time",
        ]
        for field in new_fields:
            assert field in columns, f"Job 模型缺少字段: {field}"

    def test_job_source_model(self):
        from app.db.models import JobSource
        assert JobSource.__tablename__ == "job_sources"
        columns = {c.name for c in JobSource.__table__.columns}
        assert "source_name" in columns
        assert "source_type" in columns
        assert "base_url" in columns
        assert "is_active" in columns
        assert "last_sync_at" in columns

    def test_job_sync_record_model(self):
        from app.db.models import JobSyncRecord
        assert JobSyncRecord.__tablename__ == "job_sync_records"
        columns = {c.name for c in JobSyncRecord.__table__.columns}
        assert "source_id" in columns
        assert "sync_type" in columns
        assert "jobs_added" in columns
        assert "status" in columns

    def test_company_source_model(self):
        from app.db.models import CompanySource
        assert CompanySource.__tablename__ == "company_sources"
        columns = {c.name for c in CompanySource.__table__.columns}
        assert "company_name" in columns
        assert "careers_url" in columns
        assert "linkedin_url" in columns
        assert "hiring_status" in columns


# ── API Schemas 测试 ────────────────────────────────────────────

class TestAPISchemas:
    def test_job_source_response(self):
        from app.schemas.models import JobSourceResponse
        from datetime import datetime
        resp = JobSourceResponse(
            id="src-001",
            source_name="linkedin",
            source_type="linkedin",
            base_url="https://linkedin.com/jobs",
            description="LinkedIn 招聘",
            is_active=True,
            last_sync_at=datetime.utcnow(),
            total_jobs=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert resp.source_name == "linkedin"
        assert resp.is_active is True

    def test_job_sync_record_response(self):
        from app.schemas.models import JobSyncRecordResponse
        from datetime import datetime
        resp = JobSyncRecordResponse(
            id="sync-001",
            source_id="src-001",
            source_name="linkedin",
            sync_type="incremental",
            jobs_added=10,
            jobs_updated=5,
            jobs_deleted=0,
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        assert resp.status == "completed"
        assert resp.jobs_added == 10

    def test_company_source_response(self):
        from app.schemas.models import CompanySourceResponse
        from datetime import datetime
        resp = CompanySourceResponse(
            id="cs-001",
            company_name="Microsoft",
            company_type="foreign",
            industry="科技",
            company_size="large",
            headquarters="美国雷德蒙德",
            country="美国",
            website="https://microsoft.com",
            careers_url="https://careers.microsoft.com",
            linkedin_url="https://linkedin.com/company/microsoft",
            glassdoor_url="https://glassdoor.com/Overview/Microsoft",
            hiring_status="hiring",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert resp.company_name == "Microsoft"
        assert resp.hiring_status == "hiring"

    def test_advanced_job_search_request(self):
        from app.schemas.models import AdvancedJobSearchRequest
        req = AdvancedJobSearchRequest(
            keyword="后端",
            location="北京",
            is_foreign=True,
            campus_recruitment=True,
            season="autumn",
            limit=20,
        )
        assert req.keyword == "后端"
        assert req.is_foreign is True
        assert req.season == "autumn"


# ── 端到端流程测试 ──────────────────────────────────────────────

class TestPhase8E2E:
    @pytest.fixture
    def mock_db_session(self):
        session = MagicMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_job_source_fields(self, mock_db_session):
        """岗位数据源字段测试"""
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()

        # 验证所有 Mock 岗位都有新字段
        for job in engine.MOCK_JOBS:
            assert job.get("source_name") is not None
            assert job.get("source_type") is not None
            assert job.get("source_url") is not None
            assert job.get("company_country") is not None
            assert isinstance(job.get("visa_support"), bool)
            assert isinstance(job.get("english_required"), bool)
            assert isinstance(job.get("graduate_program"), bool)
            assert isinstance(job.get("campus_recruitment"), bool)
            assert job.get("season") is not None

    @pytest.mark.asyncio
    async def test_adapter_list(self):
        """适配器列表测试"""
        from app.agents.job_source_adapters import list_adapters
        adapters = list_adapters()
        assert len(adapters) >= 7
        names = [a["source_name"] for a in adapters]
        assert "linkedin" in names
        assert "boss" in names
        assert "lagou" in names

    @pytest.mark.asyncio
    async def test_sync_engine_sources(self):
        """同步引擎数据源配置测试"""
        from app.agents.job_sync_engine import JobSyncEngine
        engine = JobSyncEngine()
        names = {s["source_name"] for s in engine.DEFAULT_SOURCES}
        assert "company" in names
        assert "linkedin" in names
        assert "boss" in names
        assert "lagou" in names
        assert "liepin" in names
        assert "indeed" in names
        assert "glassdoor" in names


# ── 岗位标签测试 ────────────────────────────────────────────────

class TestJobTags:
    def test_tag_coverage(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()

        all_tags = set()
        for job in engine.MOCK_JOBS:
            all_tags.update(job.get("tags", []))

        # 检查标签覆盖
        assert "校招" in all_tags or "秋招" in all_tags
        assert "外企" in all_tags
        assert "远程" in all_tags or "海外机会" in all_tags

    def test_season_coverage(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()

        seasons = set()
        for job in engine.MOCK_JOBS:
            seasons.add(job.get("season", "regular"))

        assert "autumn" in seasons or "spring" in seasons
        assert "regular" in seasons


# ── 数据源统计测试 ──────────────────────────────────────────────

class TestJobStats:
    def test_foreign_jobs_count(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        foreign_jobs = [j for j in engine.MOCK_JOBS if j["is_foreign"]]
        assert len(foreign_jobs) >= 2

    def test_campus_jobs_count(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        campus_jobs = [j for j in engine.MOCK_JOBS if j["campus_recruitment"]]
        assert len(campus_jobs) >= 5

    def test_remote_jobs_count(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        remote_jobs = [j for j in engine.MOCK_JOBS if j["is_remote"]]
        assert len(remote_jobs) >= 1

    def test_overseas_jobs_count(self):
        from app.agents.job_source_engine import JobSourceEngine
        engine = JobSourceEngine()
        overseas = [j for j in engine.MOCK_JOBS if j["is_foreign"] or j["is_remote"] or j["visa_support"]]
        assert len(overseas) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
