from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    nasdaq_model_path: str = Field(
        default="~/Desktop/nasdaq/models/",
        env="NASDAQ_MODEL_PATH",
    )
    xauusd_model_path: str = Field(
        default="~/Desktop/xauusddata/models/",
        env="XAUUSD_MODEL_PATH",
    )
    pattern_engine_path: str = Field(
        default="~/Desktop/video/pattern_engine_runtime.py",
        env="PATTERN_ENGINE_PATH",
    )
    claude_patterns_path: str = Field(
        default="~/Desktop/trading-pattern-system/",
        env="CLAUDE_PATTERNS_PATH",
    )
    anthropic_api_key: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    eodhd_api_key: str | None = Field(default=None, env="EODHD_API_KEY")
    marketaux_api_key: str | None = Field(default=None, env="MARKETAUX_API_KEY")
    marketaux_base_url: str = Field(
        default="https://api.marketaux.com/v1/news/all",
        env="MARKETAUX_BASE_URL",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
