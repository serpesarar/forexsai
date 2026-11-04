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

def day_and_slot(ts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Her bar için broker günü (NY 17:00 sınırlı, sıra numarası) ve slot (0..287)."""
    day_keys, slots = np.empty(len(ts), dtype=np.int64), np.empty(len(ts), dtype=np.int64)
    for i, t in enumerate(ts.tolist()):
        ny = datetime.fromtimestamp(t, NY)
        shifted = ny - timedelta(minutes=DAY_START_MIN)
        day_keys[i] = shifted.toordinal()
        slots[i] = (shifted.hour * 60 + shifted.minute) // 5
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


def build_pool(b: Bars, sessions: list[dict]) -> list[list[tuple[float, float, float, float]]]:
    """pool[slot] = geçmiş seansların o slottaki barı, bir önceki barın kapanışına oran olarak.

    Önceki bar = dizideki bir önceki bar, aralarında ≤ PREV_GAP_S varsa (günün ilk slotu önceki günün son barına
    bağlanır; CFD'de gün sınırı kesintisizdir — kaynak araçta seans kapanışı vardı, burada yok).
    """
    pool: list[list[tuple[float, float, float, float]]] = [[] for _ in range(SLOTS)]
    for s in sessions:
        for slot, i in s["idx"].items():
            if i == 0 or b.c[i - 1] <= 0 or not 0 < b.ts[i] - b.ts[i - 1] <= PREV_GAP_S:
                continue
            pc = b.c[i - 1]
            pool[slot].append((b.o[i] / pc, b.h[i] / pc, b.l[i] / pc, b.c[i] / pc))
    return pool


def _pick(pool: list[list[tuple]], rng: random.Random, i: int, window: int) -> tuple:
    """i sanal slot (gün sınırını geçebilir, SLOTS'a göre döner)."""
    j = (i if window == 0 else i + rng.randint(-window, window)) % SLOTS
    if pool[j]:
        return rng.choice(pool[j])
    for w in range(1, MAX_WINDOW + 1):          # boş slot (bakım arası): en yakın dolu slota genişle
        for k in ((j - w) % SLOTS, (j + w) % SLOTS):
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
             replays: int = REPLAYS_DEFAULT, seed: int = SEED_DEFAULT, query_index: int | None = None) -> dict[str, Any]:
    """Saf uçtan uca koşu: son (veya query_index) KAPANMIŞ bardan giriş. Geriye-dönük sınamada da aynen kullanılır."""
    if side not in ("buy", "sell"):
        raise TMError("yön 'buy' ya da 'sell' olmalı")
    if not (stop_atr > 0 and target_r > 0 and n_bars >= 1):
        raise TMError("stop_atr, target_r ve ufuk pozitif olmalı")
    days, slots = day_and_slot(b.ts)
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
    pool = build_pool(b, sess)
    mc = simulate(pool, entry, stop, target, k, last, replays=replays, seed=seed, side=side)
    hist = history_replay(b, atr, sess, k, last - k, side, stop_atr, target_r)
    return {"plan": {"side": side, "entry": entry, "stop": stop, "target": target, "atr": float(atr[q]),
                     "stop_atr": stop_atr, "target_r": target_r, "bars": last - k,
                     "entry_time": datetime.fromtimestamp(int(b.ts[q]) + BAR_S, timezone.utc).isoformat(),
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


def _load_bars_db(symbol: str, days: int = LOAD_DAYS) -> Bars:
    """candle_cache 5m, anahtar-sayfalı (PostgREST 1000 satır tavanı). Yalnız KAPANMIŞ barlar."""
    from database.supabase_client import get_supabase_client
    db = get_supabase_client()
    if db is None:
        raise TMError("veritabanı bağlantısı yok")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows: list[dict] = []
    while True:
        res = (db.table("candle_cache").select("candle_time,open,high,low,close").eq("symbol", symbol)
               .eq("timeframe", "5m").gt("candle_time", since).order("candle_time").limit(1000).execute())
        chunk = (res or {}).get("data") or []
        rows += chunk
        if len(chunk) < 1000:
            break
        since = chunk[-1]["candle_time"]
    now = time.time()
    ts = np.array([int(datetime.fromisoformat(r["candle_time"].replace("Z", "+00:00")).timestamp()) for r in rows], dtype=np.int64)
    keep = (ts % BAR_S == 0) & (ts + BAR_S <= now)
    arr = {k: np.array([float(r[k]) for r in rows])[keep] for k in ("open", "high", "low", "close")}
    return Bars(ts[keep], arr["open"], arr["high"], arr["low"], arr["close"])


async def get_time_machine(symbol: str, side: str = "buy", stop_atr: float = 1.0, target_r: float = 1.0,
                           n_bars: int = 48, replays: int = REPLAYS_DEFAULT, seed: int = SEED_DEFAULT) -> dict[str, Any]:
    sym = canonical(symbol)
    replays = int(min(max(replays, 500), REPLAYS_MAX))
    hit = _bars_cache.get(sym)
    if hit and time.time() - hit[0] < CACHE_TTL_S:
        b = hit[1]
    else:
        b = await asyncio.to_thread(_load_bars_db, sym)
        _bars_cache[sym] = (time.time(), b)
    if len(b.ts) < ATR_N + 2:
        raise TMError("yeterli 5m bar yok")
    res = await asyncio.to_thread(run_plan, b, side, stop_atr, target_r, n_bars, replays, seed)
    res["symbol"] = sym
    res["last_bar"] = datetime.fromtimestamp(int(b.ts[-1]), timezone.utc).isoformat()
    res["note"] = ("Son 60 seansın aynı gün-saatindeki 5 dk mumlarından kurulmuş simülasyondur, tahmin değildir. "
                   "Kaynak yöntem: day-trader-skill / trader-timemachine (MIT).")
    return res
