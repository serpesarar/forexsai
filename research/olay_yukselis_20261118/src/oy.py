"""oy.py — olay günü yükselişi devam (PROTOCOL). python oy.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/habersiz_gunici_20261118/src", "research/fitil_kesisim_20261118/src", "research/ndx_seri_opex_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import hg  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402
import ksg_ek2 as E  # noqa: E402
import ek1 as NDX  # noqa: E402

G = hg.G
RES = ROOT / "research/olay_yukselis_20261118/results"
P_B = 1 - 0.05 / 6


def tab_up(b: pd.DataFrame, step: int, ev: set) -> pd.DataFrame:
    """hg.table'ın yükseliş aynası: ilk 30 dk bar ≥ +e."""
    x = G._local(b, "America/New_York")
    x = x[x.day <= hg.END]
    dp = G.day_prices(b, "America/New_York", [960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"]) and z <= hg.END]
    nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}
    t, o, sp = b.t.values, b.o.values, b.sp.values
    rng = np.random.default_rng(17)
    rows = []
    for d, g in x[(x.mn >= 570) & (x.mn < 930)].groupby("day"):
        if d not in nxt:
            continue
        key = (g.mn.values - 570) // 30
        st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        en = np.r_[st[1:], len(key)] - 1
        ret = g.c.values[en] / g.o.values[st] - 1
        tend = g.t.values[en] + step
        full = key[st] >= 1
        cand = np.flatnonzero(full)
        if cand.size == 0:
            continue
        picks = [("rnd", int(rng.choice(cand)))]
        for e in hg.ES:
            hit = np.flatnonzero(full & (ret >= e))
            picks.append((f"e{e}", int(hit[0]) if hit.size else None))
        for tag, j in picks:
            if j is None:
                continue
            i = int(np.searchsorted(t, tend[j]))
            if i >= len(t) or t[i] - tend[j] > 600:
                continue
            pin = o[i] + sp[i]
            rows.append({"d": d, "tag": tag, "olay": d in ev, "x16": (dp.loc[d, "o960"] / pin - 1) * 1e4,
                         "xn16": (dp.loc[nxt[d], "o960"] / pin - 1) * 1e4 - hg.kk.FIN * (nxt[d] - d).days})
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= hg.kk.ESKI_END, "ESKI", "YENI")
    return df


def main() -> None:
    RES.mkdir(exist_ok=True)
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    F = {"NDX_DUKA": (G.ndx_bars(), 60), "MT5": (KD.mt5_m30("NAS100"), 1800), "NQ": E.bars("NQ")}
    T = {k: tab_up(b, s, ev) for k, (b, s) in F.items()}
    out = {}
    for e in hg.ES:
        for col in ("x16", "xn16"):
            rec = {}
            for nm, df in T.items():
                for grp, gm in (("olay", df.olay), ("habersiz", ~df.olay)):
                    a, z = df[gm & (df.tag == f"e{e}")], df[gm & (df.tag == "rnd")]
                    rr = {er: {"n": int((a.era == er).sum()), "ort": round(float(a[a.era == er][col].mean()), 1),
                               "taban": round(float(z[z.era == er][col].mean()), 1)} for er in ("ESKI", "YENI")}
                    rr["TUM"] = {"n": int(len(a)), "ort": round(float(a[col].mean()), 1), "taban": round(float(z[col].mean()), 1)}
                    if grp == "olay" and nm == "NDX_DUKA":
                        rr["TUM"]["P"] = round(G.KS.diff_p(a[col].values, a.d.astype(str).values, z[col].values, z.d.astype(str).values), 4)
                    rec[f"{nm}_{grp}"] = rr
            N = rec["NDX_DUKA_olay"]
            ok1 = all(N[er]["ort"] > 0 and N[er]["ort"] > N[er]["taban"] for er in ("ESKI", "YENI"))
            ok2 = all(rec[f"{f}_olay"]["TUM"]["ort"] > rec[f"{f}_olay"]["TUM"]["taban"] for f in ("MT5", "NQ"))
            rec["hukum"] = "B" if ok1 and ok2 and N["TUM"]["P"] >= P_B else ("C+" if ok1 and ok2 else "X")
            out[f"G_e{e}_{col}"] = rec
            print(f"gün içi e{e} {col}: {rec['hukum']} | NDX olay {N} | habersiz {rec['NDX_DUKA_habersiz']['TUM']} | MT5 {rec['MT5_olay']['TUM']} | NQ {rec['NQ_olay']['TUM']}", flush=True)
    x = NDX.ndx()
    x = x[(x.index >= "2007-10-01") & (x.index <= "2026-10-02")].copy()
    x["r"] = x.c.pct_change()
    x["sig"] = x.r.shift(1).rolling(20).std()
    days = x.index.to_series()
    x["f1"] = (x.c.shift(-1) / x.c - 1) * 1e4 - 2 - NDX.lib.FIN_BP_PER_DAY * (days.shift(-1) - days).dt.days.values
    x["olay"] = [d.date() in ev for d in x.index]
    x = x[x.index >= "2008-01-01"].dropna(subset=["f1", "sig"])
    for k in (1.0, 1.5):
        m = (x.r >= k * x.sig).values
        rec = {}
        for nm, a, b in (("08-15", "2008-01-01", "2015-12-31"), ("16-21", "2016-01-01", "2021-12-31"), ("22-26", "2022-01-01", "2026-12-31")):
            s = (x.index >= a) & (x.index <= b)
            o = x.olay.values
            rec[nm] = {"n": int((m & o & s).sum()), "ort": round(float(x.f1[m & o & s].mean()), 1), "taban": round(float(x.f1[o & s].mean()), 1),
                       "habersiz": round(float(x.f1[m & ~o & s].mean()), 1)}
        o = x.olay.values
        a, z = x.f1.values[m & o], x.f1.values[o]
        r = np.random.default_rng(4)
        P = float((r.choice(a, (8000, len(a))).mean(1) - r.choice(z, (8000, len(z))).mean(1) > 0).mean())
        ok = all(rec[nm]["ort"] > 0 and rec[nm]["ort"] > rec[nm]["taban"] for nm in rec)
        rec["P"] = round(P, 4)
        rec["hukum"] = "B" if ok and P >= P_B else ("C+" if ok else "X")
        out[f"D_k{k}"] = rec
        print(f"günlük k{k}:", json.dumps(rec, ensure_ascii=False), flush=True)
    (RES / "olay_yukselis.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
