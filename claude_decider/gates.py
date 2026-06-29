"""
gates.py — Faz-1 ENTRY tetiği: yalnız DOĞRULANMIŞ 5m mean-reversion kapısı.
=============================================================================
Re-damıtma (2026-06-27, sr_rejection_research/step7-8): kapsamlı tarama tek-boyut
5m mean-reversion edge'ini 5 modelde de doğruladı (nested-CV OOS, placebo p=0).
Decider'ın entry tetiği BURADAN gelir — Claude entry İCAT ETMEZ, yalnız bağlam/veto/boyut.

Kapı (yön-hizalı): 5m'de fiyat ya linreg trend-çizgisinden rev_chan>2.0σ ya da
VWAP'tan rev_vwap>1.5σ sinyal yönünün TERSİNE aşırı → mean-reversion fırsatı.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decider_config as config  # noqa: E402
from channel_filter import is_mean_reversion  # noqa: E402

# ── Re-damıtılmış allow-list (per-sembol/yön, dürüst OOS ile kilitlendi) ──────
#   ✅ NDX BUY/SELL · GDAXI BUY/SELL · USOIL SELL · XAU BUY
#   ❌ USOIL BUY (OOS %10 çöker) · XAU SELL (OOS %20, kalıcı yasak)
ALLOW: dict[str, set[str]] = {
    "NDX.INDX":    {"BUY", "SELL"},
    "GDAXI.INDX":  {"BUY", "SELL"},
    "USOIL.FOREX": {"SELL"},
    "XAUUSD":      {"BUY"},
}

# Re-damıtılmış base rate'ler (gate_WR%, OOS_WR%) — Claude'a prior olarak verilir
GATE_WR: dict[tuple[str, str], tuple[int, int]] = {
    ("GDAXI.INDX", "BUY"): (89, 80), ("GDAXI.INDX", "SELL"): (79, 66),
    ("NDX.INDX", "BUY"): (84, 75),   ("NDX.INDX", "SELL"): (80, 74),
    ("USOIL.FOREX", "SELL"): (91, 92),
    ("XAUUSD", "BUY"): (91, 84),
}

# Re-damıtılmış kapı eşikleri (modele bağlı değil — sembol-agnostik fiziksel kapı)
CHAN_Z = 2.0    # linreg trend-çizgisinden ≥2.0σ ters yönde
VWAP_Z = 1.5    # rolling VWAP'tan ≥1.5σ ters yönde
WIN_N = 50      # pencere (bar)


VIX_NEUTRAL_BAND = 0.4   # |VIX − eşik| < bu → neutral (knife-edge gürültüsünü önle)
try:
    from zoneinfo import ZoneInfo
    _NY = ZoneInfo("America/New_York")
except Exception:
    _NY = None


def _us_rth_open(now=None) -> bool:
    """US cash market açık mı? (^VIX yalnız o zaman CANLI; dışında yfinance spot DONUK).
    DST-doğru: America/New_York 09:30–16:00, Pzt–Cum. zoneinfo yoksa UTC fallback (EDT varsayar)."""
    from datetime import datetime, timezone
    now = now or datetime.now(timezone.utc)
    if _NY is None:
        h = now.hour + now.minute / 60.0
        return now.weekday() < 5 and 13.5 <= h < 20.0
    t = now.astimezone(_NY)
    if t.weekday() >= 5:
        return False
    mins = t.hour * 60 + t.minute
    return 9 * 60 + 30 <= mins < 16 * 60


def vix_regime(vix: float | None, now=None, live_24h: bool = False) -> tuple[str | None, str]:
    """VIX → NDX favored yön (eşik-dışı iken). Dönüş: (favored|None, label).
    live_24h=False (yfinance ^VIX spot): yalnız US RTH'de geçerli, off-hours bayat → favored=None.
    live_24h=True (Pepperstone MT5 futures, 24h canlı): RTH-kapısı GEREKMEZ, her saat geçerli."""
    if vix is None:
        return None, "unknown"
    if not live_24h and not _us_rth_open(now):
        return None, "stale_offhours"        # spot ^VIX off-hours donuk → yön VERME
    thr = config.VIX_REGIME_THRESHOLD
    if abs(vix - thr) < VIX_NEUTRAL_BAND:
        return None, "neutral_band"          # bıçak-sırtı → yön VERME
    return ("BUY", "stress") if vix >= thr else ("SELL", "calm")


def _blocked(symbol: str, direction: str) -> bool:
    return (symbol, direction) in getattr(config, "BLOCKED_SYMBOL_DIRECTIONS", set())


def evaluate_gates(bars_by_symbol: dict[str, list[dict]],
                   vix: float | None = None) -> list[dict]:
    """Mekanik kapı taraması (LLM YOK — bedava). Her sembol×izinli-yön için 5m
    mean-reversion kapısını dener. Dönüş: tetiklenen aday işlemler listesi.

    bars_by_symbol: {forexsai_sym: [{high,low,close,volume}, ...]}  (5m, eski→yeni)
    """
    candidates: list[dict] = []
    for symbol, dirs in ALLOW.items():
        bars = bars_by_symbol.get(symbol)
        if not bars or len(bars) < WIN_N:
            continue
        for direction in dirs:
            if _blocked(symbol, direction):
                continue
            ok, source, z = is_mean_reversion(bars, direction, n=WIN_N,
                                              chan_z=CHAN_Z, vwap_z=VWAP_Z)
            if not ok:
                continue
            cand = {
                "symbol": symbol,
                "dir": direction,
                "gate": {"source": source, "z": z, "thr": CHAN_Z if source == "channel" else VWAP_Z},
                "prior_wr": GATE_WR.get((symbol, direction)),  # (gate%, oos%) | None
            }
            if symbol == config.VIX_REGIME_SYMBOL:   # NDX → VIX bağlamı ekle
                fav, label = vix_regime(vix)
                cand["vix"] = {"value": vix, "favored": fav, "regime": label,
                               "aligned": (fav == direction) if fav else None}
            candidates.append(cand)
    return candidates


if __name__ == "__main__":
    # hızlı kendi-test: sentetik aşırı-oversold 5m serisi → NDX BUY kapısı tetiklenmeli
    import math
    base = [{"high": 100 + math.sin(i / 5), "low": 99 + math.sin(i / 5),
             "close": 100 + math.sin(i / 5), "volume": 1000} for i in range(60)]
    base[-1] = {"high": 95.1, "low": 94.8, "close": 95.0, "volume": 5000}  # sert düşüş = oversold
    cands = evaluate_gates({"NDX.INDX": base}, vix=21.3)
    print("Tetiklenen adaylar:", cands)
