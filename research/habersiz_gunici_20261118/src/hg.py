"""hg.py — habersiz gün içi sert düşüş → dönüş (PROTOCOL). python hg.py"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/korku_kuresel_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import kk  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402

G = kk.G
RES = ROOT / "research/habersiz_gunici_20261118/results"
NY = "America/New_York"
END = date(2026, 10, 2)
ES = (0.006, 0.010)
P_B = 1 - 0.05 / 4


def table(b: pd.DataFrame, step: int, ev: set) -> pd.DataFrame:
    x = G._local(b, NY)
    x = x[x.day <= END]
    dp = G.day_prices(b, NY, [960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and np.isfinite(dp.loc[z, "o960"]) and z <= END]
    nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}
    t, o, sp = b.t.values, b.o.values, b.sp.values
    rows = []
    rng = np.random.default_rng(11)
    for d, g in x[(x.mn >= 570) & (x.mn < 930)].groupby("day"):
        if d not in nxt:
            continue
        key = (g.mn.values - 570) // 30
        st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        en = np.r_[st[1:], len(key)] - 1
        op, cl, kk_ = g.o.values[st], g.c.values[en], key[st]
        ret = cl / op - 1
        tend = g.t.values[en] + step
        full = (kk_ >= 1)
        cand = np.flatnonzero(full)
        if cand.size == 0:
            continue
        r = rng.choice(cand)
        picks = [("rnd", r)]
        for e in ES:
            hit = np.flatnonzero(full & (ret <= -e))
            picks.append((f"e{e}", int(hit[0]) if hit.size else None))
        for tag, j in picks:
            if j is None:
                continue
            i = int(np.searchsorted(t, tend[j]))
            if i >= len(t) or t[i] - tend[j] > 600:
                continue
            pin = o[i] + sp[i]
            rows.append({"d": d, "tag": tag, "olay": d in ev, "x16": (dp.loc[d, "o960"] / pin - 1) * 1e4,
                         "xn16": (dp.loc[nxt[d], "o960"] / pin - 1) * 1e4 - kk.FIN * (nxt[d] - d).days})
    df = pd.DataFrame(rows)
    df["era"] = np.where(df.d <= kk.ESKI_END, "ESKI", "YENI")
    return df


def main() -> None:
    RES.mkdir(exist_ok=True)
    c = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(c.date).dt.date)
    T = {"NDX_DUKA": table(G.ndx_bars(), 60, ev), "US30": table(KD.mt5_m30("US30"), 1800, ev), "US2000": table(KD.mt5_m30("US2000"), 1800, ev)}
    out = {}
    rng = np.random.default_rng(2)
    for e in ES:
        for col in ("x16", "xn16"):
            rec = {}
            for nm, df in T.items():
                for grp, gm in (("habersiz", ~df.olay), ("olay", df.olay)):
                    a, b = df[gm & (df.tag == f"e{e}")], df[gm & (df.tag == "rnd")]
                    rr = {er: {"n": int((a.era == er).sum()), "ort": round(float(a[a.era == er][col].mean()), 1),
                               "taban": round(float(b[b.era == er][col].mean()), 1)} for er in ("ESKI", "YENI")}
                    rr["TUM"] = {"n": int(len(a)), "ort": round(float(a[col].mean()), 1), "taban": round(float(b[col].mean()), 1)}
                    if nm == "NDX_DUKA" and grp == "habersiz":
                        v, w = a[col].values, b[col].values
                        rr["P"] = round(float((rng.choice(v, (5000, len(v))).mean(1) - rng.choice(w, (5000, len(w))).mean(1) > 0).mean()), 4)
                    rec[f"{nm}_{grp}"] = rr
            H = rec["NDX_DUKA_habersiz"]
            ok1 = all(H[er]["ort"] > 0 and H[er]["ort"] > H[er]["taban"] for er in ("ESKI", "YENI"))
            ok2 = all(rec[f"{s}_habersiz"]["TUM"]["ort"] > rec[f"{s}_habersiz"]["TUM"]["taban"] for s in ("US30", "US2000"))
            rec["hukum"] = "B" if ok1 and ok2 and H["P"] >= P_B else ("C+" if ok1 and ok2 else ("C" if ok1 else "X"))
            out[f"e{e}_{col}"] = rec
            print(f"e{e} {col}: {rec['hukum']} | NDX habersiz {H} | olay {rec['NDX_DUKA_olay']['TUM']} | US30 {rec['US30_habersiz']['TUM']} | US2000 {rec['US2000_habersiz']['TUM']}", flush=True)
    (RES / "habersiz_gunici.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
