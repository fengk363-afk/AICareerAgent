"""
AICareerAgent Phase 7 测试 — 推荐引擎、公司研究、岗位排序
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── RecommendationEngine 测试 ──────────────────────────────────

class TestRecommendationEngine:
    def test_engine_has_recommendation_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'recommendation_engine')
        assert hasattr(engine, 'generate_recommendations')
        assert hasattr(engine, 'get_recommendations')

    def test_recommendation_schema(self):
        from app.schemas.models import RecommendationResponse
        from datetime import datetime
        resp = RecommendationResponse(
            id="rec-001",
            profile_id="p-001",
            job_id="job-001",
            overall_score=85.0,
            match_score=90.0,
            potential_score=80.0,
            salary_score=85.0,
            company_type_score=90.0,
            skill_growth_score=75.0,
            competition_score=70.0,
            recommendation_reason="技能匹配度高",
            advantages=["掌握核心技能"],
            risks=["工作强度大"],
            missing_skills=["Kafka"],
            estimated_competition="medium",
            should_recommend=True,
            created_at=datetime.utcnow(),
        )
        assert resp.overall_score == 85.0
        assert resp.should_recommend is True

    def test_recommendation_with_job(self):
        from app.schemas.models import RecommendationResponse
        from datetime import datetime
        resp = RecommendationResponse(
            id="rec-001",
            profile_id="p-001",
            job_id="job-001",
            overall_score=75.0,
            match_score=70.0,
            potential_score=80.0,
            salary_score=75.0,
            company_type_score=70.0,
            skill_growth_score=65.0,
            competition_score=60.0,
            recommendation_reason="综合评估",
            advantages=[],
            risks=[],
            missing_skills=[],
            estimated_competition="high",
            should_recommend=True,
            job={"id": "job-001", "company": "Test", "title": "Engineer"},
            created_at=datetime.utcnow(),
        )
        assert resp.job["company"] == "Test"


# ── CompanyResearchEngine 测试 ──────────────────────────────────

class TestCompanyResearchEngine:
    def test_engine_has_company_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'company_research_engine')
        assert hasattr(engine, 'get_company_profile')
        assert hasattr(engine, 'get_company_by_id')

    def test_company_profile_schema(self):
        from app.schemas.models import CompanyProfileResponse
        from datetime import datetime
        resp = CompanyProfileResponse(
            id="company_字节跳动",
            company_name="字节跳动",
            company_type="private",
            industry="互联网/人工智能",
            company_size="large",
            business_direction="短视频、社交、AI",
            hiring_trend="growing",
            interview_difficulty="hard",
            employee_reviews_summary="技术氛围好",
            pros=["技术栈先进", "成长空间大"],
            cons=["工作强度大", "加班文化"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert resp.company_name == "字节跳动"
        assert resp.interview_difficulty == "hard"
        assert len(resp.pros) == 2

    def test_company_data_coverage(self):
        from app.agents.company_research_engine import CompanyResearchEngine
        engine = CompanyResearchEngine()
        assert len(engine.COMPANY_DATA) >= 10
        # 检查公司类型多样性
        types = {d["company_type"] for d in engine.COMPANY_DATA.values()}
        assert len(types) >= 3


# ── JobRankingEngine 测试 ───────────────────────────────────────

class TestJobRankingEngine:
    def test_engine_has_ranking_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'job_ranking_engine')
        assert hasattr(engine, 'rank_jobs')
        assert hasattr(engine, 'get_rankings')

    def test_ranking_schema(self):
        from app.schemas.models import JobRankingResponse
        from datetime import datetime
        resp = JobRankingResponse(
            id="rank-001",
            profile_id="p-001",
            job_id="job-001",
            rank=1,
            overall_score=90.0,
            match_score=95.0,
            potential_score=85.0,
            salary_score=90.0,
            company_type_score=80.0,
            skill_growth_score=85.0,
            competition_score=75.0,
            recommendation_reason="最佳匹配",
            advantages=["技能匹配高"],
            risks=[],
            missing_skills=[],
            estimated_competition="low",
            created_at=datetime.utcnow(),
        )
        assert resp.rank == 1
        assert resp.overall_score == 90.0

    def test_weight_configuration(self):
        from app.agents.job_ranking_engine import JobRankingEngine
        engine = JobRankingEngine()
        weights = engine.WEIGHTS
        assert sum(weights.values()) == 1.0  # 权重总和为 1
        assert "match_score" in weights
        assert "potential_score" in weights
        assert "salary_score" in weights
        assert "company_type_score" in weights
        assert "skill_growth_score" in weights
        assert "competition_score" in weights


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_recommendation_record_model(self):
        from app.db.models import RecommendationRecord
        assert RecommendationRecord.__tablename__ == "recommendation_records"
        columns = {c.name for c in RecommendationRecord.__table__.columns}
        assert "overall_score" in columns
        assert "match_score" in columns
        assert "recommendation_reason" in columns
        assert "advantages" in columns
        assert "risks" in columns

    def test_company_profile_model(self):
        from app.db.models import CompanyProfile
        assert CompanyProfile.__tablename__ == "company_profiles"
        columns = {c.name for c in CompanyProfile.__table__.columns}
        assert "company_name" in columns
        assert "industry" in columns
        assert "interview_difficulty" in columns
        assert "pros" in columns
        assert "cons" in columns

    def test_job_ranking_model(self):
        from app.db.models import JobRanking
        assert JobRanking.__tablename__ == "job_rankings"
        columns = {c.name for c in JobRanking.__table__.columns}
        assert "rank" in columns
        assert "overall_score" in columns
        assert "recommendation_reason" in columns


# ── API Schemas 测试 ────────────────────────────────────────────

class TestAPISchemas:
    def test_generate_recommendation_request(self):
        from app.schemas.models import GenerateRecommendationRequest
        req = GenerateRecommendationRequest(profile_id="p-001", limit=10)
        assert req.profile_id == "p-001"
        assert req.limit == 10

    def test_all_phase7_schemas_exist(self):
        from app.schemas.models import (
            RecommendationResponse,
            CompanyProfileResponse,
            JobRankingResponse,
            GenerateRecommendationRequest,
        )
        # 验证所有 schema 可实例化
        rec = RecommendationResponse(
            id="r1", profile_id="p1", job_id="j1",
            overall_score=80.0, match_score=85.0, potential_score=75.0,
            salary_score=80.0, company_type_score=70.0,
            skill_growth_score=75.0, competition_score=70.0,
            recommendation_reason="test", advantages=[], risks=[],
            missing_skills=[], estimated_competition="medium",
            should_recommend=True, created_at=__import__('datetime').datetime.utcnow(),
        )
        assert rec.overall_score == 80.0


# ── 端到端流程测试 ──────────────────────────────────────────────

class TestPhase7E2E:
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
        profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
            {"name": "React", "level": "intermediate"},
        ]
        profile.experience = [{"company": "Alibaba", "position": "Backend Intern"}]
        profile.education = [{"school": "ZJU", "degree": "本科", "major": "CS"}]
        profile.parsed_text = "Python Go React 实习 项目"
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
    async def test_recommendation_calculation(self, mock_db_session, mock_profile, mock_job):
        """推荐分数计算测试"""
        from app.agents.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()

        async def mock_get(model, id):
            if model.__name__ == 'ResumeProfile':
                return mock_profile
            return None

        mock_db_session.get = AsyncMock(side_effect=mock_get)

        async def mock_get_db():
            yield mock_db_session

        with patch('app.agents.recommendation_engine.get_db', mock_get_db):
            score_data = await engine._calculate_recommendation(
                mock_profile, mock_job, None, [], set()
            )

        assert score_data is not None
        assert 0 <= score_data["overall_score"] <= 100
        assert 0 <= score_data["match_score"] <= 100
        assert isinstance(score_data["recommendation_reason"], str)
        assert isinstance(score_data["advantages"], list)
        assert isinstance(score_data["risks"], list)
        assert isinstance(score_data["missing_skills"], list)

    @pytest.mark.asyncio
    async def test_company_research(self):
        """公司研究测试"""
        from app.agents.company_research_engine import CompanyResearchEngine

        engine = CompanyResearchEngine()
        # 验证数据覆盖
        assert "字节跳动" in engine.COMPANY_DATA
        assert "Microsoft" in engine.COMPANY_DATA
        assert "Google" in engine.COMPANY_DATA

        # 验证公司数据完整性
        for name, data in engine.COMPANY_DATA.items():
            assert "company_type" in data
            assert "industry" in data
            assert "interview_difficulty" in data
            assert "pros" in data
            assert "cons" in data

    @pytest.mark.asyncio
    async def test_job_ranking_weights(self):
        """岗位排序权重测试"""
        from app.agents.job_ranking_engine import JobRankingEngine

        engine = JobRankingEngine()
        weights = engine.WEIGHTS
        # 验证权重总和为 1
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001
        # 验证关键维度存在
        assert weights["match_score"] == 0.30
        assert weights["potential_score"] == 0.15
        assert weights["salary_score"] == 0.15


# ── 筛选与排序测试 ──────────────────────────────────────────────

class TestFilteringAndRanking:
    def test_competition_estimation(self):
        from app.agents.job_ranking_engine import JobRankingEngine
        engine = JobRankingEngine()

        # 外企竞争中等
        foreign_job = MagicMock()
        foreign_job.is_foreign = True
        foreign_job.is_remote = False
        foreign_job.company_type = "foreign"
        result = asyncio.run(engine._estimate_competition(foreign_job))
        assert result == "medium"

        # 远程竞争低
        remote_job = MagicMock()
        remote_job.is_foreign = False
        remote_job.is_remote = True
        remote_job.company_type = "startup"
        result = asyncio.run(engine._estimate_competition(remote_job))
        assert result == "low"

        # 大厂竞争高
        bigtech_job = MagicMock()
        bigtech_job.is_foreign = False
        bigtech_job.is_remote = False
        bigtech_job.company_type = "private"
        result = asyncio.run(engine._estimate_competition(bigtech_job))
        assert result == "high"

    def test_salary_score_calculation(self):
        from app.agents.job_ranking_engine import JobRankingEngine
        engine = JobRankingEngine()

        # Mock preference
        pref = MagicMock()
        pref.salary_min = 20
        pref.salary_max = 40

        # Mock job with salary in range
        job = MagicMock()
        job.salary_range = {"min": 25, "max": 35, "unit": "K/月"}

        score = asyncio.run(engine._calc_salary_score(job, pref))
        assert 70 <= score <= 90  # 薪资在范围内，应该高分

    def test_skill_growth_score(self):
        from app.agents.job_ranking_engine import JobRankingEngine
        engine = JobRankingEngine()

        # Mock profile with Python, Go
        profile = MagicMock()
        profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
        ]

        # Mock job needing Python, Go, Redis, Kafka
        job = MagicMock()
        job.preferred_skills = ["Go", "Python", "Redis", "Kafka"]

        score = asyncio.run(engine._calc_skill_growth_score(profile, job))
        # 缺失 2 项技能，应该是高分（90）
        assert score == 90.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
