"""
AICareerAgent Application Center 测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── SmartApplicationEngine 测试 ─────────────────────────────────

class TestSmartApplicationEngine:
    def test_engine_has_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'smart_application_engine')
        assert hasattr(engine, 'create_application')
        assert hasattr(engine, 'prepare_application')
        assert hasattr(engine, 'submit_application')
        assert hasattr(engine, 'get_application_status')
        assert hasattr(engine, 'get_application_history')
        assert hasattr(engine, 'update_application_status')

    def test_application_modes(self):
        from app.agents.smart_application_engine import SmartApplicationEngine
        engine = SmartApplicationEngine()
        assert engine.MODE_AUTO == "auto"
        assert engine.MODE_SEMI_AUTO == "semi_auto"
        assert engine.MODE_REDIRECT == "redirect"

    def test_status_flow(self):
        from app.agents.smart_application_engine import SmartApplicationEngine
        engine = SmartApplicationEngine()
        assert "draft" in engine.STATUS_FLOW
        assert "applied" in engine.STATUS_FLOW
        assert "offer" in engine.STATUS_FLOW
        # 验证状态流转
        assert "preparing" in engine.STATUS_FLOW["draft"]
        assert "screening" in engine.STATUS_FLOW["applied"]
        assert "completed_apply" in engine.STATUS_FLOW["offer"]


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_application_has_new_fields(self):
        from app.db.models import Application
        columns = {c.name for c in Application.__table__.columns}
        assert "application_mode" in columns
        assert "resume_version_id" in columns
        assert "jd_keywords_matched" in columns
        assert "submitted_time" in columns

    def test_application_status_enum(self):
        from app.db.models import ApplicationStatus
        statuses = [s.value for s in ApplicationStatus]
        assert "draft" in statuses
        assert "preparing" in statuses
        assert "applied" in statuses
        assert "viewed_apply" in statuses
        assert "jumped_apply" in statuses
        assert "completed_apply" in statuses


# ── API Schemas 测试 ────────────────────────────────────────────

class TestAPISchemas:
    def test_application_create_request(self):
        from app.schemas.models import ApplicationCreateRequest
        req = ApplicationCreateRequest(
            user_id="1",
            job_id="job-001",
            application_mode="auto",
        )
        assert req.user_id == "1"
        assert req.application_mode == "auto"

    def test_application_prepare_request(self):
        from app.schemas.models import ApplicationPrepareRequest
        req = ApplicationPrepareRequest(
            user_id="1",
            job_id="job-001",
            target_position="后端开发",
        )
        assert req.target_position == "后端开发"

    def test_application_prepare_response(self):
        from app.schemas.models import ApplicationPrepareResponse
        from datetime import datetime
        resp = ApplicationPrepareResponse(
            application_id="app-001",
            job_id="job-001",
            job_title="后端开发",
            company="Test",
            cover_letter="Dear Hiring Manager...",
            recommended_resume_version="v1",
            jd_keywords_matched=["Python", "Go"],
            match_score=85.0,
            suggested_edits=[],
            status="preparing",
        )
        assert resp.match_score == 85.0
        assert len(resp.jd_keywords_matched) == 2

    def test_application_status_response(self):
        from app.schemas.models import ApplicationStatusResponse
        from datetime import datetime
        resp = ApplicationStatusResponse(
            id="app-001",
            user_id="1",
            job_id="job-001",
            status="applied",
            application_mode="auto",
            match_score=80.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert resp.status == "applied"
        assert resp.application_mode == "auto"


# ── 关键词提取测试 ──────────────────────────────────────────────

class TestKeywordExtraction:
    def test_extract_jd_keywords(self):
        from app.agents.smart_application_engine import SmartApplicationEngine
        engine = SmartApplicationEngine()

        job = MagicMock()
        job.preferred_skills = ["Python", "Go", "Redis"]
        job.requirements = ["熟悉 Python 或 Go", "了解数据结构"]
        job.description = "使用 Python 构建分布式系统"

        keywords = engine._extract_jd_keywords(job)
        assert "Python" in keywords
        assert "Go" in keywords
        assert "Redis" in keywords

    def test_match_keywords(self):
        from app.agents.smart_application_engine import SmartApplicationEngine
        engine = SmartApplicationEngine()

        profile = MagicMock()
        profile.parsed_text = "Python Go React Docker"
        profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
        ]

        keywords = ["Python", "Go", "Redis", "Kafka"]
        matched = engine._match_keywords(profile, keywords)
        assert "Python" in matched
        assert "Go" in matched
        assert "Redis" not in matched


# ── Cover Letter 生成测试 ───────────────────────────────────────

class TestCoverLetterGeneration:
    def test_generate_cover_letter(self):
        from app.agents.smart_application_engine import SmartApplicationEngine
        engine = SmartApplicationEngine()

        profile = MagicMock()
        profile.skills = [{"name": "Python", "level": "advanced"}]
        profile.experience = [{"company": "Alibaba", "position": "Backend Intern", "description": "负责后端开发"}]
        profile.education = [{"school": "ZJU", "degree": "本科", "major": "CS"}]
        profile.parsed_text = "Python Go"

        job = MagicMock()
        job.company = "字节跳动"
        job.title = "后端开发工程师"
        job.preferred_skills = ["Python", "Go"]

        letter = asyncio.run(engine._generate_cover_letter(profile, job, None, None))
        assert "字节跳动" in letter
        assert "后端开发工程师" in letter
        assert len(letter) > 100

    def test_generate_default_cover_letter(self):
        from app.agents.smart_application_engine import SmartApplicationEngine
        engine = SmartApplicationEngine()

        job = MagicMock()
        job.company = "Test Corp"
        job.title = "Engineer"

        letter = engine._generate_default_cover_letter(job)
        assert "Test Corp" in letter
        assert "Engineer" in letter


# ── 端到端测试 ──────────────────────────────────────────────────

class TestPhaseApplicationE2E:
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
    async def test_create_application(self, mock_db_session):
        """创建投递任务测试"""
        from app.agents.smart_application_engine import SmartApplicationEngine

        engine = SmartApplicationEngine()

        # Mock execute 返回 None（表示不存在）
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock get 返回 None（岗位不存在）
        mock_db_session.get = AsyncMock(return_value=None)

        async def mock_get_db():
            yield mock_db_session

        with patch('app.agents.smart_application_engine.get_db', mock_get_db):
            result = await engine.create_application(
                user_id="1",
                job_id="job-001",
                application_mode="redirect",
            )
            # 岗位不存在应返回 None
            assert result is None

    @pytest.mark.asyncio
    async def test_match_score_calculation(self):
        """匹配度计算测试"""
        from app.agents.smart_application_engine import SmartApplicationEngine

        engine = SmartApplicationEngine()

        # Mock profile
        profile = MagicMock()
        profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
            {"name": "Redis", "level": "basic"},
        ]
        profile.parsed_text = "Python Go Redis Docker"

        # Mock job
        job = MagicMock()
        job.preferred_skills = ["Go", "Python", "Redis", "Kafka"]

        score = await engine._calc_match_score(profile, job)
        # 3/4 = 75%
        assert score == 75.0

    @pytest.mark.asyncio
    async def test_suggested_edits_generation(self):
        """简历修改建议生成测试"""
        from app.agents.smart_application_engine import SmartApplicationEngine

        engine = SmartApplicationEngine()

        # Mock profile
        profile = MagicMock()
        profile.skills = [{"name": "Python"}]
        profile.experience = [{"company": "Alibaba", "position": "Intern"}]
        profile.summary = None

        # Mock job
        job = MagicMock()
        job.preferred_skills = ["Go", "Python", "Redis", "Docker"]

        edits = await engine._generate_suggested_edits(profile, job, ["Python"])
        assert len(edits) > 0
        # 应该有缺失技能建议
        assert any(e["section"] == "skills" for e in edits)


# ── API 路由测试 ────────────────────────────────────────────────

class TestAPIRoutes:
    def test_application_routes_exist(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        apply_routes = [r for r in routes if '/apply/' in r]
        assert len(apply_routes) >= 6

    def test_all_routes_count(self):
        from app.main import app
        api_routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api/')]
        assert len(api_routes) >= 80


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
