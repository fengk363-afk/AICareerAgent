"""
AIConfig — AI 模型配置管理
支持 OpenAI 兼容接口，保留 Mock 模式
"""
import os
import yaml
from pathlib import Path
from typing import Optional
from loguru import logger


class AIConfig:
    """AI 配置管理器"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        """加载配置（优先级：环境变量 > config/ai.yaml > 默认值）"""
        # 默认配置
        self.config = {
            "mode": "mock",  # mock | openai | custom
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            "match": {
                "enable_semantic": True,
                "enable_llm_analysis": False,  # 默认关闭，需要 API Key
                "weight_skill": 0.4,
                "weight_experience": 0.3,
                "weight_education": 0.15,
                "weight_industry": 0.15,
            },
            "resume": {
                "enable_ai_rewrite": False,
                "rewrite_style": "professional",  # professional | concise | detailed
            },
            "interview": {
                "enable_ai_questions": False,
                "question_count": 5,
                "follow_up_enabled": True,
            },
        }

        # 尝试加载配置文件
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "ai.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}
                self._merge(self.config, file_config)
                logger.info(f"AI 配置已从 {config_path} 加载")
            except Exception as e:
                logger.warning(f"加载 AI 配置失败: {e}")

        # 环境变量覆盖
        if os.getenv("AI_MODE"):
            self.config["mode"] = os.getenv("AI_MODE")
        if os.getenv("OPENAI_API_KEY"):
            self.config["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_MODEL"):
            self.config["openai"]["model"] = os.getenv("OPENAI_MODEL")

    def _merge(self, base: dict, override: dict):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def get(self, *keys, default=None):
        """获取配置值，支持嵌套访问如 get('openai', 'model')"""
        obj = self.config
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, default)
            else:
                return default
        return obj

    def is_mock_mode(self) -> bool:
        return self.config.get("mode", "mock") == "mock"

    def is_llm_enabled(self) -> bool:
        return not self.is_mock_mode() and bool(self.config.get("openai", {}).get("api_key"))


# 全局配置实例
ai_config = AIConfig()
