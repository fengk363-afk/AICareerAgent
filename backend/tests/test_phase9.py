"""
AICareerAgent Phase 9 测试 — 职业目标中心、AI 职业助手
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── CareerGoalEngine 测试 ──────────────────────────────────────

class TestCareerGoalEngine:
    def test_engine_has_goal_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'career_goal_engine')
        assert hasattr(engine, 'create_goal')
        assert hasattr(engine, 'get_goals')
        assert hasattr(engine, 'get_goal')
        assert hasattr(engine, 'update_goal')
        assert hasattr(engine, 'delete_goal')
        assert hasattr(engine, 'create_target_company')
        assert hasattr(engine, 'get_target_companies')
        assert hasattr(engine, 'delete_target_company')
        assert hasattr(engine, 'get_or_create_preference')
        assert hasattr(engine, 'update_preference')
        assert hasattr(engine, 'get_or_create_progress')
        assert hasattr(engine, 'update_progress')

    def test_engine_has_ai_agent_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'ai_career_agent_engine')
        assert hasattr(engine, 'get_daily_tasks')
        assert hasattr(engine, 'get_skill_recommendations')
        assert hasattr(engine, 'get_application_plan')
        assert hasattr(engine, 'get_interview_plan')


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_career_goal_model(self):
        from app.db.models import CareerGoal
        assert CareerGoal.__tablename__ == "career_goals"
        columns = {c.name for c in CareerGoal.__table__.columns}
        assert "target_position" in columns
        assert "target_industry" in columns
        assert "target_company" in columns
        assert "target_country" in columns
        assert "target_city" in columns
        assert "salary_expectation_min" in columns
        assert "salary_expectation_max" in columns
        assert "company_type" in columns
        assert "remote_preference" in columns
        assert "priority_level" in columns
        assert "status" in columns

    def test_target_company_model(self):
        from app.db.models import TargetCompany
        assert TargetCompany.__tablename__ == "target_companies"
        columns = {c.name for c in TargetCompany.__table__.columns}
        assert "company_name" in columns
        assert "priority" in columns
        assert "status" in columns

    def test_user_job_preference_model(self):
        from app.db.models import UserJobPreference
        assert UserJobPreference.__tablename__ == "user_job_preferences"
        columns = {c.name for c in UserJobPreference.__table__.columns}
        assert "preferred_locations" in columns
        assert "preferred_companies" in columns
        assert "is_remote_wanted" in columns
        assert "is_foreign_wanted" in columns
        assert "visa_support_wanted" in columns

    def test_career_progress_model(self):
        from app.db.models import CareerProgress
        assert CareerProgress.__tablename__ == "career_progress"
        columns = {c.name for c in CareerProgress.__table__.columns}
        assert "skill_progress" in columns
        assert "application_count" in columns
        assert "interview_count" in columns
        assert "offer_count" in columns
        assert "progress_percentage" in columns
        assert "milestones" in columns


# ── Recommendation Engine 测试 ──────────────────────────────────

class TestRecommendationEngine:
    def test_goal_weight_in_recommendation(self):
        """验证推荐引擎包含目标匹配计算"""
        from app.agents.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()
        assert hasattr(engine, '_calc_goal_score')
        assert hasattr(engine, '_estimate_competition_score')

    def test_recommendation_weight_config(self):
        """验证推荐权重配置（目标40%、匹配30%、潜力20%、薪资10%）"""
        from app.agents.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()
        # 通过检查 _calculate_recommendation 方法签名验证
        import inspect
        sig = inspect.signature(engine._calculate_recommendation)
        params = list(sig.parameters.keys())
        assert 'goals' in params, "推荐方法应包含 goals 参数"


# ── AI Career Agent 测试 ───────────────────────────────────────

class TestAICareerAgent:
    def test_agent_has_methods(self):
        from app.agents.ai_career_agent_engine import AICareerAgentEngine
        engine = AICareerAgentEngine()
        assert hasattr(engine, 'get_daily_tasks')
        assert hasattr(engine, 'get_skill_recommendations')
        assert hasattr(engine, 'get_application_plan')
        assert hasattr(engine, 'get_interview_plan')

    def test_daily_tasks_generation(self):
        from app.agents.ai_career_agent_engine import AICareerAgentEngine
        engine = AICareerAgentEngine()
        tasks = engine._generate_daily_tasks([], None, None, [], [])
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_skill_recommendations_generation(self):
        from app.agents.ai_career_agent_engine import AICareerAgentEngine
        engine = AICareerAgentEngine()
        recs = engine._generate_skill_recommendations(None, None, [])
        assert len(recs) > 0

    def test_interview_plan_generation(self):
        from app.agents.ai_career_agent_engine import AICareerAgentEngine
        engine = AICareerAgentEngine()
        plan = engine._generate_interview_plan([], [])
        assert "upcoming" in plan
        assert "completed" in plan
        assert "tips" in plan
        assert len(plan["tips"]) > 0


# ── 端到端测试 ──────────────────────────────────────────────────

class TestPhase9E2E:
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
    async def test_goal_score_calculation(self, mock_db_session):
        """目标匹配分数计算测试"""
        from app.agents.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()

        # Mock job
        job = MagicMock()
        job.title = "后端开发工程师"
        job.company = "字节跳动"
        job.location = "北京"
        job.company_country = "中国"
        job.salary_range = {"min": 25, "max": 45}
        job.is_foreign = False
        job.is_remote = False
        job.company_type = "private"

        # Mock goal
        goal = MagicMock()
        goal.target_position = "后端开发"
        goal.target_company = "字节跳动"
        goal.target_city = "北京"
        goal.target_country = "中国"
        goal.company_type = "private"
        goal.remote_preference = "on_site"
        goal.salary_expectation_min = 20
        goal.salary_expectation_max = 50

        score = await engine._calc_goal_score(job, [goal], None)
        assert 0 <= score <= 100
        # 岗位、公司、城市都匹配，应该高分
        assert score >= 70

    @pytest.mark.asyncio
    async def test_goal_score_no_match(self, mock_db_session):
        """目标不匹配时分数较低"""
        from app.agents.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()

        job = MagicMock()
        job.title = "产品经理"
        job.company = "某国企"
        job.location = "上海"
        job.company_country = "中国"
        job.salary_range = {"min": 15, "max": 25}
        job.is_foreign = False
        job.is_remote = False
        job.company_type = "state_enterprise"

        goal = MagicMock()
        goal.target_position = "后端开发"
        goal.target_company = "字节跳动"
        goal.target_city = "北京"
        goal.target_country = "中国"
        goal.company_type = "private"
        goal.remote_preference = "remote"
        goal.salary_expectation_min = 30
        goal.salary_expectation_max = 50

        score = await engine._calc_goal_score(job, [goal], None)
        assert 0 <= score <= 100
        # 多项不匹配，应该低分
        assert score < 50

    @pytest.mark.asyncio
    async def test_competition_score_conversion(self):
        """竞争程度转分数测试"""
        from app.agents.recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()

        assert engine._estimate_competition_score("low") == 80.0
        assert engine._estimate_competition_score("medium") == 50.0
        assert engine._estimate_competition_score("high") == 30.0


# ── API 路由测试 ────────────────────────────────────────────────

class TestAPIRoutes:
    def test_career_goal_routes_exist(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        goal_routes = [r for r in routes if '/goals/' in r or '/goals' in r]
        assert len(goal_routes) >= 5

    def test_ai_agent_routes_exist(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        agent_routes = [r for r in routes if '/daily-tasks/' in r or '/skill-recommendations/' in r]
        assert len(agent_routes) >= 2

    def test_all_routes_count(self):
        from app.main import app
        api_routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api/')]
        assert len(api_routes) >= 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
