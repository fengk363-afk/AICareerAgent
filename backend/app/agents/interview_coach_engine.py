"""
InterviewCoachEngine — AI 面试教练引擎
根据岗位JD生成面试题，提供模拟面试、AI评分、STAR优化
"""
import uuid
import random
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import (
    InterviewSession, InterviewQuestion, InterviewAnswer, InterviewFeedback,
    Job, ResumeProfile,
)
from app.db.database import get_db
from app.schemas.models import (
    InterviewSessionResponse, InterviewQuestion as InterviewQuestionSchema,
    UserAnswer, InterviewFeedback as InterviewFeedbackSchema,
)
from sqlalchemy import select


class InterviewCoachEngine:
    """AI 面试教练引擎"""

    # 扩展题库（按岗位类型 + 面试类型分类）
    QUESTION_BANK = {
        "后端": {
            "technical": [
                {"question": "Redis 缓存穿透、击穿、雪崩有什么区别？如何解决？", "difficulty": "medium"},
                {"question": "MySQL 索引底层数据结构是什么？B+树相比 B 树有什么优势？", "difficulty": "medium"},
                {"question": "设计一个短链接生成系统，要求支持高并发", "difficulty": "hard"},
                {"question": "Go 的 goroutine 和线程有什么区别？GMP 模型是什么？", "difficulty": "hard"},
                {"question": "分布式系统中如何实现分布式锁？", "difficulty": "hard"},
            ],
            "behavioral": [
                {"question": "请介绍一下你印象最深的项目，用了什么技术栈？", "difficulty": "easy"},
                {"question": "描述一次你解决的最复杂的技术问题", "difficulty": "medium"},
                {"question": "你在团队中遇到过什么冲突？怎么解决的？", "difficulty": "medium"},
            ],
            "situational": [
                {"question": "如果你发现线上服务响应变慢，你会如何排查？", "difficulty": "medium"},
                {"question": "如果线上出现OOM，你会怎么处理？", "difficulty": "hard"},
            ],
            "hr": [
                {"question": "你为什么想加入我们公司？", "difficulty": "easy"},
                {"question": "你的职业规划是什么？", "difficulty": "easy"},
                {"question": "你期望的薪资是多少？", "difficulty": "easy"},
            ],
            "english": [
                {"question": "Please introduce yourself in English.", "difficulty": "easy"},
                {"question": "Describe a challenging project you worked on.", "difficulty": "medium"},
            ],
        },
        "前端": {
            "technical": [
                {"question": "React 和 Vue 的核心区别是什么？你更倾向哪个？", "difficulty": "easy"},
                {"question": "请解释一下闭包，并给出一个实际应用场景", "difficulty": "medium"},
                {"question": "前端性能优化你做过哪些？说说具体案例", "difficulty": "medium"},
                {"question": "如何实现一个防抖和节流函数？", "difficulty": "easy"},
                {"question": "Virtual DOM 的工作原理是什么？", "difficulty": "medium"},
            ],
            "behavioral": [
                {"question": "描述一次你解决的最复杂的前端 bug", "difficulty": "hard"},
                {"question": "你为什么选择前端开发作为职业方向？", "difficulty": "easy"},
            ],
            "situational": [
                {"question": "如果产品需求频繁变更，你会如何应对？", "difficulty": "medium"},
            ],
            "hr": [
                {"question": "你平时如何保持技术敏感度？", "difficulty": "easy"},
            ],
            "english": [
                {"question": "What is the difference between let, const, and var?", "difficulty": "easy"},
            ],
        },
        "算法": {
            "technical": [
                {"question": "请实现 LRU 缓存", "difficulty": "medium"},
                {"question": "给定一个字符串数组，返回所有字母异位词分组", "difficulty": "medium"},
                {"question": "如何判断一棵二叉树是否是对称的？", "difficulty": "easy"},
                {"question": "请描述 Transformer 的核心架构", "difficulty": "hard"},
                {"question": "如何实现一个高效的 Top K 算法？", "difficulty": "medium"},
            ],
            "behavioral": [
                {"question": "你在算法竞赛中最有成就感的一道题是什么？", "difficulty": "easy"},
                {"question": "你是如何准备算法面试的？", "difficulty": "easy"},
            ],
            "english": [
                {"question": "Explain the time complexity of quicksort.", "difficulty": "medium"},
            ],
        },
        "全栈": {
            "technical": [
                {"question": "前后端分离架构下，如何处理跨域问题？", "difficulty": "easy"},
                {"question": "数据库事务隔离级别有哪些？MySQL 默认是什么？", "difficulty": "medium"},
                {"question": "如何设计一个支持高并发的秒杀系统？", "difficulty": "hard"},
                {"question": "RESTful API 设计原则有哪些？", "difficulty": "medium"},
            ],
            "behavioral": [
                {"question": "请描述你做过最完整的全栈项目", "difficulty": "medium"},
                {"question": "你在前后端开发中更倾向哪个方向？为什么？", "difficulty": "easy"},
            ],
            "situational": [
                {"question": "你在项目中遇到过最棘手的技术问题是什么？怎么解决的？", "difficulty": "hard"},
            ],
            "hr": [
                {"question": "你如何平衡前后端开发的精力分配？", "difficulty": "easy"},
            ],
        },
        "移动端": {
            "technical": [
                {"question": "Android Activity 生命周期有哪些？", "difficulty": "easy"},
                {"question": "iOS 内存管理机制是什么？ARC 如何解决内存问题？", "difficulty": "medium"},
                {"question": "跨平台方案 React Native 和 Flutter 各有什么优劣？", "difficulty": "medium"},
                {"question": "移动端性能优化你做过哪些？", "difficulty": "medium"},
            ],
            "behavioral": [
                {"question": "请介绍你开发过的最复杂的 App 功能", "difficulty": "medium"},
            ],
            "hr": [
                {"question": "你为什么选择移动端开发？", "difficulty": "easy"},
            ],
        },
        "产品": {
            "technical": [
                {"question": "如何设计一个用户增长方案？", "difficulty": "medium"},
                {"question": "如何衡量一个功能的成功？", "difficulty": "medium"},
            ],
            "behavioral": [
                {"question": "请介绍一个你主导的产品项目", "difficulty": "medium"},
                {"question": "如何处理与开发团队的分歧？", "difficulty": "medium"},
            ],
            "situational": [
                {"question": "如果上线后发现数据异常，你会怎么处理？", "difficulty": "hard"},
            ],
            "hr": [
                {"question": "你为什么想做产品经理？", "difficulty": "easy"},
            ],
        },
    }

    DEFAULT_QUESTIONS = [
        {"question": "请做一个简单的自我介绍", "category": "behavioral", "difficulty": "easy"},
        {"question": "你为什么想加入我们公司？", "category": "behavioral", "difficulty": "easy"},
        {"question": "你的职业规划是什么？", "category": "behavioral", "difficulty": "easy"},
        {"question": "描述一次你团队合作解决困难的经历", "category": "situational", "difficulty": "medium"},
        {"question": "你有什么问题想问我们？", "category": "behavioral", "difficulty": "easy"},
    ]

    # STAR 回答模板
    STAR_TEMPLATES = {
        "behavioral": {
            "S": "情境：描述项目背景、团队规模、时间周期",
            "T": "任务：你的具体职责和目标",
            "A": "行动：你采取的具体措施和技术方案",
            "R": "结果：量化成果（性能提升X%、处理X万级请求等）",
        },
        "situational": {
            "S": "情境：问题的背景和影响范围",
            "T": "任务：需要解决的核心问题",
            "A": "行动：你的分析思路和解决方案",
            "R": "结果：最终效果和学到的经验",
        },
    }

    async def generate_questions(self, job_id: str, question_types: Optional[List[str]] = None) -> List[dict]:
        """根据岗位JD生成面试题"""
        async for db in get_db():
            job = await db.get(Job, job_id)
            if not job:
                return []

            # 清除旧题目
            await db.execute(
                select(InterviewQuestion).where(InterviewQuestion.job_id == job_id)
            )
            existing = await db.execute(
                select(InterviewQuestion).where(InterviewQuestion.job_id == job_id)
            )
            for q in existing.scalars().all():
                await db.delete(q)
            await db.commit()

            questions = self._generate_questions(job, question_types)

            saved_questions = []
            for q_data in questions:
                q_id = str(uuid.uuid4())
                question = InterviewQuestion(
                    id=q_id,
                    job_id=job_id,
                    user_id=None,
                    company=job.company,
                    question_type=q_data["category"],
                    question=q_data["question"],
                    difficulty=q_data.get("difficulty", "medium"),
                    category=q_data.get("category"),
                    created_at=datetime.utcnow(),
                )
                db.add(question)
                saved_questions.append({
                    "id": q_id,
                    "question": q_data["question"],
                    "category": q_data["category"],
                    "difficulty": q_data.get("difficulty", "medium"),
                    "company": job.company,
                })

            await db.commit()
            logger.info(f"生成面试题: job_id={job_id}, 题目数={len(saved_questions)}")
            return saved_questions

    async def get_questions(self, job_id: str) -> List[dict]:
        """获取岗位题库"""
        async for db in get_db():
            result = await db.execute(
                select(InterviewQuestion).where(InterviewQuestion.job_id == job_id)
                .order_by(InterviewQuestion.created_at.desc())
            )
            return [
                {
                    "id": q.id,
                    "question": q.question,
                    "question_type": q.question_type,
                    "difficulty": q.difficulty,
                    "company": q.company,
                    "created_at": q.created_at.isoformat() if q.created_at else None,
                }
                for q in result.scalars().all()
            ]

    async def create_session(self, user_id: str, job_id: str) -> Optional[dict]:
        """创建模拟面试会话"""
        async for db in get_db():
            job = await db.get(Job, job_id)
            if not job:
                return None

            session_id = str(uuid.uuid4())
            questions = await self.get_questions(job_id)

            if not questions:
                questions = self._generate_questions(job)

            session = InterviewSession(
                id=session_id,
                user_id=int(user_id),
                job_id=job_id,
                status="scheduled",
                questions=questions,
                started_at=datetime.utcnow(),
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

            return {
                "id": session.id,
                "user_id": str(session.user_id),
                "job_id": session.job_id,
                "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
                "questions": questions,
                "started_at": session.started_at.isoformat() if session.started_at else None,
            }

    async def submit_answer(
        self, session_id: str, answer_data: dict
    ) -> Optional[dict]:
        """提交面试答案"""
        async for db in get_db():
            session = await db.get(InterviewSession, session_id)
            if not session:
                return None

            # 获取问题
            question_id = answer_data.get("question_id")
            question_text = answer_data.get("question", "")
            question_type = answer_data.get("question_type", "behavioral")

            if question_id:
                q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
                q = q_result.scalar_one_or_none()
                if q:
                    question_text = q.question
                    question_type = q.question_type

            # 保存答案
            answer_id = str(uuid.uuid4())
            answer = InterviewAnswer(
                id=answer_id,
                session_id=session_id,
                question_id=question_id,
                user_id=session.user_id,
                job_id=session.job_id,
                question=question_text,
                question_type=question_type,
                answer=answer_data.get("answer", ""),
                created_at=datetime.utcnow(),
            )
            db.add(answer)
            await db.commit()
            await db.refresh(answer)

            # 生成反馈
            feedback = await self._generate_feedback(question_text, answer_data.get("answer", ""), question_type)

            # 保存反馈
            feedback_id = str(uuid.uuid4())
            interview_feedback = InterviewFeedback(
                id=feedback_id,
                answer_id=answer_id,
                question_index=len(session.user_answers or []) if session.user_answers else 0,
                score=feedback["score"],
                strengths=feedback["strengths"],
                improvements=feedback["improvements"],
                suggested_answer=feedback["suggested_answer"],
                created_at=datetime.utcnow(),
            )
            db.add(interview_feedback)

            # 更新答案
            answer.score = feedback["score"]
            answer.feedback = {
                "strengths": feedback["strengths"],
                "improvements": feedback["improvements"],
                "suggested_answer": feedback["suggested_answer"],
            }
            answer.star_optimized = self._generate_star_optimized(answer_data.get("answer", ""), question_type)

            await db.commit()

            return {
                "answer_id": answer_id,
                "session_id": session_id,
                "question": question_text,
                "answer": answer_data.get("answer", ""),
                "score": feedback["score"],
                "feedback": feedback,
                "star_optimized": answer.star_optimized,
            }

    async def evaluate_answer(self, answer_id: str) -> Optional[dict]:
        """AI 评分反馈"""
        async for db in get_db():
            answer = await db.get(InterviewAnswer, answer_id)
            if not answer:
                return None

            feedback = await self._generate_feedback(
                answer.question, answer.answer or "", answer.question_type
            )

            # 更新评分
            answer.score = feedback["score"]
            answer.feedback = {
                "strengths": feedback["strengths"],
                "improvements": feedback["improvements"],
                "suggested_answer": feedback["suggested_answer"],
            }
            answer.star_optimized = self._generate_star_optimized(answer.answer or "", answer.question_type)

            await db.commit()

            return {
                "answer_id": answer_id,
                "question": answer.question,
                "answer": answer.answer,
                "score": feedback["score"],
                "feedback": feedback,
                "star_optimized": answer.star_optimized,
            }

    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取面试会话详情"""
        async for db in get_db():
            session = await db.get(InterviewSession, session_id)
            if not session:
                return None

            # 获取答案
            answers_result = await db.execute(
                select(InterviewAnswer).where(InterviewAnswer.session_id == session_id)
            )
            answers = answers_result.scalars().all()

            return {
                "id": session.id,
                "user_id": str(session.user_id),
                "job_id": session.job_id,
                "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
                "questions": session.questions or [],
                "answers": [
                    {
                        "id": a.id,
                        "question": a.question,
                        "answer": a.answer,
                        "score": a.score,
                        "feedback": a.feedback,
                        "star_optimized": a.star_optimized,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in answers
                ],
                "overall_score": session.overall_score,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            }

    async def get_history(self, user_id: str) -> List[dict]:
        """获取面试历史记录"""
        async for db in get_db():
            result = await db.execute(
                select(InterviewSession)
                .where(InterviewSession.user_id == int(user_id))
                .order_by(InterviewSession.created_at.desc())
            )
            sessions = result.scalars().all()

            history = []
            for session in sessions:
                # 获取岗位信息
                job_result = await db.execute(select(Job).where(Job.id == session.job_id))
                job = job_result.scalar_one_or_none()

                # 获取答案数量
                answers_result = await db.execute(
                    select(InterviewAnswer).where(InterviewAnswer.session_id == session.id)
                )
                answers = answers_result.scalars().all()

                history.append({
                    "id": session.id,
                    "job_id": session.job_id,
                    "company": job.company if job else "未知公司",
                    "position": job.title if job else "未知岗位",
                    "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
                    "question_count": len(session.questions or []),
                    "answer_count": len(answers),
                    "overall_score": session.overall_score,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                })

            return history

    def _generate_questions(self, job: Job, question_types: Optional[List[str]] = None) -> List[dict]:
        """根据岗位生成面试问题"""
        job_title = job.title
        questions = []

        # 匹配题库
        matched_bank = None
        for key in self.QUESTION_BANK:
            if key in job_title:
                matched_bank = self.QUESTION_BANK[key]
                break

        if matched_bank:
            # 从匹配的题库中随机选择
            for qtype, qlist in matched_bank.items():
                if question_types and qtype not in question_types:
                    continue
                # 随机选1-2题
                count = min(random.randint(1, 2), len(qlist))
                selected = random.sample(qlist, count)
                for q in selected:
                    questions.append({
                        "question": q["question"],
                        "category": qtype,
                        "difficulty": q.get("difficulty", "medium"),
                    })
        else:
            # 使用默认问题
            for q in self.DEFAULT_QUESTIONS:
                if not question_types or q["category"] in question_types:
                    questions.append(q)

        # 确保每种类型至少有1题
        categories = set(q["category"] for q in questions)
        for cat in ["technical", "behavioral", "situational", "hr", "english"]:
            if cat not in categories:
                for q in self.DEFAULT_QUESTIONS:
                    if q["category"] == cat:
                        questions.append(q)
                        break

        return questions

    async def _generate_feedback(
        self, question: str, answer: str, question_type: str
    ) -> dict:
        """生成面试反馈"""
        if not answer or len(answer.strip()) < 10:
            return {
                "score": 30.0,
                "strengths": ["回答过于简短"],
                "improvements": ["建议展开详细说明，使用 STAR 法则"],
                "suggested_answer": "建议使用 STAR 法则结构化回答：情境 → 任务 → 行动 → 结果",
            }

        # 基础评分
        score = 50.0
        keywords = ["实现", "使用", "因为", "所以", "结果", "提升", "优化", "方案", "数据", "性能",
                    "项目", "实习", "经验", "团队", "合作", "解决", "问题", "挑战"]
        for kw in keywords:
            if kw in answer:
                score += 3

        # 长度加分
        if len(answer) > 100:
            score += 10
        if len(answer) > 200:
            score += 5

        # 结构化加分
        if any(kw in answer for kw in ["首先", "其次", "最后", "第一", "第二", "第三"]):
            score += 5

        score = min(round(score, 1), 100.0)

        # 优势分析
        strengths = []
        if len(answer) > 100:
            strengths.append("回答内容较为详实")
        if any(kw in answer for kw in ["因为", "所以", "首先", "其次"]):
            strengths.append("逻辑结构清晰")
        if any(kw in answer for kw in ["项目", "实习", "经验"]):
            strengths.append("能结合实践经验")
        if any(kw in answer for kw in ["数据", "结果", "提升", "优化", "%"]):
            strengths.append("有量化成果描述")
        if not strengths:
            strengths.append("回答基本完整")

        # 改进建议
        improvements = []
        if len(answer) < 50:
            improvements.append("回答过于简短，建议展开说明")
        if "不知道" in answer or "不太" in answer or "可能" in answer:
            improvements.append("避免使用不确定的表述，展现自信")
        if not any(kw in answer for kw in ["数据", "结果", "提升", "优化", "%"]):
            improvements.append("建议补充量化成果（如性能提升X%、处理X万级请求）")
        if question_type in ["behavioral", "situational"] and "STAR" not in answer.upper():
            improvements.append("建议使用 STAR 法则结构化回答")
        if not improvements:
            improvements.append("整体表现良好，可进一步精炼")

        # 建议回答
        suggested = self._generate_suggested_answer(question, question_type)

        return {
            "score": score,
            "strengths": strengths,
            "improvements": improvements,
            "suggested_answer": suggested,
        }

    def _generate_star_optimized(self, answer: str, question_type: str) -> dict:
        """生成 STAR 优化版本"""
        if question_type not in self.STAR_TEMPLATES:
            return None

        template = self.STAR_TEMPLATES[question_type]
        return {
            "structure": template,
            "suggestion": "请按照 STAR 法则重新组织你的回答：\n" +
                         "\n".join([f"{k}: {v}" for k, v in template.items()]),
        }

    def _generate_suggested_answer(self, question: str, question_type: str) -> str:
        """生成建议回答"""
        if "自我介绍" in question:
            return "建议结构：基本信息 → 教育背景 → 核心技能 → 项目/实习亮点 → 求职动机，控制在 2-3 分钟"
        if "为什么" in question and "加入" in question:
            return "建议从公司业务/技术方向入手，结合个人职业规划和技能匹配度来回答"
        if "规划" in question:
            return "建议分短期（1-2年技术深耕）和长期（3-5年技术管理或专家方向）来阐述"
        if "困难" in question or "挑战" in question or "冲突" in question:
            return "使用 STAR 法则：情境 → 任务 → 行动 → 结果，重点突出你的贡献和成长"
        if "问题" in question and "问我们" in question:
            return "建议问团队技术栈、培养机制、项目方向等，展现你对岗位的认真态度"
        if "项目" in question:
            return "重点描述：项目背景、你的角色、技术方案、遇到的挑战、量化成果"
        if "技术" in question or "实现" in question:
            return "先给出核心概念，再展开技术细节，最后说明应用场景和优势"
        return "建议结合具体项目经历，使用 STAR 法则结构化回答，突出量化成果"
