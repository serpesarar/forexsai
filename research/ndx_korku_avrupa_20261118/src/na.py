"""na.py — NDX K1 → Avrupa endeksleri ertesi gün (PROTOCOL). python na.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/korku_genislik_20261118/src"))
import gn  # noqa: E402

kk = gn.kk
G = kk.G
RES = ROOT / "research/ndx_korku_avrupa_20261118/results"
EU = {"DAX": ("Europe/Berlin", 1050, kk.FIBO), "CAC": ("Europe/Paris", 1050, kk.FIBO), "STOXX": ("Europe/Berlin", 1050, kk.FIBO),
      "UK100": ("Europe/London", 990, kk.OWN)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    n = gn.nts(G.ndx_bars(), 60)
    out, pool = {}, []
    for sym, (tz, cl, src) in EU.items():
        b, spr = kk.load(sym, src)
        t = b.t.values
        dp = G.day_prices(b, tz, [cl], 60)
        edays = [z for z in dp.index if z.weekday() < 5 and np.isfinite(dp.loc[z, f"o{cl}"])]
        rows = []
        for d, k1 in zip(n.d, n.K1):
            u = int(pd.Timestamp(datetime(d.year, d.month, d.day, 16, 0), tz="America/New_York").timestamp())
            i = int(np.searchsorted(t, u))
            if i >= len(t) or t[i] - u > 18 * 3600:
                continue
            dl = pd.Timestamp(int(t[i]), unit="s", tz="UTC").tz_convert(tz)
            after_close = dl.hour * 60 + dl.minute >= cl
            j = int(np.searchsorted(np.array(edays), dl.date(), side="right" if after_close else "left"))
            if j >= len(edays):
                continue
            ex = edays[j]
            pin = b.o.values[i] + spr
            rows.append({"d": d, "K1": bool(k1), "net": (dp.loc[ex, f"o{cl}"] / pin - 1) * 1e4 - kk.FIN * (ex - d).days})
        x = pd.DataFrame(rows)
        x["era"] = np.where(x.d <= kk.ESKI_END, "ESKI", "YENI")
        rec = {}
        for e in ("ESKI", "YENI", None):
            s = x[x.era == e] if e else x
            rec[e or "TUM"] = {"n": int(s.K1.sum()), "ort": round(float(s.net[s.K1].mean()), 1), "taban": round(float(s.net[~s.K1].mean()), 1)}
        rec["P"] = round(G.KS.diff_p(x.net[x.K1].values, x.d[x.K1].astype(str).values, x.net[~x.K1].values, x.d[~x.K1].astype(str).values), 4)
        rec["gecti"] = all(rec[e]["ort"] > 0 and rec[e]["ort"] > rec[e]["taban"] for e in ("ESKI", "YENI"))
        out[sym] = rec
        pool.append(x)
        print(sym, rec, flush=True)
    p = pd.concat(pool)
    P = G.KS.diff_p(p.net[p.K1].values, p.d[p.K1].astype(str).values, p.net[~p.K1].values, p.d[~p.K1].astype(str).values)
    k = sum(out[s]["gecti"] for s in EU)
    out["ozet"] = {"gecen": int(k), "havuz_P": round(float(P), 4), "hukum": "B" if k >= 3 and P >= 0.95 else ("C" if k >= 2 else "X")}
    print(out["ozet"])
    (RES / "ndx_avrupa.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))




def sabah() -> None:
    """EK-1 (b): NDX K1(d) → Avrupa'nın sonraki işlem günü nakit açılışında AL, aynı gün kapanışta sat."""
    n = gn.nts(G.ndx_bars(), 60)
    k1 = dict(zip(n.d, n.K1))
    out = {}
    for sym, (tz, cl, src) in EU.items():
        op = 480 if sym == "UK100" else 540
        b, spr = kk.load(sym, src)
        dp = G.day_prices(b, tz, [op, cl], 60)
        ed = [z for z in dp.index if z.weekday() < 5 and np.isfinite(dp.loc[z, f"o{cl}"]) and np.isfinite(dp.loc[z, f"o{op}"])]
        rows = []
        for d, f in k1.items():
            j = int(np.searchsorted(np.array(ed), d, side="right"))
            if j >= len(ed):
                continue
            e = ed[j]
            rows.append({"d": d, "K1": f, "net": (dp.loc[e, f"o{cl}"] / (dp.loc[e, f"o{op}"] + spr) - 1) * 1e4})
        x = pd.DataFrame(rows)
        x["era"] = np.where(x.d <= kk.ESKI_END, "ESKI", "YENI")
        out[sym] = {e or "TUM": {"n": int((x[x.era == e] if e else x).K1.sum()), "ort": round(float((x[x.era == e] if e else x).pipe(lambda z: z.net[z.K1]).mean()), 1),
                                 "taban": round(float((x[x.era == e] if e else x).pipe(lambda z: z.net[~z.K1]).mean()), 1)} for e in ("ESKI", "YENI", None)}
        print(sym, out[sym], flush=True)
    (RES / "ndx_avrupa_sabah.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    {"ana": main, "sabah": sabah}[sys.argv[1] if len(sys.argv) > 1 else "ana"]()
