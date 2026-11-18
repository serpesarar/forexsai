"""od.py — EK-1: ABD olay günü büyük FX hareketi → ertesi gün devam (kör: USD egzotikleri). python od.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fh  # noqa: E402

F = fh.F
KORX = ["USDMXN", "USDNOK", "USDSEK", "USDZAR"]


def table(pair: str, ev: set, meta: dict) -> pd.DataFrame:
    x = F.load(pair, "D1")
    x["d"] = (x.et + pd.Timedelta(hours=7)).dt.normalize()
    x = x[(x.d >= fh.START - pd.Timedelta(days=60)) & (x.d <= fh.END + pd.Timedelta(days=5))].reset_index(drop=True)
    r = x.c.pct_change()
    sig = r.shift(1).rolling(20).std()
    nxt = x.c.shift(-1) / x.c - 1
    m = meta[pair]
    c = fh.cost_bp(pair, m["point"])
    sw_l = m["swap_long"] * m["point"] / x.c * 1e4
    sw_s = m["swap_short"] * m["point"] / x.c * 1e4
    sg = np.sign(r)
    swap = np.where(sg > 0, sw_l, sw_s)
    df = pd.DataFrame({"d": x.d, "r": r, "sig": sig, "dev": sg * nxt * 1e4 - c + swap, "pair": pair})
    df["olay"] = df.d.dt.date.isin(ev)
    return df[(df.d >= fh.START) & (df.d <= fh.END)].dropna()


def main() -> None:
    cal = pd.read_csv(fh.ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    meta = F.meta()
    T = pd.concat([table(p, ev, meta) for p in KORX])
    out = {}
    for k in fh.KS:
        b = T[T.r.abs() >= k * T.sig]
        o, h = b[b.olay], b[~b.olay]
        rec = {"olay": {"n": int(len(o)), "ort": round(float(o.dev.mean()), 2), "P": round(F.boot_p(o.dev.values, o.d.astype(str).values), 4)},
               "habersiz_kontrol": {"n": int(len(h)), "ort": round(float(h.dev.mean()), 2)},
               "cift": {p: [int(len(g)), round(float(g.dev.mean()), 1)] for p, g in o.groupby("pair")},
               "donem": {nm: round(float(o[(o.d >= a) & (o.d <= z)].dev.mean()), 2) for nm, a, z in fh.ERAS}}
        pos = sum(v[1] > 0 for v in rec["cift"].values())
        ok = rec["olay"]["ort"] > 0 and pos >= 3
        rec["hukum"] = "B" if ok and rec["olay"]["P"] >= 0.975 else ("C+" if ok else "X")
        out[f"k{k}"] = rec
        print(k, json.dumps(rec, ensure_ascii=False), flush=True)
    (fh.RES / "olay_devam_kor.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
