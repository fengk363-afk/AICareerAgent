"""
InterviewAgent — 岗位定制化 AI 模拟面试 + 反馈报告
"""
import uuid
import json
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import InterviewSession, Job, ResumeProfile
from app.db.database import get_db
from app.schemas.models import (
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewQuestion,
    UserAnswer,
    InterviewFeedback,
    InterviewStatus,
)


class InterviewAgent:
    """模拟面试 Agent"""

    # Mock 面试题库（按岗位类型分类）
    QUESTION_BANK = {
        "后端": [
            {"question": "请介绍一下你印象最深的项目，用了什么技术栈？", "category": "behavioral", "difficulty": "easy"},
            {"question": "Redis 缓存穿透、击穿、雪崩有什么区别？如何解决？", "category": "technical", "difficulty": "medium"},
            {"question": "设计一个短链接生成系统，要求支持高并发", "category": "technical", "difficulty": "hard"},
            {"question": "MySQL 索引底层数据结构是什么？B+树相比 B 树有什么优势？", "category": "technical", "difficulty": "medium"},
            {"question": "如果你发现线上服务响应变慢，你会如何排查？", "category": "situational", "difficulty": "medium"},
        ],
        "前端": [
            {"question": "React 和 Vue 的核心区别是什么？你更倾向哪个？", "category": "technical", "difficulty": "easy"},
            {"question": "请解释一下闭包，并给出一个实际应用场景", "category": "technical", "difficulty": "medium"},
            {"question": "前端性能优化你做过哪些？说说具体案例", "category": "behavioral", "difficulty": "medium"},
            {"question": "如何实现一个防抖和节流函数？", "category": "technical", "difficulty": "easy"},
            {"question": "描述一次你解决的最复杂的前端 bug", "category": "behavioral", "difficulty": "hard"},
        ],
        "算法": [
            {"question": "请实现 LRU 缓存", "category": "technical", "difficulty": "medium"},
            {"question": "给定一个字符串数组，返回所有字母异位词分组", "category": "technical", "difficulty": "medium"},
            {"question": "如何判断一棵二叉树是否是对称的？", "category": "technical", "difficulty": "easy"},
            {"question": "请描述 Transformer 的核心架构", "category": "technical", "difficulty": "hard"},
            {"question": "你在算法竞赛中最有成就感的一道题是什么？", "category": "behavioral", "difficulty": "easy"},
        ],
        "全栈": [
            {"question": "前后端分离架构下，如何处理跨域问题？", "category": "technical", "difficulty": "easy"},
            {"question": "请描述你做过最完整的全栈项目", "category": "behavioral", "difficulty": "medium"},
            {"question": "数据库事务隔离级别有哪些？MySQL 默认是什么？", "category": "technical", "difficulty": "medium"},
            {"question": "如何设计一个支持高并发的秒杀系统？", "category": "technical", "difficulty": "hard"},
            {"question": "你在项目中遇到过最棘手的技术问题是什么？怎么解决的？", "category": "situational", "difficulty": "hard"},
        ],
        "移动端": [
            {"question": "Android Activity 生命周期有哪些？", "category": "technical", "difficulty": "easy"},
            {"question": "iOS 内存管理机制是什么？ARC 如何解决内存问题？", "category": "technical", "difficulty": "medium"},
            {"question": "跨平台方案 React Native 和 Flutter 各有什么优劣？", "category": "technical", "difficulty": "medium"},
            {"question": "如何优化 App 的启动速度？", "category": "technical", "difficulty": "hard"},
            {"question": "请介绍你开发过的最复杂的 App 功能", "category": "behavioral", "difficulty": "medium"},
        ],
    }

    # 默认通用问题
    DEFAULT_QUESTIONS = [
        {"question": "请做一个简单的自我介绍", "category": "behavioral", "difficulty": "easy"},
        {"question": "你为什么想加入我们公司？", "category": "behavioral", "difficulty": "easy"},
        {"question": "你的职业规划是什么？", "category": "behavioral", "difficulty": "easy"},
        {"question": "描述一次你团队合作解决困难的经历", "category": "situational", "difficulty": "medium"},
        {"question": "你有什么问题想问我们？", "category": "behavioral", "difficulty": "easy"},
    ]

    async def create_session(self, user_id, job_id: str) -> InterviewSessionResponse:
        """创建面试会话并生成问题"""
        async for db in get_db():
            job = await db.get(Job, job_id)
            if not job:
                return None

            session_id = str(uuid.uuid4())
            questions = self._generate_questions(job)

            session = InterviewSession(
                id=session_id,
                user_id=int(user_id),
                job_id=job_id,
                status=InterviewStatus.SCHEDULED,
                questions=[q.model_dump() for q in questions],
                started_at=datetime.utcnow(),
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            logger.info(f"面试会话创建: {session_id}, 问题数: {len(questions)}")
            return InterviewSessionResponse.model_validate(session)

    async def submit_answers(
        self, session_id: str, answers: List[UserAnswer]
    ) -> InterviewSessionResponse:
        """提交面试答案并生成反馈"""
        async for db in get_db():
            session = await db.get(InterviewSession, session_id)
            if not session:
                return None

            # Convert dicts to UserAnswer if needed
            if isinstance(answers[0], dict):
                answers = [UserAnswer(**a) for a in answers]

            session.user_answers = [a.model_dump() for a in answers]
            session.status = InterviewStatus.COMPLETED
            session.completed_at = datetime.utcnow()

            # 生成反馈
            feedback = await self._generate_feedback(session, answers)
            session.feedback = [f.model_dump() for f in feedback]
            session.overall_score = sum(f.score for f in feedback) / len(feedback) if feedback else 0

            await db.commit()
            await db.refresh(session)
            logger.info(f"面试反馈生成: {session_id}, 总分: {session.overall_score}")
            return InterviewSessionResponse.model_validate(session)

    def _generate_questions(self, job: Job) -> List[InterviewQuestion]:
        """根据岗位类型生成面试问题"""
        job_title = job.title
        # 匹配题库
        for key in self.QUESTION_BANK:
            if key in job_title:
                return [InterviewQuestion(**q) for q in self.QUESTION_BANK[key]]
        return [InterviewQuestion(**q) for q in self.DEFAULT_QUESTIONS]

    async def _generate_feedback(
        self, session: InterviewSession, answers: List[UserAnswer]
    ) -> List[InterviewFeedback]:
        """生成面试反馈（MVP 使用规则生成，后续可接 LLM）"""
        questions = session.questions or []
        feedback_list = []

        for i, ans in enumerate(answers):
            if i >= len(questions):
                break
            q = questions[i]
            answer_text = ans.answer.lower()

            # 简单评分规则
            score = self._score_answer(q, answer_text)
            strengths = self._extract_strengths(q, answer_text)
            improvements = self._extract_improvements(q, answer_text)
            suggested = self._generate_suggested_answer(q)

            feedback_list.append(InterviewFeedback(
                question_index=i,
                score=score,
                strengths=strengths,
                improvements=improvements,
                suggested_answer=suggested,
            ))

        return feedback_list

    def _score_answer(self, question: dict, answer: str) -> float:
        """简单答案评分（MVP 规则版）"""
        if not answer or len(answer.strip()) < 10:
            return 30.0
        # 关键词匹配加分
        keywords = ["实现", "使用", "因为", "所以", "结果", "提升", "优化", "方案"]
        score = 50.0 + sum(8 for kw in keywords if kw in answer)
        return min(round(score, 1), 100.0)

    def _extract_strengths(self, question: dict, answer: str) -> List[str]:
        strengths = []
        if len(answer) > 50:
            strengths.append("回答内容较为详实")
        if "因为" in answer or "所以" in answer:
            strengths.append("逻辑结构清晰")
        if any(kw in answer for kw in ["项目", "实习", "经验"]):
            strengths.append("能结合实践经验")
        return strengths if strengths else ["回答基本完整"]

    def _extract_improvements(self, question: dict, answer: str) -> List[str]:
        improvements = []
        if len(answer) < 50:
            improvements.append("回答过于简短，建议展开说明")
        if "不知道" in answer or "不太" in answer:
            improvements.append("避免使用不确定的表述，展现自信")
        if not any(kw in answer for kw in ["数据", "结果", "提升", "优化"]):
            improvements.append("建议补充量化成果（如性能提升X%）")
        return improvements if improvements else ["整体表现良好，可进一步精炼"]

    def _generate_suggested_answer(self, question: dict) -> str:
        """生成参考答案（MVP 通用模板）"""
        q_text = question.get("question", "")
        if "自我介绍" in q_text:
            return "建议结构：基本信息 → 教育背景 → 核心技能 → 项目/实习亮点 → 求职动机，控制在 2-3 分钟"
        if "为什么" in q_text and "加入" in q_text:
            return "建议从公司业务/技术方向入手，结合个人职业规划和技能匹配度来回答"
        if "规划" in q_text:
            return "建议分短期（1-2年技术深耕）和长期（3-5年技术管理或专家方向）来阐述"
        if "困难" in q_text or "挑战" in q_text:
            return "使用 STAR 法则：情境 → 任务 → 行动 → 结果，重点突出你的贡献和成长"
        if "问题" in q_text and "问我们" in q_text:
            return "建议问团队技术栈、培养机制、项目方向等，展现你对岗位的认真态度"
        return "建议结合具体项目经历，使用 STAR 法则结构化回答，突出量化成果"
