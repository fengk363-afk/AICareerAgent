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


# ── ResumeEngine 技能解析测试 ────────────────────────────────────

class TestResumeEngineSkills:
    """测试 ResumeEngine._parse_skills_lines() 方法"""

    def test_pdf_broken_lines_merge(self):
        """测试PDF断行合并：A/PI、竞品数/据、进度追/踪等应合并"""
        from app.agents.resume_engine import ResumeEngine
        engine = ResumeEngine()

        # 模拟PDF断行文本
        lines = [
            "· AI数据协助：Claude Code用于编写轻量级Python/Shell脚本，实现批量数据清洗、A",
            "PI接口调用、报表自动生成，提升数据处理效率。",
            "· 市场调研：熟练使用Google Trends、Statista、similarweb等进行行业趋势与竞品数",
            "据搜集，输出市场洞察报告。",
            "· 项目管理：熟练运用Notion、Asana进行项目拆解、任务分配、甘特图排期与进度追",
            "踪，确保多线程协作高效执行。",
        ]

        result = engine._parse_skills_lines(lines)
        names = [s.name for s in result]

        # 验证断行已合并
        assert "AI数据协助" in names, "AI数据协助 应被正确识别"
        assert "市场调研" in names, "市场调研 应被正确识别"
        assert "项目管理" in names, "项目管理 应被正确识别"

        # 验证不会产生断行碎片
        for name in names:
            assert not name.startswith("PI"), f"不应产生断行碎片: {name}"
            assert not name.startswith("据"), f"不应产生断行碎片: {name}"
            assert not name.startswith("踪"), f"不应产生断行碎片: {name}"
            assert not name.endswith("。"), f"不应产生句子碎片: {name}"
            assert "实现批量数据清洗、A" not in name, f"不应产生断行碎片: {name}"
            assert "提升数据处理效率" not in name, f"不应产生句子碎片: {name}"

    def test_no_sentence_fragments(self):
        """测试不会产生句子碎片"""
        from app.agents.resume_engine import ResumeEngine
        engine = ResumeEngine()

        lines = [
            "· AI数据协助：Claude Code用于编写轻量级Python/Shell脚本，实现批量数据清洗、API接口调用、报表自动生成，提升数据处理效率。",
            "· 市场调研：熟练使用Google Trends、Statista、similarweb等进行行业趋势与竞品数据搜集，输出市场洞察报告。",
            "· 项目管理：熟练运用Notion、Asana进行项目拆解、任务分配、甘特图排期与进度追踪，确保多线程协作高效执行。",
        ]

        result = engine._parse_skills_lines(lines)
        names = [s.name for s in result]

        # 验证不会产生句子碎片
        bad_patterns = [
            "实现批量数据清洗",
            "提升数据处理效率",
            "输出市场洞察报告",
            "确保多线程协作高效执行",
            "支撑策略优化",
        ]
        for pattern in bad_patterns:
            assert not any(pattern in name for name in names), f"不应包含句子碎片: {pattern}"

    def test_sub_skills_extraction(self):
        """测试子技能提取（聚合到description中）"""
        from app.agents.resume_engine import ResumeEngine
        engine = ResumeEngine()

        lines = [
            "· AI数据协助：Claude Code用于编写轻量级Python/Shell脚本，实现批量数据清洗、API接口调用、报表自动生成，提升数据处理效率。",
            "· 市场调研：熟练使用Google Trends、Statista、similarweb等进行行业趋势与竞品数据搜集，输出市场洞察报告。",
            "· 数据分析：擅长使用Tableau搭建可视化看板，结合Excel进行投放效果、用户行为、销售数据多维度分析，支撑策略优化。",
        ]

        result = engine._parse_skills_lines(lines)
        names = [s.name for s in result]

        # 验证主技能
        assert "AI数据协助" in names
        assert "市场调研" in names
        assert "数据分析" in names

        # 验证子技能已聚合到description中
        for sk in result:
            if sk.name == "AI数据协助":
                assert "Python" in sk.description
                assert "Shell" in sk.description
                assert "Claude Code" in sk.description
                assert "API" in sk.description
            elif sk.name == "市场调研":
                assert "Google Trends" in sk.description
                assert "Statista" in sk.description
            elif sk.name == "数据分析":
                assert "Tableau" in sk.description
                assert "Excel" in sk.description

        # 验证不会产生独立的子技能SkillItem
        for sk in result:
            assert sk.name not in ["Python", "Shell", "Claude Code", "API", "Google Trends", "Statista", "Tableau", "Excel"]

    def test_real_resume_text(self):
        """测试真实简历文本"""
        import asyncio
        import asyncpg
        from app.agents.resume_engine import ResumeEngine

        async def run_test():
            conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/aicareragent')
            row = await conn.fetchrow("SELECT parsed_text FROM resume_profiles WHERE id = '02eb166b-0747-4431-957a-3a510c07319c'")
            await conn.close()
            parsed_text = row[0]

            engine = ResumeEngine()
            sections = engine._detect_sections(parsed_text)

            # Find skills section
            for s in sections:
                if s['name'] == 'skills':
                    result = engine._parse_skills_lines(s['lines'])
                    names = [s.name for s in result]

                    # 验证主技能（约6个）
                    assert "AI数据协助" in names, "应包含 AI数据协助"
                    assert "市场调研" in names, "应包含 市场调研"
                    assert "项目管理" in names, "应包含 项目管理"
                    assert "数据分析" in names, "应包含 数据分析"
                    assert "内容制作" in names, "应包含 内容制作"
                    assert "平台运营" in names, "应包含 平台运营"

                    # 验证技能数量合理（约6-8个主技能）
                    assert 5 <= len(result) <= 10, f"应有约6-8个主技能，实际: {len(result)}"

                    # 验证子技能已聚合到description中
                    for sk in result:
                        if sk.name == "AI数据协助":
                            assert "Python" in sk.description or "Claude Code" in sk.description
                        elif sk.name == "市场调研":
                            assert "Google Trends" in sk.description or "Statista" in sk.description
                        elif sk.name == "项目管理":
                            assert "Notion" in sk.description or "Asana" in sk.description
                        elif sk.name == "数据分析":
                            assert "Tableau" in sk.description or "Excel" in sk.description
                        elif sk.name == "内容制作":
                            assert "剪映" in sk.description or "PR" in sk.description

                    # 验证不会产生独立的子技能SkillItem
                    for sk in result:
                        assert sk.name not in ["Python", "Claude Code", "Google Trends", "Statista",
                                              "Notion", "Asana", "Tableau", "Excel", "PR", "AE",
                                              "FCP", "PS", "剪映"], f"子技能不应作为独立SkillItem: {sk.name}"

                    # 验证不会产生断行碎片（检查skill name，description可能包含原始文本）
                    bad_name_patterns = [
                        "实现批量数据清洗、A",
                        "PI接口调用",
                        "提升数据处理效率",
                        "据搜集",
                        "确保多线程协作高效执行",
                        "销售数据多维度分析",
                        "支撑策略优化",
                        "可独立产出",
                        "文、海报",
                    ]
                    for pattern in bad_name_patterns:
                        assert not any(pattern in name for name in names), f"技能名称不应包含断行碎片: {pattern}"

                    return

            raise AssertionError("未找到 skills 章节")

        asyncio.run(run_test())

    def test_empty_input(self):
        """测试空输入"""
        from app.agents.resume_engine import ResumeEngine
        engine = ResumeEngine()
        result = engine._parse_skills_lines([])
        assert len(result) == 0

    def test_no_colon_format(self):
        """测试无冒号格式"""
        from app.agents.resume_engine import ResumeEngine
        engine = ResumeEngine()

        lines = [
            "Python, Go, Java, JavaScript",
        ]

        result = engine._parse_skills_lines(lines)
        names = [s.name.lower() for s in result]

        # 无冒号格式应按逗号分割
        assert "python" in names
        assert "go" in names
        assert "java" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
