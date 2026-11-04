"""prereg.md §3 tetikleri. Her fonksiyon (t, d) döndürür: t = karar dakikası (kapanışı bilinen bar), d = ±1.
Giriş e = t + 1 (geçerlilik ayrıca süzülür)."""
from __future__ import annotations

import numpy as np
import pandas as pd

import common as C


def refractory(t: np.ndarray, gap: int) -> np.ndarray:
    t = np.sort(t)
    keep = []
    last = -10 ** 12
    for x in t:
        if x - last >= gap:
            keep.append(x)
            last = x
    return np.array(keep, dtype=np.int64)


def _pack(tL, tS):
    t = np.concatenate([tL, tS]).astype(np.int64)
    d = np.concatenate([np.ones(len(tL), int), -np.ones(len(tS), int)])
    return t, d


# ── VS1: 5m sıkışma kırılımı ──────────────────────────────────────────────
def vs1(g: C.Grid, squeeze: bool = True, q: float = 0.10):
    c5 = pd.Series(g.c5)
    bbw = c5.rolling(20, min_periods=20).std() / c5.rolling(20, min_periods=20).mean()
    pct = bbw.rolling(2017, min_periods=1000).rank(pct=True).to_numpy()
    sq_prev = np.concatenate([[False], (pct <= q)[:-1]])
    hh = pd.Series(g.h5).rolling(12, min_periods=12).max().shift(1).to_numpy()
    ll = pd.Series(g.l5).rolling(12, min_periods=12).min().shift(1).to_numpy()
    upk = g.c5 > hh
    dnk = g.c5 < ll
    if squeeze:
        upk &= sq_prev
        dnk &= sq_prev
    tL = np.where(upk)[0] * 5 + 4
    tS = np.where(dnk)[0] * 5 + 4
    return _pack(refractory(tL, 60), refractory(tS, 60))


# ── VS2: 1m sıkışma kırılımı ──────────────────────────────────────────────
def vs2(g: C.Grid, squeeze: bool = True, q: float = 0.05):
    c = pd.Series(g.C)
    bbw = c.rolling(60, min_periods=55).std() / c.rolling(60, min_periods=55).mean()
    pct = bbw.rolling(1441, min_periods=1000).rank(pct=True).to_numpy()
    sq_prev = np.concatenate([[False], (pct <= q)[:-1]])
    hh = pd.Series(g.H).rolling(60, min_periods=55).max().shift(1).to_numpy()
    ll = pd.Series(g.L).rolling(60, min_periods=55).min().shift(1).to_numpy()
    up = g.C > hh
    dn = g.C < ll
    if squeeze:
        up &= sq_prev
        dn &= sq_prev
    return _pack(refractory(np.where(up)[0], 60), refractory(np.where(dn)[0], 60))


# ── ST-S: sabit çapa, iki yön ─────────────────────────────────────────────
def anchors_ny(g: C.Grid, mod: int) -> np.ndarray:
    return np.where((g.ny_mod == mod) & (g.ny_wd < 5))[0]


def st_s(g: C.Grid, mod: int):
    A = anchors_ny(g, mod)
    t = A - 1
    return _pack(t, t)


# ── OR: açılış aralığı ────────────────────────────────────────────────────
def session_anchors(g: C.Grid, sess: str) -> np.ndarray:
    if sess == "ASIA":
        m = np.arange(g.N)
        return np.where((m % 1440 == 0) & (g.utc_wd < 5))[0]
    if sess == "LON":
        return np.where((g.lo_mod == 480) & (g.lo_wd < 5))[0]
    if sess == "US":
        return anchors_ny(g, 570)
    raise ValueError(sess)


def orb_orf(g: C.Grid, sess: str, lor: int, watch: int = 120):
    A = session_anchors(g, sess)
    bL, bS, fL, fS = [], [], [], []
    H, L, Cc, atr = g.H, g.L, g.C, g.atr5
    for a in A:
        if a + lor + watch + 5 >= g.N:
            continue
        hs, ls = H[a:a + lor], L[a:a + lor]
        if np.isnan(hs).sum() > lor // 3:
            continue
        orh, orl = np.nanmax(hs), np.nanmin(ls)
        w0, w1 = a + lor, a + lor + watch
        cw = Cc[w0:w1]
        # ORB: ilk kapanış dışarıda
        up = np.where(cw > orh)[0]
        dn = np.where(cw < orl)[0]
        iu = up[0] if len(up) else 10 ** 9
        idn = dn[0] if len(dn) else 10 ** 9
        if iu < idn:
            bL.append(w0 + iu)
        elif idn < iu:
            bS.append(w0 + idn)
        # ORF yukarı dürtme → S
        hw = H[w0:w1]
        pj = np.where(hw > orh)[0]
        if len(pj):
            j = w0 + pj[0]
            mx = -np.inf
            for t in range(j, j + 4):
                mx = max(mx, H[t]) if not np.isnan(H[t]) else mx
                if Cc[t] < orh:
                    if mx - orh <= atr[t + 1]:
                        fS.append(t)
                    break
        lw = L[w0:w1]
        pj = np.where(lw < orl)[0]
        if len(pj):
            j = w0 + pj[0]
            mn = np.inf
            for t in range(j, j + 4):
                mn = min(mn, L[t]) if not np.isnan(L[t]) else mn
                if Cc[t] > orl:
                    if orl - mn <= atr[t + 1]:
                        fL.append(t)
                    break
    return _pack(np.array(bL), np.array(bS)), _pack(np.array(fL), np.array(fS))


# ── VW: VWAP sapması ──────────────────────────────────────────────────────
def vwap_frame(g: C.Grid, anchor: str):
    n = g.N
    m = np.arange(n)
    if anchor == "D":
        grp = g.utc_day.astype(np.int64)
        since = m % 1440
        act = since >= 60
        inwin = np.ones(n, bool)
    else:
        inwin = (g.ny_mod >= 570) & (g.ny_mod < 960) & (g.ny_wd < 5)
        grp = np.where(inwin, g.ny_day, -1).astype(np.int64)
        since = g.ny_mod - 570
        act = inwin & (since >= 30)
    v = np.where(np.isfinite(g.V) & inwin, g.V, 0.0)
    q = np.where(np.isfinite(g.Q) & inwin, g.Q, 0.0)
    p = np.divide(q, v, out=np.zeros(n), where=v > 0)
    df = pd.DataFrame({"g": grp, "v": v, "q": q, "vp2": v * p * p})
    cs = df.groupby("g")[["v", "q", "vp2"]].cumsum()
    cv, cq, cvp2 = cs["v"].to_numpy(), cs["q"].to_numpy(), cs["vp2"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = cq / cv
        var = cvp2 / cv - vw ** 2
    sig = np.sqrt(np.clip(var, 0, None))
    ok = act & np.isfinite(vw) & (sig > 0) & np.isfinite(g.C)
    return grp, vw, sig, ok


def vw_rev(g: C.Grid, anchor: str, k: float):
    grp, vw, sig, ok = vwap_frame(g, anchor)
    c = g.C
    hi = c > vw + k * sig
    lo = c < vw - k * sig
    prev_ok = np.concatenate([[False], ok[:-1] & (grp[:-1] == grp[1:])])
    hi_p = np.concatenate([[True], hi[:-1]])
    lo_p = np.concatenate([[True], lo[:-1]])
    tS = np.where(ok & prev_ok & hi & ~hi_p)[0]
    tL = np.where(ok & prev_ok & lo & ~lo_p)[0]
    return _pack(refractory(tL, 30), refractory(tS, 30))


def vw_rec(g: C.Grid, anchor: str, k: float, lookback: int = 120):
    grp, vw, sig, ok = vwap_frame(g, anchor)
    c = g.C
    n = g.N
    idx = np.arange(n, dtype=float)

    def last_flag(flag):
        s = pd.Series(np.where(flag & ok, idx, np.nan))
        return s.groupby(grp).ffill().to_numpy()

    lastlo = last_flag(c <= vw - k * sig)
    lasthi = last_flag(c >= vw + k * sig)
    above = c > vw
    below = c < vw
    prev_ok = np.concatenate([[False], ok[:-1] & (grp[:-1] == grp[1:])])
    ab_p = np.concatenate([[True], above[:-1]])
    be_p = np.concatenate([[True], below[:-1]])
    llp = np.concatenate([[np.nan], lastlo[:-1]])
    lhp = np.concatenate([[np.nan], lasthi[:-1]])
    tL = np.where(ok & prev_ok & above & ~ab_p & (idx - llp <= lookback))[0]
    tS = np.where(ok & prev_ok & below & ~be_p & (idx - lhp <= lookback))[0]
    return _pack(refractory(tL, 30), refractory(tS, 30))


# ── LS: önceki saat/gün ucu süpürme ───────────────────────────────────────
def sweep(g: C.Grid, period: int):
    nper = g.N // period
    Hm = g.H[:nper * period].reshape(nper, period)
    Lm = g.L[:nper * period].reshape(nper, period)
    with np.errstate(all="ignore"):
        import warnings
        warnings.simplefilter("ignore")
        PH = np.concatenate([[np.nan], np.nanmax(Hm, axis=1)[:-1]])
        PL = np.concatenate([[np.nan], np.nanmin(Lm, axis=1)[:-1]])
    out = {}
    for side in ("S", "L"):
        if side == "S":
            br = Hm > PH[:, None]
        else:
            br = Lm < PL[:, None]
        has = br.any(axis=1) & np.isfinite(PH if side == "S" else PL)
        rows = np.where(has)[0]
        jj = br[rows].argmax(axis=1)
        res = []
        for r_, j_ in zip(rows, jj):
            j = r_ * period + j_
            lev = PH[r_] if side == "S" else PL[r_]
            ext = -np.inf if side == "S" else np.inf
            for t in range(j, min(j + 4, g.N - 2)):
                if side == "S":
                    if not np.isnan(g.H[t]):
                        ext = max(ext, g.H[t])
                    if g.C[t] < lev:
                        if ext - lev <= g.atr5[t + 1]:
                            res.append(t)
                        break
                else:
                    if not np.isnan(g.L[t]):
                        ext = min(ext, g.L[t])
                    if g.C[t] > lev:
                        if lev - ext <= g.atr5[t + 1]:
                            res.append(t)
                        break
        out[side] = np.array(res, dtype=np.int64)
    return _pack(out["L"], out["S"])


# ── MA: makro olay dakikası ───────────────────────────────────────────────
CAL = "/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/makro/out/calendar.csv"


def macro(g: C.Grid, events: tuple, mode: str):
    cal = pd.read_csv(CAL, parse_dates=["ts_utc"])
    cal = cal[cal["event"].isin(events)]
    T = ((cal["ts_utc"] - C.T0) / pd.Timedelta(minutes=1)).to_numpy()
    T = T[(T >= 0) & (T < g.N - 2)].astype(np.int64)
    r0 = np.log(g.C[T] / g.O[T])
    ok = np.isfinite(r0) & (r0 != 0)
    T, r0 = T[ok], r0[ok]
    d = np.sign(r0).astype(int)
    if mode == "F":
        d = -d
    return T, d


def all_variants(g: C.Grid) -> dict:
    """Hipotez varyantı → (t, d, aile, kontrol mü)."""
    V = {}
    t, d = vs1(g, True); V["VS1"] = (t, d, "VS1", False)
    t, d = vs1(g, False); V["VS1-C"] = (t, d, "VS1-C", True)
    t, d = vs2(g, True); V["VS2"] = (t, d, "VS2", False)
    t, d = vs2(g, False); V["VS2-C"] = (t, d, "VS2-C", True)
    for mod, nm in ((570, "0930"), (600, "1000")):
        t, d = st_s(g, mod); V[f"ST-S-{nm}"] = (t, d, "ST-S", False)
    for sess, lor in (("ASIA", 30), ("LON", 30), ("US", 15), ("US", 30)):
        (tb, db), (tf, df) = orb_orf(g, sess, lor)
        V[f"ORB-{sess}{lor}"] = (tb, db, "ORB", False)
        V[f"ORF-{sess}{lor}"] = (tf, df, "ORF", False)
    for anc in ("D", "U"):
        for k in (2.0, 3.0):
            t, d = vw_rev(g, anc, k); V[f"VWREV-{anc}{k:g}"] = (t, d, "VW-REV", False)
        for k in (1.5, 2.5):
            t, d = vw_rec(g, anc, k); V[f"VWREC-{anc}{k:g}"] = (t, d, "VW-REC", False)
    t, d = sweep(g, 60); V["LS-H"] = (t, d, "LS", False)
    t, d = sweep(g, 1440); V["LS-D"] = (t, d, "LS", False)
    for ev, nm in ((("CPI", "NFP"), "CPINFP"), (("FOMC",), "FOMC")):
        for mode in ("C", "F"):
            t, d = macro(g, ev, mode); V[f"MA-{nm}-{mode}"] = (t, d, "MA", False)
    return V
