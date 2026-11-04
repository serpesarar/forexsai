"""ON keşif koşusu (< 2026-07-01). Kasa AÇILMAZ (lockbox.py ayrı)."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from engine import *  # noqa
from long_data import macro as load_macro

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
OUT = {}
MAC = load_macro()
T0 = pd.Timestamp("2016-05-29", tz="UTC")


def disc(b):
    return b[b.ts < pd.Timestamp(DISC_END, tz="UTC")].reset_index(drop=True)


ndx1h = disc(load_bars("ndx1h")); ndx30 = disc(load_bars("ndx30m")); ndx1m = disc(load_bars("ndx1m"))
ET = "America/New_York"

# ---------- 1. saat-saat tablo ----------
def hourly(b, tz, step_min=60, label=""):
    t = b.ts.dt.tz_convert(tz)
    x = b.set_index("ts")
    nxt = b.ts + pd.Timedelta(minutes=step_min)
    o_next = x.open.reindex(nxt).to_numpy()
    r = o_next / b.open.to_numpy() - 1
    d = pd.DataFrame({"h": t.dt.hour, "r": r, "y": t.dt.year}).dropna()
    return d

def htable(d, eras):
    rows = {}
    for name, m in eras.items():
        g = d[m(d)].groupby("h").r
        rows[name + "_bp"] = g.mean() * 1e4
        rows[name + "_t"] = g.mean() / (g.std() / np.sqrt(g.count()))
    return pd.DataFrame(rows).round(2)

h1 = hourly(ndx1h, ET)
tab = htable(h1, {"16-20": lambda d: d.y <= 2020, "21-26": lambda d: d.y >= 2021, "tum": lambda d: d.y > 0})
# 1m → saatlik (hh:00 → hh+1:00, ilk bar ≥ T ≤5dk)
px1m = Px(ndx1m, exact=False)
hrs = pd.date_range(ndx1m.ts.min().floor("h"), ndx1m.ts.max().floor("h"), freq="h")
a = px1m.get(hrs.tz_localize(None).values); bb = px1m.get((hrs + pd.Timedelta(hours=1)).tz_localize(None).values)
m1 = pd.DataFrame({"h": hrs.tz_convert(ET).hour, "r": bb / a - 1, "y": hrs.year}).dropna()
tab1m = htable(m1, {"1m_25_26": lambda d: d.y > 0})
tab = tab.join(tab1m)
print("\n=== Saat-saat ortalama getiri (bp) ve t — NY saati, bar başlangıcı ===")
print(tab.to_string())
OUT["hourly"] = tab.reset_index().to_dict("records")
# kararlılık: iki çağ korelasyonu
print("çağlar arası korelasyon (24 saat bp):", round(tab["16-20_bp"].corr(tab["21-26_bp"]), 3))

# ---------- 2. stratejiler ----------
S = {
    "S1_NIGHT": Win("S1", ET, ("pcal", 18, 0), (0, 9, 30)),
    "S2_CTO": Win("S2", ET, (-1, 16, 0), (0, 9, 30)),
    "S3_EU": Win("S3", ET, (0, 1, 0), (0, 4, 0)),
    "S4_OD": Win("S4", ET, (0, 2, 0), (0, 3, 0)),
    "S5_EU_dn05": Win("S5", ET, (0, 1, 0), (0, 4, 0), "dn0.5"),
    "S6_EU_dn10": Win("S6", ET, (0, 1, 0), (0, 4, 0), "dn1.0"),
    "S7_NIGHT_dn05": Win("S7", ET, ("pcal", 18, 0), (0, 9, 30), "dn0.5"),
    "S8_NIGHT_dn10": Win("S8", ET, ("pcal", 18, 0), (0, 9, 30), "dn1.0"),
    "S9_EU_vix": Win("S9", ET, (0, 1, 0), (0, 4, 0), "vix"),
    "S10_EU_dn05vix": Win("S10", ET, (0, 1, 0), (0, 4, 0), "dn0.5vix"),
    "INTRA": Win("IN", ET, (0, 9, 30), (0, 16, 0)),
    "HOLD": Win("HO", ET, (-1, 16, 0), (0, 16, 0)),
}

def proxy1h(w: Win) -> Win:
    """1h vekili: 09:30 çıkış → 09:00; INTRA 09:30 giriş → 10:00."""
    e, x = w.ent, w.ext
    if w.code == "IN":
        e = (0, 10, 0)
    if x[1:] == (9, 30):
        x = (x[0], 9, 0)
    return Win(w.code, w.tz, e, x, w.cond)

def yearly(df):
    return df.groupby(df.index.year).R.agg(["count", "mean"]).round(3)

def daily_stats(df, days):
    s = df.ret_net.reindex(days).fillna(0)
    return dict(ann_pct=s.mean() * 252 * 100, sharpe=s.mean() / s.std() * np.sqrt(252) if s.std() > 0 else np.nan)

days1h = trading_days(ndx1h, ET, 16, 0)
EV = {}
rows = []
for name, w in S.items():
    ev = build_events(ndx1h, proxy1h(w), (16, 0), True, MAC, ARR_USD)
    ex = build_events(ndx1m, w, (16, 0), False, MAC, ARR_USD, delay=1)
    EV[name] = ev
    c = card(ev, ex)
    c.update(daily_stats(ev, days1h))
    c["name"] = name
    rows.append(c)
    print(f"\n--- {name} yıl yıl (R net) ---"); print(yearly(ev).T.to_string())
    OUT.setdefault("yearly", {})[name] = yearly(ev).reset_index().to_dict("records")
cards = pd.DataFrame(rows).set_index("name")
cols = ["n", "wr", "ortR", "P", "h1", "h2", "sp15", "sp3", "exec_n", "exec_real", "exec_opt", "bp_gross", "bp_net",
        "pts_net", "swap_pts", "ex_top5", "ann_pct", "sharpe", "crit", "pass"]
print("\n=== KART (NDX 1h 2016-05 → 2026-06; icra ölçütü 1m 2025-01 → 2026-06) ===")
print(cards[cols].round(4).to_string())
OUT["cards"] = cards[cols].reset_index().astype(str).to_dict("records")

# çağlar
era = []
for name, ev in EV.items():
    a_, b_ = ev[ev.index.year <= 2020], ev[ev.index.year >= 2021]
    era.append(dict(name=name, n1620=len(a_), R1620=a_.R.mean(), P1620=month_boot(a_), n2126=len(b_), R2126=b_.R.mean(),
                    P2126=month_boot(b_), bp1620=a_.ret_gross.mean() * 1e4, bp2126=b_.ret_gross.mean() * 1e4))
era = pd.DataFrame(era).set_index("name").round(4)
print("\n=== Çağlar (net R; brüt bp) ==="); print(era.to_string())
OUT["era"] = era.reset_index().to_dict("records")

# ---------- 3. Taban A: aynı süre, her başlangıç saati ----------
def same_len(b, tz, L_h):
    px = Px(b, True)
    dates = pd.date_range(b.ts.min().tz_convert(tz).normalize().tz_localize(None), b.ts.max().tz_convert(tz).normalize().tz_localize(None), freq="D")
    res = {}
    for h in range(24):
        te = local_ts(dates, h, 0, tz)
        tx = (pd.to_datetime(te) + pd.Timedelta(hours=L_h)).values
        p0, p1 = px.get(te), px.get(tx)
        r = p1 / p0 - 1
        d = pd.Series(r, index=dates).dropna()
        res[h] = dict(n=len(d), bp=d.mean() * 1e4, t=d.mean() / d.std() * np.sqrt(len(d)),
                      bp1620=d[d.index.year <= 2020].mean() * 1e4, bp2126=d[d.index.year >= 2021].mean() * 1e4)
    return pd.DataFrame(res).T

for L, tgt in [(3, 1), (1, 2), (15, 18), (17, 16)]:
    t = same_len(ndx1h, ET, L)
    rank = int((t.bp > t.loc[tgt, "bp"]).sum()) + 1
    other = t.drop(tgt).bp.mean()
    print(f"\n=== Taban A: {L} saatlik pencere, başlangıç saatine göre (brüt bp); hedef {tgt:02d}:00 sıra {rank}/{len(t)}; diğerleri ort {other:.2f} bp ===")
    print(t.round(2).T.to_string())
    OUT.setdefault("baseA", {})[f"L{L}_h{tgt}"] = dict(rank=rank, of=len(t), target_bp=t.loc[tgt, "bp"], others_bp=other,
                                                       table=t.round(3).reset_index().to_dict("records"))

# ---------- 4. Taban B: koşul katkısı ----------
print("\n=== Taban B: koşullu − koşulsuz (aynı pencere), net R ===")
for c, u in [("S5_EU_dn05", "S3_EU"), ("S6_EU_dn10", "S3_EU"), ("S9_EU_vix", "S3_EU"), ("S10_EU_dn05vix", "S3_EU"),
             ("S7_NIGHT_dn05", "S1_NIGHT"), ("S8_NIGHT_dn10", "S1_NIGHT")]:
    a_, b_ = EV[c], EV[u]
    rest = b_.drop(a_.index, errors="ignore")
    p = month_boot_diff(a_, rest)
    print(f"{c:16s} {a_.R.mean():+.4f} (n={len(a_)}) vs koşul-dışı {rest.R.mean():+.4f} (n={len(rest)})  fark {a_.R.mean()-rest.R.mean():+.4f}  P(fark>0)={p:.3f}"
          f" | brüt bp {a_.ret_gross.mean()*1e4:+.2f} vs {rest.ret_gross.mean()*1e4:+.2f}")
    OUT.setdefault("baseB", {})[c] = dict(cond=a_.R.mean(), rest=rest.R.mean(), P=p, n=len(a_))

# ---------- 5. 30m birebir 09:30 (2021-06+) ----------
print("\n=== NDX 30m birebir 09:30 (2021-06 → 2026-06) ===")
for name in ["S1_NIGHT", "S2_CTO", "S7_NIGHT_dn05", "S8_NIGHT_dn10", "INTRA", "HOLD", "S3_EU", "S5_EU_dn05"]:
    ev = build_events(ndx30, S[name], (16, 0), True, MAC, ARR_USD)
    c = card(ev)
    print(f"{name:16s} n={c['n']:4d} ortR={c['ortR']:+.4f} P={c['P']:.3f} h1={c['h1']:+.4f} h2={c['h2']:+.4f} sp15={c['sp15']:+.4f} bp_net={c['bp_net']:+.2f} swap={c['swap_pts']:.2f}")
    OUT.setdefault("ndx30m", {})[name] = {k: c[k] for k in ["n", "ortR", "P", "h1", "h2", "sp15", "bp_net"]}

# ---------- 6. 1m keşif (2025-01 → 2026-06) birebir ----------
print("\n=== NDX 1m (2025-01 → 2026-06) gerçekçi icra (T+1dk + spread) ===")
for name, w in S.items():
    ev = build_events(ndx1m, w, (16, 0), False, MAC, ARR_USD, delay=1)
    c = card(ev)
    print(f"{name:16s} n={c['n']:4d} ortR={c['ortR']:+.4f} opt={ev.R_opt.mean():+.4f} P={c['P']:.3f} sp3={c['sp3']:+.4f} bp_net={c['bp_net']:+.2f}")
    OUT.setdefault("ndx1m", {})[name] = {k: c[k] for k in ["n", "ortR", "P", "sp3", "bp_net"]} | {"opt": ev.R_opt.mean()}

# ---------- 7. DAX ----------
dax1h = disc(load_bars("dax1h")); dax1h = dax1h[dax1h.ts >= pd.Timestamp("2019-01-01", tz="UTC")].reset_index(drop=True)
dax30 = disc(load_bars("dax30m"))
BER = "Europe/Berlin"
DX = {
    "DX_EU": (dax1h, Win("DE", ET, (0, 1, 0), (0, 4, 0)), (17, 0), BER),
    "DX_PRE": (dax1h, Win("DP", BER, (0, 8, 0), (0, 9, 0)), (17, 0), BER),
    "DX_EU_dn05": (dax1h, Win("DE5", ET, (0, 1, 0), (0, 4, 0), "dn0.5"), (17, 0), BER),
    "DX_EU_dn10": (dax1h, Win("DE10", ET, (0, 1, 0), (0, 4, 0), "dn1.0"), (17, 0), BER),
    "DX_NIGHT": (dax30, Win("DN", BER, (-1, 17, 30), (0, 9, 0)), (17, 30), BER),
}
print("\n=== DAX (bağımsız piyasa) ===")
dax_rows = []
for name, (b, w, ref, reftz) in DX.items():
    ev = build_events(b, w, ref, True, None, ARR_EUR, ref_tz=reftz)
    c = card(ev)
    c["name"] = name
    dax_rows.append(c)
    print(f"--- {name} yıl yıl ---"); print(yearly(ev).T.to_string())
    OUT.setdefault("dax_yearly", {})[name] = yearly(ev).reset_index().to_dict("records")
dc = pd.DataFrame(dax_rows).set_index("name")
dcols = ["n", "wr", "ortR", "P", "h1", "h2", "sp15", "sp3", "bp_gross", "bp_net", "pts_net", "swap_pts", "ex_top5", "crit", "pass"]
print(dc[dcols].round(4).to_string())
OUT["dax_cards"] = dc[dcols].reset_index().astype(str).to_dict("records")
hd = hourly(dax1h, ET)
td = htable(hd, {"dax19_26": lambda d: d.y > 0})
print("DAX saat-saat (ET saati) bp/t:"); print(td.T.to_string())
OUT["dax_hourly_et"] = td.reset_index().to_dict("records")
print("NDX-DAX saat profili korelasyonu (ET, 2021-26 NDX):", round(tab["21-26_bp"].corr(td["dax19_26_bp"]), 3))
json.dump(OUT, open("results/discovery.json", "w"), default=str, indent=1)
