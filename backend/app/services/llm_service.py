"""
LLMService — LLM 调用服务（OpenAI 兼容接口）
"""
import json
import asyncio
from typing import Optional, List, Dict, Any
from loguru import logger

from app.core.ai_config import ai_config


class LLMService:
    """LLM 服务，支持 OpenAI 兼容接口"""

    # Token 限制配置（字符数估算，1 token ≈ 2 字符中文 / 4 字符英文）
    MAX_INPUT_CHARS = 200_000  # 保守限制，预留 output tokens 空间
    TRUNCATE_KEEP_MESSAGES = 10  # 截断时保留最近 N 条消息（含 system）

    def __init__(self):
        self._client = None
        self._embedding_client = None

    def _get_client(self):
        """延迟导入 OpenAI client"""
        if self._client is None and ai_config.is_llm_enabled():
            try:
                from openai import OpenAI
                cfg = ai_config.get("openai")
                self._client = OpenAI(
                    api_key=cfg["api_key"],
                    base_url=cfg["base_url"],
                )
                logger.info("LLM 服务初始化成功")
            except ImportError:
                logger.warning("openai 包未安装，使用 Mock 模式")
            except Exception as e:
                logger.warning(f"LLM 服务初始化失败: {e}，使用 Mock 模式")
        return self._client

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """估算文本 token 数（中文 2 字符/token，英文 4 字符/token）"""
        if not text:
            return 0
        # 简单估算：中文字符约 2 字符/token，英文约 4 字符/token
        cn_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - cn_chars
        return cn_chars // 2 + other_chars // 4

    def _truncate_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """截断消息列表，保留 system + 最近 N 条，返回截断后的消息"""
        if len(messages) <= self.TRUNCATE_KEEP_MESSAGES:
            return messages

        # 保留 system 消息（如果有）和最近的消息
        system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
        kept = messages[-(self.TRUNCATE_KEEP_MESSAGES - 1):] if system_msg else messages[-self.TRUNCATE_KEEP_MESSAGES:]
        if system_msg and system_msg not in kept:
            kept = [system_msg] + kept

        logger.warning(
            f"LLM 输入超限，已截断：原始 {len(messages)} 条消息 → 保留 {len(kept)} 条 "
            f"（保留 system + 最近对话）"
        )
        return kept

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """调用 LLM 生成文本"""
        client = self._get_client()
        if not client:
            return self._mock_completion(messages)

        # ── Token 保护：估算并截断 ──────────────────────────────
        total_chars = sum(len(m.get("content", "")) for m in messages)
        total_tokens_est = self._estimate_tokens(" ".join(m.get("content", "") for m in messages))

        if total_chars > self.MAX_INPUT_CHARS:
            logger.warning(
                f"LLM 输入字符数 {total_chars} 超过限制 {self.MAX_INPUT_CHARS}，开始截断"
            )
            messages = self._truncate_messages(messages)
            # 重新估算
            total_chars = sum(len(m.get("content", "")) for m in messages)
            total_tokens_est = self._estimate_tokens(" ".join(m.get("content", "") for m in messages))

        logger.info(
            f"LLM 调用：model={model or ai_config.get('openai', {}).get('model', 'unknown')}, "
            f"messages={len(messages)} 条, 估算 tokens≈{total_tokens_est}, 字符数={total_chars}"
        )

        cfg = ai_config.get("openai")
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model or cfg["model"],
                    messages=messages,
                    temperature=temperature if temperature is not None else cfg.get("temperature", 0.3),
                    max_tokens=max_tokens or cfg.get("max_tokens", 2000),
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return self._mock_completion(messages)

    async def extract_json(
        self,
        messages: List[Dict[str, str]],
        schema: dict,
    ) -> Optional[dict]:
        """调用 LLM 并解析 JSON 输出"""
        messages = messages + [{"role": "system", "content": "Please respond with valid JSON only."}]
        text = await self.chat_completion(messages)
        if not text:
            return None
        try:
            # 提取 JSON 部分
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
        return None

    def _mock_completion(self, messages: List[Dict[str, str]]) -> str:
        """Mock 回复（用于测试）"""
        last_msg = messages[-1]["content"] if messages else ""
        if "匹配" in last_msg or "match" in last_msg.lower():
            return json.dumps({
                "overall_score": 75.0,
                "skill_match": 70.0,
                "experience_match": 80.0,
                "education_match": 75.0,
                "strengths": ["技术栈匹配良好", "有相关实习经验"],
                "weaknesses": ["缺少分布式系统经验"],
                "gaps": ["Kafka", "Kubernetes"],
                "suggestions": ["建议学习 Kafka 消息队列", "补充分布式系统项目经验"],
            }, ensure_ascii=False)
        elif "面试" in last_msg or "interview" in last_msg.lower():
            return json.dumps({
                "questions": [
                    {"question": "请介绍一下你印象最深的项目", "category": "behavioral", "difficulty": "easy"},
                    {"question": "Redis 缓存穿透如何解决", "category": "technical", "difficulty": "medium"},
                ]
            }, ensure_ascii=False)
        return "Mock response for testing"

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """生成文本嵌入向量"""
        client = self._get_client()
        if not client:
            return None
        cfg = ai_config.get("openai")
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.embeddings.create(
                    model=cfg.get("embedding_model", "text-embedding-3-small"),
                    input=text,
                )
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding 生成失败: {e}")
            return None


# 全局服务实例
llm_service = LLMService()
