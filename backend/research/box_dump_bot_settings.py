"""box_dump_bot_settings.py — kutudaki botun ETKİN ayarlarını dökümler.

`yeni deneme/config.py` gitignore'da olduğu için panel tarafı gerçek değerleri
göremez. Bu script yalnız BEYAZ LİSTEdeki ayarları yazdırır (şifre/anahtar
asla yazdırılmaz) ve kodun getattr varsayılanıyla karşılaştırır.

Çalıştırma (kutuda): python backend/research/box_dump_bot_settings.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

import config  # type: ignore  # noqa: E402

# (ad, kodun varsayılanı) — config'te yoksa varsayılan geçerlidir.
KEYS = [
    ("SYMBOL_MAP", None), ("ROBUST_SCOPES", None),
    ("MOMENTUM_FILTERED_SCOPES", None), ("BLOCKED_SYMBOL_DIRECTIONS", set()),
    ("LOT_SIZE", None), ("SCOPE_LOTS", None), ("POLL_SECONDS", 60),
    ("MIN_MODEL_VOTES", 1), ("ONLY_CONFIRM_SIGNALS", True),
    ("MAX_OPEN_PER_SCOPE", 1), ("MAX_TOTAL_POSITIONS", 6),
    ("DAILY_MAX_LOSS", 3000.0), ("LIVE_TRADING", False),
    ("USE_SR_ENTRY", True), ("HYBRID_ENTRY", True),
    ("MOMENTUM_EXCESS_ATR", 2.0), ("SESSION_MOM_FACTOR", None),
    ("HIGH_MOM_WINDOWS", None), ("QUIET_LOCAL", None),
    ("ZONE_LOOKBACK", 100), ("ZONE_MIN_TOUCH_CANDLES", 4),
    ("ZONE_WIDTH", None), ("SR_MAX_ENTRY_DIST", None), ("SR_MIN_TP_DIST", None),
    ("PENDING_EXPIRY_MIN", 30), ("SR_FALLBACK_MARKET", False),
    ("PULSE_ATR_GEOMETRY_BOT", None), ("ATR_GEOMETRY_SCOPES", None),
    ("CHANNEL_REVERSION_ENABLED", False), ("CHANNEL_REVERSION", None),
    ("CHANNEL_REVERSION_MODEL", "pulse3"), ("CHANNEL_REVERSION_MT5_TF", "30m"),
    ("CHREV_ADX_GATE_ENABLED", True), ("CHREV_ADX_GATE_BLOCK", True),
    ("CHREV_ADX_MAX", 25.0), ("CHREV_MODE_OVERRIDE", {}),
    ("VIX_REGIME_ENABLED", False), ("VIX_REGIME_THRESHOLD", 18.4),
    ("VIX_REGIME_MODELS", None), ("VIX_REGIME_TP", 80), ("VIX_REGIME_SL", 110),
    ("VIXREG_SL_ATR_ENABLED", True), ("VIXREG_SL_ATR_MULT", 2.0),
    ("VIXREG_SL_MIN", 60.0), ("VIXREG_SL_MAX", 200.0),
    ("VIXREG_SELL_PATIENCE", False), ("VIXREG_SELL_PATIENCE_MIN", 10),
    ("DAYCOMBO_ENABLED", True), ("DAYCOMBO_TP", 80.0), ("DAYCOMBO_SL", 110.0),
    ("USOIL_BREAKOUT_ENABLED", True), ("USOIL_BREAKOUT_LIVE", False),
    ("TQ_ENABLED", True), ("TQ_FRIDAY_COOL", True),
    ("TQ_COOL_HOURS_UTC", (15, 16, 17)), ("TQ_COOL_FAMILIES", ("vixreg", "chrev")),
    ("TQ_COOL_MIN_VOTERS", 2), ("TQ_FRIDAY_EXTRA_VOTES", 1),
    ("TQ_DECIDER_APPROVAL", True), ("TQ_DECIDER_FRESH_MIN", 45),
    ("TQ_DECIDER_MIN_SIZE", 0.3),
    ("TREND_GATE_ENABLED", True), ("VIXREG_TREND_GATE", True),
    ("POSITION_GATE_ENABLED", True), ("VIXREG_POSITION_GATE", True),
    ("POS_SELL_MIN", 0.40), ("POS_BUY_MAX", 0.60), ("POS_LOOKBACK_M5", 48),
    ("ENTRY_SCORE_GATE_ENABLED", True), ("ENTRY_SCORE_GATE_BLOCK", False),
    ("ENTRY_SCORE_GATE_CHREV", False), ("ENTRY_SCORE_MIN", 7),
    ("ENTRY_SCORE_SYMBOLS", None), ("SESSION_BLOCK_HOURS_UTC", None),
    ("VIX_REGIME_MICRO_GATE", True), ("VIX_REGIME_MICRO_BLOCK", False),
    ("BACKEND_ADVICE_ENABLED", True), ("VIXREG_BACKEND_VETO", False),
    ("CHREV_BACKEND_VETO", False),
    ("TRADE_MGMT_ENABLED", True), ("MGMT_BE_MINUTES", 30), ("MGMT_TRAIL_R", 0.6),
    ("MGMT_INCLUDE_CHREV", True), ("MGMT_RUNNER_MIN_TP_SL_RATIO", 0.4),
    ("REFLEX_ENABLED", True), ("REFLEX_LIVE", False),
    ("SHADOW_SCOPES_ENABLED", True), ("SHADOW_SCOPES", None),
    ("FOREXSAI_API", None),
]

SECRET_HINT = ("PASSWORD", "KEY", "SECRET", "TOKEN", "ACCOUNT")


def main() -> None:
    print(f"{'AYAR':<32} {'DEĞER':<46} KAYNAK")
    for name, default in KEYS:
        if any(h in name for h in SECRET_HINT):
            continue
        if hasattr(config, name):
            val, src = getattr(config, name), "config"
        else:
            val, src = default, "varsayılan(kod)"
        s = str(val)
        if len(s) > 300:
            s = s[:300] + "…"
        print(f"{name:<32} {s:<46} {src}")


if __name__ == "__main__":
    main()
