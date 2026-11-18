"""vw.py — V / W dip girişleri ve çok-çıkışlı hızlı değerlendirici (PROTOCOL §2–4).

Sızıntı ilkesi: her giriş karar mumunun kapanışından (tend) SONRA açılan ilk 1m barın açılışında; çapalar ve W yapısı yalnız
karar anına kadar kapanmış 15m mumlarla kurulur (fraktal dip m, m+2 kapanışında teyit edilir).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/fitil210_15m_20261117/src"))
import veri  # noqa: E402  (PathBars, build_15m, build_210m, duka_path, mt5_path)
import lib   # noqa: E402  (FIN_BP_PER_DAY, nyse, era, vix_prev_map)

NY = ZoneInfo("America/New_York")
LOOK = 192            # ≈2 işlem günü 15m
SCAN = 96             # V2/V3/W arama penceresi (15m)
NECK_SCAN = 32        # W boyun kırılımı penceresi
STOP_BUF = 0.001      # dip − %0,10
MIN_RISK = 0.0005     # en az 5 bp
W_UNDER = 0.0025      # L2 en çok %0,25 altına inebilir / iptal eşiği
W_OVER = 0.004        # L2 en çok %0,40 üstünde
NECK_MIN = 0.003      # boyun ≥ L1 + %0,30
AG_DROP = 0.015
RETEST_TOL = 0.001
TPS = (1.0, 2.0, 3.0, 5.0, np.inf)
TIMES = ("4h", "24h", "D1_16")
ENTRY_TYPES = ("V1", "V2", "V3", "VG", "W1b", "W1a", "WGb", "WGa")


def duka_path_stable() -> veri.PathBars:
    """Sabit kaynak: ana Dukascopy 1m (lib.load_m1 önbelleği, ndx_1m_v3_duka). Ortak `kaynak.load_duka_1m` başka bir
    oturumca değiştirildiği için (2025 yeniden indirme birleşimi) bu araştırma ona bağlanmaz (PROTOCOL EK-2)."""
    m = lib.load_m1()
    return veri.PathBars(m.t, m.o, m.h, m.l, m.c, m.spr, 60, "DUKA_1m_v3")


# ═══════════════════════════ çapalar ve girişler ═══════════════════════════

def _drop(q: pd.DataFrame, j: int, low: float) -> float:
    a = max(0, j - LOOK + 1)
    hi = float(q.high.values[a:j + 1].max())
    return (hi - low) / hi


def _w_scan(q: pd.DataFrame, a: int, L1: float, s0: int) -> tuple[int, int, float, float] | None:
    """W: L1 (bar a) sonrası ikinci dip. Döner (L2 bar m, teyit barı m+2, L2, boyun) ya da None."""
    lo, hi, cl = q.low.values, q.high.values, q.close.values
    n = len(q)
    floor = L1 * (1 - W_UNDER)
    for m in range(max(a + 3, s0), min(a + SCAN, n - 2)):
        if lo[a + 1:m].size and lo[a + 1:m].min() < floor:
            return None                                   # L2'den önce yeni dip → W iptal
        if lo[m] < floor:
            return None
        if not (lo[m] <= lo[m - 2:m + 3].min()):
            continue
        if not (L1 * (1 - W_UNDER) <= lo[m] <= L1 * (1 + W_OVER)):
            continue
        neck = float(hi[a + 1:m].max()) if m > a + 1 else -np.inf
        if (neck - L1) / L1 < NECK_MIN:
            continue
        if cl[m + 2] > cl[m]:
            return m, m + 2, float(lo[m]), neck
    return None


def a210_anchors(q: pd.DataFrame, b: pd.DataFrame, excl: set[int]) -> pd.DataFrame:
    """Kullanıcının çapası: 210m alt fitil ≥ %0,50 ∧ üst ≤ alt/2."""
    e = b[(b.lw_pct >= 0.5) & (b.uw_pct <= 0.5 * b.lw_pct) & ~b.t.isin(excl)].sort_values("tend")
    rows = []
    for r in e.itertuples():
        i0, i1 = int(r.i_first), int(r.i_last)
        seg = np.arange(i0, i1 + 1)
        a = int(seg[np.argmin(q.low.values[seg])])
        o, c = q.open.values[seg], q.close.values[seg]
        body = np.where(c < o, o - c, -1.0)
        bt = float(o[np.argmax(body)]) if body.max() > 0 else np.nan
        rows.append({"anchor": "A210", "a": a, "L1": float(r.low), "dec": i1, "t_dec": int(r.tend), "hi210": float(r.high),
                     "bt": bt, "drop": _drop(q, a, float(r.low))})
    return pd.DataFrame(rows)


def ag_anchors(q: pd.DataFrame) -> pd.DataFrame:
    lo, hi, te = q.low.values, q.high.values, q.tend.values
    rmin = pd.Series(lo).rolling(LOOK, min_periods=LOOK).min().values
    rmax = pd.Series(hi).rolling(LOOK, min_periods=LOOK).max().values
    rows, cool = [], -1
    for m in range(LOOK, len(q) - 2):
        if m <= cool or lo[m] != rmin[m]:
            continue
        drop = (rmax[m] - lo[m]) / rmax[m]
        if drop < AG_DROP or not (lo[m + 1] > lo[m] and lo[m + 2] > lo[m]):
            continue
        rows.append({"anchor": "AG", "a": m, "L1": float(lo[m]), "dec": m + 2, "t_dec": int(te[m + 2]), "hi210": np.nan,
                     "bt": np.nan, "drop": float(drop)})
        cool = m + SCAN
    return pd.DataFrame(rows)


def entries(q: pd.DataFrame, anc: pd.DataFrame) -> pd.DataFrame:
    """Çapalardan 8 giriş tipi (PROTOCOL §3)."""
    cl, te = q.close.values, q.tend.values
    n = len(q)
    out = []
    for k, r in enumerate(anc.itertuples()):
        base = {"aid": f"{r.anchor}{k}", "L1": r.L1, "drop": r.drop}
        stopV = r.L1 * (1 - STOP_BUF)
        s0 = r.dec + 1
        if r.anchor == "A210":
            out.append({**base, "typ": "V1", "j": r.dec, "t_sig": r.t_dec, "stop": stopV})
            for typ, lvl in (("V2", r.hi210), ("V3", r.bt)):
                if not np.isfinite(lvl):
                    continue
                for j in range(s0, min(s0 + SCAN, n)):
                    if cl[j] > lvl:
                        out.append({**base, "typ": typ, "j": j, "t_sig": int(te[j]), "stop": stopV})
                        break
        else:
            out.append({**base, "typ": "VG", "j": r.dec, "t_sig": r.t_dec, "stop": stopV})
        w = _w_scan(q, r.a, r.L1, s0)
        if w is not None:
            m, mc, L2, neck = w
            stopW = min(r.L1, L2) * (1 - STOP_BUF)
            pre = "W1" if r.anchor == "A210" else "WG"
            out.append({**base, "typ": pre + "b", "j": mc, "t_sig": int(te[mc]), "stop": stopW, "L2": L2, "neck": neck})
            for j in range(mc + 1, min(mc + 1 + NECK_SCAN, n)):
                if cl[j] > neck:
                    out.append({**base, "typ": pre + "a", "j": j, "t_sig": int(te[j]), "stop": stopW, "L2": L2, "neck": neck})
                    lo_ = q.low.values
                    for jr in range(j + 1, min(j + 1 + NECK_SCAN, n)):      # EK-3 boyun geri-testi
                        if lo_[jr] <= neck * (1 + RETEST_TOL) and cl[jr] > neck:
                            out.append({**base, "typ": pre + "r", "j": jr, "t_sig": int(te[jr]), "stop": stopW, "L2": L2, "neck": neck})
                            break
                    break
    e = pd.DataFrame(out)
    e["sig_close"] = cl[e.j.values]
    return e


# ═══════════════════════════ çok-çıkışlı değerlendirici ═══════════════════════════

def next_day_16(t_utc: int) -> int:
    d = datetime.fromtimestamp(t_utc, NY).date() + timedelta(days=1)
    while d.weekday() >= 5 or lib.nyse.is_holiday(d):
        d += timedelta(days=1)
    return int(datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).timestamp())


@dataclass
class Eval:
    R: np.ndarray        # (len(TPS), len(TIMES))
    R15: np.ndarray
    bp: np.ndarray
    t_out: np.ndarray
    t_in: int
    risk_bp: float


def evaluate(p: veri.PathBars, t_sig: int, stop: float, sig_close: float | None = None,
             stop_pct: float | None = None) -> Eval | None:
    """t_sig'den sonraki ilk bar açılışında AL; tüm TP × zaman bileşimleri. stop_pct verilirse stop = giriş·(1−stop_pct)."""
    i = int(np.searchsorted(p.t, t_sig))
    if i >= len(p.t) or p.t[i] - t_sig > 4 * 86400:
        return None
    opt = sig_close is not None
    spi = 0.0 if opt else float(p.spr[i])
    ask = (sig_close if opt else float(p.o[i])) + spi
    if stop_pct is not None:
        stop = ask * (1 - stop_pct)
    stop = min(stop, ask * (1 - MIN_RISK))
    risk = ask - stop
    if risk <= 0:
        return None
    t0 = int(p.t[i])
    ends = {"4h": t0 + 4 * 3600, "24h": t0 + 24 * 3600, "D1_16": next_day_16(t0)}
    jmax = int(np.searchsorted(p.t, max(ends.values())))
    jmax = min(max(jmax, i + 1), len(p.t))
    lo, hi, op = p.l[i:jmax], p.h[i:jmax], p.o[i:jmax]
    hs = np.flatnonzero(lo <= stop)
    js = int(hs[0]) if hs.size else 10 ** 9
    cm = np.maximum.accumulate(hi)
    R = np.full((len(TPS), len(TIMES)), np.nan)
    R15, bp, tout = R.copy(), R.copy(), R.copy()
    for b_, tn in enumerate(TIMES):
        jT = int(np.searchsorted(p.t[i:jmax], ends[tn]))
        for a_, k in enumerate(TPS):
            tp = ask + k * risk if np.isfinite(k) else np.inf
            jt = int(np.searchsorted(cm, tp)) if np.isfinite(tp) else 10 ** 9
            if js < jT and js <= jt:
                j, px = js, min(stop, float(op[js]))
            elif jt < jT:
                j, px = jt, max(tp, float(op[jt]))
            else:
                g = i + jT
                if g < len(p.t) and p.t[g] - ends[tn] <= 4 * 86400:
                    j, px = jT, float(p.o[g])
                else:
                    j, px = jT - 1, float(p.c[i + jT - 1])
            g = min(i + j, len(p.t) - 1)
            nights = (datetime.fromtimestamp(int(p.t[g]), NY).date() - datetime.fromtimestamp(t0, NY).date()).days
            gross = (px / ask - 1) * 1e4
            net = gross - lib.FIN_BP_PER_DAY * max(0, nights)
            extra = 0.5 * (spi + float(p.spr[g])) / ask * 1e4
            rb = risk / ask * 1e4
            R[a_, b_], R15[a_, b_], bp[a_, b_], tout[a_, b_] = net / rb, (net - extra) / rb, net, p.t[g]
    return Eval(R, R15, bp, tout, t0, risk / ask * 1e4)


def evaluate_all(p: veri.PathBars, e: pd.DataFrame, optimistic: bool = False, shift: np.ndarray | None = None) -> pd.DataFrame:
    """Her giriş için TP × zaman R'leri (uzun tablo). shift: plasebo için t_sig kaydırma (sn); stop aynı % mesafe."""
    rows = []
    for n, r in enumerate(e.itertuples()):
        ts = int(r.t_sig + (shift[n] if shift is not None else 0))
        stop_pct = None
        if shift is not None:
            i = int(np.searchsorted(p.t, int(r.t_sig)))
            ref = float(p.o[min(i, len(p.t) - 1)]) + float(p.spr[min(i, len(p.t) - 1)])
            stop_pct = max(MIN_RISK, (ref - r.stop) / ref)
        ev = evaluate(p, ts, r.stop, sig_close=(r.sig_close if optimistic else None), stop_pct=stop_pct)
        if ev is None:
            continue
        for a_, k in enumerate(TPS):
            for b_, tn in enumerate(TIMES):
                rows.append((n, k, tn, ev.R[a_, b_], ev.R15[a_, b_], ev.bp[a_, b_], ev.t_in, ev.t_out[a_, b_], ev.risk_bp))
    out = pd.DataFrame(rows, columns=["e", "tp", "time", "R", "R15", "bp", "t_in", "t_out", "risk_bp"])
    return out


# ═══════════════════════════ Tur 2: zaman çıkışı (EK-1) ═══════════════════════════

HOLDS = (2, 3, 5)                  # işlem günü sonra NY 16:00
STOP_MULTS = (1.0, 2.0)            # yapı stopu / felaket stopu (2 × yapı riski)


def day_n_16(t_utc: int, n: int) -> int:
    d = datetime.fromtimestamp(t_utc, NY).date()
    k = 0
    while k < n:
        d += timedelta(days=1)
        if d.weekday() < 5 and not lib.nyse.is_holiday(d):
            k += 1
    return int(datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).timestamp())


def evaluate_hold(p: veri.PathBars, t_sig: int, stop: float, sig_close: float | None = None,
                  stop_pct: float | None = None) -> np.ndarray | None:
    """Dönüş: (len(STOP_MULTS), len(HOLDS), 3) → [R, R15, bp]. R yapı riski (1×) cinsinden."""
    i = int(np.searchsorted(p.t, t_sig))
    if i >= len(p.t) or p.t[i] - t_sig > 4 * 86400:
        return None
    opt = sig_close is not None
    spi = 0.0 if opt else float(p.spr[i])
    ask = (sig_close if opt else float(p.o[i])) + spi
    if stop_pct is not None:
        stop = ask * (1 - stop_pct)
    stop = min(stop, ask * (1 - MIN_RISK))
    risk = ask - stop
    if risk <= 0:
        return None
    t0 = int(p.t[i])
    ends = [day_n_16(t0, n) for n in HOLDS]
    jmax = min(max(int(np.searchsorted(p.t, max(ends))), i + 1), len(p.t))
    lo, op = p.l[i:jmax], p.o[i:jmax]
    out = np.full((len(STOP_MULTS), len(HOLDS), 3), np.nan)
    for a_, sm in enumerate(STOP_MULTS):
        st = ask - sm * risk
        hs = np.flatnonzero(lo <= st)
        js = int(hs[0]) if hs.size else 10 ** 9
        for b_, te in enumerate(ends):
            jT = int(np.searchsorted(p.t[i:jmax], te))
            if js < jT:
                j, px = js, min(st, float(op[js]))
            else:
                g = i + jT
                if g < len(p.t) and p.t[g] - te <= 4 * 86400:
                    j, px = jT, float(p.o[g])
                else:
                    j, px = jT - 1, float(p.c[i + jT - 1])
            g = min(i + j, len(p.t) - 1)
            nights = (datetime.fromtimestamp(int(p.t[g]), NY).date() - datetime.fromtimestamp(t0, NY).date()).days
            net = (px / ask - 1) * 1e4 - lib.FIN_BP_PER_DAY * max(0, nights)
            extra = 0.5 * (spi + float(p.spr[g])) / ask * 1e4
            rb = risk / ask * 1e4
            out[a_, b_] = (net / rb, (net - extra) / rb, net)
    return out


def evaluate_hold_all(p: veri.PathBars, e: pd.DataFrame, optimistic: bool = False, shift: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    for n, r in enumerate(e.itertuples()):
        ts = int(r.t_sig + (shift[n] if shift is not None else 0))
        stop_pct = None
        if shift is not None:
            i = min(int(np.searchsorted(p.t, int(r.t_sig))), len(p.t) - 1)
            ref = float(p.o[i]) + float(p.spr[i])
            stop_pct = max(MIN_RISK, (ref - r.stop) / ref)
        res = evaluate_hold(p, ts, r.stop, sig_close=(r.sig_close if optimistic else None), stop_pct=stop_pct)
        if res is None:
            continue
        i = min(int(np.searchsorted(p.t, ts)), len(p.t) - 1)
        for a_, sm in enumerate(STOP_MULTS):
            for b_, h in enumerate(HOLDS):
                rows.append((n, sm, h, *res[a_, b_], int(p.t[i]), day_n_16(int(p.t[i]), h)))
    return pd.DataFrame(rows, columns=["e", "tp", "time", "R", "R15", "bp", "t_in", "t_out"])



# ═══════════════════════════ Tur 3: ölçülen hareket / genel değerlendirici (EK-3) ═══════════════════════════

TPS3 = ("MM", "2R", "yok")
TIMES3 = ("24h", "D1_16", "D3_16")


def _end(t0: int, name: str) -> int:
    return {"24h": t0 + 24 * 3600, "D1_16": day_n_16(t0, 1), "D3_16": day_n_16(t0, 3)}[name]


def evaluate_r3(p: veri.PathBars, t_sig: int, stop: float, mm: float, sig_close: float | None = None,
                stop_pct: float | None = None, mm_pct: float | None = None) -> tuple[np.ndarray, int, list[int]] | None:
    i = int(np.searchsorted(p.t, t_sig))
    if i >= len(p.t) or p.t[i] - t_sig > 4 * 86400:
        return None
    opt = sig_close is not None
    spi = 0.0 if opt else float(p.spr[i])
    ask = (sig_close if opt else float(p.o[i])) + spi
    if stop_pct is not None:
        stop = ask * (1 - stop_pct)
    if mm_pct is not None:
        mm = ask * (1 + mm_pct)
    stop = min(stop, ask * (1 - MIN_RISK))
    risk = ask - stop
    if risk <= 0:
        return None
    t0 = int(p.t[i])
    ends = [_end(t0, n) for n in TIMES3]
    jmax = min(max(int(np.searchsorted(p.t, max(ends))), i + 1), len(p.t))
    lo, hi, op = p.l[i:jmax], p.h[i:jmax], p.o[i:jmax]
    hs = np.flatnonzero(lo <= stop)
    js = int(hs[0]) if hs.size else 10 ** 9
    cm = np.maximum.accumulate(hi)
    tps = {"MM": mm if mm > ask else np.nan, "2R": ask + 2 * risk, "yok": np.inf}
    out = np.full((len(TPS3), len(TIMES3), 3), np.nan)
    touts = []
    for b_, te in enumerate(ends):
        jT = int(np.searchsorted(p.t[i:jmax], te))
        for a_, tn in enumerate(TPS3):
            tp = tps[tn]
            if not np.isfinite(tp) and tn != "yok":
                continue                                   # MM girişin altında → hücre dışı
            jt = int(np.searchsorted(cm, tp)) if np.isfinite(tp) else 10 ** 9
            if js < jT and js <= jt:
                j, px = js, min(stop, float(op[js]))
            elif jt < jT:
                j, px = jt, max(tp, float(op[jt]))
            else:
                g = i + jT
                if g < len(p.t) and p.t[g] - te <= 4 * 86400:
                    j, px = jT, float(p.o[g])
                else:
                    j, px = jT - 1, float(p.c[i + jT - 1])
            g = min(i + j, len(p.t) - 1)
            nights = (datetime.fromtimestamp(int(p.t[g]), NY).date() - datetime.fromtimestamp(t0, NY).date()).days
            net = (px / ask - 1) * 1e4 - lib.FIN_BP_PER_DAY * max(0, nights)
            extra = 0.5 * (spi + float(p.spr[g])) / ask * 1e4
            rb = risk / ask * 1e4
            out[a_, b_] = (net / rb, (net - extra) / rb, net)
        touts.append(int(p.t[min(i + jT, len(p.t) - 1)]))
    return out, t0, touts


def evaluate_r3_all(p: veri.PathBars, e: pd.DataFrame, optimistic: bool = False, shift: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    for n, r in enumerate(e.itertuples()):
        mm = r.neck + (r.neck - min(r.L1, r.L2))
        ts = int(r.t_sig + (shift[n] if shift is not None else 0))
        stop_pct = mm_pct = None
        if shift is not None:
            i = min(int(np.searchsorted(p.t, int(r.t_sig))), len(p.t) - 1)
            ref = float(p.o[i]) + float(p.spr[i])
            stop_pct, mm_pct = max(MIN_RISK, (ref - r.stop) / ref), (mm - ref) / ref
        res = evaluate_r3(p, ts, r.stop, mm, sig_close=(r.sig_close if optimistic else None), stop_pct=stop_pct, mm_pct=mm_pct)
        if res is None:
            continue
        arr, t0, touts = res
        for a_, tn in enumerate(TPS3):
            for b_, tm in enumerate(TIMES3):
                if np.isfinite(arr[a_, b_, 0]):
                    rows.append((n, tn, tm, *arr[a_, b_], t0, touts[b_]))
    return pd.DataFrame(rows, columns=["e", "tp", "time", "R", "R15", "bp", "t_in", "t_out"])
