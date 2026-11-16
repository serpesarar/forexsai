"""q_shape.py — PROTOCOL EK-3: 1m gerçekleşen çarpıklık / sıçrama payı → ertesi gün / hafta. Çıktı results/q_shape.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402
from q_daily import PER, per  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"


def ols_t(df, f, y, ctrls):
    cols = [f] + ctrls
    X = np.c_[np.ones(len(df)), *[(df[k] - df[k].mean()) / df[k].std() for k in cols]]
    b, *_ = np.linalg.lstsq(X, df[y].values, rcond=None)
    res = df[y].values - X @ b
    se = np.sqrt(np.diag(res @ res / (len(df) - X.shape[1]) * np.linalg.inv(X.T @ X)))
    return float(b[1]), float(b[1] / se[1])


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1)
    full = D[D.full].reset_index(drop=True)
    days = D.d.tolist(); ix = {d: i for i, d in enumerate(days)}
    rows = []
    for r in full.itertuples():
        a, b = int(np.searchsorted(m1.t, lib.utc(r.d, 570))), int(np.searchsorted(m1.t, lib.utc(r.d, 960)))
        c = m1.c[a:b]
        if len(c) < 300:
            continue
        lr = np.diff(np.log(c))
        rv = (lr ** 2).sum()
        bv = np.pi / 2 * (np.abs(lr[1:]) * np.abs(lr[:-1])).sum()
        i = ix[r.d]
        if i + 5 >= len(days):
            continue
        g = lib.time_trade(m1, "G", r.d, lib.utc(r.d, 960), lib.utc(days[i + 1], lib.nyse.cash_close_minutes(days[i + 1])), +1)
        w = lib.time_trade(m1, "W", r.d, lib.utc(r.d, 960), lib.utc(days[i + 5], lib.nyse.cash_close_minutes(days[i + 5])), +1)
        if g is None or w is None:
            continue
        rows.append({"d": r.d, "per": per(r.d), "RSK": np.sqrt(len(lr)) * (lr ** 3).sum() / rv ** 1.5, "JMP": max(0.0, 1 - bv / rv),
                     "lRV": np.log(rv), "r_gun": c[-1] / m1.o[a] - 1, "close": r.close,
                     "IBS": (c[-1] - m1.l[a:b].min()) / max(1e-9, m1.h[a:b].max() - m1.l[a:b].min()),
                     "gun": g.net_bp(), "hafta": w.net_bp(), "t_in": g.t_in, "t_w": w.t_out})
    q = pd.DataFrame(rows).sort_values("d").reset_index(drop=True)
    q["RSK5"] = q.RSK.rolling(5).mean()
    q["r5"] = q.close / q.close.shift(5) - 1
    q = q.dropna().reset_index(drop=True)
    ctrls = ["r_gun", "r5", "IBS", "lRV"]
    out = {}
    for f, low_good in (("RSK5", True), ("RSK", True), ("JMP", None)):
        e = list(q[q.per == "KESIF"][f].quantile([1 / 3, 2 / 3]))
        out[f] = {"esik": e}
        for y in ("gun", "hafta"):
            cell = {}
            for p in PER:
                g = q[q.per == p]
                lo, hi = g[g[f] <= e[0]], g[g[f] > e[1]]
                sig = lo if low_good in (True, None) else hi
                oth = hi if sig is lo else lo
                mo = pd.to_datetime(sig.d).dt.to_period("M").astype(str).values
                b, t = ols_t(g, f, y, ctrls)
                cell[p] = {"n": len(sig), "sinyal": float(sig[y].mean()), "karsi": float(oth[y].mean()), "tum": float(g[y].mean()),
                           "P": lib.block_boot_p(sig[y].values, mo), "ols_b": b, "ols_t": t}
            bs = [cell[p]["ols_b"] for p in PER]
            cell["havuz_t"] = ols_t(q, f, y, ctrls)[1]
            cell["gecti"] = bool(all(cell[p]["sinyal"] > 0 for p in PER) and cell["TEST"]["P"] >= 0.9 and cell["BAGIMSIZ"]["P"] >= 0.9
                                 and all(cell[p]["sinyal"] > cell[p]["karsi"] for p in PER)
                                 and (all(x > 0 for x in bs) or all(x < 0 for x in bs)) and abs(cell["havuz_t"]) >= 2)
            out[f][y] = cell
    # Kural: RSK5 alt tertil → hafta, örtüşmesiz
    e = out["RSK5"]["esik"]
    sel, busy = [], 0
    for r in q.itertuples():
        if r.RSK5 <= e[0] and r.t_in >= busy:
            sel.append(r); busy = r.t_w
    s = pd.DataFrame(sel)
    out["kural_RSK5_hafta_ortusmesiz"] = {p: {"n": int((s.per == p).sum()), "bp": float(s[s.per == p].hafta.mean())} for p in PER}
    q.to_parquet(OUT / "q_shape.parquet")
    (OUT / "q_shape.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for f in ("RSK5", "RSK", "JMP"):
        for y in ("gun", "hafta"):
            c = out[f][y]
            print(f, y, {p: (c[p]["n"], round(c[p]["sinyal"], 1), round(c[p]["karsi"], 1), round(c[p]["tum"], 1), round(c[p]["P"], 2), round(c[p]["ols_t"], 2)) for p in PER},
                  "havuz_t", round(c["havuz_t"], 2), "GEÇTİ", c["gecti"])
    print(out["kural_RSK5_hafta_ortusmesiz"])


if __name__ == "__main__":
    main()
