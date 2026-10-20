"""Mum benzerlik motoru — son N mumu geçmişteki görsel olarak benzer N mumlarla otomatik eşleştirir.

Görsel benzerlik tanımı (TradingView oto-ölçek ile birebir):
  Her N mumluk pencere kendi [en düşük, en yüksek] aralığına sıkıştırılır → her mumun açılış/yüksek/düşük/kapanış
  noktası 0..1 arası bir "piksel" konumu olur (4N sayı). İki grafik ekranda aynı görünüyorsa bu 4N sayı aynıdır.
  Mesafe = konum farklarının karekök-ortalaması (RMS); mum mum, gövde + fitil birlikte. Ölçekten (fiyat düzeyi,
  hareketin yüzdesi) ve zaman diliminden bağımsız.
Hızlı tarama: kayan toplamlar + np.correlate ile ~100 bin pencere tek geçişte (büyük matris kurulmaz).

Dürüstlük: ME-02…ME-11 sınamalarında eşleşmelerin YÖN isabeti rastgele komşudan farksız çıktı. Bu motor bilgi
amaçlıdır; çıktı her zaman koşulsuz taban + aynı-saat tipik hareket tabanıyla birlikte ve geçmiş isabet karnesiyle
(`backend/data/candle_similarity_reliability.json`, üretici `backend/scripts/candle_similarity_backtest.py`) döner.
Geçmiş arşiv: `backend/data/candle_history/` (üretici `backend/scripts/build_candle_history.py`).
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_DIR = DATA_DIR / "candle_history"
RELIABILITY_FILE = DATA_DIR / "candle_similarity_reliability.json"

SYMBOLS = {"NDX": "NDX.INDX", "NAS100": "NDX.INDX", "NDX.INDX": "NDX.INDX", "DAX": "GDAXI.INDX",
           "GDAXI": "GDAXI.INDX", "GDAXI.INDX": "GDAXI.INDX", "XAU": "XAUUSD", "XAUUSD": "XAUUSD",
           "GOLD": "XAUUSD", "USOIL": "USOIL.FOREX", "OIL": "USOIL.FOREX", "USOIL.FOREX": "USOIL.FOREX"}
TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h")
TF_SECONDS = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}
HORIZONS = {"5m": (6, 12, 48), "15m": (4, 16, 32), "30m": (2, 8, 16), "1h": (4, 8, 24), "4h": (3, 6, 30)}
WINDOW_MIN, WINDOW_MAX = 10, 300
TOP_K_MAX = 50
CHART_MATCHES = 10
GAP_MAX_S = 4 * 86400            # pencere/ufuk içinde > 4 gün veri boşluğu → aday değil (tatil/kesinti)
PARTITION_POOL = 4000            # dedup öncesi en yakın aday havuzu
CACHE_TTL_S = 60
LIVE_TRUST = ("NDX.INDX", "GDAXI.INDX")   # canlı DataHub mumları broker verisi (emtia Yahoo vadelisi → yalnız arşiv)


@dataclass(frozen=True)
class Series:
    ts: np.ndarray        # int64 UTC saniye
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray


# ═════════════════════════════ saf çekirdek ═════════════════════════════

def normalize_window(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray) -> np.ndarray | None:
    """N mumu (N, 4) 0..1 konumlarına çevir (oto-ölçek). Aralık sıfırsa None."""
    lo, hi = float(np.min(l)), float(np.max(h))
    if not hi > lo:
        return None
    return (np.column_stack([o, h, l, c]) - lo) / (hi - lo)


def _rolling_sum(x: np.ndarray, n: int) -> np.ndarray:
    cs = np.concatenate([[0.0], np.cumsum(x)])
    return cs[n:] - cs[:-n]


def window_rms(s: Series, q: np.ndarray) -> np.ndarray:
    """Her kayan pencere (başlangıç i, uzunluk N) için oto-ölçekli OHLC konumlarının sorguya RMS mesafesi.

    Dönüş uzunluğu len(s) − N + 1; indeks = pencere başlangıcı. Aralığı sıfır pencereler inf.
    Σ((A−L)/R − q)² = [ΣA² − 2LΣA + NL²]/R² − 2[A·q − LΣq]/R + Σq²  (her OHLC sütunu için).
    """
    n = q.shape[0]
    off = float(np.median(s.c))                        # sayısal sağlamlık: öteleme mesafeyi değiştirmez
    cols = [s.o - off, s.h - off, s.l - off, s.c - off]
    lo = pd.Series(cols[2]).rolling(n).min().to_numpy()[n - 1:]
    hi = pd.Series(cols[1]).rolling(n).max().to_numpy()[n - 1:]
    rng = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = np.where(rng > 0, 1.0 / rng, np.nan)
        tot = np.zeros(len(lo))
        for a, qa in zip(cols, q.T):
            s1, s2 = _rolling_sum(a, n), _rolling_sum(a * a, n)
            dot = np.correlate(a, qa, mode="valid")
            tot += (s2 - 2 * lo * s1 + n * lo * lo) * inv * inv - 2 * (dot - lo * qa.sum()) * inv + float(qa @ qa)
        rms = np.sqrt(np.maximum(tot, 0.0) / (4 * n))
    return np.where(np.isfinite(rms), rms, np.inf)


def valid_starts(s: Series, n: int, h_max: int, end_before_ts: int | None) -> np.ndarray:
    """Aday pencere başlangıçları: ileri ufuk verisi var, içinde büyük boşluk yok, sorguyla çakışmıyor."""
    m = len(s.ts) - n + 1
    starts = np.arange(m)
    ok = starts + n - 1 + h_max < len(s.ts)
    gap = np.concatenate([[0], (np.diff(s.ts) > GAP_MAX_S).astype(np.int64)])
    gcs = np.concatenate([[0], np.cumsum(gap)])
    span_end = np.minimum(starts + n - 1 + h_max, len(s.ts) - 1)
    ok &= (gcs[span_end + 1] - gcs[starts + 1]) == 0
    if end_before_ts is not None:
        ok &= s.ts[span_end] < end_before_ts
    return ok


def pick_matches(dist: np.ndarray, ok: np.ndarray, k: int, gap: int) -> np.ndarray:
    """En yakın k pencere; seçilenlerin başlangıçları arası ≥ gap bar (aynı olayın kaydırılmış kopyaları değil)."""
    d = np.where(ok, dist, np.inf)
    pool = min(PARTITION_POOL, int(np.isfinite(d).sum()))
    if pool == 0:
        return np.array([], dtype=np.int64)
    cand = np.argpartition(d, pool - 1)[:pool]
    cand = cand[np.argsort(d[cand], kind="stable")]
    kept: list[int] = []
    for i in cand.tolist():
        if all(abs(i - j) >= gap for j in kept):
            kept.append(i)
            if len(kept) >= k:
                break
    return np.array(kept, dtype=np.int64)


def binom_two_sided(k: int, n: int, p: float) -> float:
    if n == 0 or not 0 < p < 1:
        return 1.0
    pk = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
    tot = sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(n + 1)
              if math.comb(n, j) * p ** j * (1 - p) ** (n - j) <= pk * (1 + 1e-9))
    return float(min(1.0, tot))


def forward_stats(s: Series, ends: np.ndarray, hs: tuple[int, ...]) -> dict[int, np.ndarray]:
    """Her uç bar için H bar sonraki getiri (oran)."""
    return {h: s.c[ends + h] / s.c[ends] - 1.0 for h in hs}


def summarize(ret: np.ndarray, base: np.ndarray, price: float) -> dict[str, Any]:
    up = int((ret > 0).sum())
    p_base = float((base > 0).mean()) if len(base) else 0.5
    return {"n": int(len(ret)), "up_pct": 100 * up / len(ret) if len(ret) else None,
            "median_pct": 100 * float(np.median(ret)) if len(ret) else None,
            "mean_pct": 100 * float(np.mean(ret)) if len(ret) else None,
            "q25_pct": 100 * float(np.percentile(ret, 25)) if len(ret) else None,
            "q75_pct": 100 * float(np.percentile(ret, 75)) if len(ret) else None,
            "median_points": float(np.median(ret) * price) if len(ret) else None,
            "base_up_pct": 100 * p_base, "base_median_abs_pct": 100 * float(np.median(np.abs(base))) if len(base) else None,
            "p_value_vs_base": binom_two_sided(up, len(ret), p_base) if len(ret) else None}


def match_core(s: Series, q: Series, tf: str, n: int, k: int, end_before_ts: int | None = None) -> dict[str, Any]:
    """Saf eşleştirme (I/O yok). q: sorgunun son n mumu. s: kütüphane. Geriye-dönük sınamada da aynen kullanılır."""
    hs = HORIZONS[tf]
    qn = normalize_window(q.o[-n:], q.h[-n:], q.l[-n:], q.c[-n:])
    if qn is None or len(s.ts) < n + max(hs) + 10:
        return {"error": "yetersiz veri"}
    dist = window_rms(s, qn)
    ok = valid_starts(s, n, max(hs), end_before_ts)
    starts = pick_matches(dist, ok, k, gap=max(1, n // 2))
    if len(starts) == 0:
        return {"error": "aday yok"}
    ends = starts + n - 1
    lib_ends = np.flatnonzero(ok) + n - 1
    ref_rms = float(np.median(dist[ok])) if ok.any() else float("nan")
    price = float(q.c[-1])
    fwd, base = forward_stats(s, ends, hs), forward_stats(s, lib_ends, hs)
    q_hour = pd.Timestamp(int(q.ts[-1]), unit="s", tz="UTC").hour
    same_hour = pd.to_datetime(s.ts[lib_ends], unit="s", utc=True).hour == q_hour
    horizons = {}
    for h in hs:
        row = summarize(fwd[h], base[h], price)
        if tf != "4h":
            row["hour_median_abs_pct"] = 100 * float(np.median(np.abs(base[h][same_hour]))) if same_hour.any() else None
        horizons[str(h)] = row
    return {"matches_idx": starts, "dist": dist[starts], "ref_rms": ref_rms, "n_candidates": int(ok.sum()),
            "rank_pct": [100 * float((dist[ok] < d).mean()) for d in dist[starts]], "horizons": horizons,
            "query_norm": qn}


# ═════════════════════════════ veri ═════════════════════════════

def canonical(symbol: str) -> str:
    key = symbol.upper().strip()
    if key not in SYMBOLS:
        raise ValueError(f"desteklenmeyen sembol: {symbol}")
    return SYMBOLS[key]


@lru_cache(maxsize=24)
def load_history(symbol: str, tf: str) -> Series:
    path = HISTORY_DIR / f"{symbol.split('.')[0]}_{tf}.npz"
    if not path.exists():
        raise FileNotFoundError(f"geçmiş arşivi yok: {path.name} — python3 backend/scripts/build_candle_history.py")
    with np.load(path) as z:
        return Series(z["ts"].astype(np.int64), *(z[c].astype(np.float64) for c in ("open", "high", "low", "close")))


async def _live_series(symbol: str, tf: str, n: int) -> Series | None:
    """DataHub'dan son kapanmış n mum (yalnız broker beslemeli semboller)."""
    if symbol not in LIVE_TRUST:
        return None
    try:
        from services.data_fetcher import fetch_ohlc_data
        rows = await fetch_ohlc_data(symbol, tf, n + 5)
    except Exception as e:                                      # pragma: no cover
        logger.warning("candle-similarity canlı mum alınamadı %s %s: %s", symbol, tf, e)
        return None
    now = time.time()
    rows = [r for r in rows if r.get("timestamp") and r["timestamp"] / 1000 + TF_SECONDS[tf] <= now]
    if len(rows) < n:
        return None
    rows = rows[-n:]
    ts = np.array([int(r["timestamp"] // 1000) for r in rows], dtype=np.int64)
    arr = {c: np.array([float(r[c]) for r in rows]) for c in ("open", "high", "low", "close")}
    return Series(ts, arr["open"], arr["high"], arr["low"], arr["close"])


def _slice(s: Series, a: int, b: int) -> Series:
    return Series(s.ts[a:b], s.o[a:b], s.h[a:b], s.l[a:b], s.c[a:b])


def load_reliability() -> dict[str, Any]:
    try:
        return json.loads(RELIABILITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ═════════════════════════════ yanıt ═════════════════════════════

def _iso(t: int) -> str:
    return pd.Timestamp(int(t), unit="s", tz="UTC").isoformat()


def _chart_match(s: Series, start: int, n: int, h_max: int) -> dict[str, Any]:
    a, b = start, start + n
    lo, hi = float(s.l[a:b].min()), float(s.h[a:b].max())
    cont = slice(b, b + h_max)
    norm = lambda arr: np.round((arr - lo) / (hi - lo), 4).tolist()  # noqa: E731
    return {"window": np.column_stack([norm(s.o[a:b]), norm(s.h[a:b]), norm(s.l[a:b]), norm(s.c[a:b])]).tolist(),
            "future": np.column_stack([norm(s.o[cont]), norm(s.h[cont]), norm(s.l[cont]), norm(s.c[cont])]).tolist()}


def build_response(symbol: str, tf: str, n: int, k: int, s: Series, q: Series, source: str,
                   end_before_ts: int | None) -> dict[str, Any]:
    core = match_core(s, q, tf, n, k, end_before_ts)
    if "error" in core:
        return {"symbol": symbol, "timeframe": tf, "window": n, "error": core["error"]}
    hs, h_max = HORIZONS[tf], max(HORIZONS[tf])
    price = float(q.c[-1])
    matches = []
    for rank, (st, d, pr) in enumerate(zip(core["matches_idx"], core["dist"], core["rank_pct"])):
        e = int(st + n - 1)
        row = {"rank": rank + 1, "start": _iso(s.ts[st]), "end": _iso(s.ts[e]),
               "similarity": round(max(0.0, 100 * (1 - float(d) / core["ref_rms"])), 1), "rms": round(float(d), 4),
               "rank_pct": round(pr, 4), "end_close": float(s.c[e]),
               "fwd_pct": {str(h): round(100 * (s.c[e + h] / s.c[e] - 1), 3) for h in hs},
               "mfe_pct": round(100 * (s.h[e + 1:e + 1 + h_max].max() / s.c[e] - 1), 3),
               "mae_pct": round(100 * (s.l[e + 1:e + 1 + h_max].min() / s.c[e] - 1), 3)}
        if rank < CHART_MATCHES:
            row["chart"] = _chart_match(s, int(st), n, h_max)
        matches.append(row)
    rel = load_reliability().get(f"{symbol}|{tf}|{n}")
    return {"symbol": symbol, "timeframe": tf, "window": n, "source": source, "price": price,
            "query": {"start": _iso(q.ts[-n]), "end": _iso(q.ts[-1]), "chart": np.round(core["query_norm"], 4).tolist()},
            "library": {"start": _iso(s.ts[0]), "end": _iso(s.ts[-1]), "bars": int(len(s.ts)),
                        "candidates": core["n_candidates"]},
            "horizons_bars": list(hs), "horizons": core["horizons"], "matches": matches,
            "reliability": rel,
            "note": ("Bilgi amaçlıdır: geçmiş sınamalarda (ME-02…ME-11) eşleşmelerin yön isabeti rastgele komşudan "
                     "farksız çıktı. Hareket büyüklüğü için en iyi tahminci aynı saatin tipik hareketidir.")}


_cache: dict[tuple, tuple[float, dict]] = {}


async def get_similarity(symbol: str, tf: str = "1h", n: int = 50, k: int = 20) -> dict[str, Any]:
    sym = canonical(symbol)
    if tf not in TIMEFRAMES:
        raise ValueError(f"desteklenmeyen zaman dilimi: {tf}")
    n = int(min(max(n, WINDOW_MIN), WINDOW_MAX)); k = int(min(max(k, 1), TOP_K_MAX))
    s = load_history(sym, tf)
    live = await _live_series(sym, tf, n)
    if live is not None and live.ts[-1] > s.ts[-1]:
        q, source, end_before = live, "canli", int(live.ts[0])
    else:
        q, source, end_before = _slice(s, len(s.ts) - n, len(s.ts)), "arsiv_sonu", int(s.ts[-n])
    key = (sym, tf, n, k, int(q.ts[-1]))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        return hit[1]
    res = await asyncio.to_thread(build_response, sym, tf, n, k, s, q, source, end_before)
    _cache[key] = (time.time(), res)
    return res
