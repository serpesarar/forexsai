"""D1 + S7 (FOMC öncesi/sonrası) + S9 (Truth) + S12 (ORB × veri günü) NDX; yalnız KEŞİF (≤2025-12-31) sonuçları basılır."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
ROOT = Path(__file__).resolve().parents[2]
KESIF_END = int(pd.Timestamp("2026-01-01", tz="UTC").timestamp())
BAS = int(pd.Timestamp("2024-01-02", tz="UTC").timestamp())

def cal() -> pd.DataFrame:
    c = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    c["ts"] = pd.to_datetime(c.ts_utc, utc=True); c["u"] = c.ts.astype("int64") // 10**9
    return c[(c.u >= BAS)]

def stats(vals: np.ndarray, u: np.ndarray, plc: np.ndarray | None = None) -> dict:
    m = np.isfinite(vals); v, t = vals[m], u[m]
    if len(v) < 5: return {"n": len(v)}
    o = np.argsort(t); v, t = v[o], t[o]; h = len(v) // 2
    r = {"n": len(v), "ort_bp": round(v.mean(), 2), "med_bp": round(np.median(v), 2), "isabet": round((v > 0).mean(), 3),
         "P": round(O.boot_p(v, t // 86400), 3), "y1": round(v[:h].mean(), 2), "y2": round(v[h:].mean(), 2)}
    if plc is not None and len(plc):
        r["plasebo_p"] = round(float((plc >= v.mean()).mean()), 3)
    return r

def evalset(B: O.Bars, ts: np.ndarray, side: np.ndarray, h: int, N: int = 1000, seed: int = 11) -> dict:
    v = np.array([B.trade(float(t), int(s), h) or np.nan for t, s in zip(ts, side)], float)
    st = np.array([B.trade(float(t), int(s), h, stress=True) or np.nan for t, s in zip(ts, side)], float)
    rng = np.random.default_rng(seed); means = []
    for _ in range(N):
        off = rng.integers(1, 9, len(ts)) * rng.choice([-1, 1], len(ts)) * 7 * 86400
        p = np.array([B.trade(float(t + o), int(s), h) or np.nan for t, o, s in zip(ts, off, side)], float)
        if np.isfinite(p).sum() > 3: means.append(np.nanmean(p))
    r = stats(v, ts, np.array(means)); r["stres"] = round(float(np.nanmean(st)), 2)
    return r

if __name__ == "__main__":
    B = O.Bars("NDX")
    c = cal()
    print("takvim", c.event.value_counts().to_dict())
    # D1 pozitif kontrol: olay dakikası |getiri| / aynı dakika ±hafta
    res = []
    for ev in ("CPI", "NFP", "FOMC"):
        u = c[c.event == ev].u.to_numpy()
        for lag in (-5, -1, 0, 1, 2, 5, 15, 30):
            def mv(t):
                i = int(np.searchsorted(B.t, t + lag * 60))
                return abs(B.ret[i]) * 1e4 if i < len(B.t) and B.t[i] == t + lag * 60 else np.nan
            a = np.nanmean([mv(t) for t in u]); p = np.nanmean([mv(t + w * 7 * 86400) for t in u for w in (-3, -2, -1, 1, 2, 3)])
            res.append({"olay": ev, "lag": lag, "oran": round(a / p, 2)})
    print(pd.DataFrame(res).pivot(index="olay", columns="lag", values="oran").to_string())
    # 2025 gözlenen spread: olay dakikası vs olağan
    i25 = (B.t >= 1735689600) & (B.t < 1767225600)
    sp = (B.ao - B.o)
    for ev in ("CPI", "NFP", "FOMC"):
        u = c[(c.event == ev) & (c.u.between(1735689600, 1767225600))].u.to_numpy()
        row = {}
        for lag in (0, 1, 2, 5):
            ix = np.searchsorted(B.t, u + lag * 60); ix = ix[ix < len(B.t)]; row[lag] = round(float(np.median(sp[ix])), 2)
        print("gözlenen spread", ev, row, "o saatin medyanı", round(float(np.median(sp[i25])), 2))
    out = []
    # S7a: FOMC öncesi uzun: açıklamadan 24 sa önce → 5 dk önce
    f = c[(c.event == "FOMC") & (c.u < KESIF_END)]
    out.append({"h": "S7a FOMC öncesi uzun 24s", **evalset(B, f.u.to_numpy() - 86400, np.ones(len(f), int), 24 * 60 - 5, N=300)})
    out.append({"h": "S7a2 FOMC öncesi uzun 4s", **evalset(B, f.u.to_numpy() - 4 * 3600, np.ones(len(f), int), 4 * 60 - 5, N=300)})
    # S7b: açıklama sonrası ilk 30 dk yönünü ertesi gün kapanışa kadar TERS (ertesi gün dönüşü)
    for lb, h in ((30, 60 * 22), (60, 60 * 22)):
        ts, sd = [], []
        for t in f.u.to_numpy():
            i0, i1 = np.searchsorted(B.t, t), np.searchsorted(B.t, t + lb * 60)
            if i1 < len(B.t) and i0 < len(B.t) and B.t[i1] - (t + lb * 60) < 180:
                ts.append(t + lb * 60); sd.append(-int(np.sign(B.c[i1] - B.o[i0]) or 1))
        out.append({"h": f"S7b FOMC +{lb}dk tersi, {h}dk", **evalset(B, np.array(ts), np.array(sd), h, N=300)})
    # S7c: CPI/NFP ilk 5 dk yönüne uy ve ters, 15/60/240 dk
    for ev in ("CPI", "NFP"):
        e = c[(c.event == ev) & (c.u < KESIF_END)]
        ts, sd = [], []
        for t in e.u.to_numpy():
            i0, i1 = np.searchsorted(B.t, t), np.searchsorted(B.t, t + 300)
            if i1 < len(B.t) and B.t[i1] - (t + 300) < 120:
                ts.append(t + 300); sd.append(int(np.sign(B.c[i1 - 1] - B.o[i0]) or 1))
        ts, sd = np.array(ts), np.array(sd)
        for h in (15, 60, 240):
            out.append({"h": f"S3k {ev} 5dk yönüne uy, {h}dk", **evalset(B, ts, sd, h, N=300)})
    print(pd.DataFrame(out).to_string(index=False))
    # S9 Truth
    tr = json.load(open(O.DATA / "truth_archive.json"))
    d = pd.DataFrame(tr); d["ts"] = pd.to_datetime(d.created_at, utc=True, format="ISO8601"); d["u"] = d.ts.astype("int64") // 10**9
    d["txt"] = d.content.fillna("").astype(str).map(lambda s: re.sub(r"<[^>]+>", " ", s))
    print("Truth", len(d), d.ts.min(), d.ts.max())
    rx = {"tarife": r"\b(tariffs?|trade deal|reciprocal|trade war|duties)\b", "fed": r"\b(powell|federal reserve|interest rates?|rate cut|fed)\b",
          "cin": r"\b(china|xi jinping|chinese)\b", "petrol": r"\b(opec|oil prices?|iran|hormuz|drill)\b", "borsa": r"\b(stock market|dow|nasdaq|s&p|great time to buy)\b"}
    rows = []
    for k, p in rx.items():
        e = d[d.txt.str.contains(p, case=False, regex=True) & (d.u >= BAS) & (d.u < KESIF_END)].sort_values("u")
        e = e[e.u.diff().fillna(1e9) >= 3600]   # 60 dk bağımsız
        u = e.u.to_numpy()
        ts, sd, r0 = [], [], []
        for t in u:
            i0, i1 = np.searchsorted(B.t, t), np.searchsorted(B.t, t + 120)
            if i1 < len(B.t) and i0 < len(B.t) and B.t[i1] - (t + 120) < 120 and t - B.t[max(i0 - 1, 0)] < 300:
                ts.append(t + 120); sd.append(int(np.sign(B.c[i1 - 1] - B.c[max(i0 - 1, 0)]) or 1)); r0.append(abs(B.c[i1 - 1] / B.c[max(i0 - 1, 0)] - 1) * 1e4)
        ts, sd = np.array(ts), np.array(sd)
        # oynaklık oranı: gönderi sonrası 5/15 dk |getiri|, aynı hafta-dakika plasebo
        def absmove(t, h):
            i0 = np.searchsorted(B.t, t); i1 = np.searchsorted(B.t, t + h * 60)
            return abs(B.c[i1] / B.c[i0] - 1) * 1e4 if i1 < len(B.t) and B.t[i0] - t < 120 and abs(B.t[i1] - t - h * 60) < 120 else np.nan
        vr = {}
        for h in (5, 15, 60):
            a = np.nanmean([absmove(t, h) for t in ts - 120]); p = np.nanmean([absmove(t + w * 7 * 86400, h) for t in ts - 120 for w in (-3, -2, -1, 1, 2, 3)])
            vr[h] = round(a / p, 2)
        for h in (15, 60, 240):
            rows.append({"konu": k, "h": h, "oyn_oran5_15_60": vr, **evalset(B, ts, sd, h, N=200)})
    print(pd.DataFrame(rows).to_string(index=False))
