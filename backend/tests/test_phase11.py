"""
AICareerAgent Phase 11 测试 — AI 职业顾问平台
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── CareerAgentEngine 测试 ──────────────────────────────────────

class TestCareerAgentEngine:
    def test_engine_has_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'career_agent_engine')
        assert hasattr(engine.career_agent_engine, 'chat')
        assert hasattr(engine.career_agent_engine, 'get_insights')
        assert hasattr(engine.career_agent_engine, 'create_learning_plan')
        assert hasattr(engine.career_agent_engine, 'get_learning_tasks')
        assert hasattr(engine.career_agent_engine, 'get_dashboard')
        assert hasattr(engine.career_agent_engine, 'get_notifications')
        assert hasattr(engine.career_agent_engine, 'mark_notification_read')
        assert hasattr(engine.career_agent_engine, 'mark_all_notifications_read')
        assert hasattr(engine.career_agent_engine, 'check_and_notify')

    def test_response_templates(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()
        assert "greeting" in engine.RESPONSE_TEMPLATES
        assert "resume_analysis" in engine.RESPONSE_TEMPLATES
        assert "job_recommendation" in engine.RESPONSE_TEMPLATES
        assert "interview_prep" in engine.RESPONSE_TEMPLATES
        assert "career_advice" in engine.RESPONSE_TEMPLATES


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_career_message_model(self):
        from app.db.models import CareerMessage
        assert CareerMessage.__tablename__ == "career_messages"
        columns = {c.name for c in CareerMessage.__table__.columns}
        assert "user_id" in columns
        assert "session_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "context_type" in columns

    def test_career_insight_model(self):
        from app.db.models import CareerInsight
        assert CareerInsight.__tablename__ == "career_insights"
        columns = {c.name for c in CareerInsight.__table__.columns}
        assert "user_id" in columns
        assert "insight_type" in columns
        assert "title" in columns
        assert "content" in columns
        assert "is_read" in columns

    def test_learning_task_model(self):
        from app.db.models import LearningTask
        assert LearningTask.__tablename__ == "learning_tasks"
        columns = {c.name for c in LearningTask.__table__.columns}
        assert "user_id" in columns
        assert "skill_name" in columns
        assert "task_type" in columns
        assert "status" in columns
        assert "estimated_hours" in columns
        assert "completed_hours" in columns

    def test_notification_model_enhanced(self):
        from app.db.models import Notification
        columns = {c.name for c in Notification.__table__.columns}
        assert "user_id" in columns
        assert "type" in columns
        assert "title" in columns
        assert "is_read" in columns


# ── Chat 功能测试 ───────────────────────────────────────────────

class TestChatFunctionality:
    def test_greeting_response(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        response = asyncio.run(engine._generate_response("你好", {}))
        assert "你好" in response["text"] or "AI 求职顾问" in response["text"]

    def test_resume_analysis_response(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        context = {
            "resume": MagicMock(
                skills=[{"name": "Python"}, {"name": "Go"}],
            ),
        }
        response = asyncio.run(engine._generate_response("分析我的简历", context))
        assert response["context_type"] == "resume"
        assert "技能" in response["text"] or "匹配" in response["text"]

    def test_job_recommendation_response(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        context = {
            "goals": [
                MagicMock(target_position="后端开发", target_company="字节跳动"),
            ],
        }
        response = asyncio.run(engine._generate_response("推荐岗位", context))
        assert response["context_type"] == "recommendation"

    def test_interview_prep_response(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        response = asyncio.run(engine._generate_response("如何准备面试", {}))
        assert response["context_type"] == "interview"
        assert len(response["text"]) > 10

    def test_career_advice_response(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        response = asyncio.run(engine._generate_response("职业规划", {}))
        assert response["context_type"] == "career"

    def test_default_response(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        response = asyncio.run(engine._generate_response("随机问题", {}))
        assert len(response["text"]) > 10


# ── 学习任务生成测试 ─────────────────────────────────────────────

class TestLearningTasks:
    def test_generate_learning_tasks(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        context = {
            "goals": [
                MagicMock(target_position="后端开发"),
                MagicMock(target_position="前端开发"),
            ],
            "resume": MagicMock(skills=[{"name": "Python"}]),
        }

        tasks = engine._generate_learning_tasks(context)
        assert len(tasks) > 0
        assert any(t["type"] == "learn" for t in tasks)
        assert any(t["type"] == "practice" for t in tasks)

    def test_learning_task_structure(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        tasks = engine._generate_learning_tasks({"goals": [], "resume": None})
        for task in tasks:
            assert "skill" in task
            assert "type" in task
            assert "title" in task
            assert "estimated_hours" in task
            assert "priority" in task


# ── 仪表盘生成测试 ──────────────────────────────────────────────

class TestDashboard:
    def test_generate_recommendations(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        stats = {
            "total_applications": 1,
            "total_interviews": 0,
            "by_status": {"applied": 1},
        }
        goals = []

        recs = engine._generate_dashboard_recommendations(stats, goals)
        assert len(recs) > 0
        assert any(r["type"] == "action" for r in recs)

    def test_generate_recommendations_with_goals(self):
        from app.agents.career_agent_engine import CareerAgentEngine
        engine = CareerAgentEngine()

        stats = {
            "total_applications": 5,
            "total_interviews": 2,
            "by_status": {"applied": 3, "interview_invited": 2},
        }
        goals = [MagicMock()]

        recs = engine._generate_dashboard_recommendations(stats, goals)
        # 有足够投递和面试，不应该有"增加投递"建议
        assert not any(r["title"] == "增加投递" for r in recs)


# ── API 路由测试 ────────────────────────────────────────────────

class TestAPIRoutes:
    def test_career_agent_routes_exist(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        agent_routes = [r for r in routes if '/agent/' in r]
        assert len(agent_routes) >= 6

    def test_all_routes_count(self):
        from app.main import app
        api_routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api/')]
        assert len(api_routes) >= 95


# ── 端到端测试 ──────────────────────────────────────────────────

class TestPhase11E2E:
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
    async def test_chat_with_context(self, mock_db_session):
        """聊天功能测试"""
        from app.agents.career_agent_engine import CareerAgentEngine

        engine = CareerAgentEngine()

        # Mock 数据库查询
        mock_profile = MagicMock()
        mock_profile.skills = [{"name": "Python"}]
        mock_profile.experience = []
        mock_profile.education = []

        mock_goal = MagicMock()
        mock_goal.target_position = "后端开发"
        mock_goal.target_company = "字节跳动"

        mock_db_session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_profile)),  # ResumeProfile
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_goal])))),  # CareerGoal
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Application
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # Interview
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # CareerProgress
        ])
        mock_db_session.get = AsyncMock(return_value=None)

        async def mock_get_db():
            yield mock_db_session

        with patch('app.agents.career_agent_engine.get_db', mock_get_db):
            # 测试生成回复（不依赖数据库）
            context = {
                "user_id": "1",
                "resume": mock_profile,
                "goals": [mock_goal],
                "applications": [],
                "interviews": [],
                "progress": None,
            }
            response = await engine._generate_response("推荐岗位", context)
            assert response["context_type"] == "recommendation"
            assert len(response["text"]) > 0

    @pytest.mark.asyncio
    async def test_generate_insight(self, mock_db_session):
        """生成洞察测试"""
        from app.agents.career_agent_engine import CareerAgentEngine

        engine = CareerAgentEngine()

        mock_db_session.add = AsyncMock()
        mock_db_session.commit = AsyncMock()

        async def mock_get_db():
            yield mock_db_session

        with patch('app.agents.career_agent_engine.get_db', mock_get_db):
            response = {
                "text": "测试洞察",
                "context_type": "recommendation",
                "generate_insight": True,
            }
            await engine._create_insight(mock_db_session, "1", response)
            mock_db_session.add.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
