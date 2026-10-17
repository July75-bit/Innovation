"""集中配置。

所有可调参数都从环境变量读取（见 backend/.env.example），代码里不要写死魔数：
交易规则参数是 B 的，定价参数是 C 的，模型参数是 D 的，改这里不动机器。

负责人：B（结构） / C、D（各自的参数）
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- 应用 ----------
    app_name: str = "PlayerStock API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./playerstock.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---------- 交易规则（B） ----------
    initial_balance: int = 5000
    max_position_per_player: int = 50

    # ---------- 定价参数（C） ----------
    pricing_alpha: float = 0.15
    pricing_beta: float = 0.0
    pricing_floor: float = 1.0

    # ---------- 大模型（D） ----------
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_timeout_seconds: float = 20.0

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        """Render 给的连接串可能以 postgres:// 开头，SQLAlchemy 2.x 只认 postgresql://。

        不转换的话，线上启动会直接抛
        `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres`。
        """
        if v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://") :]
        return v

    @property
    def is_sqlite(self) -> bool:
        """是否在用本地 SQLite（线上必须为 False，否则数据会随部署丢失）。"""
        return self.database_url.startswith("sqlite")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        """没有密钥时 AI 接口必须降级为规则版，而不是让整个系统不可用。"""
        return bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
