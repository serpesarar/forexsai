"""Zaman Makinesi — bir işlem planının (yön, stop, hedef, ufuk) olasılıklarını, sembolün KENDİ son 60 seansının aynı
gün-saatindeki 5 dakikalık mumlarından 10.000'e kadar simülasyonla ve aynı planın geçmiş seanslardaki gerçek sonucuyla verir.

Uyarlandığı kaynak: github.com/jakeschincariol/day-trader-skill, trader-timemachine/timemachine.py
(MIT License, Copyright (c) 2026 Jake Schincariol — izin metni lisans gereği aşağıda korunur). Değişiklikler:
  * Hisse seansı (9:30–16:00, 78 bar) yerine CFD broker günü: NY 17:00 → 17:00, slot = o andan beri 5 dk sayısı.
    Bir günün bir slotu boşsa (bakım arası/tatil) o gün o slot için havuza katkı vermez; boş slotta pencere genişler.
  * ORB kuralı yerine genel plan: giriş = son KAPANMIŞ 5m mum; stop = giriş ∓ stop_atr × ATR14(5m); hedef = target_r × risk.
  * Geçmiş tekrarı: aynı plan, havuzdaki her geçmiş seansta AYNI SLOTTA, o anın ATR'siyle (gerçek sonuç, simülasyon değil).
  * Hüküm cümleleri Türkçe; eşikler aynı (başabaş 1/(1+R) ± 5 / 15 puan).
Algoritma (değiştirilmedi): her bar (o, h, l, c) / önceki kapanış oranı; replay her adımda aynı slotun ± pencere
içinden rastgele bir geçmiş bar seçip güncel fiyata ölçekler; her barda ÖNCE stop, sonra hedef (ikisi birden → stop).

MIT License — Copyright (c) 2026 Jake Schincariol. Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
following conditions: The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Simülasyon tahmin değildir: son 60 seansın gün-içi davranışından kurulmuş olasılıktır; haber/veri günleri onu aşabilir.
"""
from __future__ import annotations

import asyncio
import logging
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

logger = logging.getLogger(__name__)

NY = ZoneInfo("America/New_York")
BAR_S = 300
SLOTS = 288                    # 24 saat × 12 beşer dakika
DAY_START_MIN = 17 * 60        # broker günü NY 17:00'de başlar
POOL_SESSIONS = 60
MIN_SESSIONS = 20
MIN_DAY_FRACTION = 0.8         # bir seansın havuza girmesi için tipik bar sayısının en az bu kadarı
ATR_N = 14
WINDOW = 2
MAX_WINDOW = 6
PREV_GAP_S = 3 * 3600          # önceki bar bundan uzaksa (hafta sonu/tatil) oran havuza girmez
REPLAYS_DEFAULT = 5000
REPLAYS_MAX = 20000
SEED_DEFAULT = 19
SAMPLE_PATHS = 60
BAND_PATHS = 1000
BAND_Q = (0.05, 0.25, 0.5, 0.75, 0.95)
COIN_FLIP = 0.05
STRONG = 0.15
MANY_NEITHER = 0.40
LOAD_DAYS = 95
CACHE_TTL_S = 300


class TMError(ValueError):
    """Plan veya veri simülasyona uygun değil (kullanıcıya düz cümleyle döner)."""


@dataclass
class Bars:
    ts: np.ndarray       # int64 UTC saniye (bar açılışı)
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray


# ═════════════════════════════ saf çekirdek ═════════════════════════════

def n_slots(bar_min: int) -> int:
    return 1440 // bar_min


def day_and_slot(ts: np.ndarray, bar_min: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Her bar için broker günü (NY 17:00 sınırlı, sıra numarası) ve slot (0..1440/bar_min − 1)."""
    day_keys, slots = np.empty(len(ts), dtype=np.int64), np.empty(len(ts), dtype=np.int64)
    for i, t in enumerate(ts.tolist()):
        ny = datetime.fromtimestamp(t, NY)
        shifted = ny - timedelta(minutes=DAY_START_MIN)
        day_keys[i] = shifted.toordinal()
        slots[i] = (shifted.hour * 60 + shifted.minute) // bar_min
    return day_keys, slots


def atr_series(b: Bars, n: int = ATR_N) -> np.ndarray:
    prev = np.r_[b.c[0], b.c[:-1]]
    tr = np.maximum(b.h - b.l, np.maximum(np.abs(b.h - prev), np.abs(b.l - prev)))
    out = np.full(len(tr), np.nan)
    if len(tr) >= n:
        cs = np.cumsum(tr)
        out[n - 1:] = (cs[n - 1:] - np.r_[0.0, cs[:-n]]) / n
    return out


def sessions_before(days: np.ndarray, slots: np.ndarray, before_day: int, keep: int = POOL_SESSIONS) -> list[dict]:
    """before_day'den ÖNCEKİ yeterince dolu seanslar (en eski → en yeni, son `keep` tanesi): [{day, idx: {slot: i}}]."""
    by_day: dict[int, dict[int, int]] = {}
    for i, (d, s) in enumerate(zip(days.tolist(), slots.tolist())):
        if d < before_day:
            by_day.setdefault(d, {})[s] = i
    if not by_day:
        return []
    typical = float(np.median([len(v) for v in by_day.values()]))
    full = [{"day": d, "idx": v} for d, v in sorted(by_day.items()) if len(v) >= MIN_DAY_FRACTION * typical]
    return full[-keep:]


def build_pool(b: Bars, sessions: list[dict], bar_min: int = 5) -> list[list[tuple[float, float, float, float]]]:
    """pool[slot] = geçmiş seansların o slottaki barı, bir önceki barın kapanışına oran olarak.

    Önceki bar = dizideki bir önceki bar, aralarında ≤ PREV_GAP_S varsa (günün ilk slotu önceki günün son barına
    bağlanır; CFD'de gün sınırı kesintisizdir — kaynak araçta seans kapanışı vardı, burada yok).
    """
    pool: list[list[tuple[float, float, float, float]]] = [[] for _ in range(n_slots(bar_min))]
    gap_s = max(PREV_GAP_S, 2 * bar_min * 60)
    for s in sessions:
        for slot, i in s["idx"].items():
            if i == 0 or b.c[i - 1] <= 0 or not 0 < b.ts[i] - b.ts[i - 1] <= gap_s:
                continue
            pc = b.c[i - 1]
            pool[slot].append((b.o[i] / pc, b.h[i] / pc, b.l[i] / pc, b.c[i] / pc))
    return pool


def _pick(pool: list[list[tuple]], rng: random.Random, i: int, window: int) -> tuple:
    """i sanal slot (gün sınırını geçebilir, havuz uzunluğuna göre döner)."""
    m = len(pool)
    j = (i if window == 0 else i + rng.randint(-window, window)) % m
    if pool[j]:
        return rng.choice(pool[j])
    for w in range(1, MAX_WINDOW + 1):          # boş slot (bakım arası): en yakın dolu slota genişle
        for k in ((j - w) % m, (j + w) % m):
            if pool[k]:
                return rng.choice(pool[k])
    return (1.0, 1.0, 1.0, 1.0)


def _replay(pool, rng, entry, stop, target, k, last, window, long) -> tuple[str | None, float, list[float]]:
    p, outcome, path = entry, None, [entry]
    for i in range(k + 1, last + 1):
        _o, h, l, c = _pick(pool, rng, i, window)
        hi, lo = p * h, p * l
        if outcome is None:
            if long:
                outcome = "stop" if lo <= stop else ("target" if hi >= target else None)
            else:
                outcome = "stop" if hi >= stop else ("target" if lo <= target else None)
        p = p * c
        path.append(p)
    return outcome, p, path


def simulate(pool, entry: float, stop: float, target: float, k: int, last: int, replays: int = REPLAYS_DEFAULT,
             seed: int = SEED_DEFAULT, window: int = WINDOW, side: str = "buy") -> dict[str, Any]:
    """Monte Carlo: k'dan sonraki last'e kadar olan slotları yeniden oynatır (kaynaktaki sim ile aynı akış)."""
    long = side == "buy"
    risk = (entry - stop) if long else (stop - entry)
    r_target = round(((target - entry) if long else (entry - target)) / risk, 4)
    rng = random.Random(seed)
    outcomes, closes, paths = [], [], []
    for n in range(replays):
        oc, p, path = _replay(pool, rng, entry, stop, target, k, last, window, long)
        outcomes.append(oc or "close")
        closes.append(p)
        if n < SAMPLE_PATHS:
            paths.append([round(x, 4) for x in path])
    cnt = {x: outcomes.count(x) for x in ("target", "stop", "close")}
    green = sum(1 for o, p in zip(outcomes, closes) if o == "target" or (o == "close" and ((p > entry) if long else (p < entry))))
    rs = [r_target if o == "target" else -1.0 if o == "stop" else ((p - entry) if long else (entry - p)) / risk
          for o, p in zip(outcomes, closes)]
    srt = sorted(closes)
    q = lambda a, x: a[min(len(a) - 1, int(x * len(a)))]  # noqa: E731
    return {"replays": replays, "seed": seed, "window": window, "bars_left": last - k,
            "p_target": round(cnt["target"] / replays, 4), "p_stop": round(cnt["stop"] / replays, 4),
            "p_neither": round(cnt["close"] / replays, 4), "p_green": round(green / replays, 4),
            "median_close": q(srt, 0.5), "p5_close": q(srt, 0.05), "p95_close": q(srt, 0.95),
            "avg_R": round(statistics.mean(rs), 3), "r_at_target": r_target,
            "bands": _bands(pool, entry, k, last, seed, window), "sample_paths": paths}


def _bands(pool, entry, k, last, seed, window) -> list[list[float]]:
    rng = random.Random(seed)
    allp = []
    for _ in range(BAND_PATHS):
        p, path = entry, [entry]
        for i in range(k + 1, last + 1):
            p = p * _pick(pool, rng, i, window)[3]
            path.append(p)
        allp.append(path)
    out = []
    for j in range(last - k + 1):
        col = sorted(pp[j] for pp in allp)
        out.append([round(col[min(len(col) - 1, int(x * len(col)))], 4) for x in BAND_Q])
    return out


def history_replay(b: Bars, atr: np.ndarray, sessions: list[dict], slot: int, n_bars: int, side: str,
                   stop_atr: float, target_r: float) -> dict[str, Any]:
    """Aynı plan her geçmiş seansta aynı slotta: giriş o barın kapanışı, stop/hedef o anın ATR'siyle (gerçek sonuç)."""
    long = side == "buy"
    trades = []
    for s in sessions:
        i = s["idx"].get(slot)
        if i is None or not np.isfinite(atr[i]) or atr[i] <= 0:
            continue
        e = float(b.c[i]); risk = stop_atr * float(atr[i])
        st, tg = (e - risk, e + target_r * risk) if long else (e + risk, e - target_r * risk)
        oc, last_c = None, e
        for j in range(i + 1, min(len(b.c), i + n_bars + 1)):       # sonraki n gerçek bar (gün sınırını geçer)
            last_c = float(b.c[j])
            if (b.l[j] <= st) if long else (b.h[j] >= st):
                oc = "stop"; break
            if (b.h[j] >= tg) if long else (b.l[j] <= tg):
                oc = "target"; break
        r = target_r if oc == "target" else -1.0 if oc == "stop" else ((last_c - e) if long else (e - last_c)) / risk
        trades.append({"day": datetime.fromordinal(s["day"]).date().isoformat(), "outcome": oc or "close", "R": round(r, 2)})
    n = len(trades)
    return {"sessions": len(sessions), "trades": n,
            "target": sum(t["outcome"] == "target" for t in trades), "stop": sum(t["outcome"] == "stop" for t in trades),
            "close": sum(t["outcome"] == "close" for t in trades),
            "avg_R": round(statistics.mean(t["R"] for t in trades), 3) if n else None, "recent": trades[-10:]}


def lean(mc: dict) -> tuple[float, float, float] | None:
    pt, ps = mc["p_target"], mc["p_stop"]
    if pt + ps <= 0:
        return None
    r = mc.get("r_at_target") or 1.0
    share, even = pt / (pt + ps), 1.0 / (1.0 + r)
    return share - even, share, even


def verdict(mc: dict) -> str:
    """Kaynağın hüküm cümlesi (Türkçe): yalnız bir tarafa değen simülasyonlarda hedefin payı vs başabaş payı."""
    lv = lean(mc)
    if lv is None:
        return "Hiçbir simülasyon ufuk içinde hedefe ya da stopa değmedi; sonucu ufuk sonundaki fiyat belirler."
    d, share, even = lv
    r = mc.get("r_at_target") or 1.0
    one_r = abs(r - 1.0) < 0.005
    if abs(d) < COIN_FLIP:
        head = "Yazı-tura" if one_r else "Başabaşa yakın"
    elif abs(d) < STRONG:
        head = "Hedefe meyilli" if d > 0 else "Stopa meyilli"
    else:
        head = "Güçlü biçimde hedefe" if d > 0 else "Güçlü biçimde stopa"
    odds = "hedef önce %%%.1f, stop önce %%%.1f" % (100 * mc["p_target"], 100 * mc["p_stop"])
    if one_r:
        return f"{head}: {odds}."
    return (f"{head}: {r:g}R hedefte, bir tarafa değenlerin %{100 * even:.0f}'inde hedef önce gelmeli; "
            f"%{100 * share:.0f}'inde geldi ({odds}).")


def verdict_notes(mc: dict) -> list[str]:
    notes, lv, avg = [], lean(mc), mc.get("avg_R")
    if mc.get("p_neither", 0) > MANY_NEITHER and lv is not None:
        notes.append(f"Simülasyonların %{100 * mc['p_neither']:.1f}'i ufuk içinde iki tarafa da değmedi; onları ufuk sonundaki fiyat belirler.")
    if lv and abs(lv[0]) >= COIN_FLIP and avg not in (None, 0) and (avg > 0) != (lv[0] > 0):
        notes.append(f"Yine de ortalama R {avg:+.3f}: değmeyen simülasyonlar onu ters yöne çekiyor.")
    return notes


def run_plan(b: Bars, side: str = "buy", stop_atr: float = 1.0, target_r: float = 1.0, n_bars: int = 48,
             replays: int = REPLAYS_DEFAULT, seed: int = SEED_DEFAULT, query_index: int | None = None,
             bar_min: int = 5) -> dict[str, Any]:
    """Saf uçtan uca koşu: son (veya query_index) KAPANMIŞ bardan giriş. Geriye-dönük sınamada da aynen kullanılır."""
    if side not in ("buy", "sell"):
        raise TMError("yön 'buy' ya da 'sell' olmalı")
    if not (stop_atr > 0 and target_r > 0 and n_bars >= 1):
        raise TMError("stop_atr, target_r ve ufuk pozitif olmalı")
    days, slots = day_and_slot(b.ts, bar_min)
    q = len(b.ts) - 1 if query_index is None else query_index
    atr = atr_series(b)
    if not np.isfinite(atr[q]) or atr[q] <= 0:
        raise TMError("ATR hesaplanamadı (yetersiz bar)")
    sess = sessions_before(days, slots, int(days[q]))
    if len(sess) < MIN_SESSIONS:
        raise TMError(f"havuz için en az {MIN_SESSIONS} dolu seans gerekir, {len(sess)} var")
    k = int(slots[q]); last = k + int(n_bars)
    entry = float(b.c[q]); risk = stop_atr * float(atr[q]); long = side == "buy"
    stop, target = (entry - risk, entry + target_r * risk) if long else (entry + risk, entry - target_r * risk)
    pool = build_pool(b, sess, bar_min)
    mc = simulate(pool, entry, stop, target, k, last, replays=replays, seed=seed, side=side)
    hist = history_replay(b, atr, sess, k, last - k, side, stop_atr, target_r)
    return {"plan": {"side": side, "entry": entry, "stop": stop, "target": target, "atr": float(atr[q]),
                     "stop_atr": stop_atr, "target_r": target_r, "bars": last - k, "timeframe": f"{bar_min}m",
                     "entry_time": datetime.fromtimestamp(int(b.ts[q]) + bar_min * 60, timezone.utc).isoformat(),
                     "pool_sessions": len(sess),
                     "pool_from": datetime.fromordinal(sess[0]["day"]).date().isoformat(),
                     "pool_to": datetime.fromordinal(sess[-1]["day"]).date().isoformat()},
            "mc": mc, "history": hist, "verdict": verdict(mc), "notes": verdict_notes(mc)}


# ═════════════════════════════ veri (canlı: Supabase candle_cache 5m) ═════════════════════════════

SYMBOLS = {"NDX": "NDX.INDX", "NAS100": "NDX.INDX", "NDX.INDX": "NDX.INDX", "DAX": "GDAXI.INDX", "GDAXI": "GDAXI.INDX",
           "GDAXI.INDX": "GDAXI.INDX", "XAU": "XAUUSD", "XAUUSD": "XAUUSD", "GOLD": "XAUUSD",
           "USOIL": "USOIL.FOREX", "OIL": "USOIL.FOREX", "USOIL.FOREX": "USOIL.FOREX"}
_bars_cache: dict[str, tuple[float, Bars]] = {}


def canonical(symbol: str) -> str:
    key = symbol.upper().strip()
    if key not in SYMBOLS:
        raise TMError(f"desteklenmeyen sembol: {symbol}")
    return SYMBOLS[key]


TF_MIN = {"5m": 5, "15m": 15, "1h": 60}


def _load_bars_db(symbol: str, tf: str = "5m", days: int = LOAD_DAYS) -> Bars:
    """candle_cache (5m/15m/1h), anahtar-sayfalı (PostgREST 1000 satır tavanı). Yalnız KAPANMIŞ ve ızgaradaki barlar."""
    from database.supabase_client import get_supabase_client
    db = get_supabase_client()
    if db is None:
        raise TMError("veritabanı bağlantısı yok")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows: list[dict] = []
    while True:
        res = (db.table("candle_cache").select("candle_time,open,high,low,close").eq("symbol", symbol)
               .eq("timeframe", tf).gt("candle_time", since).order("candle_time").limit(1000).execute())
        chunk = (res or {}).get("data") or []
        rows += chunk
        if len(chunk) < 1000:
            break
        since = chunk[-1]["candle_time"]
    now = time.time()
    ts = np.array([int(datetime.fromisoformat(r["candle_time"].replace("Z", "+00:00")).timestamp()) for r in rows], dtype=np.int64)
    bar_s = TF_MIN[tf] * 60
    keep = (ts % bar_s == 0) & (ts + bar_s <= now)
    arr = {k: np.array([float(r[k]) for r in rows])[keep] for k in ("open", "high", "low", "close")}
    return Bars(ts[keep], arr["open"], arr["high"], arr["low"], arr["close"])


async def get_time_machine(symbol: str, side: str = "buy", stop_atr: float = 1.0, target_r: float = 1.0,
                           n_bars: int = 48, replays: int = REPLAYS_DEFAULT, seed: int = SEED_DEFAULT,
                           tf: str = "5m") -> dict[str, Any]:
    sym = canonical(symbol)
    if tf not in TF_MIN:
        raise TMError(f"desteklenmeyen zaman dilimi: {tf} (5m / 15m / 1h)")
    replays = int(min(max(replays, 500), REPLAYS_MAX))
    key = f"{sym}|{tf}"
    hit = _bars_cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        b = hit[1]
    else:
        b = await asyncio.to_thread(_load_bars_db, sym, tf)
        _bars_cache[key] = (time.time(), b)
    if len(b.ts) < ATR_N + 2:
        raise TMError(f"yeterli {tf} bar yok")
    res = await asyncio.to_thread(run_plan, b, side, stop_atr, target_r, n_bars, replays, seed, None, TF_MIN[tf])
    res["symbol"] = sym
    res["last_bar"] = datetime.fromtimestamp(int(b.ts[-1]), timezone.utc).isoformat()
    res["note"] = (f"Son 60 seansın aynı gün-saatindeki {tf} mumlarından kurulmuş simülasyondur, tahmin değildir. "
                   "Kaynak yöntem: day-trader-skill / trader-timemachine (MIT).")
    return res


# ═════════════════════════════ ortak bant çekirdeği (bot / decider / panel / sinyal etiketi) ═════════════════════════════
# DTS-03 (research/dts_uyarlama_20261104): ufuk-sonu %90 bant 5m/15m/1h × 4 sembol × 3 ufukta %88,2–91,7 kapsama (A).
# DTS-06: bandın TP/SL'ye uygulanması bot işlemlerinde ayırt edici DEĞİL; panel sinyallerinde 'TP1 %90 bandın dışında'
# zayıf olumsuz işaret (C) → yalnız etiket + gölge. Bant YÖN söylemez.

BAND_REPLAYS = 1000
BAND_HORIZON_MIN = 60          # lifecycle ATR-merdiveni çözüm penceresiyle aynı (PULSE_ATR_WINDOW_MIN)
_band_cache: dict[str, tuple[float, dict]] = {}


def range_band(b: Bars, n_bars: int = 12, bar_min: int = 5, replays: int = BAND_REPLAYS, seed: int = SEED_DEFAULT,
               query_index: int | None = None) -> dict[str, Any]:
    """Son kapanmış bardan n_bars sonrası kapanış dağılımı: oran (rel_*) ve fiyat (p*) yüzdelikleri."""
    days, slots = day_and_slot(b.ts, bar_min)
    q = len(b.ts) - 1 if query_index is None else query_index
    sess = sessions_before(days, slots, int(days[q]))
    if len(sess) < MIN_SESSIONS:
        raise TMError(f"havuz için en az {MIN_SESSIONS} dolu seans gerekir, {len(sess)} var")
    pool = build_pool(b, sess, bar_min)
    k, rng, ends = int(slots[q]), random.Random(seed), []
    for _ in range(replays):
        p = 1.0
        for i in range(k + 1, k + n_bars + 1):
            p *= _pick(pool, rng, i, WINDOW)[3]
        ends.append(p)
    rel = np.quantile(ends, BAND_Q)
    price = float(b.c[q])
    keys = ("p5", "p25", "p50", "p75", "p95")
    return {"price": price, "bar_time": int(b.ts[q]), "bars": n_bars, "bar_min": bar_min, "horizon_min": n_bars * bar_min,
            **{f"rel_{k_}": float(v) for k_, v in zip(keys, rel)}, **{k_: price * float(v) for k_, v in zip(keys, rel)},
            "width_pct": 100 * float(rel[4] - rel[0]), "pool_sessions": len(sess),
            "calibration": "DTS-03: %90 bant 33/33 hücrede %88,2–91,7 kapsama (5m/15m/1h, 4 sembol)"}


def level_check(band: dict, entry: float, tp: float | None, sl: float | None, side: str) -> dict[str, Any]:
    """Bant oranlarını işlemin KENDİ girişine uygular (besleme taban farkına dayanıklı) ve TP/SL'yi konumlar."""
    long = side.lower() in ("buy", "long")
    p5, p25, p75, p95 = (entry * band[f"rel_{k}"] for k in ("p5", "p25", "p75", "p95"))
    out: dict[str, Any] = {"band_p5": p5, "band_p95": p95, "band_p25": p25, "band_p75": p75}
    if tp:
        out["tp_outside_p90"] = bool(tp > p95) if long else bool(tp < p5)
        out["tp_vs_p95"] = round((tp - entry) / (p95 - entry), 3) if long and p95 != entry else (
            round((entry - tp) / (entry - p5), 3) if not long and p5 != entry else None)
    if sl:
        out["sl_inside_p50"] = bool(p25 <= sl <= p75)
    return out


def bars_from_mt5_rates(rates, broker_offset_s: int) -> Bars:
    """MT5 copy_rates çıktısı (broker saati!) → UTC Bars. Offset çıkarılmazsa slotlar kayar (CLAUDE.md §9)."""
    ts = np.array([int(r["time"]) - int(broker_offset_s) for r in rates], dtype=np.int64)
    col = lambda k: np.array([float(r[k]) for r in rates])  # noqa: E731
    return Bars(ts, col("open"), col("high"), col("low"), col("close"))


async def get_range_band(symbol: str, tf: str = "5m", horizon_min: int = BAND_HORIZON_MIN) -> dict[str, Any]:
    """Önbellekli (5 dk) canlı bant — candle_cache'ten."""
    sym = canonical(symbol)
    if tf not in TF_MIN:
        raise TMError(f"desteklenmeyen zaman dilimi: {tf}")
    key = f"{sym}|{tf}|{horizon_min}"
    hit = _band_cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        return hit[1]
    bkey = f"{sym}|{tf}"
    bh = _bars_cache.get(bkey)
    if bh and time.time() - bh[0] < CACHE_TTL_S:
        b = bh[1]
    else:
        b = await asyncio.to_thread(_load_bars_db, sym, tf)
        _bars_cache[bkey] = (time.time(), b)
    n_bars = max(1, horizon_min // TF_MIN[tf])
    band = await asyncio.to_thread(range_band, b, n_bars, TF_MIN[tf])
    band.update({"symbol": sym, "tf": tf})
    _band_cache[key] = (time.time(), band)
    return band


def peek_range_band(symbol: str, tf: str = "5m", horizon_min: int = BAND_HORIZON_MIN) -> dict[str, Any] | None:
    """Sıcak yol (sinyal loglama) için bloklamayan okuma: önbellekte varsa döner, yoksa arka planda ısıtır ve None döner."""
    try:
        sym = canonical(symbol)
    except TMError:
        return None
    hit = _band_cache.get(f"{sym}|{tf}|{horizon_min}")
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        return hit[1]
    try:
        asyncio.get_running_loop().create_task(get_range_band(sym, tf, horizon_min))
    except RuntimeError:
        pass
    return hit[1] if hit else None


# ── MT5 köprüsü (bot ve decider kutuda bunu çağırır; backend HTTP'ye bağımlılık yok) ──
MT5_FETCH_BARS = 18000          # ≈ 65 broker günü × 276 bar (5m) → 60 dolu seanslık havuz
BROKER_OFFSET_MAX_S = 6 * 3600
_mt5_band_cache: dict[str, tuple[float, dict]] = {}


def broker_offset_from_tick(tick_time: float, now: float | None = None) -> int | None:
    """Broker saati − UTC (tam saate yuvarlı). Bayat tick (hafta sonu) → None."""
    now = time.time() if now is None else now
    off = int(round((tick_time - now) / 3600.0) * 3600)
    if abs(off) <= BROKER_OFFSET_MAX_S and abs(tick_time - now - off) < 600:
        return off
    return None


def range_band_mt5(mt5, mt5_symbol: str, horizon_min: int = BAND_HORIZON_MIN, tf_min: int = 5,
                   broker_offset_s: int | None = None) -> dict[str, Any] | None:
    """Kutudaki MT5'ten (pos=1: oluşmakta olan bar hariç) bant; sembol başına 5 dk önbellek. Hata → None (fail-open)."""
    key = f"{mt5_symbol}|{tf_min}|{horizon_min}"
    hit = _mt5_band_cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        return hit[1]
    try:
        if broker_offset_s is None:
            tick = mt5.symbol_info_tick(mt5_symbol)
            broker_offset_s = broker_offset_from_tick(tick.time) if tick and tick.time else None
            if broker_offset_s is None:
                return hit[1] if hit else None
        tf = {5: mt5.TIMEFRAME_M5, 15: mt5.TIMEFRAME_M15, 60: mt5.TIMEFRAME_H1}[tf_min]
        rates = mt5.copy_rates_from_pos(mt5_symbol, tf, 1, MT5_FETCH_BARS if tf_min == 5 else MT5_FETCH_BARS // (tf_min // 5))
        if rates is None or len(rates) < 2000:
            return hit[1] if hit else None
        band = range_band(bars_from_mt5_rates(rates, broker_offset_s), max(1, horizon_min // tf_min), tf_min)
        band.update({"mt5_symbol": mt5_symbol, "broker_offset_s": broker_offset_s})
        _mt5_band_cache[key] = (time.time(), band)
        return band
    except Exception as e:  # pragma: no cover — fail-open
        logger.debug("range_band_mt5 %s: %s", mt5_symbol, e)
        return hit[1] if hit else None
