"""PROTOCOL.md §3 kurallarının olay üreticileri. Her olay: sig (H1 karar barı), ent (giriş barı), atr, hold (bar)."""
from __future__ import annotations
import numpy as np, pandas as pd
from mech import h4_frame

# (tp, sl, hold) — hold: int bar sayısı ya da "NY16" (NY 15:00 barının kapanışına kadar)
GEOM = {
    "R0": [(None, 1.5, 20), (1.0, 1.0, 12), (2.0, 1.5, 24)],
    "R1": [(2.0, 1.5, 24), (1.0, 1.0, 12), (None, 1.5, 8)],
    "R2": [(1.5, 1.0, 8), (1.0, 1.0, 8), (None, 1.0, "NY16")],
    "R3": [(None, 1.5, "NY16"), (1.5, 1.0, "NY16"), (1.0, 1.0, "NY16")],
    "R4": [(2.0, 1.5, 24), (1.0, 1.0, 12), (None, 1.5, 12)],
    "R5": [(2.0, 1.5, 24), (1.0, 1.0, 24), (None, 1.0, 24)],
}
DESC = {
    "R0": "MK-04 replikasyonu: H1 high ≥ önceki 20 high (filtre yok)",
    "R1": "H1 close > önceki 48 high + D1>EMA200 + H4>EMA50",
    "R2": "Londra 07-12: Asya (00-07 Ldn) high'ının üstünde ilk kapanış + D1>EMA200",
    "R3": "NY 09:00 barı kapanışı > gün açılışı ve > NY08 açılışı + D1>EMA200",
    "R4": "BB(20,2) sıkışma (bw ≤ 120-bar %20) sonrası üst band üstü kapanış + D1>EMA200",
    "R5": "H4 close > önceki 20 H4 high + D1>EMA200 (H4 ATR)",
}


def _ny16_hold(d: pd.DataFrame, ent: np.ndarray) -> np.ndarray:
    """Giriş barından aynı NY gününün 15:00 barına (dahil) kadar bar sayısı; yoksa 0."""
    day = d["day"].to_numpy(); nyh = d["ny_h"].to_numpy(); n = len(d)
    is15 = np.where(nyh == 15)[0]
    out = np.zeros(len(ent), int)
    k = np.searchsorted(is15, ent)
    ok = k < len(is15)
    j = is15[np.clip(k, 0, len(is15) - 1)]
    same = ok & (day[j] == day[np.clip(ent, 0, n - 1)])
    out[same] = j[same] - ent[same] + 1
    return out


def events(d: pd.DataFrame, rule: str, side: int) -> pd.DataFrame:
    """side +1: BUY kuralı, −1: SELL aynası. Dönüş: sig, ent, atr (kural TF'inde), year, utc_h, day."""
    o, h, l, c = (d[k].to_numpy() for k in "ohlc")
    n = len(d)
    tu = d.trend_up.to_numpy() if side > 0 else d.trend_dn.to_numpy()
    atr = d.atr.to_numpy()
    if rule == "R0":
        if side > 0:
            m = h >= pd.Series(h).rolling(20).max().shift(1).to_numpy()
        else:
            m = l <= pd.Series(l).rolling(20).min().shift(1).to_numpy()
        sig = np.where(m)[0]
    elif rule == "R1":
        h4 = (d.h4_c > d.h4_ema50).to_numpy() if side > 0 else (d.h4_c < d.h4_ema50).to_numpy()
        if side > 0:
            m = c > pd.Series(h).rolling(48).max().shift(1).to_numpy()
        else:
            m = c < pd.Series(l).rolling(48).min().shift(1).to_numpy()
        sig = np.where(m & tu & h4)[0]
    elif rule == "R2":
        ldate = d.ts.dt.tz_convert("Europe/London").dt.strftime("%Y-%m-%d").to_numpy()
        lh = d.ldn_h.to_numpy()
        asia = pd.DataFrame({"ld": ldate, "h": h, "l": l})[lh <= 6].groupby("ld").agg(ah=("h", "max"), al=("l", "min"), k=("h", "size"))
        asia = asia[asia.k >= 5]
        ah = pd.Series(ldate).map(asia.ah).to_numpy(); al = pd.Series(ldate).map(asia.al).to_numpy()
        win = (lh >= 7) & (lh <= 11)
        m = win & tu & ((c > ah) if side > 0 else (c < al))
        idx = np.where(m)[0]
        _, first = np.unique(ldate[idx], return_index=True)
        sig = np.sort(idx[first])
    elif rule == "R3":
        nyh = d.ny_h.to_numpy(); day = d.day.to_numpy()
        o8 = pd.Series(day).map(pd.Series(o[nyh == 8], index=day[nyh == 8]).groupby(level=0).first()).to_numpy()
        dop = d.day_open.to_numpy()
        if side > 0:
            m = (nyh == 9) & (c > dop) & (c > o8)
        else:
            m = (nyh == 9) & (c < dop) & (c < o8)
        sig = np.where(m & tu)[0]
    elif rule == "R4":
        cs = pd.Series(c)
        mid, sd = cs.rolling(20).mean(), cs.rolling(20).std(ddof=0)
        bw = (4 * sd / mid)
        q = bw.shift(1).rolling(120).quantile(0.2)
        sq = (bw.shift(1) <= q).to_numpy()
        brk = (c > (mid + 2 * sd).to_numpy()) if side > 0 else (c < (mid - 2 * sd).to_numpy())
        cand = np.where(sq & brk & tu)[0]
        keep, lastf = [], -10 ** 9
        for i in cand:
            if i - lastf > 12:
                keep.append(i); lastf = i
            # 12 bar içindeki tekrar tetikler atlanır (epizod başına ilk)
        sig = np.array(keep, int)
    elif rule == "R5":
        H4 = h4_frame(d)
        hh = H4.h.rolling(20).max().shift(1); ll = H4.l.rolling(20).min().shift(1)
        if side > 0:
            m = (H4.c > hh) & H4.trend_up
        else:
            m = (H4.c < ll) & H4.trend_dn
        sel = H4[m.fillna(False)]
        sig = sel.i_last.to_numpy().astype(int)
    else:
        raise KeyError(rule)
    sig = sig[(sig + 1 < n)]
    ent = sig + 1
    seg = d.seg.to_numpy()
    ok = seg[ent] == seg[sig]
    sig, ent = sig[ok], ent[ok]
    A = (H4_atr_at(d, sig) if rule == "R5" else atr[sig])
    e = pd.DataFrame({"sig": sig, "ent": ent, "atr": A})
    e = e[np.isfinite(e.atr) & (e.atr > 0)]
    e["year"] = d.year.to_numpy()[e.sig]; e["utc_h"] = d.utc_h.to_numpy()[e.sig]
    e["date"] = d.ts.dt.strftime("%Y-%m-%d").to_numpy()[e.sig]
    return e.reset_index(drop=True)


def H4_atr_at(d: pd.DataFrame, sig: np.ndarray) -> np.ndarray:
    """H1 karar barı sig'in kapanışında son kapanmış H4 barının ATR'si."""
    H4 = h4_frame(d)
    end = (d.ts + pd.Timedelta(hours=1)).to_numpy()[sig]
    k = np.searchsorted(H4["end"].to_numpy(), end, side="right") - 1
    return np.where(k >= 0, H4.atr.to_numpy()[np.clip(k, 0, None)], np.nan)


def holds(d: pd.DataFrame, ent: np.ndarray, hold) -> np.ndarray:
    if hold == "NY16":
        return _ny16_hold(d, ent)
    return np.full(len(ent), int(hold))
