from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    nasdaq_model_path: str = Field(
        default="~/Desktop/nasdaq/models/",
        validation_alias="NASDAQ_MODEL_PATH",
    )
    xauusd_model_path: str = Field(
        default="~/Desktop/xauusddata/models/",
        validation_alias="XAUUSD_MODEL_PATH",
    )
    pattern_engine_path: str = Field(
        default="~/Desktop/video/pattern_engine_runtime.py",
        validation_alias="PATTERN_ENGINE_PATH",
    )
    claude_patterns_path: str = Field(
        default="~/Desktop/trading-pattern-system/",
        validation_alias="CLAUDE_PATTERNS_PATH",
    )
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    deepseek_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DEEP_SEEKR1", "DEEPSEEK_API_KEY"),
    )
    eodhd_api_key: str | None = Field(default=None, validation_alias="EODHD_API_KEY")
    marketaux_api_key: str | None = Field(default=None, validation_alias="MARKETAUX_API_KEY")
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    xai_api_key: str | None = Field(default=None, validation_alias="XAI_API_KEY")
    x_bearer_token: str | None = Field(default=None, validation_alias="X_BEARER_TOKEN")
    marketaux_base_url: str = Field(
        default="https://api.marketaux.com/v1/news/all",
        validation_alias="MARKETAUX_BASE_URL",
    )
    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, validation_alias="SUPABASE_KEY")
    resend_api_key: str | None = Field(default=None, validation_alias="RESEND_API_KEY")
    turnstile_secret_key: str | None = Field(default=None, validation_alias="TURNSTILE_SECRET_KEY")
    ob_fractal_period: int = Field(default=2, validation_alias="OB_FRACTAL_PERIOD")
    ob_min_displacement_atr: float = Field(default=1.0, validation_alias="OB_MIN_DISPLACEMENT_ATR")
    ob_min_score: float = Field(default=50.0, validation_alias="OB_MIN_SCORE")
    ob_zone_type: str = Field(default="wick", validation_alias="OB_ZONE_TYPE")
    ob_max_tests: int = Field(default=2, validation_alias="OB_MAX_TESTS")
    rtyhiim_window_seconds: int = Field(default=600, validation_alias="RTYHIIM_WINDOW_SECONDS")
    rtyhiim_tick_rate_hz: float = Field(default=1.0, validation_alias="RTYHIIM_TICK_RATE_HZ")
    rtyhiim_min_period_s: float = Field(default=8.0, validation_alias="RTYHIIM_MIN_PERIOD_S")
    rtyhiim_max_period_s: float = Field(default=240.0, validation_alias="RTYHIIM_MAX_PERIOD_S")
    
    # Redis (for WebSocket broadcast cache)
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = Field(default=None, validation_alias="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str | None = Field(default=None, validation_alias="TELEGRAM_CHAT_ID")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
