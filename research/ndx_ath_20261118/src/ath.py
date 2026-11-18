"""ath.py — NASDAQ ATH dinamiği (PROTOCOL). python ath.py gunluk | gunici"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/ndx_10y_1m_20261116/src", "research/korku_kuresel_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import lib  # noqa: E402
import kk  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402
import ksg_ek2 as E  # noqa: E402

G = kk.G
D = ROOT / "research/qs03_akis_takvim_20261111/data"
RES = ROOT / "research/ndx_ath_20261118/results"
ERAS = (("KESIF", "1990-01-01", "2009-12-31"), ("TEST", "2010-01-01", "2017-12-31"), ("YENI", "2018-01-01", "2026-12-31"))
P_A = 1 - 0.05 / 7
NY = "America/New_York"


def daily(sym: str) -> pd.DataFrame:
    d = pd.read_parquet(D / f"{sym}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    x = pd.DataFrame({"c": d.Close})
    cm = x.c.cummax()
    x["ath"] = x.c >= cm
    x["gap20"] = x.ath.rolling(21).sum().shift(1).fillna(0) == 0
    x["dd250"] = (x.c / cm).rolling(250, min_periods=50).min().shift(1) <= 0.90
    x["athprev"] = x.ath.shift(1).fillna(False).astype(bool)
    days = x.index.to_series()
    for h in (1, 5, 20, 60):
        x[f"f{h}"] = (x.c.shift(-h) / x.c - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (days.shift(-h) - days).dt.days.values
    return x


def bboot(v: np.ndarray, w: np.ndarray, block: int, n: int = 4000) -> float:
    """fark > 0 için blok bootstrap (tetik ve taban ayrı blok örneklemi)."""
    rng = np.random.default_rng(5)

    def bs(a):
        if len(a) <= block:
            return rng.choice(a, (n, len(a))).mean(1)
        k = int(np.ceil(len(a) / block))
        st = rng.integers(0, len(a) - block + 1, (n, k))
        idx = (st[:, :, None] + np.arange(block)).reshape(n, -1)[:, :len(a)]
        return a[idx].mean(1)
    return float((bs(v) - bs(w) > 0).mean())


CELLS = (("A1", "gap20", (1, 5, 20)), ("A2", "dd250", (20, 60)), ("A3", "athprev", (1, 5)))


def gunluk() -> None:
    RES.mkdir(exist_ok=True)
    out = {}
    X = {s: daily(s) for s in ("QQQ", "SPY", "DIA", "IWM")}
    for nm, cond, hs in CELLS:
        for h in hs:
            rec = {}
            q = X["QQQ"]
            col = f"f{h}"
            for e, a, b in ERAS:
                z = q[(q.index >= a) & (q.index <= b)].dropna(subset=[col])
                m = (z.ath & z[cond]).values
                rec[e] = {"n": int(m.sum()), "ort": round(float(z[col][m].mean()), 1), "taban": round(float(z[col].mean()), 1)}
                rec[e]["fark"] = round(rec[e]["ort"] - rec[e]["taban"], 1)
            z = q.dropna(subset=[col])
            m = (z.ath & z[cond]).values
            rec["P_fark_pozitif"] = round(bboot(z[col].values[m], z[col].values, max(h, 1)), 4)
            for s in ("SPY", "DIA", "IWM"):
                y = X[s].dropna(subset=[col])
                mm = (y.ath & y[cond]).values
                rec[s] = {"n": int(mm.sum()), "fark": round(float(y[col][mm].mean() - y[col].mean()), 1)}
            sg = np.sign(np.mean([rec[e]["fark"] for e, _, _ in ERAS]))
            same = all(np.sign(rec[e]["fark"]) == sg for e, _, _ in ERAS)
            kor = sum(np.sign(rec[s]["fark"]) == sg for s in ("SPY", "DIA", "IWM")) >= 2
            pp = rec["P_fark_pozitif"] if sg > 0 else 1 - rec["P_fark_pozitif"]
            rec["hukum"] = ("B" if same and kor and pp >= P_A else ("C+" if same and kor else "X")) + (" (devam)" if sg > 0 else " (dönüş)")
            out[f"{nm}_h{h}"] = rec
            print(nm, h, json.dumps(rec, ensure_ascii=False), flush=True)
    (RES / "gunluk.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


def gunici_tab(b: pd.DataFrame, step: int) -> pd.DataFrame:
    x = G._local(b, NY)
    dp = G.day_prices(b, NY, [960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"])]
    nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}
    t, o, h, sp = b.t.values, b.o.values, b.h.values, b.sp.values
    runmax = np.maximum.accumulate(h)
    rng = np.random.default_rng(21)
    rows = []
    for d, g in x[(x.mn >= 600) & (x.mn < 900)].groupby("day"):
        if d not in nxt:
            continue
        idx = g.index.values
        i0 = idx[0]
        prev = runmax[i0 - 1] if i0 > 0 else np.inf
        near = g.o.values[0] >= prev * 0.99
        hit = np.flatnonzero(h[idx] > prev)
        rr = rng.integers(len(idx))
        picks = [("rnd", idx[rr])]
        if hit.size:
            picks.append(("ath", idx[hit[0]]))
        for tag, j in picks:
            k = j + 1
            if k >= len(t):
                continue
            pin, pbid = o[k] + sp[k], o[k]
            x16, xn = dp.loc[d, "o960"], dp.loc[nxt[d], "o960"]
            fin = kk.FIN * (nxt[d] - d).days
            rows.append({"d": d, "tag": tag, "near": bool(near), "al16": (x16 / pin - 1) * 1e4, "aln16": (xn / pin - 1) * 1e4 - fin,
                         "sat16": -((x16 + sp[k]) / pbid - 1) * 1e4, "satn16": -((xn + sp[k]) / pbid - 1) * 1e4 - fin})
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= kk.ESKI_END, "ESKI", "YENI")
    return df


def gunici() -> None:
    RES.mkdir(exist_ok=True)
    F = {"NDX_DUKA": (G.ndx_bars(), 60), "MT5": (KD.mt5_m30("NAS100"), 1800), "NQ": E.bars("NQ")}
    T = {k: gunici_tab(b, s) for k, (b, s) in F.items()}
    out = {}
    for col in ("al16", "aln16", "sat16", "satn16"):
        rec = {}
        for nm, df in T.items():
            a = df[df.tag == "ath"]
            z = df[(df.tag == "rnd") & df.near]
            rec[nm] = {e: {"n": int((a.era == e).sum()), "ort": round(float(a[a.era == e][col].mean()), 1),
                           "taban_yakin": round(float(z[z.era == e][col].mean()), 1)} for e in ("ESKI", "YENI")}
            rec[nm]["TUM"] = {"n": int(len(a)), "ort": round(float(a[col].mean()), 1), "taban_yakin": round(float(z[col].mean()), 1),
                              "taban_tum": round(float(df[df.tag == "rnd"][col].mean()), 1),
                              "P": round(G.KS.diff_p(a[col].values, a.d.astype(str).values, z[col].values, z.d.astype(str).values), 4)}
        N = rec["NDX_DUKA"]
        ok1 = all(N[e]["ort"] > 0 and N[e]["ort"] > N[e]["taban_yakin"] for e in ("ESKI", "YENI"))
        ok2 = all(rec[f]["TUM"]["ort"] > rec[f]["TUM"]["taban_yakin"] for f in ("MT5", "NQ"))
        rec["hukum"] = "B" if ok1 and ok2 and N["TUM"]["P"] >= 0.9875 else ("C+" if ok1 and ok2 else "X")
        out[col] = rec
        print(col, json.dumps(rec, ensure_ascii=False), flush=True)
    (RES / "gunici.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"gunluk": gunluk, "gunici": gunici}[sys.argv[1]]()
