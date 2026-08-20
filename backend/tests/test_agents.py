"""
AICareerAgent 单元测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ── ResumeAgent 测试 ────────────────────────────────────────────

class TestResumeAgent:
    def test_extract_skills(self):
        from app.agents.resume_agent import ResumeAgent
        agent = ResumeAgent()

        text = """
        Skills: Python, Go, React, Docker, Kubernetes, Redis, MySQL
        """
        result = asyncio.run(agent._extract_skills(text))
        names = [s.name.lower() for s in result]
        assert "python" in names
        assert "go" in names
        assert "react" in names
        assert len(result) > 0

    def test_extract_skills_empty(self):
        from app.agents.resume_agent import ResumeAgent
        agent = ResumeAgent()
        result = asyncio.run(agent._extract_skills("No skills here"))
        assert len(result) == 0

    def test_extract_education(self):
        from app.agents.resume_agent import ResumeAgent
        agent = ResumeAgent()
        text = "教育背景: 浙江大学 · 本科 · 计算机科学与技术 · 2020.09-2024.06"
        result = asyncio.run(agent._extract_education(text))
        assert len(result) > 0
        assert "浙江大学" in result[0].school

    def test_mock_parsed_text(self):
        from app.agents.resume_agent import ResumeAgent
        agent = ResumeAgent()
        text = agent._mock_parsed_text()
        assert len(text) > 0
        assert "张小明" in text
        assert "阿里巴巴" in text


# ── JobMatchingAgent 测试 ───────────────────────────────────────

class TestJobMatchingAgent:
    def test_mock_jobs_count(self):
        from app.agents.job_matching_agent import JobMatchingAgent
        agent = JobMatchingAgent()
        assert len(agent.MOCK_JOBS) == 5

    def test_mock_jobs_structure(self):
        from app.agents.job_matching_agent import JobMatchingAgent
        agent = JobMatchingAgent()
        job = agent.MOCK_JOBS[0]
        assert "company" in job
        assert "title" in job
        assert "description" in job
        assert "preferred_skills" in job

    def test_generate_suggestions(self):
        from app.agents.job_matching_agent import JobMatchingAgent
        agent = JobMatchingAgent()
        suggestions = agent._generate_suggestions(
            skill_match=40.0,
            gaps=["Kafka", "Docker"],
            requirements=["熟悉 Go 或 Python"]
        )
        assert len(suggestions) > 0
        assert any("Kafka" in s for s in suggestions)


# ── ResumeOptimizerAgent 测试 ───────────────────────────────────

class TestResumeOptimizerAgent:
    def test_optimize_summary(self):
        from app.agents.resume_optimizer_agent import ResumeOptimizerAgent
        agent = ResumeOptimizerAgent()

        # Mock profile
        profile = MagicMock()
        profile.skills = [{"name": "Python"}, {"name": "Go"}]
        profile.experience = [{"company": "Alibaba", "position": "Backend Intern"}]
        profile.education = [{"school": "ZJU", "degree": "本科", "major": "CS"}]
        profile.summary = "Test summary"

        # Mock job
        job = MagicMock()
        job.title = "后端开发工程师"
        job.preferred_skills = ["Go", "Python", "Redis"]

        result = asyncio.run(agent._optimize_summary(profile, job))
        assert "后端" in result or "毕业生" in result

    def test_calc_improvement_score(self):
        from app.agents.resume_optimizer_agent import ResumeOptimizerAgent
        agent = ResumeOptimizerAgent()

        profile = MagicMock()
        profile.skills = [{"name": "Python"}]
        job = MagicMock()
        job.preferred_skills = ["Go", "Python", "Redis"]

        score = asyncio.run(agent._calc_improvement_score(profile, job, {"go", "redis"}))
        assert 0 <= score <= 100


# ── InterviewAgent 测试 ─────────────────────────────────────────

class TestInterviewAgent:
    def test_question_bank_coverage(self):
        from app.agents.interview_agent import InterviewAgent
        agent = InterviewAgent()
        assert len(agent.QUESTION_BANK) >= 5
        for key, questions in agent.QUESTION_BANK.items():
            assert len(questions) >= 3
            for q in questions:
                assert "question" in q
                assert "category" in q
                assert "difficulty" in q

    def test_generate_questions_backend(self):
        from app.agents.interview_agent import InterviewAgent
        agent = InterviewAgent()

        job = MagicMock()
        job.title = "后端开发工程师（校招）"
        questions = agent._generate_questions(job)
        assert len(questions) > 0
        assert questions[0].category in ["technical", "behavioral", "situational"]

    def test_generate_questions_frontend(self):
        from app.agents.interview_agent import InterviewAgent
        agent = InterviewAgent()

        job = MagicMock()
        job.title = "前端开发工程师（校招）"
        questions = agent._generate_questions(job)
        assert len(questions) > 0

    def test_score_answer_empty(self):
        from app.agents.interview_agent import InterviewAgent
        agent = InterviewAgent()
        score = agent._score_answer({"question": "Test"}, "")
        assert score < 50

    def test_score_answer_detailed(self):
        from app.agents.interview_agent import InterviewAgent
        agent = InterviewAgent()
        answer = "我使用 Python 实现了分布式系统，因为采用了 Redis 缓存，所以性能提升了 50%"
        score = agent._score_answer({"question": "Test"}, answer)
        assert score >= 50

    def test_default_questions(self):
        from app.agents.interview_agent import InterviewAgent
        agent = InterviewAgent()
        job = MagicMock()
        job.title = "产品经理"
        questions = agent._generate_questions(job)
        assert len(questions) > 0
        assert "自我介绍" in questions[0].question


# ── ApplicationTrackerAgent 测试 ────────────────────────────────

class TestApplicationTrackerAgent:
    def test_status_enum(self):
        from app.db.models import ApplicationStatus
        statuses = [s.value for s in ApplicationStatus]
        assert "draft" in statuses
        assert "applied" in statuses
        assert "offer" in statuses
        assert "rejected" in statuses


# ── Schema 测试 ─────────────────────────────────────────────────

class TestSchemas:
    def test_job_create(self):
        from app.schemas.models import JobCreate
        job = JobCreate(
            company="Test Corp",
            title="Engineer",
            location="Beijing",
            description="Test job",
        )
        assert job.company == "Test Corp"
        assert job.source == "mock"

    def test_match_score_response(self):
        from app.schemas.models import MatchScoreResponse
        match = MatchScoreResponse(
            job_id="1",
            job_title="Engineer",
            company="Test",
            overall_score=85.0,
            skill_match=90.0,
            experience_match=80.0,
            education_match=75.0,
            gaps=["Go"],
            strengths=["good"],
            weaknesses=["need improve"],
            suggestions=["Learn Go"],
        )
        assert match.overall_score == 85.0
        assert len(match.gaps) == 1
        assert len(match.strengths) == 1
        assert len(match.weaknesses) == 1

    def test_interview_question(self):
        from app.schemas.models import InterviewQuestion
        q = InterviewQuestion(
            question="Tell me about yourself",
            category="behavioral",
            difficulty="easy",
        )
        assert q.category == "behavioral"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
