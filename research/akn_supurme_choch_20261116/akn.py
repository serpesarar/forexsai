"""akntrade zinciri: 1H iğne süpürmesi → 15m renk-dönüşlü süpürme → 5m/3m CHoCH → FVG limit girişi (PROTOCOL.md).

Sızıntı garantileri:
- Her bar ancak kapanınca bilinir; fraktal salınım sağdaki 2. bar kapanınca.
- Her katman bir öncekinin onay anından SONRA açılan barlara bakar.
- Limit emir FVG bilindikten sonra konur; dolum 1m'de; dolum barında hedef sayılmaz, stop sayılır; aynı barda SL+TP → SL.
Taban motor: research/mtf_supurme_20261029/mtf.py (bar kovaları, Crosser, events_htf, time_end).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "mtf_supurme_20261029"))
import mtf as M  # noqa: E402

DATA = HERE.parent / "nom_20261113" / "data" / "ndx_1m_v3_duka.parquet"
K = 2
PIN_WICK, PIN_BODY = 0.5, 0.33
W2_MIN = 180            # 1H kapanışından sonra 15m onayı için süre
W3_MIN = 60             # 15m onayından sonra CHoCH için süre
C5_FIRST = 6            # C53: önce 5m'de bu kadar bar, sonra 3m de devrede (ikisinden hangisi önce)
FVG_AFTER = 3           # CHoCH'tan sonra FVG için en fazla bar
LIMIT_MIN = 60
HOLD_MIN = 1440
T1_MIN_R, T2_MIN_R = 0.5, 1.0
LTFS = {"C53": (5, 3), "C5": (5,), "C3": (3,), "C1": (1,)}


def load() -> M.Base:
    d = pd.read_parquet(DATA)
    d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True), spread=d.spr.astype(float)).sort_values("ts")
    d = d.drop_duplicates("ts").reset_index(drop=True)
    return M.make_base(d[["ts", "open", "high", "low", "close", "spread", "src"]], "NDX", 1)


def swings_fast(T: M.TF, B: M.Base, cr: M.Crosser) -> tuple[M.Levels, M.Levels]:
    """Vektörel fraktal (k=2): sol 2 kesin, sağ 2 ≤ / ≥. Geçerlilik T.avail[j+2]."""
    out = []
    for side, a in ((1, T.h), (-1, T.l)):
        s = -a if side == -1 else a
        n = len(s)
        j = np.arange(K, n - K)
        ok = (s[j] > s[j - 1]) & (s[j] > s[j - 2]) & (s[j] >= s[j + 1]) & (s[j] >= s[j + 2])
        j = j[ok]
        av = T.avail[j + K]
        keep = av < len(B.h)
        j, av = j[keep], av[keep]
        x = a[j]
        dd = np.array([cr.dead(float(v), int(t), side) for v, t in zip(x, av)], int)
        lv = M.Levels(x.astype(float), av.astype(int), dd, side)
        lv.bar = j          # type: ignore[attr-defined]
        out.append(lv)
    return out[0], out[1]


@dataclass
class Ctx:
    B: M.Base
    T: dict          # tf → TF
    lv: dict         # tf → (tepe, dip)


def build(B: M.Base, tfs=(60, 15, 5, 3, 1)) -> Ctx:
    cr = M.Crosser(B)
    T = {tf: M.resample(B, tf) for tf in tfs}
    lv = {tf: swings_fast(T[tf], B, cr) for tf in tfs}
    return Ctx(B, T, lv)


def pin_ok(T: M.TF, b: int, side: int) -> bool:
    rng = T.h[b] - T.l[b]
    if rng <= 0:
        return False
    body = abs(T.c[b] - T.o[b])
    wick = (T.h[b] - max(T.o[b], T.c[b])) if side == -1 else (min(T.o[b], T.c[b]) - T.l[b])
    return wick >= PIN_WICK * rng and body <= PIN_BODY * rng


def k1_events(cx: Ctx) -> list[tuple[int, int, int]]:
    """(başlangıç taban idx = 1H bar ilk, onay taban idx = 1H kapanışı, yön)."""
    T = cx.T[60]
    ev = M.events_htf(T, *cx.lv[60])
    return [(int(T.first[b]), int(T.avail[b]), side) for b, side, _, _ in ev if pin_ok(T, b, side)]


def k2_table(cx: Ctx) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """15m: süpürme barı j (SAT: yeşil, fraktal tepe aşılıp altında kapanış) + j+1 ters renk. → yön: (j ilk idx, onay idx)."""
    T = cx.T[15]
    out = {}
    for b_side in (-1, 1):
        rows = []
        for b, side, _, _ in M.events_htf(T, *cx.lv[15]):
            if side != b_side or b + 1 >= len(T.first):
                continue
            green, nxt_red = T.c[b] > T.o[b], T.c[b + 1] < T.o[b + 1]
            if (side == -1 and green and nxt_red) or (side == 1 and (not green) and T.c[b] < T.o[b] and T.c[b + 1] > T.o[b + 1]):
                rows.append((int(T.first[b]), int(T.avail[b + 1])))
        a = np.array(rows, int).reshape(-1, 2)
        out[b_side] = (a[:, 0], a[:, 1])
    return out


def k0_starts(cx: Ctx) -> list[tuple[int, int, int]]:
    """Kontrol: her 15m fraktal tepe/dip teyidi bir başlangıç (süpürme / renk / 1H yok)."""
    T = cx.T[15]
    hi, lo = cx.lv[15]
    out = [(int(T.first[j]), int(a), -1) for j, a in zip(hi.bar, hi.avail)]
    out += [(int(T.first[j]), int(a), 1) for j, a in zip(lo.bar, lo.avail)]
    return sorted(out, key=lambda r: r[1])


def chain_starts(cx: Ctx, chain: str) -> list[tuple[int, int, int]]:
    """Zincir varyantı → (uç arama başlangıcı, CHoCH arama başlangıcı = onay, yön)."""
    if chain == "K0":
        return k0_starts(cx)
    k2 = k2_table(cx)
    if chain == "K2":
        return sorted([(int(a), int(c), s) for s in (-1, 1) for a, c in zip(*k2[s])], key=lambda r: r[1])
    out = []
    um = cx.B.um
    if chain == "K1K2n":
        return k1k2_nested(cx)
    for a1, c1, side in k1_events(cx):
        if c1 >= len(um):
            continue
        if chain == "K1":
            out.append((a1, c1, side))
            continue
        ja, jc = k2[side]
        lim = int(np.searchsorted(um, um[c1] + W2_MIN, side="left"))
        m = np.flatnonzero((ja >= c1) & (jc <= lim))
        if len(m):
            out.append((a1, int(jc[m[0]]), side))
    return out


def k1k2_nested(cx: Ctx) -> list[tuple[int, int, int]]:
    """EK-0 iç içe okuma: 1H iğnesinin ucunu yapan 15m barı j süpürme yönünde renkte (SAT: yeşil), j+1 ters renkte.
    Onay = max(1H kapanışı, j+1 kapanışı) — ikisi de bilindikten sonra."""
    B, T, T15 = cx.B, cx.T[60], cx.T[15]
    out = []
    for b, side, _, ext in M.events_htf(T, *cx.lv[60]):
        if not pin_ok(T, b, side):
            continue
        j0 = int(np.searchsorted(T15.first, T.first[b], side="left"))
        j1 = int(np.searchsorted(T15.last, T.last[b], side="right"))
        js = np.arange(j0, min(j1, len(T15.first)))
        if not len(js):
            continue
        j = int(js[np.argmax(T15.h[js])] if side == -1 else js[np.argmin(T15.l[js])])
        if j + 1 >= len(T15.first):
            continue
        green, nxt_green = T15.c[j] > T15.o[j], T15.c[j + 1] > T15.o[j + 1]
        nxt_red = T15.c[j + 1] < T15.o[j + 1]
        red = T15.c[j] < T15.o[j]
        if (side == -1 and green and nxt_red) or (side == 1 and red and nxt_green):
            out.append((int(T.first[b]), int(max(T.avail[b], T15.avail[j + 1])), side))
    return out


def _alive_level(lv: M.Levels, t: int) -> float:
    """t anında bilinen ve hâlâ aşılmamış en son fraktal seviyesi."""
    i = int(np.searchsorted(lv.avail, t, side="right")) - 1
    for _ in range(60):
        if i < 0:
            return np.nan
        if lv.dead[i] >= t:
            return float(lv.x[i])
        i -= 1
    return np.nan


def choch(cx: Ctx, tf: int, t0: int, ext: float, side: int, t_end: int, max_bars: int | None = None):
    """t0'dan sonra açılan ilk LTF barı CHoCH seviyesinin ötesinde kapanırsa → bar idx. Uç aşılırsa ölür."""
    L = cx.T[tf]
    hi, lo = cx.lv[tf]
    x = _alive_level(lo if side == -1 else hi, t0)
    if not np.isfinite(x):
        return None
    i0 = int(np.searchsorted(L.first, t0, side="left"))
    i1 = int(np.searchsorted(L.last, t_end, side="left"))
    if max_bars is not None:
        i1 = min(i1, i0 + max_bars)
    for i in range(i0, min(i1, len(L.first))):
        if (side == -1 and L.h[i] > ext) or (side == 1 and L.l[i] < ext):
            return None
        if (side == -1 and L.c[i] < x) or (side == 1 and L.c[i] > x):
            return i
    return None


def fvg(L: M.TF, i_ext: int, i_ch: int, side: int):
    """Ayı FVG: h_c < l_a (boğa: l_c > h_a). Önce [i_ext+2, i_ch] içinde en sonuncusu, yoksa sonraki FVG_AFTER bar."""
    def is_gap(c: int) -> bool:
        return (L.h[c] < L.l[c - 2]) if side == -1 else (L.l[c] > L.h[c - 2])
    for c in range(i_ch, max(i_ext + 2, 2) - 1, -1):
        if is_gap(c):
            return c
    for c in range(i_ch + 1, min(i_ch + 1 + FVG_AFTER, len(L.first))):
        if is_gap(c):
            return c
    return None


def nearest(lv: M.Levels, t: int, side: int, entry: float, risk: float, min_r: float) -> float:
    m = (lv.avail <= t) & (lv.dead >= t)
    x = lv.x[m]
    if side == -1:
        x = x[x <= entry - min_r * risk]
        return float(x.max()) if len(x) else np.nan
    x = x[x >= entry + min_r * risk]
    return float(x.min()) if len(x) else np.nan


def sim_from(B: M.Base, side: int, f: int, entry: float, stop_bid: float, t_end: int, tps: list[float],
             spm: float, skip_tp_first: bool) -> tuple[float, list[float], list[int]]:
    """Girişi f barında 'entry' (yürütme fiyatı) olan işlem. Stop/hedef bid cinsinden; SAT ask = bid + spread ile."""
    sp = B.sp * spm
    q = slice(f, t_end + 1)
    if side == 1:
        fav, adv, op, cl = B.h[q], B.l[q], B.o[q], B.c[q]
        sl = stop_bid
    else:
        s = sp[q]
        fav, adv, op, cl = B.l[q] + s, B.h[q] + s, B.o[q] + s, B.c[q] + s
        sl = stop_bid + sp[f]
    risk = side * (entry - sl)
    hit = (adv <= sl) if side == 1 else (adv >= sl)
    T = len(adv)
    st = int(np.argmax(hit)) if hit.any() else T
    if st < T:
        px = sl
        if st > 0 and ((side == 1 and op[st] < sl) or (side == -1 and op[st] > sl)):
            px = op[st]
        r_stop = side * (px - entry) / risk
    else:
        r_stop = side * (cl[-1] - entry) / risk
    rs, xs = [], []
    for tp in tps:
        if not np.isfinite(tp):
            rs.append(r_stop)
            xs.append(f + min(st, T - 1))
            continue
        tpx = tp if side == 1 else tp + sp[f]
        th = (fav >= tpx) if side == 1 else (fav <= tpx)
        if skip_tp_first:
            th = th.copy()
            th[0] = False
        t = int(np.argmax(th)) if th.any() else T
        rs.append(side * (tpx - entry) / risk if t < st else r_stop)
        xs.append(f + min(t, st, T - 1))
    return risk, rs, xs


def make_trade(cx: Ctx, a0: int, t0: int, side: int, ltf: str, entry_mode: str, spm: float = 1.0) -> dict | None:
    """Bir başlangıçtan (uç arama a0, onay t0) tam işlem; yoksa None."""
    B = cx.B
    um = B.um
    if t0 >= len(um):
        return None
    seg = B.h[a0:t0] if side == -1 else B.l[a0:t0]
    if not len(seg):
        return None
    k_ext = a0 + (int(np.argmax(seg)) if side == -1 else int(np.argmin(seg)))
    ext = float(B.h[k_ext] if side == -1 else B.l[k_ext])
    t_end = int(np.searchsorted(um, um[t0] + W3_MIN, side="left"))
    best = None
    for tf in LTFS[ltf]:
        mb = C5_FIRST if (ltf == "C53" and tf == 5) else None
        i = choch(cx, tf, t0, ext, side, t_end, mb)
        if i is not None and (best is None or cx.T[tf].avail[i] < best[0]):
            best = (int(cx.T[tf].avail[i]), tf, i)
    if best is None:
        return None
    _, tf, i_ch = best
    L = cx.T[tf]
    i_ext = int(np.searchsorted(L.last, k_ext, side="left"))
    c = fvg(L, i_ext, i_ch, side)
    if c is None:
        return None
    lo_gap, hi_gap = (L.h[c], L.l[c - 2]) if side == -1 else (L.h[c - 2], L.l[c])
    px = (lo_gap if side == -1 else hi_gap) if entry_mode == "E1" else (lo_gap + hi_gap) / 2
    place = int(max(L.avail[i_ch], L.avail[c]))
    if place >= len(B.o):
        return None
    stop_bid = ext + (B.tick if side == -1 else -B.tick)
    sp_p = B.sp[place] * spm
    risk0 = (stop_bid + sp_p - px) if side == -1 else (px - stop_bid)
    if risk0 < M.MIN_RISK_SP * sp_p or (side == -1 and px >= stop_bid) or (side == 1 and px <= stop_bid):
        return None
    hi15, lo15 = cx.lv[15]
    hi60, lo60 = cx.lv[60]
    t1 = nearest(lo15 if side == -1 else hi15, place, side, px, risk0, T1_MIN_R)
    lim_end = int(np.searchsorted(um, um[place] + LIMIT_MIN, side="left"))
    f = None
    for j in range(place, min(lim_end, len(B.o))):
        if side == -1:
            if B.h[j] >= px:
                f = j
                break
            if np.isfinite(t1) and B.l[j] + B.sp[j] * spm <= t1 + sp_p:
                return None
        else:
            if B.l[j] + B.sp[j] * spm <= px:
                f = j
                break
            if np.isfinite(t1) and B.h[j] >= t1:
                return None
    if f is None:
        return None
    entry = px
    t2 = nearest(lo60 if side == -1 else hi60, f, side, px, risk0, T2_MIN_R)
    t_hold = M.time_end(B, f, HOLD_MIN)
    to_bid = lambda p: p - (B.sp[f] * spm if side == -1 else 0.0)  # noqa: E731
    tps = [to_bid(entry + side * r * risk0) for r in (1.0, 2.0)] + [t1, t2]
    risk, rs, xs = sim_from(B, side, f, entry, stop_bid, t_hold, tps, spm, True)
    r_of = lambda x: side * ((x + (B.sp[f] * spm if side == -1 else 0.0)) - entry) / risk if np.isfinite(x) else np.nan  # noqa: E731
    return {"side": side, "a0": a0, "t0": t0, "f": f, "ltf": tf, "um": int(um[f]), "day": B.day[f],
            "rth": bool(B.rth[f]), "risk": risk, "risk_sp": risk / (B.sp[f] * spm), "entry": entry, "stop": stop_bid,
            "t1_r": r_of(t1), "t2_r": r_of(t2), "R1": rs[0], "R2": rs[1], "RT1": rs[2], "RT2": rs[3],
            "x1": xs[0], "x2": xs[1], "xT1": xs[2], "xT2": xs[3], "t_hold": t_hold}


def run(cx: Ctx, chain: str, ltf: str, entry_mode: str, spm: float = 1.0) -> pd.DataFrame:
    rows, seen = [], set()
    for a0, t0, side in chain_starts(cx, chain):
        tr = make_trade(cx, a0, t0, side, ltf, entry_mode, spm)
        if tr is None or (tr["side"], tr["f"], round(tr["entry"], 3)) in seen:
            continue
        seen.add((tr["side"], tr["f"], round(tr["entry"], 3)))
        rows.append(tr)
    return pd.DataFrame(rows).assign(chain=chain, ltf_v=ltf, giris=entry_mode) if rows else pd.DataFrame()


def mirror(cx: Ctx, df: pd.DataFrame, col: str, spm: float = 1.0) -> np.ndarray:
    """Aynı dolum barı ve fiyatı, ters yön, aynı risk, aynı hedef R (hedef yoksa zaman)."""
    B, out = cx.B, []
    rcol = {"RT1": "t1_r", "RT2": "t2_r"}.get(col)
    for r in df.itertuples():
        side = -r.side
        sp_f = B.sp[r.f] * spm
        entry = r.entry
        stop_bid = entry - side * r.risk - (sp_f if side == -1 else 0.0)
        tr_ = getattr(r, rcol) if rcol else {"R1": 1.0, "R2": 2.0}[col]
        tp = (entry + side * tr_ * r.risk - (sp_f if side == -1 else 0.0)) if np.isfinite(tr_) else np.nan
        out.append(sim_from(B, side, r.f, entry, stop_bid, r.t_hold, [tp], spm, True)[1][0])
    return np.array(out)
