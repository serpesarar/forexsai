"""t_teslim.py — PROTOCOL EK-4: korku rejiminde 1m teslimiyet mumu. Çıktı results/t_teslim.json, t_teslim_trades.parquet"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402
import rules  # noqa: E402
from q_daily import PER, per  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
WICK_K = 0.75                    # EK-4b: sıklıkla seçildi (EK-4 ilk değer 3,0 → 0 olay)


def events(m1, D, vixp) -> list[dict]:
    ctx = rules.caprev_ctx(D, vixp)
    days = D.d.tolist(); nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}
    rng_all = m1.h - m1.l
    a60 = pd.Series(rng_all).rolling(60).mean().shift(1).values
    out = []
    for r in D[D.full].itertuples():
        d, v, c = r.d, vixp.get(r.d), ctx.get(r.d)
        if v is None or v < 18.4 or c is None or d not in nxt or not np.isfinite(r.open930):
            continue
        a, b = int(np.searchsorted(m1.t, lib.utc(d, 600))), int(np.searchsorted(m1.t, lib.utc(d, 901)))
        thr = r.open930 * (1 - c["dvol"])
        kj = tj = None
        for j in range(a, b):
            if m1.c[j] > thr:
                continue
            if kj is None:
                kj = j
            o, h, l, cl = m1.o[j], m1.h[j], m1.l[j], m1.c[j]
            rg = h - l
            lw = min(o, cl) - l
            if rg > 0 and np.isfinite(a60[j]) and lw >= WICK_K * a60[j] and lw / rg >= 0.5 and (cl - l) / rg >= 0.5:
                tj = j
                break
        for name, j in (("T", tj), ("K", kj)):
            if j is None:
                continue
            t_in = int(m1.t[j + 1])
            t0 = lib.time_trade(m1, name + "0", d, t_in, lib.utc(d, 955), +1)
            t1 = lib.time_trade(m1, name + "1", d, t_in, lib.utc(nxt[d], lib.nyse.cash_close_minutes(nxt[d])), +1)
            if t0 and t1:
                out.append({"kol": name, "d": d, "per": per(d), "minute": int(m1.m[j]), "t_in": t_in, "vix": v,
                            "T0": t0.net_bp(), "T0_s15": t0.net_bp(1.5), "T1": t1.net_bp(), "T1_s15": t1.net_bp(1.5),
                            "mae1": t1.mae, "px_in": t1.px_in, "t_out1": t1.t_out})
    return out


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    ev = pd.DataFrame(events(m1, D, vixp))
    ev.to_parquet(OUT / "t_teslim_trades.parquet")
    res = {}
    for h in ("T0", "T1"):
        cell = {}
        for p in PER:
            T, K = ev[(ev.kol == "T") & (ev.per == p)], ev[(ev.kol == "K") & (ev.per == p)]
            mo = pd.to_datetime(T.d).dt.to_period("M").astype(str).values
            cell[p] = {"n_T": len(T), "T": float(T[h].mean()), "T_s15": float(T[h + "_s15"].mean()), "P_T": lib.block_boot_p(T[h].values, mo),
                       "hit_T": float((T[h] > 0).mean()), "n_K": len(K), "K": float(K[h].mean()),
                       "T_med": float(T[h].median()), "T_en_kotu": float(T[h].min())}
        cell["gecti"] = bool(all(cell[p]["T"] > 0 and cell[p]["T"] > cell[p]["K"] and cell[p]["T_s15"] > 0 for p in PER)
                             and cell["TEST"]["P_T"] >= 0.9 and cell["BAGIMSIZ"]["P_T"] >= 0.9)
        res[h] = cell
    T = ev[ev.kol == "T"]
    res["yil_T1"] = {int(y): (len(g), round(float(g.T1.mean()), 1)) for y, g in T.groupby(pd.to_datetime(T.d).dt.year)}
    res["mae1_min"] = float(T.mae1.min())
    (OUT / "t_teslim.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
