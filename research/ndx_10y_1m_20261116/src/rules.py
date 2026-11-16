"""rules.py — canlı NASDAQ kurallarının 1m simülatörleri (PROTOCOL.md §2). Varsayılan parametreler = canlı kod (dondurulmuş).
Parametreler yalnız B komşuluk haritası için açıktır."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

import lib
from lib import M1, Trade, utc


# ─────────────────────────── yardımcılar ───────────────────────────

def rsi2(x: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """Wilder RSI(2) — c3b_shadow.rsi2 ile aynı özyineleme; ilk değer NaN."""
    out = np.full(len(x), np.nan)
    up = dn = 0.0
    for i in range(1, len(x)):
        g = x[i] - x[i - 1]
        if i == 1:
            up, dn = max(g, 0.0), max(-g, 0.0)
        else:
            up = alpha * max(g, 0.0) + (1 - alpha) * up
            dn = alpha * max(-g, 0.0) + (1 - alpha) * dn
        out[i] = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
    return out


def bars_tf(m1: M1, d: date, start_min: int, end_min: int, tf: int) -> list[dict]:
    """NY gün dakikasına hizalı tf-dk barlar, [start_min, end_min) içinde; eksik ilk/son dakikaya toleranslı."""
    out = []
    for s in range(start_min, end_min, tf):
        a = int(np.searchsorted(m1.t, utc(d, s)))
        b = int(np.searchsorted(m1.t, utc(d, s + tf)))
        if b - a < max(1, tf // 2):
            continue
        out.append({"s": s, "e": s + tf, "o": m1.o[a], "h": m1.h[a:b].max(), "l": m1.l[a:b].min(), "c": m1.c[b - 1],
                    "t_end": utc(d, s + tf)})
    return out


# ─────────────────────────── A1 C3b / C3 ───────────────────────────

def c3b(m1: M1, D: pd.DataFrame, rsi_th: float = 10.0, max_hold: int = 5, entry_min: int = 930,
        exit_mode: str = "up", add_units: int = 0, rule: str = "C3B") -> list[Trade]:
    """C3b (exit_mode='up') / C3 (exit_mode='next'). Giriş = entry_min'de açılan bar (+spread); çıkış = 15:30 E fiyatı.
    add_units > 0 → KT-01 A4 kademe: pozisyon açıkken sonraki 15:30'da S yine düştü ∧ RSI2 < eşik → ek birim (ayrı Trade, tag add)."""
    s = D[D.S.notna() & D.E.notna() & ~D.early].reset_index(drop=True)
    S = s.S.values
    r = rsi2(S)
    trades: list[Trade] = []
    pos = None                                  # {"k": giriş indeksi, "units": [...]}
    for i in range(len(s)):
        d = s.d[i]
        if pos is not None:
            up = S[i] > S[i - 1]
            if (exit_mode == "up" and (up or i - pos["k"] >= max_hold)) or (exit_mode == "next" and i - pos["k"] >= 1):
                for u in pos["units"]:
                    x = lib.time_trade(m1, rule, u["d"], u["t_in"], utc(d, 930), +1, rsi2=u["rsi"], unit=u["unit"],
                                       hold=i - u["k"])
                    if x:
                        trades.append(x)
                pos = None
            elif add_units and len(pos["units"]) <= add_units and S[i] < S[i - 1] and r[i] < rsi_th:
                pos["units"].append({"d": d, "t_in": utc(d, entry_min), "rsi": float(r[i]), "unit": len(pos["units"]), "k": i})
        if pos is None and np.isfinite(r[i]) and r[i] < rsi_th:
            pos = {"k": i, "units": [{"d": d, "t_in": utc(d, entry_min), "rsi": float(r[i]), "unit": 0, "k": i}]}
    return trades


# ─────────────────────────── A2 CAPREV ───────────────────────────

def caprev_ctx(D: pd.DataFrame, vixp: dict, vix_min: float = 18.4) -> dict[date, dict]:
    """Gün başında bilinen bağlam (yalnız ÖNCEKİ günlerden): r1, r5, dvol, pdl, stres, VIX."""
    full = D[D.full & D.close.notna()].reset_index(drop=True)
    cl = full.close.values
    out = {}
    all_days = D.d.tolist()
    lows = dict(zip(D.d, D.low900))
    for i, d in enumerate(all_days):
        k = int(np.searchsorted(full.d.values, d))      # full günlerde d'den önceki son indeks = k−1
        if k < 22:
            continue
        c = cl[:k]
        rets = c[1:] / c[:-1] - 1
        w = rets[-20:]
        r1, r5 = rets[-1], c[-1] / c[-6] - 1
        prev = all_days[i - 1] if i > 0 else None
        pdl = lows.get(prev) if prev is not None and (d - prev).days <= 4 else None
        v = vixp.get(d)
        out[d] = {"r1": r1, "r5": r5, "dvol": float(np.std(w, ddof=1)), "pdl": pdl, "vix": v,
                  "stress": bool(r1 <= -0.015 or r5 <= -0.04), "vix_ok": v is not None and v >= vix_min}
    return out


def caprev(m1: M1, D: pd.DataFrame, vixp: dict, tf: int = 60, exit_next_day: bool = False, vix_min: float = 18.4,
           win: tuple[int, int] = (180, 900), rule: str = "CAPREV") -> list[Trade]:
    ctx = caprev_ctx(D, vixp, vix_min)
    days = D.d.tolist()
    trades = []
    for j, d in enumerate(days):
        c = ctx.get(d)
        if c is None or d.weekday() > 3 or not (c["stress"] and c["vix_ok"]) or c["pdl"] is None or D.early.iloc[j]:
            continue
        trig = next((b for b in bars_tf(m1, d, win[0], win[1], tf) if b["e"] <= win[1] and b["c"] < c["pdl"]), None)
        if trig is None:
            continue
        i0, bid = lib.entry_ix(m1, trig["t_end"])
        if i0 is None:
            continue
        ask = bid + m1.spr[i0] + 0.2
        stop = ask * (1 - c["dvol"])
        if exit_next_day:
            nd = days[j + 1] if j + 1 < len(days) else None
            if nd is None:
                continue
            t_end = utc(nd, lib.nyse.cash_close_minutes(nd))
        else:
            t_end = utc(d, 960)
        k, px, why, mae = lib.walk(m1, i0, t_end, +1, stop, None)
        trades.append(Trade(rule, d, int(trig["t_end"]), int(m1.t[k]), +1, ask, px - 0.2 if why == "time" else px,
                            risk=ask * c["dvol"], spr_in=m1.spr[i0], spr_out=m1.spr[k], mae=mae, why=why,
                            tags={"vix": c["vix"], "trig_min": trig["s"], "pre_open": trig["e"] <= 570,
                                  "r1": c["r1"], "r5": c["r5"]}))
    return trades


# ─────────────────────────── A3 ORB × VIX ───────────────────────────

def orb(m1: M1, D: pd.DataFrame, vixp: dict, or_min: int = 15, tp_r: float | None = 2.0, vix_min: float | None = 18.4,
        tf: int = 5, rule: str = "ORBVIX", arm: str = "hi", optimistic: bool = False) -> list[Trade]:
    """arm='hi' → dünkü VIX ≥ vix_min; 'lo' → altı (karşı kol); 'all' → koşulsuz."""
    trades = []
    for row in D[D.full].itertuples():
        d, v = row.d, vixp.get(row.d)
        if v is None:
            continue
        if (arm == "hi" and v < vix_min) or (arm == "lo" and v >= vix_min):
            continue
        a, b = int(np.searchsorted(m1.t, utc(d, 570))), int(np.searchsorted(m1.t, utc(d, 570 + or_min)))
        if b - a < or_min * 0.8:
            continue
        hi, lo = m1.h[a:b].max(), m1.l[a:b].min()
        mid = (hi + lo) / 2
        trig = next((x for x in bars_tf(m1, d, 570 + or_min, 930, tf) if x["c"] > hi), None)
        if trig is None:
            continue
        i0 = m1.idx_from(trig["t_end"])
        if i0 is None:
            continue
        ask = trig["c"] if optimistic else m1.o[i0] + m1.spr[i0]     # iyimser = tetik barı kapanışı, spreadsiz (kart 5. ölçüt)
        risk = ask - mid
        if risk <= 0.0005 * ask:
            continue
        k, px, why, mae = lib.walk(m1, i0, utc(d, 955), +1, mid, None if tp_r is None else ask + tp_r * risk)
        trades.append(Trade(rule, d, int(m1.t[i0]), int(m1.t[k]), +1, ask, px, risk=risk,
                            spr_in=0.0 if optimistic else m1.spr[i0], spr_out=m1.spr[k], mae=mae, why=why,
                            tags={"vix": v, "or_w": hi - lo, "or_hi": hi, "trig_min": trig["s"]}))
    return trades


# ─────────────────────────── A4 FR-15 teyitli çekiç ───────────────────────────

def h1_utc(m1: M1) -> pd.DataFrame:
    p = lib.CACHE / "h1_utc.parquet"
    if p.exists():
        return pd.read_parquet(p)
    hr = m1.t // 3600
    df = pd.DataFrame({"hr": hr, "o": m1.o, "h": m1.h, "l": m1.l, "c": m1.c, "spr": m1.spr})
    g = df.groupby("hr")
    out = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "n": g.size()}).reset_index()
    out = out[out.n >= 30].reset_index(drop=True)
    out["t"] = out.hr * 3600
    out.to_parquet(p)
    return out


def cekic(m1: M1, H: pd.DataFrame, lw_min: float = 0.70, tp_r: float = 5.0, hold_h: int = 24,
          rule: str = "CEKIC") -> list[Trade]:
    o, h, l, c, t = H.o.values, H.h.values, H.l.values, H.c.values, H.t.values.astype(np.int64)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    atr = pd.Series(tr).rolling(14).mean().values
    rng = h - l
    lw = np.minimum(o, c) - l
    uw = h - np.maximum(o, c)
    dom = np.where(uw <= 0, np.inf, lw / np.where(uw <= 0, 1, uw))
    ham = (rng > 0) & (lw > 0) & (lw / np.where(rng > 0, rng, 1) >= lw_min) & (lw / atr >= 0.20) & (dom >= 1.0)
    trades, busy_until = [], 0
    for i in np.where(ham)[0]:
        if i + 1 >= len(t) or t[i + 1] - t[i] > 7200:
            continue
        if not (l[i + 1] > l[i] and c[i + 1] > h[i]):
            continue
        t_in = int(t[i + 1] + 3600)
        if t_in < busy_until:
            continue
        i0 = m1.idx_from(t_in, 600)
        if i0 is None:
            continue
        ask = m1.o[i0] + m1.spr[i0]
        dist = ask - l[i]
        if dist <= 0 or dist < 2 * m1.spr[i0]:
            continue
        t_end = t_in + hold_h * 3600
        # Cuma 16:45 NY çıkışı: girişten sonraki ilk Cuma 16:45
        dloc = pd.Timestamp(t_in, unit="s", tz="UTC").tz_convert(lib.NY)
        days_to_fri = (4 - dloc.weekday()) % 7
        fri = (dloc + pd.Timedelta(days=days_to_fri)).date()
        t_fri = utc(fri, 16 * 60 + 45)
        if t_fri <= t_in:
            t_fri = utc(fri + timedelta(days=7), 16 * 60 + 45)
        t_end = min(t_end, t_fri)
        k, px, why, mae = lib.walk(m1, i0, t_end, +1, l[i], ask + tp_r * dist)
        d = dloc.date()
        trades.append(Trade(rule, d, int(m1.t[i0]), int(m1.t[k]), +1, ask, px, risk=dist, spr_in=m1.spr[i0],
                            spr_out=m1.spr[k], mae=mae, why=why))
        busy_until = int(m1.t[k]) + 60
    return trades


# ─────────────────────────── A5 KSG ───────────────────────────

def ksg(m1: M1, D: pd.DataFrame, sig_from: str = "O15", exit_min: int = 570, rule: str = "KSG") -> list[Trade]:
    days = D.d.tolist()
    trades = []
    for j, row in enumerate(D.itertuples()):
        if not row.full or j + 1 >= len(days):
            continue
        o0 = getattr(row, sig_from)
        o16 = row.O16 if np.isfinite(row.O16) else row.c1600
        if not (np.isfinite(o0) and np.isfinite(o16)):
            continue
        ret = o16 / o0 - 1
        if ret >= 0:
            continue
        nd = days[j + 1]
        x = lib.time_trade(m1, rule, row.d, utc(row.d, 960), utc(nd, exit_min), +1, ret_bp=ret * 1e4)
        if x:
            trades.append(x)
    return trades


# ─────────────────────────── A6/A7 ay sonu ───────────────────────────

def month_last_days(days: list[date]) -> list[int]:
    return [i for i in range(len(days) - 1) if days[i + 1].month != days[i].month]


def aysonu(m1: M1, D: pd.DataFrame, th: float = 0.02) -> tuple[list[Trade], list[Trade]]:
    spy, tlt = lib.etf("SPY"), lib.etf("TLT")
    eqd = set(spy.index) & set(tlt.index)
    days = [d for d in lib.trading_days(m1)]
    son, e2 = [], []
    for i in month_last_days(days):
        Dd = days[i]
        # önceki ay son işlem günü
        p = i - 1
        while p >= 0 and days[p].month == Dd.month:
            p -= 1
        if p < 0 or i < 3:
            continue
        d0, d3 = days[p], days[i - 3]
        if not {d0, d3, Dd} <= eqd:
            continue
        dl = (spy[d3] / spy[d0] - 1) - (tlt[d3] / tlt[d0] - 1)
        side = -1 if dl >= th else (1 if dl <= -th else 0)
        if side and not lib.nyse.is_early_close(Dd):
            x = lib.time_trade(m1, "AYSONU_SON", Dd, utc(Dd, 570), utc(Dd, 960), side, delta=dl)
            if x:
                son.append(x)
        dD = (spy[Dd] / spy[d0] - 1) - (tlt[Dd] / tlt[d0] - 1)
        if dD >= th and i + 3 < len(days):
            d3f = days[i + 3]
            # Dukascopy 16:15–18:00 boşluğu: 16:30 yerine 16:14 kapanışı (EK notu)
            x = lib.time_trade(m1, "AYSONU_E2", Dd, utc(Dd, 975), utc(d3f, 975), +1, tol_s=60, delta=dD)
            if x:
                e2.append(x)
    return son, e2


# ─────────────────────────── A8 FOMC gecesi ───────────────────────────

def fomc_gece(m1: M1, D: pd.DataFrame, rule: str = "FOMC_GECE") -> list[Trade]:
    fd = lib.fomc_days()
    days = D.d.tolist()
    full = dict(zip(D.d, D.full))
    out = []
    for j in range(1, len(days)):
        if days[j] in fd and full.get(days[j - 1], False):
            x = lib.time_trade(m1, rule, days[j - 1], utc(days[j - 1], 960), utc(days[j], 570), +1)
            if x:
                out.append(x)
    return out
