"""HK-2 — Değer alanı dışı açılış → VA'ya dönüş → karşı kenar (Dalton/AMT %80 kuralı; PROTOCOL.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, SPREAD, SYMS, load, run_with_placebo, simulate

SESS = {"NDX": ("America/New_York", "09:30", "16:00"), "DAX": ("Europe/Berlin", "09:00", "17:30"),
        "XAU": ("America/New_York", "08:30", "13:30"), "OIL": ("America/New_York", "09:00", "14:30")}
VA_SHARE, BIN_FRAC, MIN_LEFT_MIN = 0.70, 0.02, 60


def sessionize(d: pd.DataFrame, sym: str) -> pd.DataFrame:
    tz, a, b = SESS[sym]
    loc = d.ts.dt.tz_convert(tz)
    mins = loc.dt.hour * 60 + loc.dt.minute
    s0, s1 = (int(x[:2]) * 60 + int(x[3:]) for x in (a, b))
    ins = (mins >= s0) & (mins + 30 <= s1) & (loc.dt.dayofweek < 5)
    d = d.copy()
    d["sess"] = np.where(ins, loc.dt.date.astype(str), None)
    d["left_min"] = s1 - (mins + 30)                      # bar kapanışından seans sonuna dakika
    d["ny_hour"] = d.ts.dt.tz_convert("America/New_York").dt.hour
    last = d[ins].groupby("sess").apply(lambda g: g.index.max())
    d["sess_last"] = d.sess.map(last).fillna(-1).astype(int)
    return d


def value_area(g: pd.DataFrame) -> tuple[float, float] | None:
    lo, hi = g.low.min(), g.high.max()
    if not np.isfinite(lo) or hi <= lo or len(g) < 6:
        return None
    step = (hi - lo) * BIN_FRAC
    edges = lo + step * np.arange(int(np.ceil((hi - lo) / step)) + 1)
    cnt = np.zeros(len(edges))
    for l, h in zip(g.low.values, g.high.values):
        cnt[(edges >= l - 1e-12) & (edges <= h + 1e-12)] += 1
    poc = int(np.argmax(cnt))
    a = b = poc
    tot, acc = cnt.sum(), cnt[poc]
    while acc < VA_SHARE * tot:
        up = cnt[b + 1] if b + 1 < len(cnt) else -1
        dn = cnt[a - 1] if a - 1 >= 0 else -1
        if up >= dn:
            b += 1
            acc += up
        else:
            a -= 1
            acc += dn
    return edges[a], edges[b]


def signals(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sess = [s for s in pd.unique(d.sess.dropna())]
    groups = {s: g for s, g in d[d.sess.notna()].groupby("sess")}
    for prev, cur in zip(sess[:-1], sess[1:]):
        va = value_area(groups[prev])
        g = groups[cur]
        if va is None or len(g) < 4:
            continue
        val, vah = va
        op = g.open.iloc[0]
        if val <= op <= vah:
            continue
        direction = 1 if op < val else -1
        ext = g.high.iloc[0] if direction < 0 else g.low.iloc[0]
        inside = ((g.close >= val) & (g.close <= vah)).values
        for k in range(1, len(g)):
            ext = max(ext, g.high.iloc[k]) if direction < 0 else min(ext, g.low.iloc[k])
            if inside[k] and inside[k - 1]:
                if g.left_min.iloc[k] >= MIN_LEFT_MIN:
                    rows.append(dict(i=int(g.index[k]), dir=direction, tp_px=vah if direction > 0 else val, ext=ext))
                break
    return pd.DataFrame(rows)


def maker(d: pd.DataFrame, sym: str, sig: pd.DataFrame):
    a, sp, o, last, left = d.atr.values, SPREAD[sym], d.open.values, d.sess_last.values, d.left_min.values
    par = sig.set_index("i")
    cur = {}

    def mk(i: int, direction: int, ref):
        if ref is None:
            p = par.loc[i]
            px = o[i + 1]
            sl = max((p.ext + 0.1 * a[i] * -direction - px) * -direction, 0.5 * a[i])
            tp = (p.tp_px - px) * direction
            if tp <= 0:
                return None
            cur.update(sl_atr=sl / a[i], tp_atr=tp / a[i])
            return simulate(d, i, direction, sl, tp, 100, sp, exit_at=int(last[i]))
        if last[i] < i + 1 or left[i] < MIN_LEFT_MIN:      # plasebo havuzu: yalnız ≥60 dk kalan seans barları
            return None
        return simulate(d, i, direction, cur["sl_atr"] * a[i], cur["tp_atr"] * a[i], 100, sp, exit_at=int(last[i]))
    return mk


def main() -> None:
    allt = []
    for sym in SYMS:
        d = sessionize(load(sym, "30m"), sym)
        sig = signals(d)
        t = run_with_placebo(d, sig, sym, maker(d, sym, sig), pool_key=("year", "ny_hour"))
        t["tf"], t["exit"] = "30m", "VA"
        allt.append(t)
        print(sym, len(sig), len(t), round(t.r.mean(), 3), round(t.d.mean(), 3), "tp oranı", round((t.hit == "tp").mean(), 3),
              flush=True)
    pd.concat(allt).to_parquet(OUT / "hk2_trades.parquet")


if __name__ == "__main__":
    main()
