import importlib

__all__ = [
    "nasdaq",
    "xauusd",
    "usoil",
    "dax",
    "oil_baltic_intelligence",
    "pattern_engine",
    "claude_news",
    "claude_sentiment",
    "order_blocks",
    "rtyhiim",
    "ta",
    "data",
    "prediction",
    "ai_analysis",
    "learning",
    "fvg",
    "emel_pulse",
    "admin",
    "clear_trend",
    "deepseek_analysis",
    "news_correlation",
    "rss_router",
    "auth",
    "mtf_analysis",
    "trading_engine_test",
    "signal_lifecycle_router",
    "strategy_optimizer",
    "chart_data",
    "websocket",
    "economic_calendar_router",
    "prices",
]


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    return sorted(set(globals()) | set(__all__))
