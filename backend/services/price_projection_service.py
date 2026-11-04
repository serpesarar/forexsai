"""Price Projection Service — "nereye kadar?" motoru (2026-07-10).

Klasik trader hedef-seviye tekniklerini GERÇEK veriden hesaplar (LLM tahmini
değil) ve tek bir snapshot'ta toplar. Debate ajanlarına, Claude Decider'a ve
panele beslenir. Kavramlar:

  1. Fibonacci retracement/extension  — son belirgin impulstan (swing A→B)
  2. Measured Move                    — |A→B| büyüklüğünün C'den projeksiyonu
  3. ADR (Average Daily Range)        — 20 günlük ort. gün içi menzil +
                                        bugün ne kadarı kullanıldı (tükenme)
  4. Volatility expansion/squeeze     — ATR & BB-genişlik yüzdelik dilimleri
  5. Mean-reversion stretch           — günlük EMA20'den ATR-birimlik sapma
  6. ORB (Opening Range Breakout)     — seans ilk-15dk aralığı + kırılım
                                        (⚠ backtest edge'i YOK — sadece bağlam)
  7. Conditional probability          — AYRICA HESAPLANMAZ: sistemin sızıntısız
                                        confluence base-rate playbook'u zaten bu
                                        (cortex_confluence_rules → CIO'ya gider)
  8. Market Profile                   — 5 günlük 5m hacim-fiyat histogramından
                                        POC / VAH / VAL (%70 value area)

Tamamı fail-open: veri yoksa bölüm None döner, asla uydurulmaz.
Veri yolu: data_fetcher (DataHub) → yetersizse Supabase candle_cache fallback,
böylece hem canlı backend'de hem standalone araçlarda çalışır.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_FIB_RETR = (0.236, 0.382, 0.5, 0.618, 0.786)
_FIB_EXT = (1.272, 1.618, 2.0)
_ADR_DAYS = 20
_SWING_BARS = 120          # 1h bars scanned for the dominant impulse
_VOL_LOOKBACK_H1 = 1200    # ~60 gün 1h — ATR/BB yüzdelik dağılımı
_PROFILE_DAYS = 5
_PROFILE_BINS = 40
_CACHE_TTL_S = 300

_cache: Dict[str, tuple[float, dict]] = {}


# ── data loading (DataHub → candle_cache fallback) ────────────────────────────
def _norm(c: dict) -> Optional[dict]:
    def g(*keys):
        for k in keys:
            v = c.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
        return None
    o, h, l, cl = g("open", "o"), g("high", "h"), g("low", "l"), g("close", "c")
    if cl is None:
        return None
    ts = str(c.get("timestamp") or c.get("time") or c.get("candle_time") or "")
    return {"ts": ts, "open": o if o is not None else cl, "high": h if h is not None else cl,
            "low": l if l is not None else cl, "close": cl, "volume": g("volume", "v") or 0.0}


async def _load(symbol: str, timeframe: str, limit: int) -> List[dict]:
    candles: list = []
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, timeframe=timeframe, limit=limit) or []
    except Exception:
        candles = []
    if len(candles) < min(50, limit):
        try:
            from database.supabase_client import get_supabase_client, is_db_available
            if is_db_available():
                client = get_supabase_client()
                rows = (client.table("candle_cache")
                        .select("candle_time,open,high,low,close,volume")
                        .eq("symbol", symbol).eq("timeframe", timeframe)
                        .order("candle_time", desc=True).limit(limit).execute()
                        ).get("data") or []
                if len(rows) > len(candles):
                    candles = list(reversed(rows))
        except Exception as e:
            logger.debug("[projection] cache fallback failed %s %s: %s", symbol, timeframe, e)
    out = [n for n in (_norm(c) for c in candles) if n]
    out.sort(key=lambda x: x["ts"])
    return out


# ── 1+2) Fibonacci + Measured Move ────────────────────────────────────────────
def compute_fib(h1: List[dict], current_price: float) -> Optional[dict]:
    """Dominant impulse of the last _SWING_BARS 1h bars → retr/ext/measured move.

    Impulse yönü: pencere içindeki mutlak tepe ve dip'ten HANGİSİ daha yeni ise
    hareket ona doğru bitmiştir (tepe önce, dip sonra → düşüş impulsu)."""
    bars = h1[-_SWING_BARS:]
    if len(bars) < 30 or not current_price:
        return None
    hi_i = max(range(len(bars)), key=lambda i: bars[i]["high"])
    lo_i = min(range(len(bars)), key=lambda i: bars[i]["low"])
    A_hi, B_lo = bars[hi_i]["high"], bars[lo_i]["low"]
    size = A_hi - B_lo
    if size <= 0:
        return None
    down = lo_i > hi_i          # tepe önce → son impuls AŞAĞI
    if down:
        # düşüş A(=tepe)→B(=dip); retracement YUKARI geri alma seviyeleri
        retr = {f"{r:.3f}": round(B_lo + size * r, 2) for r in _FIB_RETR}
        ext = {f"{e:.3f}": round(A_hi - size * e, 2) for e in _FIB_EXT}   # dip altı hedefler
        mm_target = round(current_price - size, 2)   # measured move: C - |A→B|
    else:
        # yükseliş B(=dip)→A(=tepe); retracement AŞAĞI geri alma seviyeleri
        retr = {f"{r:.3f}": round(A_hi - size * r, 2) for r in _FIB_RETR}
        ext = {f"{e:.3f}": round(B_lo + size * e, 2) for e in _FIB_EXT}   # tepe üstü hedefler
        mm_target = round(current_price + size, 2)   # measured move: C + |A→B|
    return {
        "impulse": "down" if down else "up",
        "swing_high": round(A_hi, 2), "swing_low": round(B_lo, 2),
        "impulse_size": round(size, 2),
        "retracements": retr, "extensions": ext,
        "golden_618": retr["0.618"],
        "measured_move_target": mm_target,
    }


# ── 3) ADR ────────────────────────────────────────────────────────────────────
def compute_adr(h1: List[dict], current_price: float) -> Optional[dict]:
    days: Dict[str, dict] = {}
    for b in h1:
        d = b["ts"][:10]
        if not d:
            continue
        e = days.setdefault(d, {"high": b["high"], "low": b["low"], "open": b["open"]})
        e["high"] = max(e["high"], b["high"])
        e["low"] = min(e["low"], b["low"])
    keys = sorted(days)
    if len(keys) < 6:
        return None
    today_key, hist_keys = keys[-1], keys[-1 - _ADR_DAYS:-1]
    ranges = [days[k]["high"] - days[k]["low"] for k in hist_keys
              if days[k]["high"] > days[k]["low"]]
    if not ranges:
        return None
    adr = sum(ranges) / len(ranges)
    t = days[today_key]
    used = t["high"] - t["low"]
    return {
        "adr_points": round(adr, 2),
        "adr_pct": round(adr / current_price * 100, 2) if current_price else None,
        "today_range": round(used, 2),
        "today_used_pct": round(used / adr * 100, 1),
        "exhausted": used >= adr * 0.9,
        "projected_high_from_low": round(t["low"] + adr, 2),
        "projected_low_from_high": round(t["high"] - adr, 2),
    }


# ── 4) Volatility state ───────────────────────────────────────────────────────
def _atr_series(bars: List[dict], n: int = 14) -> List[float]:
    trs, out, prev_close = [], [], None
    for b in bars:
        tr = b["high"] - b["low"]
        if prev_close is not None:
            tr = max(tr, abs(b["high"] - prev_close), abs(b["low"] - prev_close))
        prev_close = b["close"]
        trs.append(tr)
        if len(trs) >= n:
            out.append(sum(trs[-n:]) / n)
    return out


def _pctile(series: List[float], value: float) -> Optional[float]:
    if not series:
        return None
    below = sum(1 for s in series if s <= value)
    return round(below / len(series) * 100, 1)


def compute_vol_state(h1: List[dict]) -> Optional[dict]:
    if len(h1) < 120:
        return None
    atrs = _atr_series(h1)
    if not atrs:
        return None
    atr_now = atrs[-1]
    atr_pct = _pctile(atrs, atr_now)
    closes = [b["close"] for b in h1]
    widths = []
    for i in range(20, len(closes)):
        w = closes[i - 20:i]
        m = sum(w) / 20
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / 20)
        widths.append(4 * sd / m * 100 if m else 0.0)
    bb_pct = _pctile(widths, widths[-1]) if widths else None
    state = "normal"
    if atr_pct is not None and bb_pct is not None:
        if atr_pct <= 25 and bb_pct <= 25:
            state = "squeeze"           # sıkışma → genişleme potansiyeli
        elif atr_pct >= 80:
            state = "expanding"
    return {"atr14_1h": round(atr_now, 3), "atr_percentile": atr_pct,
            "bb_width_percentile": bb_pct, "state": state}


# ── 5) Mean-reversion stretch ─────────────────────────────────────────────────
def compute_mean_reversion(h1: List[dict], current_price: float) -> Optional[dict]:
    days: Dict[str, float] = {}
    for b in h1:
        d = b["ts"][:10]
        if d:
            days[d] = b["close"]
    closes_d = [days[k] for k in sorted(days)]
    if len(closes_d) < 21 or not current_price:
        return None
    ema, k = closes_d[0], 2 / 21
    for c in closes_d[1:]:
        ema = c * k + ema * (1 - k)
    dranges = []
    keys = sorted(days)
    for i in range(1, len(keys)):
        dranges.append(abs(days[keys[i]] - days[keys[i - 1]]))
    atr_d = sum(dranges[-14:]) / min(14, len(dranges)) if dranges else None
    stretch = round((current_price - ema) / atr_d, 2) if atr_d else None
    # 1h RSI14
    closes_h = [b["close"] for b in h1]
    gains = losses = 0.0
    for i in range(max(1, len(closes_h) - 14), len(closes_h)):
        d = closes_h[i] - closes_h[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    rsi = round(100 - 100 / (1 + gains / losses), 1) if losses else 100.0
    return {"ema20_daily": round(ema, 2), "stretch_atr": stretch,
            "rsi14_1h": rsi,
            "stretched": stretch is not None and abs(stretch) >= 2.0}


# ── 6) ORB — sadece bağlam (backtest edge'i YOK, dürüst etiketli) ─────────────
def compute_orb(m5: List[dict], current_price: float) -> Optional[dict]:
    if not m5 or not current_price:
        return None
    today = m5[-1]["ts"][:10]
    todays = [b for b in m5 if b["ts"][:10] == today]
    if len(todays) < 4:
        return None
    first3 = todays[:3]     # ilk 15 dakika
    hi = max(b["high"] for b in first3)
    lo = min(b["low"] for b in first3)
    status = "inside"
    if current_price > hi:
        status = "broken_up"
    elif current_price < lo:
        status = "broken_down"
    return {"or15_high": round(hi, 2), "or15_low": round(lo, 2), "status": status,
            "note": "context-only: ORB backtest edge'i bu sistemde kanıtlanamadı"}


# ── 8) Market Profile (POC / VAH / VAL) ───────────────────────────────────────
def compute_market_profile(m5: List[dict], current_price: float) -> Optional[dict]:
    days = sorted({b["ts"][:10] for b in m5 if b["ts"]})[-_PROFILE_DAYS:]
    bars = [b for b in m5 if b["ts"][:10] in days and b["volume"] > 0]
    if len(bars) < 100:
        return None
    lo = min(b["low"] for b in bars)
    hi = max(b["high"] for b in bars)
    if hi <= lo:
        return None
    step = (hi - lo) / _PROFILE_BINS
    vols = [0.0] * _PROFILE_BINS
    for b in bars:
        mid = (b["high"] + b["low"]) / 2
        idx = min(_PROFILE_BINS - 1, max(0, int((mid - lo) / step)))
        vols[idx] += b["volume"]
    total = sum(vols)
    if total <= 0:
        return None
    poc_i = max(range(_PROFILE_BINS), key=lambda i: vols[i])
    # %70 value area: POC'tan iki yana genişle
    included, acc = {poc_i}, vols[poc_i]
    left, right = poc_i - 1, poc_i + 1
    while acc < total * 0.70 and (left >= 0 or right < _PROFILE_BINS):
        lv = vols[left] if left >= 0 else -1
        rv = vols[right] if right < _PROFILE_BINS else -1
        if lv >= rv:
            included.add(left); acc += max(lv, 0); left -= 1
        else:
            included.add(right); acc += max(rv, 0); right += 1
    va_bins = sorted(included)
    val = lo + va_bins[0] * step
    vah = lo + (va_bins[-1] + 1) * step
    poc = lo + (poc_i + 0.5) * step
    pos = "inside_value"
    if current_price and current_price > vah:
        pos = "above_value"       # piyasa bu fiyatı henüz 'kabul etmedi'
    elif current_price and current_price < val:
        pos = "below_value"
    return {"poc": round(poc, 2), "vah": round(vah, 2), "val": round(val, 2),
            "price_vs_value": pos, "days": len(days)}


# ── snapshot + prompt block ───────────────────────────────────────────────────
async def projection_snapshot(symbol: str, current_price: Optional[float] = None) -> dict:
    """Tüm hedef-seviye hesaplarını tek dict'te toplar (5dk cache, fail-open)."""
    import time
    now = time.time()
    hit = _cache.get(symbol)
    if hit and now - hit[0] < _CACHE_TTL_S:
        return hit[1]

    h1 = await _load(symbol, "1h", _VOL_LOOKBACK_H1)
    m5 = await _load(symbol, "5m", 1600)
    if current_price is None:
        try:
            from services.data_fetcher import fetch_latest_price
            current_price = await fetch_latest_price(symbol)
        except Exception:
            current_price = None
    if not current_price and h1:
        current_price = h1[-1]["close"]

    snap: dict[str, Any] = {"symbol": symbol, "price": current_price,
                            "generated_at": datetime.now(timezone.utc).isoformat()}
    for key, fn, args in (
        ("fib", compute_fib, (h1, current_price)),
        ("adr", compute_adr, (h1, current_price)),
        ("vol", compute_vol_state, (h1,)),
        ("mean_reversion", compute_mean_reversion, (h1, current_price)),
        ("orb", compute_orb, (m5, current_price)),
        ("market_profile", compute_market_profile, (m5, current_price)),
    ):
        try:
            snap[key] = fn(*args)
        except Exception as e:
            logger.debug("[projection] %s.%s failed: %s", symbol, key, e)
            snap[key] = None

    _cache[symbol] = (now, snap)
    return snap


def projection_prompt_block(snap: dict) -> str:
    """LLM ajanları için kompakt, gerçek-sayılı satırlar."""
    if not snap:
        return ""
    lines: list[str] = []
    f = snap.get("fib")
    if f:
        r = f["retracements"]
        lines.append(
            f"REAL Fibonacci (last {f['impulse'].upper()} impulse "
            f"{f['swing_high']}→{f['swing_low']}, size {f['impulse_size']}): "
            f"retr 38.2%={r['0.382']} 50%={r['0.500']} 61.8%={r['0.618']} | "
            f"ext 127.2%={f['extensions']['1.272']} 161.8%={f['extensions']['1.618']} | "
            f"measured-move target={f['measured_move_target']}")
    a = snap.get("adr")
    if a:
        lines.append(
            f"REAL ADR({_ADR_DAYS}d): {a['adr_points']} pts ({a['adr_pct']}%) | today used "
            f"{a['today_used_pct']}%{' — EXHAUSTED, continuation harder' if a['exhausted'] else ''} | "
            f"ADR-projected high {a['projected_high_from_low']} / low {a['projected_low_from_high']}")
    v = snap.get("vol")
    if v:
        lines.append(
            f"REAL volatility state: {v['state'].upper()} (ATR pctile {v['atr_percentile']}, "
            f"BB-width pctile {v['bb_width_percentile']})"
            + (" — squeeze: büyük hareket potansiyeli, yön belirsiz" if v["state"] == "squeeze" else ""))
    m = snap.get("mean_reversion")
    if m:
        lines.append(
            f"REAL mean-reversion: price vs daily EMA20 = {m['stretch_atr']} ATR | RSI14(1h)={m['rsi14_1h']}"
            + (" — STRETCHED (reversion riski; güçlü trendde tehlikeli sinyal)" if m["stretched"] else ""))
    o = snap.get("orb")
    if o:
        lines.append(
            f"Opening range (first 15m): {o['or15_low']}–{o['or15_high']} | status: {o['status']} "
            f"(context-only; no proven edge in our backtests)")
    mp = snap.get("market_profile")
    if mp:
        lines.append(
            f"REAL Market Profile ({mp['days']}d, 5m volume): POC={mp['poc']} "
            f"VAH={mp['vah']} VAL={mp['val']} | price is {mp['price_vs_value'].replace('_', ' ')}")
    return "\n".join(lines)
