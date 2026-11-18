"""bk.py — BTC 16:00 NY korkusu + NDX K1 → BTC (PROTOCOL). python bk.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/korku_genislik_20261118/src"))
import gn  # noqa: E402

G = gn.kk.G
RES = ROOT / "research/btc_korku_20261118/results"
NY = "America/New_York"
COST = 10.0
P_B = 1 - 0.05 / 3


def btc() -> pd.DataFrame:
    a = pd.read_parquet(ROOT / "research/btc_indep_2017_2021/data/btc_5m.parquet")
    b = pd.read_parquet(ROOT / "research/btc_5y_20261021/data/btc_5m.parquet")
    x = pd.concat([a, b]).drop_duplicates("ts").sort_values("ts")
    t = (x.ts.astype("int64") // 10**9).values
    return pd.DataFrame({"t": t, "o": x.open.values, "h": x.high.values, "l": x.low.values, "c": x.close.values, "sp": np.zeros(len(x))})


def table() -> pd.DataFrame:
    b = btc()
    dp = G.day_prices(b, NY, [900, 960], 300)
    x = G._local(b, NY)
    tw = x[(x.mn >= 570) & (x.mn < 960)].groupby("day").c.mean()
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    rows = []
    for i in range(len(days) - 1):
        a, c = days[i], days[i + 1]
        pc, p15 = dp.loc[a, "o960"], dp.loc[a, "o900"]
        rows.append({"d": a, "dev": pc / tw.get(a, np.nan) - 1, "down": pc < p15, "net": (dp.loc[c, "o960"] / pc - 1) * 1e4 - COST})
    t = pd.DataFrame(rows).dropna(subset=["net"])
    t["era"] = np.where(t.d <= gn.kk.ESKI_END, "ESKI", "YENI")
    return t


def cell(t: pd.DataFrame, m: np.ndarray) -> dict:
    rec = {}
    for e in ("ESKI", "YENI", None):
        s = (t.era == e).values if e else np.ones(len(t), bool)
        a, b = t.net[m & s], t.net[~m & s]
        rec[e or "TUM"] = {"n": int(len(a)), "ort": round(float(a.mean()), 1), "taban": round(float(b.mean()), 1), "en_kotu": round(float(a.min()), 1)}
    rec["P"] = round(G.KS.diff_p(t.net[m].values, t.d[m].astype(str).values, t.net[~m].values, t.d[~m].astype(str).values), 4)
    ok = all(rec[e]["ort"] > 0 and rec[e]["ort"] > rec[e]["taban"] for e in ("ESKI", "YENI"))
    rec["hukum"] = "B" if ok and rec["P"] >= P_B else ("C" if ok else "X")
    return rec


def main() -> None:
    RES.mkdir(exist_ok=True)
    t = table()
    out = {}
    for e in (0.005, 0.010):
        out[f"H1_K1btc_{e}"] = cell(t, ((t.dev <= -e) & t.down).values)
    n = gn.nts(G.ndx_bars(), 60)
    k1 = set(n.d[n.K1])
    out["H2_NDX_K1"] = cell(t, t.d.isin(k1).values)
    for k, v in out.items():
        print(k, json.dumps(v, ensure_ascii=False))
    (RES / "btc_korku.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
