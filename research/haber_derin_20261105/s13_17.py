"""S9 maxT, S9b, S13, S14, S15, S16 — yalnız KEŞİF (2024-01→2025-12)."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
from takvim_truth import cal, BAS, KESIF_END
NY = ZoneInfo("America/New_York")
B = O.Bars("NDX")
N = 1000

def et(d: pd.Timestamp, hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return int(pd.Timestamp(d.year, d.month, d.day, h, m, tz=NY).timestamp())

# ---- S13 bilanço
eds = {}
for s in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"):
    x = yf.Ticker(s).get_earnings_dates(limit=40)
    for ts in x.index:
        loc = ts.tz_convert(NY)
        if loc.hour >= 15 and pd.Timestamp("2024-01-01", tz=NY) <= loc < pd.Timestamp("2026-01-01", tz=NY):
            eds.setdefault(loc.normalize(), []).append(s)
D = sorted(eds)
print("bilanço günü", len(D), "olay", sum(map(len, eds.values())))
bd = lambda d, k: (d + pd.tseries.offsets.BDay(k))
pre = np.array([et(bd(d, -1), "15:55") for d in D]); ngt = np.array([et(d, "15:55") for d in D])
# süreler ET'ye göre değişir: gerçek dakika farkı hesaplanır (hücre sabit h ister, yaklaşık: tek gün 1440, gece 1060)
cells = [{"name": "S13a D-1 15:55→D 15:55 uzun", "ts": pre, "side": np.ones(len(pre), int), "h": 1440},
         {"name": "S13b D 15:55→D+1 09:35 uzun", "ts": ngt, "side": np.ones(len(ngt), int), "h": 1060},
         {"name": "S13c çok büyük(NVDA,AAPL,MSFT) gece", "ts": np.array([et(d, "15:55") for d in D if set(eds[d]) & {"NVDA", "AAPL", "MSFT"}]), "side": None, "h": 1060}]
cells[2]["side"] = np.ones(len(cells[2]["ts"]), int)
print(O.family(B, cells, N=N, extra_bp=1.0).to_string(index=False))

# ---- S14 hafta sonu boşluğu
tt = B.t; idx = np.flatnonzero(np.diff(tt) > 40 * 3600)   # hafta sonu boşluğu
rows, ts, sd, up = [], [], [], []
tr = pd.DataFrame(json.load(open(O.DATA / "truth_archive.json")))
tr["u"] = pd.to_datetime(tr.created_at, utc=True, format="ISO8601").astype("int64") // 10**9
tr["txt"] = tr.content.fillna("").astype(str).map(lambda s: re.sub(r"<[^>]+>", " ", s))
TAR = tr[tr.txt.str.contains(r"\b(?:tariffs?|trade deal|reciprocal|trade war|duties|china|chinese|xi jinping)\b", case=False, regex=True)].u.to_numpy()
for i in idx:
    if not (BAS <= tt[i + 1] < KESIF_END): continue
    g = (B.o[i + 1] / B.c[i] - 1) * 1e4
    if abs(g) < 20: continue
    ts.append(tt[i + 1]); sd.append(-int(np.sign(g))); up.append(((TAR > tt[i]) & (TAR < tt[i + 1])).any())
ts, sd, up = np.array(ts), np.array(sd), np.array(up)
h = 60 * 15  # Paz 18:00 ET → Pzt 09:00 ET (~15 sa)
cells = [{"name": "S14 boşluk tersi tüm", "ts": ts, "side": sd, "h": h}, {"name": "S14 tarife gönderili", "ts": ts[up], "side": sd[up], "h": h}, {"name": "S14 gönderisiz", "ts": ts[~up], "side": sd[~up], "h": h},
         {"name": "S14 boşluk yönü tüm", "ts": ts, "side": -sd, "h": h}]
print(O.family(B, cells, N=N).to_string(index=False))

# ---- S15 olay söndürme
c = cal(); c = c[c.u < KESIF_END]
cells = []
for ev in ("CPI", "NFP", "FOMC"):
    u = c[c.event == ev].u.to_numpy()
    for lb in (1, 5):
        tss, sds = [], []
        for t in u:
            a, b = np.searchsorted(B.t, t), np.searchsorted(B.t, t + lb * 60)
            if b < len(B.t) and a < b and B.t[a] == t and B.t[b] - (t + lb * 60) < 120:
                tss.append(t + lb * 60 - 1); sds.append(-int(np.sign(B.c[b - 1] - B.o[a]) or 1))
        for h in (15, 60, 240):
            cells.append({"name": f"S15 {ev} ilk{lb}dk tersi {h}dk", "ts": np.array(tss), "side": np.array(sds), "h": h})
print(O.family(B, cells, N=N).to_string(index=False))

# ---- S9 Truth maxT
d = tr[(tr.u >= BAS) & (tr.u < KESIF_END)].sort_values("u")
rx = {"tarife": r"\b(?:tariffs?|trade deal|reciprocal|trade war|duties)\b", "fed": r"\b(?:powell|federal reserve|interest rates?|rate cut|fed)\b",
      "cin": r"\b(?:china|xi jinping|chinese)\b", "petrol": r"\b(?:opec|oil prices?|iran|hormuz|drill)\b"}
cells = []
for k, p in rx.items():
    e = d[d.txt.str.contains(p, case=False, regex=True)]; e = e[e.u.diff().fillna(1e9) >= 3600]
    tss, sds = [], []
    for t in e.u.to_numpy():
        a, b = np.searchsorted(B.t, t), np.searchsorted(B.t, t + 120)
        if 0 < a and b < len(B.t) and t - B.t[a - 1] < 300 and B.t[b] - (t + 120) < 120:
            tss.append(t + 120); sds.append(int(np.sign(B.c[b - 1] - B.c[a - 1]) or 1))
    for h in (15, 60, 240):
        cells.append({"name": f"S9 {k} 2dk tepkiye uy {h}dk", "ts": np.array(tss), "side": np.array(sds), "h": h})
print(O.family(B, cells, N=N).to_string(index=False))

# ---- S9b metin yönü
ESC = r"\b(?:raise|raising|increase|impose|imposing|additional|higher|100%|50%|25%)\b.{0,60}\b(?:tariffs?|duties)\b|\btariffs?\b.{0,40}\b(?:will|effective|starting|immediately)\b|\bretaliat"
DEAL = r"\b(?:trade deal|agreement|pause|paused|deal with|reduce[ds]? tariffs?|lower(?:ed|ing)? tariffs?|exempt|very good (?:talks|call|meeting)|great (?:talks|call|meeting)|truce)\b"
e = d[d.txt.str.contains(r"\b(?:tariffs?|trade|china)\b", case=False, regex=True)].copy()
e["esc"] = e.txt.str.contains(ESC, case=False, regex=True); e["deal"] = e.txt.str.contains(DEAL, case=False, regex=True)
e = e[e.esc != e.deal]; e = e[e.u.diff().fillna(1e9) >= 1800]
print("S9b", len(e), "esc", int(e.esc.sum()), "deal", int(e.deal.sum()))
cells = []
for h in (5, 15, 60, 240):
    side = np.where(e.deal, 1, -1)
    cells.append({"name": f"S9b metin yönü {h}dk", "ts": e.u.to_numpy().astype(float), "side": side, "h": h})
    cells.append({"name": f"S9b yalnız anlaşma BUY {h}dk", "ts": e[e.deal].u.to_numpy().astype(float), "side": np.ones(int(e.deal.sum()), int), "h": h})
    cells.append({"name": f"S9b yalnız tırmanma SELL {h}dk", "ts": e[e.esc].u.to_numpy().astype(float), "side": -np.ones(int(e.esc.sum()), int), "h": h})
print(O.family(B, cells, N=N).to_string(index=False))

# ---- S16 bracket (bar içi; ikisi aynı barda → zarar)
res = []
sp = np.nanmedian(B.ao - B.o)
for ev in ("CPI", "NFP", "FOMC"):
    u = c[c.event == ev].u.to_numpy()
    for mult in (0.5, 1, 2):
        pnl = []
        for t in u:
            a = np.searchsorted(B.t, t)
            if a < 61 or a + 16 >= len(B.t) or B.t[a] != t: continue
            atr5 = np.mean(np.abs(B.ret[a - 60:a])) * 5 * B.c[a - 1]
            X = mult * atr5; ref = B.c[a - 1]; up, dn = ref + X, ref - X; pos = 0; res_bp = None; slip = sp
            for k in range(a, a + 15):
                hi, lo, ci = B.h[k], B.l[k], B.c[k]
                if pos == 0:
                    hu, hd = hi >= up, lo <= dn
                    if hu and hd: res_bp = -(2 * X + 2 * slip) / ref * 1e4; break
                    if hu: pos, en = 1, up + slip
                    elif hd: pos, en = -1, dn - slip
                    else: continue
                    tp = en + pos * 2 * X; sl = en - pos * 2 * X
                    # aynı barda devam: yalnız kapanışa bak, bar içi sıra bilinmez: sl önce
                    if (pos > 0 and lo <= sl) or (pos < 0 and hi >= sl): res_bp = -(2 * X + slip) / ref * 1e4; break
                    continue
                if (pos > 0 and lo <= sl) or (pos < 0 and hi >= sl): res_bp = -(2 * X + slip) / ref * 1e4; break
                if (pos > 0 and hi >= tp) or (pos < 0 and lo <= tp): res_bp = (2 * X - slip) / ref * 1e4; break
            if res_bp is None:
                res_bp = 0.0 if pos == 0 else pos * (B.c[a + 14] - en) / ref * 1e4 - slip / ref * 1e4
            pnl.append((t, res_bp))
        v = np.array([p[1] for p in pnl]); tt = np.array([p[0] for p in pnl])
        res.append({"h": f"S16 {ev} X={mult}", "n": len(v), "ort": round(v.mean(), 2), "isabet": round((v > 0).mean(), 3), "P": round(O.boot_p(v, tt // 86400), 3), "işlemsiz": round((v == 0).mean(), 2)})
print(pd.DataFrame(res).to_string(index=False))
