"""
LearningEngine — 能力提升路线引擎
"""
import uuid
from typing import Optional, List
from datetime import datetime
from loguru import logger

from app.db.models import LearningPlan, Job
from app.db.database import get_db
from app.core.ai_config import ai_config
from app.services.llm_service import llm_service


class LearningEngine:
    """能力提升路线引擎"""

    LEARNING_PROMPT = """你是一个职业规划导师，请根据候选人的技能差距和目标岗位，生成能力提升路线。

## 目标岗位
{job_title} @ {company}
{job_description}

## 候选人现状
- 已有技能: {existing_skills}
- 缺失技能: {missing_skills}
- 已有经验: {experience_summary}

## 要求
生成一个结构化的学习路线（JSON格式）：
{{
  "phases": [
    {{
      "phase": "阶段名称",
      "duration": "预计学习时间",
      "topics": ["学习主题1", "学习主题2"],
      "resources": ["学习资源1", "学习资源2"],
      "tasks": ["练习任务1", "练习任务2"]
    }}
  ],
  "priority_skills": ["优先学习的技能1", "优先学习的技能2"],
  "estimated_time": "总预计学习时间",
  "tips": ["学习建议1", "学习建议2"]
}}"""

    async def generate_learning_plan(
        self, profile_id: str, job_id: str, missing_skills: List[str],
        existing_skills: List[str], experience_summary: str = ""
    ) -> Optional[dict]:
        """生成能力提升路线"""
        async for db in get_db():
            job = await db.get(Job, job_id)
            if not job:
                return None

            use_llm = ai_config.is_llm_enabled() and ai_config.get("match", "enable_llm_analysis", default=False)

            if use_llm:
                plan = await self._llm_generate(plan)
            else:
                plan = await self._rule_generate(job, missing_skills, existing_skills, experience_summary)

            # 保存学习路线
            plan_id = str(uuid.uuid4())
            learning_plan = LearningPlan(
                id=plan_id,
                profile_id=profile_id,
                job_id=job_id,
                plan_data=plan,
                status="active",
                created_at=datetime.utcnow(),
            )
            db.add(learning_plan)
            await db.commit()

            return {
                "plan_id": plan_id,
                "job_id": job_id,
                "job_title": job.title,
                "company": job.company,
                **plan,
            }

    async def _llm_generate(self, context: dict) -> dict:
        """LLM 生成学习路线"""
        prompt = self.LEARNING_PROMPT.format(
            job_title=context.get("job_title", ""),
            company=context.get("company", ""),
            job_description=context.get("job_description", ""),
            existing_skills=", ".join(context.get("existing_skills", [])),
            missing_skills=", ".join(context.get("missing_skills", [])),
            experience_summary=context.get("experience_summary", ""),
        )
        text = await llm_service.chat_completion([
            {"role": "system", "content": "你是职业规划导师，请生成能力提升路线。"},
            {"role": "user", "content": prompt},
        ])
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return await self._rule_generate_mock()

    async def _rule_generate(
        self, job: Job, missing_skills: List[str], existing_skills: List[str], experience_summary: str
    ) -> dict:
        """规则生成学习路线"""
        phases = []
        priority_skills = missing_skills[:3] if missing_skills else []

        # 根据缺失技能生成学习阶段
        if missing_skills:
            phases.append({
                "phase": "基础补强",
                "duration": "2-4周",
                "topics": missing_skills[:3],
                "resources": ["官方文档", "在线教程", "技术博客"],
                "tasks": [f"学习 {skill} 基础概念" for skill in missing_skills[:3]] + [f"完成 {skill} 小项目" for skill in missing_skills[:2]],
            })

        phases.append({
            "phase": "项目实践",
            "duration": "4-8周",
            "topics": ["综合项目", "技术深度"],
            "resources": ["GitHub开源项目", "技术社区", "在线课程"],
            "tasks": [
                "参与开源项目贡献",
                "独立完成一个完整项目",
                "撰写技术博客总结",
            ],
        })

        phases.append({
            "phase": "面试准备",
            "duration": "2-4周",
            "topics": ["算法刷题", "行为面试", "系统设计"],
            "resources": ["LeetCode", "《剑指Offer》", "系统设计入门"],
            "tasks": [
                "每天刷2道LeetCode",
                "准备3个STAR法则项目故事",
                "学习系统设计基础",
            ],
        })

        return {
            "phases": phases,
            "priority_skills": priority_skills,
            "estimated_time": "2-4个月",
            "tips": [
                "保持每天学习2-3小时",
                "理论与实践结合",
                "定期复盘总结",
                "加入技术社区交流",
            ],
        }

    async def _rule_generate_mock(self) -> dict:
        return {
            "phases": [
                {"phase": "基础补强", "duration": "2-4周", "topics": ["Kafka", "Kubernetes"], "resources": ["官方文档", "在线教程"], "tasks": ["学习基础概念", "完成小项目"]},
                {"phase": "项目实践", "duration": "4-8周", "topics": ["综合项目"], "resources": ["GitHub"], "tasks": ["参与开源项目", "独立完成项目"]},
                {"phase": "面试准备", "duration": "2-4周", "topics": ["算法", "行为面试"], "resources": ["LeetCode"], "tasks": ["每天刷题", "准备项目故事"]},
            ],
            "priority_skills": ["Kafka", "Kubernetes"],
            "estimated_time": "2-4个月",
            "tips": ["保持每天学习2-3小时", "理论与实践结合"],
        }

    async def get_learning_plans(self, profile_id: str) -> List[dict]:
        """获取学习路线列表"""
        async for db in get_db():
            from sqlalchemy import select
            result = await db.execute(
                select(LearningPlan)
                .where(LearningPlan.profile_id == profile_id)
                .order_by(LearningPlan.created_at.desc())
            )
            return [p.model_dump() for p in result.scalars().all()]
        return []
