import numpy as np, pandas as pd, itertools
from lab2 import *
from r4_core import series, feats
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 34)
PER = (("k", "2022-08-15", "2025-01-01"), ("b", "2018-05-25", "2022-08-15"), ("s", "2025-01-01", "2027-01-01"))
def mb(x):
    u, inv = np.unique(x.index.to_period("M").astype(str), return_inverse=True); S, N = np.bincount(inv, x.to_numpy()), np.bincount(inv); ix = np.random.default_rng(3).integers(0, len(u), (1200, len(u))); return float(((S[ix].sum(1) / N[ix].sum(1)) > 0).mean())
OUT = []
def add(fam, sym, lab, r):
    r = r.dropna(); row = {"aile": fam, "sym": sym, "hücre": lab}
    for p, a, b in PER:
        q = r[(r.index >= a) & (r.index < b)]; row[f"{p}_n"] = len(q)
        if len(q) >= 12: row[f"{p}_ort"] = round(q.mean(), 2); row[f"{p}_P"] = round(mb(q), 3); row[f"{p}_is"] = round((q > 0).mean(), 3)
    OUT.append(row); ledger(sym, fam, lab, "kbs", {"n": row.get("k_n"), "bp": row.get("k_ort"), "P": row.get("k_P")})
# T9 C3 çıkışları
s = series("NAS100", "M30", 930); f = feats(s, "NAS100"); m = f.rsi2 < 10; x = mt5_bars("NAS100", "M30"); x["d"] = x.ts_et.dt.normalize(); x["mm"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute
op = x.pivot_table(index="d", columns="mm", values="o", aggfunc="first")
e = s.E + 1.3
add("T9", "NAS100", "ertesi 09:30", (op[570].reindex(s.index).shift(-1) / e - 1) * 1e4 - 2)
add("T9", "NAS100", "ertesi 10:00", (op[600].reindex(s.index).shift(-1) / e - 1) * 1e4 - 2)
add("T9", "NAS100", "ertesi 12:00", (op[720].reindex(s.index).shift(-1) / e - 1) * 1e4 - 2)
add("T9", "NAS100", "ertesi 15:30", (s.E.shift(-1) / e - 1) * 1e4 - 2)
# ilk yükselen S (≤5 gün)
ii = np.flatnonzero(m.to_numpy()); res = {}
S = s.S.to_numpy(); E = s.E.to_numpy()
for i in ii:
    j = next((k for k in range(i + 1, min(i + 6, len(S))) if S[k] > S[k - 1]), min(i + 5, len(S) - 1)); res[s.index[i]] = (E[j] / (E[i] + 1.3) - 1) * 1e4 - 2 * (j - i)
add("T9", "NAS100", "ilk yükselen kapanış ≤5g", pd.Series(res))
for nm, sp in (("NAS100", 1.3), ("XAUUSD", .25), ("SpotCrude", .03)):
    for dm in (930, 570 if nm == "NAS100" else 510 if nm == "XAUUSD" else 540):
        s_ = series(nm, "M30", dm); ff = feats(s_, nm); S_ = s_.S; idx = pd.DatetimeIndex(s_.index)
        for N, h in itertools.product((5, 10, 20, 55), (1, 3, 5, 10)):
            hi = S_ >= S_.rolling(N).max(); lo = S_ <= S_.rolling(N).min(); ex = s_.E.shift(-h); lg = (ex / (s_.E + sp) - 1) * 1e4 - 2 * h; st = (s_.E / (ex + sp) - 1) * 1e4 - .5 * h
            for lab, m_, r_ in ((f"{N}g zirve uzun h{h}", hi, lg), (f"{N}g dip kısa h{h}", lo, st), (f"{N}g dip uzun h{h}", lo, lg), (f"{N}g zirve kısa h{h}", hi, st), (f"{N}g zirve uzun iv düşük h{h}", hi & (ff.iv < ff.ivm), lg), (f"{N}g zirve uzun iv yüksek h{h}", hi & (ff.iv >= ff.ivm), lg), (f"{N}g dip kısa iv yüksek h{h}", lo & (ff.iv >= ff.ivm), st), (f"{N}g dip uzun iv yüksek h{h}", lo & (ff.iv >= ff.ivm), lg)):
                add(f"T11 Donchian {dm//60}:{dm%60:02d}", nm, lab, r_[m_.fillna(False)])
        for dow, nmd in enumerate(["Pzt", "Sal", "Çar", "Per", "Cum"]):
            ex = s_.E.shift(-1); lg = (ex / (s_.E + sp) - 1) * 1e4 - 2; st = (s_.E / (ex + sp) - 1) * 1e4 - .5; k = idx.dayofweek == dow
            add(f"T11 gün {dm//60}:{dm%60:02d}", nm, f"{nmd} uzun", lg[k]); add(f"T11 gün {dm//60}:{dm%60:02d}", nm, f"{nmd} kısa", st[k])
        tm = pd.Series(idx).groupby([idx.year, idx.month]).cumcount().to_numpy(); tmr = pd.Series(idx).groupby([idx.year, idx.month]).cumcount(ascending=False).to_numpy(); ex = s_.E.shift(-1); lg = (ex / (s_.E + sp) - 1) * 1e4 - 2
        add(f"T11 ay dönümü {dm//60}:{dm%60:02d}", nm, "son 2 + ilk 3 gün uzun", lg[(tmr < 2) | (tm < 3)]); add(f"T11 ay dönümü {dm//60}:{dm%60:02d}", nm, "ayın orta günü uzun", lg[(tm >= 9) & (tmr >= 9)])
# olay barı: EIA Çarşamba 10:30, CPI/NFP 08:30, FOMC 14:00 (M30): olay barı yönüne uy/ters, h saat; 3 sembol
cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv"); cal["dd"] = pd.to_datetime(cal.date); DAYS = {e_: set(cal[cal.event == e_].dd) for e_ in ("CPI", "NFP", "FOMC")}
for nm, sp in (("NAS100", 1.3), ("XAUUSD", .25), ("SpotCrude", .03)):
    x = mt5_bars(nm, "M30"); x["d"] = x.ts_et.dt.normalize(); x["mm"] = x.ts_et.dt.hour * 60 + x.ts_et.dt.minute; Ox = x.pivot_table(index="d", columns="mm", values="o", aggfunc="first"); Cx = x.pivot_table(index="d", columns="mm", values="c", aggfunc="first")
    events = {"EIA": (630, Ox.index.dayofweek == 2), "CPI": (510, Ox.index.isin(DAYS["CPI"])), "NFP": (510, Ox.index.isin(DAYS["NFP"])), "FOMC": (840, Ox.index.isin(DAYS["FOMC"]))}
    for ev, (t0, k) in events.items():
        sign = np.sign(Cx[t0] - Ox[t0])
        for hb in (1, 2, 4, 6):
            te = t0 + 30; tx = te + 30 * hb
            if te not in Ox or tx not in Ox: continue
            lg = (Ox[tx] / (Ox[te] + sp) - 1) * 1e4; st = (Ox[te] / (Ox[tx] + sp) - 1) * 1e4
            fo = lg.where(sign > 0, st); fa = st.where(sign > 0, lg)
            add(f"T11 olay {ev}", nm, f"uy {hb*30}dk", fo[k]); add(f"T11 olay {ev}", nm, f"ters {hb*30}dk", fa[k])
            pre = (Ox[t0] / (Ox[t0 - 60] + sp) - 1) * 1e4 if (t0 - 60) in Ox else None
df = pd.DataFrame(OUT); df.to_csv(HERE / "results/r9.csv", index=False); df["mp"] = df[["k_P", "b_P", "s_P"]].min(axis=1)
c = ["aile", "hücre", "k_n", "k_ort", "k_is", "b_n", "b_ort", "s_n", "s_ort", "mp"]
print("T9"); print(df[df.aile == "T9"][c].to_string(index=False))
for s_, g in df[df.aile != "T9"].groupby("sym"):
    ok = g[(g.k_ort > 0) & (g.b_ort > 0) & (g.s_ort > 0)].sort_values("mp", ascending=False)
    print(f"\n== {s_} hücre {len(g)}, minP≥.9: {(g.mp >= .9).sum()} (şans {len(g) * .001:.1f}), ≥.95: {(g.mp >= .95).sum()} (şans {len(g) * .000125:.2f})"); print(ok[c].head(12).to_string(index=False))
