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
    ob_fractal_period: int = Field(default=2, env="OB_FRACTAL_PERIOD")
    ob_min_displacement_atr: float = Field(default=1.0, env="OB_MIN_DISPLACEMENT_ATR")
    ob_min_score: float = Field(default=50.0, env="OB_MIN_SCORE")
    ob_zone_type: str = Field(default="wick", env="OB_ZONE_TYPE")
    ob_max_tests: int = Field(default=2, env="OB_MAX_TESTS")
    rtyhiim_window_seconds: int = Field(default=600, env="RTYHIIM_WINDOW_SECONDS")
    rtyhiim_tick_rate_hz: float = Field(default=1.0, env="RTYHIIM_TICK_RATE_HZ")
    rtyhiim_min_period_s: float = Field(default=8.0, env="RTYHIIM_MIN_PERIOD_S")
    rtyhiim_max_period_s: float = Field(default=240.0, env="RTYHIIM_MAX_PERIOD_S")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
