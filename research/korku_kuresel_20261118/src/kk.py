"""kk.py — K1/K3 korku gecesinin ABD dışı endekslere taşınması (PROTOCOL). python kk.py"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fitil_gece_20261118/src"))
import gece as G  # noqa: E402

RES = ROOT / "research/korku_kuresel_20261118/results"
FIBO = ROOT / "research/fibo_altin_bolge_20261116/cache"
OWN = ROOT / "research/korku_kuresel_20261118/cache"
IDX = {"DAX": ("Europe/Berlin", 540, 1050, FIBO), "CAC": ("Europe/Paris", 540, 1050, FIBO), "STOXX": ("Europe/Berlin", 540, 1050, FIBO),
       "UK100": ("Europe/London", 480, 990, OWN), "JPN225": ("Asia/Tokyo", 540, 900, OWN)}
FIN = G.lib.FIN_BP_PER_DAY
ESKI_END = date(2021, 10, 31)


def load(sym: str, src: Path) -> pd.DataFrame:
    x = pd.read_parquet(src / f"{sym}_1m_raw.parquet").sort_values("t").drop_duplicates("t")
    a = x.dropna(subset=["ask_open"])
    spr = float(np.median(a.ask_open - a.open)) if len(a) > 100 else np.nan
    return pd.DataFrame({"t": x.t.values.astype(np.int64), "o": x.open.values, "h": x.high.values, "l": x.low.values,
                         "c": x.close.values, "sp": np.full(len(x), spr)}), spr


def nights(d: pd.DataFrame, tz: str, op: int, cl: int) -> pd.DataFrame:
    dp = G.day_prices(d, tz, [cl - 60, cl], 60)
    x = G._local(d, tz)
    r = x[(x.mn >= op) & (x.mn < cl)]
    tw = r.groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and np.isfinite(dp.loc[z, f"o{cl}"])]
    rows = []
    for i in range(len(days) - 1):
        a, b = days[i], days[i + 1]
        pc, p60, s = dp.loc[a, f"o{cl}"], dp.loc[a, f"o{cl - 60}"], dp.loc[a, f"s{cl}"]
        px = dp.loc[b, f"o{cl}"]
        pin = pc + s
        net = (px / pin - 1) * 1e4 - FIN * (b - a).days
        rows.append({"d": a, "twap": tw.get(a, np.nan), "pc": pc, "p60": p60, "net": net,
                     "n15": net - 0.5 * (s + dp.loc[b, f"s{cl}"]) / pin * 1e4})
    n = pd.DataFrame(rows)
    n["K1"] = ((n.pc / n.twap - 1) <= -0.005) & (n.pc < n.p60)
    n["K3"] = (n.pc / n.p60 - 1) <= -0.003
    n["era"] = np.where(n.d <= ESKI_END, "ESKI", "YENI")
    return n


def summ(n: pd.DataFrame, k: str) -> dict:
    m = n[k].values & np.isfinite(n.net.values)
    b = ~n[k].values & np.isfinite(n.net.values)
    out = {"n": int(m.sum()), "tetik": round(float(n.net[m].mean()), 1), "taban": round(float(n.net[b].mean()), 1),
           "s15": round(float(n.n15[m].mean()), 1), "isabet": round(float((n.net[m] > 0).mean()), 3), "en_kotu": round(float(n.net[m].min()), 1),
           "P": round(G.KS.diff_p(n.net[m].values, n.d[m].astype(str).values, n.net[b].values, n.d[b].astype(str).values), 4)}
    for e in ("ESKI", "YENI"):
        me, be = m & (n.era == e).values, b & (n.era == e).values
        out[e] = {"n": int(me.sum()), "tetik": round(float(n.net[me].mean()), 1), "taban": round(float(n.net[be].mean()), 1)}
    out["yillar"] = {int(y): round(float(v), 1) for y, v in n[m].groupby(pd.to_datetime(n.d[m]).dt.year).net.mean().items()}
    out["tasindi"] = bool(out["n"] >= 30 and out["P"] >= 0.90 and all(out[e]["tetik"] > 0 and out[e]["tetik"] > out[e]["taban"] for e in ("ESKI", "YENI")))
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    res, pool = {}, {k: [] for k in ("K1", "K3")}
    for sym, (tz, op, cl, src) in IDX.items():
        if not (src / f"{sym}_1m_raw.parquet").exists():
            print(sym, "veri yok")
            continue
        d, spr = load(sym, src)
        n = nights(d, tz, op, cl)
        res[sym] = {"spread": spr, "gun": int(len(n)), "aralik": [str(n.d.min()), str(n.d.max())]}
        for k in ("K1", "K3"):
            res[sym][k] = summ(n, k)
            pool[k].append(n.assign(sym=sym)[[k, "net", "d", "sym"]].rename(columns={k: "m"}))
            r = res[sym][k]
            print(f"{sym} {k}: n {r['n']} tetik {r['tetik']:+.1f} taban {r['taban']:+.1f} P {r['P']:.3f} | ESKİ {r['ESKI']['tetik']:+.1f}/{r['ESKI']['taban']:+.1f} "
                  f"YENİ {r['YENI']['tetik']:+.1f}/{r['YENI']['taban']:+.1f} | s15 {r['s15']:+.1f} | taşındı {r['tasindi']} | yıllar {r['yillar']}", flush=True)
    oz = {}
    for k, fr in pool.items():
        p = pd.concat(fr).dropna(subset=["net"])
        a, b = p[p.m], p[~p.m]
        P = G.KS.diff_p(a.net.values, a.d.astype(str).values, b.net.values, b.d.astype(str).values)
        nt = sum(res[s][k]["tasindi"] for s in res)
        hk = "B" if nt >= 3 and P >= 0.95 else ("C" if nt >= 1 else "X (ABD'ye özgü)")
        oz[k] = {"endeks": len(fr), "tasinan": int(nt), "havuz_tetik": round(float(a.net.mean()), 1), "havuz_taban": round(float(b.net.mean()), 1),
                 "havuz_P": round(float(P), 4), "hukum": hk}
        print(k, oz[k])
    res["ozet"] = oz
    (RES / "kuresel.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
