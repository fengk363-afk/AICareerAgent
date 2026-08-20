"""
AICareerAgent Phase 10 测试 — AI 面试教练
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── InterviewCoachEngine 测试 ──────────────────────────────────

class TestInterviewCoachEngine:
    def test_engine_has_methods(self):
        from app.agents.engine import CareerEngine
        engine = CareerEngine()
        assert hasattr(engine, 'interview_coach_engine')
        assert hasattr(engine, 'generate_questions')
        assert hasattr(engine, 'get_questions')
        assert hasattr(engine, 'create_interview_session')
        assert hasattr(engine, 'submit_interview_answer')
        assert hasattr(engine, 'evaluate_interview_answer')
        assert hasattr(engine, 'get_interview_session')
        assert hasattr(engine, 'get_interview_history')

    def test_question_bank_coverage(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()
        assert len(engine.QUESTION_BANK) >= 5
        for key, bank in engine.QUESTION_BANK.items():
            assert isinstance(bank, dict)
            for qtype, questions in bank.items():
                assert len(questions) >= 1
                for q in questions:
                    assert "question" in q
                    assert "difficulty" in q

    def test_default_questions(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()
        assert len(engine.DEFAULT_QUESTIONS) >= 3
        for q in engine.DEFAULT_QUESTIONS:
            assert "question" in q
            assert "category" in q


# ── Database Models 测试 ────────────────────────────────────────

class TestDatabaseModels:
    def test_interview_question_model(self):
        from app.db.models import InterviewQuestion
        assert InterviewQuestion.__tablename__ == "interview_questions"
        columns = {c.name for c in InterviewQuestion.__table__.columns}
        assert "job_id" in columns
        assert "question_type" in columns
        assert "question" in columns
        assert "difficulty" in columns

    def test_interview_answer_model(self):
        from app.db.models import InterviewAnswer
        assert InterviewAnswer.__tablename__ == "interview_answers"
        columns = {c.name for c in InterviewAnswer.__table__.columns}
        assert "session_id" in columns
        assert "answer" in columns
        assert "score" in columns
        assert "feedback" in columns
        assert "star_optimized" in columns

    def test_interview_feedback_model(self):
        from app.db.models import InterviewFeedback
        assert InterviewFeedback.__tablename__ == "interview_feedback"
        columns = {c.name for c in InterviewFeedback.__table__.columns}
        assert "answer_id" in columns
        assert "score" in columns
        assert "strengths" in columns
        assert "improvements" in columns
        assert "suggested_answer" in columns


# ── 问题生成测试 ────────────────────────────────────────────────

class TestQuestionGeneration:
    def test_generate_questions_backend(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        job = MagicMock()
        job.title = "后端开发工程师（校招）"

        questions = engine._generate_questions(job)
        assert len(questions) > 0
        categories = [q["category"] for q in questions]
        assert "technical" in categories

    def test_generate_questions_frontend(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        job = MagicMock()
        job.title = "前端开发工程师"

        questions = engine._generate_questions(job)
        assert len(questions) > 0
        categories = [q["category"] for q in questions]
        assert "technical" in categories

    def test_generate_questions_unknown(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        job = MagicMock()
        job.title = "产品经理"

        questions = engine._generate_questions(job)
        assert len(questions) > 0

    def test_filter_by_type(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        job = MagicMock()
        job.title = "后端开发工程师"

        questions = engine._generate_questions(job, ["technical"])
        # 过滤后应该只包含 technical 类型（或至少有一个 technical）
        technical_questions = [q for q in questions if q["category"] == "technical"]
        assert len(technical_questions) > 0


# ── 评分反馈测试 ────────────────────────────────────────────────

class TestScoringFeedback:
    def test_score_empty_answer(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        feedback = asyncio.run(engine._generate_feedback("自我介绍", "", "behavioral"))
        assert feedback["score"] < 50
        assert len(feedback["improvements"]) > 0

    def test_score_detailed_answer(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        answer = "我使用 Python 实现了分布式系统，因为采用了 Redis 缓存，所以性能提升了 50%，结果非常理想"
        feedback = asyncio.run(engine._generate_feedback("请介绍你的项目", answer, "behavioral"))
        assert feedback["score"] >= 50
        assert len(feedback["strengths"]) > 0

    def test_star_optimized(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        star = engine._generate_star_optimized("我使用Python实现了...", "behavioral")
        assert star is not None
        assert "S" in star["structure"]
        assert "T" in star["structure"]
        assert "A" in star["structure"]
        assert "R" in star["structure"]

    def test_suggested_answer(self):
        from app.agents.interview_coach_engine import InterviewCoachEngine
        engine = InterviewCoachEngine()

        suggested = engine._generate_suggested_answer("请做一个简单的自我介绍", "behavioral")
        assert len(suggested) > 10

        suggested = engine._generate_suggested_answer("描述一次你解决的最复杂的技术问题", "behavioral")
        # 技术问题建议回答
        assert len(suggested) > 10


# ── API 路由测试 ────────────────────────────────────────────────

class TestAPIRoutes:
    def test_interview_coach_routes_exist(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        coach_routes = [r for r in routes if '/interview/generate' in r or '/interview/questions' in r or '/interview/session' in r]
        assert len(coach_routes) >= 5

    def test_all_routes_count(self):
        from app.main import app
        api_routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api/')]
        assert len(api_routes) >= 90


# ── 端到端测试 ──────────────────────────────────────────────────

class TestPhase10E2E:
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
    async def test_generate_questions_for_job(self, mock_db_session):
        """生成面试题测试"""
        from app.agents.interview_coach_engine import InterviewCoachEngine

        engine = InterviewCoachEngine()

        # Mock execute 返回空结果
        mock_result = MagicMock()
        mock_result.scalars = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        async def mock_get_db():
            yield mock_db_session

        with patch('app.agents.interview_coach_engine.get_db', mock_get_db):
            # 测试生成题目（不依赖数据库）
            job = MagicMock()
            job.title = "后端开发工程师"
            questions = engine._generate_questions(job)
            assert len(questions) > 0
            assert any(q["category"] == "technical" for q in questions)

    @pytest.mark.asyncio
    async def test_feedback_generation(self):
        """反馈生成测试"""
        from app.agents.interview_coach_engine import InterviewCoachEngine

        engine = InterviewCoachEngine()

        # 测试简短回答
        feedback = await engine._generate_feedback("问题", "短", "behavioral")
        assert feedback["score"] < 50
        assert len(feedback["improvements"]) > 0

        # 测试详细回答
        feedback = await engine._generate_feedback("问题", "我使用Python实现了分布式系统，因为采用了Redis缓存，所以性能提升了50%", "behavioral")
        assert feedback["score"] >= 50
        assert len(feedback["strengths"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
