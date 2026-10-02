"""W7: açılış alımı vs dip kırılımı vs birleşik — NDX (1h/30m/15m) ve DAX (1h/30m)."""
import json, numpy as np, pandas as pd
from common import OUT
from round4 import build, events as ev_ndx, exits as ex_ndx, stat as st_ndx
from long_data import load_long
import cross_market as cm

def open_events(d, open_m, stress_fn, wd_max=3):
    st = (d.r1 <= -.015) | (d.r5 <= -.04)
    m = (d.m == open_m) & st & (d.vix >= 18.4) & (d.wd <= wd_max) & d.dvol.notna()
    e = d[m].groupby("nyd").head(1).copy()
    e["ei"] = e.index           # açılış barının AÇILIŞINDA al (karar: önceki gün bilgisi)
    return e

res = {}
for tf, step in [("1h", 60), ("30m", 30), ("15m", 15)]:
    d = build(load_long(tf), step, 540 if step == 60 else 570)
    om = 540 if step == 60 else 570          # 1h: 09:00 barı (09:30'a en yakın)
    A = ex_ndx(d, open_events(d, om, None))
    B = ex_ndx(d, ev_ndx(d, "stress", "hi"))
    r = {}
    for col in ["d0_16", "d1_16"]:
        r[f"(a) açılış BUY {col}"] = st_ndx(A[col], A.nyd)
        r[f"(b) dip kırılımı {col}"] = st_ndx(B[col], B.nyd)
        # (c) birleşik: gün başına toplam R (açılış birimi + varsa kırılım birimi)
        c = A.set_index("nyd")[col].add(B.set_index("nyd")[col], fill_value=0)
        cc = c.reset_index(); cc.columns = ["nyd", col]
        r[f"(c) birleşik gün-toplamı {col}"] = st_ndx(cc[col], cc.nyd)
    r["olay günü: açılış / kırılım / ikisi"] = (int(A.nyd.nunique()), int(B.nyd.nunique()), int(len(set(A.nyd) & set(B.nyd))))
    res[f"NDX {tf}"] = r
for tf in ["1h", "30m"]:
    d = cm.build_dax(tf)
    st = (d.r1 <= -.015) | (d.r5 <= -.04)
    e = d[(d.m == 540) & st & (d.vix >= 18.4) & (d.wd <= 3) & d.dvol.notna()].groupby("nyd").head(1).copy()
    e["ei"] = e.index
    A = cm.exits(d, e); B = cm.exits(d, cm.events(d, "stress", "hi"))
    r = {}
    for col in ["d0", "d1"]:
        r[f"(a) açılış BUY {col}"] = cm.stat(A, col)
        r[f"(b) dip kırılımı {col}"] = cm.stat(B, col)
        c = A.set_index("nyd")[col].add(B.set_index("nyd")[col], fill_value=0).reset_index()
        c.columns = ["nyd", col]; c["year"] = c.nyd.dt.year
        r[f"(c) birleşik {col}"] = cm.stat(c, col)
    res[f"DAX {tf}"] = r
(OUT / "w7.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
for k, r in res.items():
    print(f"\n===== {k} =====")
    for kk, v in r.items(): print(f"  {kk}: {v}")
