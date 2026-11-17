"""EK-1 F3 — "stop olduktan sonra hedefe gidiyorsa stopu korunan uca koy" (madde 3).

Taban: 15 dk aralık kırılımı (09:30, 10:00, 13:30). Hedef fiyatı sabit = giriş ± 2 × taban risk.
Stop: taban (aralığın karşı ucu) · korunan (girişten önce teyitli son 5m fraktal, k 2) · geniş 1,5× · dar 0,5×.
Plasebo: aynı anda yazı-tura yön, aynı mesafeler (korunan = karşı taraftaki fraktal).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from derin_lib import CLOSE, DOW_NAMES, OUT, RNG, load_mat

STARTS = {"0930": 570, "1000": 600, "1330": 810}
OR_LEN = 15
TGT_R = 2.0
FRACTAL_K = 2
STOPS = ("taban", "korunan", "genis", "dar")


def fractals_5m(h: np.ndarray, l: np.ndarray, upto: int) -> tuple[float, float]:
    """Gün başından `upto` dakikasına kadar kapanmış 5m barlarda teyitli son fraktal dip/tepe."""
    n5 = upto // 5
    if n5 < 2 * FRACTAL_K + 1:
        return np.nan, np.nan
    hh = np.array([np.nanmax(h[5 * b:5 * b + 5]) if np.isfinite(h[5 * b:5 * b + 5]).any() else np.nan for b in range(n5)])
    ll = np.array([np.nanmin(l[5 * b:5 * b + 5]) if np.isfinite(l[5 * b:5 * b + 5]).any() else np.nan for b in range(n5)])
    lo = hi = np.nan
    for j in range(FRACTAL_K, n5 - FRACTAL_K):
        wl, wh = ll[j - FRACTAL_K:j + FRACTAL_K + 1], hh[j - FRACTAL_K:j + FRACTAL_K + 1]
        if np.isfinite(wl).all() and ll[j] == wl.min() and (wl == ll[j]).sum() == 1:
            lo = ll[j]
        if np.isfinite(wh).all() and hh[j] == wh.max() and (wh == hh[j]).sum() == 1:
            hi = hh[j]
    return lo, hi


def run_trade(h, l, c, e, side, stop, tgt, k, cost_pts, r0):
    """k: giriş dakikası. Sonuç taban-risk biriminde; ayrıca stop sonrası hedefe varış (pişmanlık)."""
    hs, ls = h[k:CLOSE], l[k:CLOSE]
    hit_s = (ls <= stop) if side > 0 else (hs >= stop)
    hit_t = (hs >= tgt) if side > 0 else (ls <= tgt)
    js = np.argmax(hit_s) if hit_s.any() else 10 ** 6
    jt = np.argmax(hit_t) if hit_t.any() else 10 ** 6
    if js <= jt and js < 10 ** 6:
        regret = bool(hit_t[js + 1:].any()) if js + 1 < len(hit_t) else False
        return (stop - e) * side / r0 - cost_pts / r0, "stop", regret
    if jt < 10 ** 6:
        return (tgt - e) * side / r0 - cost_pts / r0, "hedef", False
    last = c[k:CLOSE][np.isfinite(c[k:CLOSE])]
    return (last[-1] - e) * side / r0 - cost_pts / r0, "zaman", False


def trades(m) -> pd.DataFrame:
    rows = []
    for i in range(len(m.days)):
        h, l, c, o = m.H[i], m.L[i], m.C[i], m.O[i]
        for sname, s in STARTS.items():
            rng_h, rng_l = np.nanmax(h[s:s + OR_LEN]), np.nanmin(l[s:s + OR_LEN])
            if not (np.isfinite(rng_h) and np.isfinite(rng_l)) or rng_h <= rng_l:
                continue
            seg = c[s + OR_LEN:CLOSE - 30]
            out = np.flatnonzero((seg > rng_h) | (seg < rng_l))
            if len(out) == 0:
                continue
            kb = s + OR_LEN + out[0]
            k = kb + 1
            if not np.isfinite(o[k]):
                continue
            e = o[k]
            real = 1 if c[kb] > rng_h else -1
            flo, fhi = fractals_5m(h, l, k)
            cost = m.S[i, k]
            for kind, side in (("gercek", real), ("yazitura", int(RNG.choice([-1, 1])))):
                base_stop = rng_l if real > 0 else rng_h
                r0 = abs(e - base_stop)
                if r0 <= 2 * cost:
                    continue
                tgt = e + side * TGT_R * r0
                prot = flo if side > 0 else fhi
                stops = {"taban": e - side * r0, "genis": e - side * 1.5 * r0, "dar": e - side * 0.5 * r0,
                         "korunan": prot if np.isfinite(prot) and (e - prot) * side > cost else np.nan}
                for sn, st in stops.items():
                    if not np.isfinite(st):
                        continue
                    r, how, regret = run_trade(h, l, c, e, side, st, tgt, k, cost, r0)
                    rows.append(dict(i=i, start=sname, tur=kind, stop=sn, R=r, sonuc=how, pisman=regret,
                                     stop_mesafe=abs(e - st) / r0, dow=DOW_NAMES[m.dow[i]], K=bool(m.kesif[i])))
    return pd.DataFrame(rows)


def summarize(t: pd.DataFrame) -> pd.DataFrame:
    def f(g):
        st = g[g.sonuc == "stop"]
        return pd.Series(dict(n=len(g), ortR=g.R.mean(), tR=g.R.mean() / g.R.std(ddof=1) * np.sqrt(len(g)),
                              hedef=(g.sonuc == "hedef").mean(), stop=(g.sonuc == "stop").mean(),
                              pisman_stoplarin=st.pisman.mean() if len(st) else np.nan,
                              stop_mesafe_med=g.stop_mesafe.median()))
    return t.groupby(["tur", "start", "stop", "K"]).apply(f).round(3)


def main() -> None:
    m = load_mat()
    t = trades(m)
    t.to_parquet(OUT / "f3_islemler.parquet")
    s = summarize(t)
    s.to_csv(OUT / "f3_ozet.csv")
    dow = t[t.tur == "gercek"].groupby(["start", "stop", "dow", "K"]).R.agg(["count", "mean"]).round(3)
    dow.to_csv(OUT / "f3_gun.csv")
    print(s.to_string())
    print(dow.unstack("K").to_string())


if __name__ == "__main__":
    main()
