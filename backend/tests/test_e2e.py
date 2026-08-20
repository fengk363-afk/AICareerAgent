"""
AICareerAgent 端到端集成测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestEndToEnd:
    """端到端流程测试：上传简历 → 匹配 → 优化 → 面试 → 投递"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库会话"""
        session = MagicMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_profile(self):
        """Mock 简历画像"""
        profile = MagicMock()
        profile.id = "profile-001"
        profile.user_id = "test_user"
        profile.original_filename = "resume.pdf"
        profile.parsed_text = "Python, Go, React, Docker"
        profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
            {"name": "React", "level": "intermediate"},
            {"name": "Docker", "level": "basic"},
        ]
        profile.experience = [
            {
                "company": "阿里巴巴",
                "position": "后端开发实习生",
                "start_date": "2023.06",
                "end_date": "2023.09",
                "description": "负责用户增长模块开发",
            }
        ]
        profile.education = [
            {"school": "浙江大学", "degree": "本科", "major": "计算机科学与技术"}
        ]
        profile.summary = "浙江大学计算机毕业生"
        profile.strength_analysis = [
            {"type": "technical", "desc": "技术栈丰富", "score": 80}
        ]
        return profile

    @pytest.fixture
    def mock_job(self):
        """Mock 岗位"""
        job = MagicMock()
        job.id = "job-001"
        job.source = "mock"
        job.company = "字节跳动"
        job.title = "后端开发工程师（校招）"
        job.location = "北京"
        job.job_type = "full_time"
        job.salary_range = {"min": 25, "max": 45, "unit": "K/月"}
        job.description = "负责推荐系统后端服务开发"
        job.requirements = ["计算机相关专业", "熟悉 Go 或 Python"]
        job.preferred_skills = ["Go", "Python", "Redis", "Kafka", "MySQL", "Docker"]
        return job

    @pytest.mark.asyncio
    async def test_full_pipeline(self, mock_db_session, mock_profile, mock_job):
        """完整流程测试"""
        from app.agents.engine import CareerEngine

        engine = CareerEngine()

        # Mock DB context
        async def mock_get_db():
            yield mock_db_session

        # Patch get_db in the correct module (where it's imported)
        with patch('app.agents.resume_engine.get_db', mock_get_db):
            with patch('app.agents.match_engine.get_db', mock_get_db):
                with patch.object(engine.resume_engine, 'parse_and_create', return_value=mock_profile):
                    with patch.object(engine.job_source_engine, 'search_jobs', return_value=[mock_job]):
                        with patch.object(engine.match_engine, 'calculate_match') as mock_match:
                            mock_match.return_value = MagicMock(
                                job_id="job-001",
                                job_title="后端开发工程师（校招）",
                                company="字节跳动",
                                overall_score=78.5,
                                skill_match=85.0,
                                experience_match=72.0,
                                education_match=70.0,
                                gaps=["Kafka"],
                                suggestions=["建议学习 Kafka"],
                            )
                            result = await engine.full_pipeline(
                                "test_user", b"mock_pdf_content", "resume.pdf"
                            )

        # 验证结果
        assert result["profile"] == mock_profile
        assert len(result["jobs"]) == 1
        assert len(result["matches"]) == 1
        assert result["matches"][0].overall_score == 78.5

    @pytest.mark.asyncio
    async def test_match_score_calculation(self, mock_profile, mock_job):
        """匹配度计算测试"""
        from app.agents.match_engine import MatchEngine

        agent = MatchEngine()

        # 模拟 profile 有 Python, Go, Docker
        # 模拟 job 需要 Go, Python, Redis, Kafka, MySQL, Docker
        # 技能匹配 = 3/6 = 50%
        mock_profile.skills = [
            {"name": "Python", "level": "advanced"},
            {"name": "Go", "level": "intermediate"},
            {"name": "Docker", "level": "basic"},
        ]
        mock_profile.parsed_text = "Python Go Docker React"
        mock_job.preferred_skills = ["Go", "Python", "Redis", "Kafka", "MySQL", "Docker"]
        mock_job.requirements = ["计算机相关专业", "熟悉 Go 或 Python"]
        mock_job.company_type = "private"
        mock_job.tags = ["大厂"]
        mock_job.is_remote = False
        mock_job.is_foreign = False

        # Mock db.get to return our mock objects
        mock_db = MagicMock()

        async def async_get(model, id):
            if model.__name__ == 'ResumeProfile':
                return mock_profile
            return mock_job

        mock_db.get = AsyncMock(side_effect=async_get)
        mock_db.execute = AsyncMock()

        async def mock_get_db():
            yield mock_db

        with patch('app.agents.match_engine.get_db', mock_get_db):
            match = await agent.calculate_match("profile-001", "job-001")

        assert match is not None
        assert match.job_id == "job-001"
        assert match.skill_match == 50.0  # 3/6
        assert "Kafka" in match.gaps
        assert "Redis" in match.gaps

    @pytest.mark.asyncio
    async def test_interview_flow(self):
        """面试流程测试"""
        from app.agents.interview_agent import InterviewAgent

        agent = InterviewAgent()

        # 创建面试会话
        job = MagicMock()
        job.title = "后端开发工程师（校招）"
        questions = agent._generate_questions(job)
        assert len(questions) >= 3

        # 提交答案
        answers = [
            MagicMock(question_index=0, answer="我在阿里巴巴实习期间负责后端开发"),
            MagicMock(question_index=1, answer="Redis 缓存穿透可以通过布隆过滤器解决"),
        ]

        session = MagicMock()
        # questions are now InterviewQuestion objects, convert to dicts
        session.questions = [q.model_dump() for q in questions[:2]]

        feedback = await agent._generate_feedback(session, answers)
        assert len(feedback) == 2
        assert all(0 <= f.score <= 100 for f in feedback)
        assert all(len(f.strengths) > 0 for f in feedback)

    @pytest.mark.asyncio
    async def test_resume_optimization(self):
        """简历优化测试"""
        from app.agents.resume_optimizer_agent import ResumeOptimizerAgent

        agent = ResumeOptimizerAgent()

        profile = MagicMock()
        profile.skills = [{"name": "Python"}]
        profile.experience = [{"company": "Alibaba", "position": "Intern"}]
        profile.education = [{"school": "ZJU", "degree": "本科"}]
        profile.summary = "Test"

        job = MagicMock()
        job.title = "后端开发工程师"
        job.preferred_skills = ["Go", "Python", "Redis", "Docker"]

        edits = await agent._generate_edits(profile, job, {"go", "redis", "docker"})
        assert len(edits) > 0
        assert any(e["section"] == "skills" for e in edits)

    def test_database_models(self):
        """数据库模型测试"""
        from app.db.models import ResumeProfile, Job, Application, InterviewSession
        from app.db.models import ApplicationStatus, InterviewStatus

        # 验证枚举值
        assert ApplicationStatus.DRAFT.value == "draft"
        assert ApplicationStatus.OFFER.value == "offer"
        assert InterviewStatus.COMPLETED.value == "completed"

        # 验证表名
        assert ResumeProfile.__tablename__ == "resume_profiles"
        assert Job.__tablename__ == "jobs"
        assert Application.__tablename__ == "applications"
        assert InterviewSession.__tablename__ == "interview_sessions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
