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
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    # ─── Bias debate engine — model routing (OpenAI-compatible APIs) ───
    deepseek_base_url: str = Field(default="https://api.deepseek.com", validation_alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-reasoner", validation_alias="DEEPSEEK_MODEL")
    kimi_api_key: str | None = Field(default=None, validation_alias=AliasChoices("KIMI_API_KEY", "MOONSHOT_API_KEY"))
    kimi_base_url: str = Field(default="https://api.moonshot.ai/v1", validation_alias="KIMI_BASE_URL")
    kimi_model: str = Field(default="kimi-k2-0711-preview", validation_alias="KIMI_MODEL")
    # ─── Bias auto-runner (scheduled debate + outcome fill) ───
    bias_auto_run_enabled: bool = Field(default=False, validation_alias="BIAS_AUTO_RUN_ENABLED")
    bias_run_windows_et: str = Field(default="08:00=0800_main,09:45=0945_confirm", validation_alias="BIAS_RUN_WINDOWS_ET")
    bias_fill_time_et: str = Field(default="16:15", validation_alias="BIAS_FILL_TIME_ET")
    # Çok-sembol UTC pencereleri (2026-07-19'da lokal koda geri inşa edildi —
    # önceki deploy yalnız-NDX runner içeriyordu ve XAU/DAX/USOIL koşularını
    # susturmuştu). Biçim: "HH:MM=label:SYMBOL,..."; XAU 08:00, DAX 08:10
    # (aynı tick'te iki ~6dk'lık debate çakışmasın diye bilinçli kaydırma),
    # USOIL 13:05 UTC. Notlama 22:20 UTC (tüm semboller, fill_outcomes).
    bias_symbol_runs_utc: str = Field(
        default="08:00=xau_daily:XAUUSD,08:10=dax_daily:GDAXI.INDX,"
                "13:05=usoil_daily:USOIL.FOREX",
        validation_alias="BIAS_SYMBOL_RUNS_UTC")
    bias_symbol_fill_utc: str = Field(default="22:20", validation_alias="BIAS_SYMBOL_FILL_UTC")
    # ─── CORTEX (episodic memory + analog retrieval) ───
    cortex_enabled: bool = Field(default=True, validation_alias="CORTEX_ENABLED")
    cortex_analog_k: int = Field(default=8, validation_alias="CORTEX_ANALOG_K")
    # Analog base-rate injection into the debate is OFF by default: the 2019-24
    # backtest found NO reliable directional edge for the forward target, so we
    # keep RECORDING memory (Phase 2/3) but don't feed a misleading P(up) to the
    # CIO. Flip to 1 only if a future feature set proves predictive.
    cortex_analog_inject: bool = Field(default=False, validation_alias="CORTEX_ANALOG_INJECT")
    # Validated confluence playbook (OOS-tested rules) → debate CIO as prior evidence.
    cortex_rules_inject: bool = Field(default=True, validation_alias="CORTEX_RULES_INJECT")
    # Live SHADOW confluence signals (14:00/15:00 UTC, log-only, needs yfinance).
    cortex_signal_enabled: bool = Field(default=False, validation_alias="CORTEX_SIGNAL_ENABLED")
    xai_api_key: str | None = Field(default=None, validation_alias="XAI_API_KEY")
    x_bearer_token: str | None = Field(default=None, validation_alias="X_BEARER_TOKEN")
    aisstream_api_key: str | None = Field(default=None, validation_alias="AISSTREAM_API_KEY")
    aisstream_ws_url: str = Field(default="wss://stream.aisstream.io/v0/stream", validation_alias="AISSTREAM_WS_URL")
    oil_ais_autostart: bool = Field(default=False, validation_alias="OIL_AIS_AUTOSTART")
    baltic_bdti_url: str | None = Field(default=None, validation_alias="BALTIC_BDTI_URL")
    baltic_bcti_url: str | None = Field(default=None, validation_alias="BALTIC_BCTI_URL")
    baltic_td3c_url: str | None = Field(default=None, validation_alias="BALTIC_TD3C_URL")
    baltic_stockq_enabled: bool = Field(default=True, validation_alias="BALTIC_STOCKQ_ENABLED")
    oil_baltic_sync_autostart: bool = Field(default=True, validation_alias="OIL_BALTIC_SYNC_AUTOSTART")
    oil_baltic_sync_interval_seconds: int = Field(default=3600, validation_alias="OIL_BALTIC_SYNC_INTERVAL_SECONDS")
    # ─── AIS ingest throttle + DB retention (2026-08-27 Supabase disk audit) ───
    # tanker_positions yalnızca 12-48 saatlik pencerelerle okunuyor (bkz.
    # oil_maritime_data_service._aggregate_from_positions). Her AIS pozisyon
    # raporunu yazmak 45 GB DB'nin 38 GB'ını tek tabloya şişirdi. Vessel başına
    # en fazla bu aralıkta bir satır yaz; retention_days'ten eskisini sil.
    ais_min_persist_interval_seconds: int = Field(default=60, validation_alias="AIS_MIN_PERSIST_INTERVAL_SECONDS")
    ais_store_raw_payload: bool = Field(default=False, validation_alias="AIS_STORE_RAW_PAYLOAD")
    tanker_position_retention_days: int = Field(default=7, validation_alias="TANKER_POSITION_RETENTION_DAYS")
    trajectory_snapshot_retention_days: int = Field(default=30, validation_alias="TRAJECTORY_SNAPSHOT_RETENTION_DAYS")
    signal_checks_retention_days: int = Field(default=30, validation_alias="SIGNAL_CHECKS_RETENTION_DAYS")
    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY"))
    resend_api_key: str | None = Field(default=None, validation_alias="RESEND_API_KEY")
    turnstile_secret_key: str | None = Field(default=None, validation_alias="TURNSTILE_SECRET_KEY")
    # MiroShark → ForexSAI daily-bias webhook (shared HMAC-SHA256 secret).
    miroshark_webhook_secret: str | None = Field(default=None, validation_alias="WEBHOOK_SECRET")
    # GÖLGE MODU (default AÇIK): MiroShark bias'ı yalnız bias_test_log'a yazılır,
    # daily_bias'a (canlı veto katmanı) DOKUNMAZ. İsabet ≥%55 kanıtlanınca 0 yap.
    miroshark_shadow_only: bool = Field(default=True, validation_alias="MIROSHARK_SHADOW_ONLY")
    ob_fractal_period: int = Field(default=2, validation_alias="OB_FRACTAL_PERIOD")
    ob_min_displacement_atr: float = Field(default=1.0, validation_alias="OB_MIN_DISPLACEMENT_ATR")
    ob_min_score: float = Field(default=50.0, validation_alias="OB_MIN_SCORE")
    ob_zone_type: str = Field(default="wick", validation_alias="OB_ZONE_TYPE")
    ob_max_tests: int = Field(default=2, validation_alias="OB_MAX_TESTS")
    rtyhiim_window_seconds: int = Field(default=600, validation_alias="RTYHIIM_WINDOW_SECONDS")
    rtyhiim_tick_rate_hz: float = Field(default=1.0, validation_alias="RTYHIIM_TICK_RATE_HZ")
    rtyhiim_min_period_s: float = Field(default=8.0, validation_alias="RTYHIIM_MIN_PERIOD_S")
    rtyhiim_max_period_s: float = Field(default=240.0, validation_alias="RTYHIIM_MAX_PERIOD_S")
    # v3 (sample/bar-based) — the engine works on bars; seconds_per_bar bridges to clock time
    rtyhiim_window_samples: int = Field(default=600, validation_alias="RTYHIIM_WINDOW_SAMPLES")
    rtyhiim_seconds_per_bar: float = Field(default=300.0, validation_alias="RTYHIIM_SECONDS_PER_BAR")
    rtyhiim_min_period_samples: int = Field(default=4, validation_alias="RTYHIIM_MIN_PERIOD_SAMPLES")
    rtyhiim_max_period_samples: int = Field(default=120, validation_alias="RTYHIIM_MAX_PERIOD_SAMPLES")
    # Sub-minute bar size (seconds) synthesized from the live tick buffer for rhythm
    # detection. 0 disables and falls back to 1m/5m. 15s resolves intraday channel
    # cycles that sit below the 5m period-floor.
    rtyhiim_subminute_bar_seconds: int = Field(default=15, validation_alias="RTYHIIM_SUBMINUTE_BAR_SECONDS")
    
    # Redis (for WebSocket broadcast cache)
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")
    market_data_source: str = Field(default="mt5_redis", validation_alias="MARKET_DATA_SOURCE")
    mt5_redis_tick_channel: str = Field(default="mt5:tick", validation_alias="MT5_REDIS_TICK_CHANNEL")
    mt5_redis_bar_channel: str = Field(default="mt5:bar", validation_alias="MT5_REDIS_BAR_CHANNEL")

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = Field(default=None, validation_alias="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str | None = Field(default=None, validation_alias="TELEGRAM_CHAT_ID")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
