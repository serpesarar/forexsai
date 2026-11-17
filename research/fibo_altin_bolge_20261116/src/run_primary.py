"""run_primary.py — PROTOCOL §2 birincil 12 hücre + §3 kontroller K1–K4 + §4 kırılımlar (NDX)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import fblib as F

PRIM = dict(pattern="eng", zone="altin", smin=4.0, spmin=0.5, sl="L", tp="H", hold=100)


def run_cell(cand, bars, p, pattern, zone, smin, spmin, sl, tp, hold):
    s = F.signals(cand, pattern, zone, smin, spmin)
    return F.resolve(F.setup_trades(s, bars, p, sl, tp, hold, zone), p)


def per_period(tr, col="R"):
    out = {"TUM": F.summarize(tr, col, boot=True)}
    for per in ["KESIF", "TEST", "KOR"]:
        out[per] = F.summarize(tr[tr.period == per], col, boot=True)
    return out


def main() -> None:
    p = F.load_main()
    rows, breaks, trades_all = [], [], []
    holm = []
    for tf, (m, a) in F.TFS_NDX.items():
        bars = F.build_bars(p, m, a, tf)
        for side in (1, -1):
            cand = F.detect(bars, side)
            lab = f"{tf}|{'UZUN' if side > 0 else 'KISA'}"
            tr = run_cell(cand, bars, p, **PRIM)
            tr = tr.assign(tf=tf)
            trades_all.append(tr)
            res = {"hucre": lab, "birincil": per_period(tr)}
            res["birincil_spread15"] = F.summarize(tr, "R15")
            res["tek_pozisyon"] = F.summarize(F.single_position(tr), boot=True)
            if len(tr) >= 5:
                top5 = tr.drop(tr.R.nlargest(5).index)
                res["en_iyi5_haric"] = F.summarize(top5)
            # K1 yanlış bantlar
            for z in ["cok_sig", "sig382", "derin"]:
                res[f"K1_{z}"] = F.summarize(run_cell(cand, bars, p, "eng", z, 4.0, 0.5, "L", "H", 100), boot=True)
            # K2 teyitsiz, K3 itkisiz
            res["K2_teyitsiz"] = F.summarize(run_cell(cand, bars, p, "none", "altin", 4.0, 0.5, "L", "H", 100), boot=True)
            res["K3_itkisiz"] = F.summarize(run_cell(cand, bars, p, "eng", "altin", 1.5, 0.0, "L", "H", 100), boot=True)
            # K4 zaman plasebosu
            if len(tr):
                pl = F.placebo(tr, bars, p, 100, draws=5)
                res["K4_plasebo"] = F.summarize(pl)
                res["K4_fark"] = round(float(tr.R.mean() - pl.R.mean()), 4)
            mu, t, g = F.day_stats(tr.R.values, tr.date.values) if len(tr) > 1 else (np.nan, np.nan, 0)
            holm.append((lab, t))
            rows.append(res)
            for key in ["session", "hour", "dow", "year"]:
                if tr.empty:
                    continue
                for v, g_ in tr.groupby(key):
                    sm = F.summarize(g_)
                    breaks.append({"hucre": lab, "boyut": key, "deger": v, **sm,
                                   "KESIF": F.summarize(g_[g_.period == "KESIF"]).get("ortR"),
                                   "TEST": F.summarize(g_[g_.period == "TEST"]).get("ortR"),
                                   "KOR": F.summarize(g_[g_.period == "KOR"]).get("ortR")})
            print(lab, res["birincil"]["TUM"], "| K4 fark", res.get("K4_fark"), flush=True)
    # Holm (tek yönlü, t > 0 iddiası; normal yaklaşım)
    from math import erf, sqrt
    ps = [(lab, 0.5 * (1 - erf((t if t == t else -9) / sqrt(2)))) for lab, t in holm]
    ps.sort(key=lambda x: x[1])
    m = len(ps)
    holm_out = [{"hucre": lab, "p": round(pv, 4), "holm_esik": round(0.05 / (m - i), 4), "gecti": pv < 0.05 / (m - i)}
                for i, (lab, pv) in enumerate(ps)]
    F.RESULTS.mkdir(parents=True, exist_ok=True)
    (F.RESULTS / "birincil.json").write_text(json.dumps({"hucreler": rows, "holm": holm_out}, indent=1, default=str))
    pd.DataFrame(breaks).to_csv(F.RESULTS / "birincil_kirilim.csv", index=False)
    pd.concat(trades_all).to_parquet(F.RESULTS / "birincil_islemler.parquet")


if __name__ == "__main__":
    main()
