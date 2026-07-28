"""audit_claimB3.py — ATR 2.0/1.0 geometrisinde ayni denetim (iddianin 2. ayagi).

Iddia: 'ATR 2.0/1.0'de de ayni: izgara SELL EV -0.038 vs pulse SELL +0.095, ve
bu fark train/val/test UCUNDE de ayni yonde (+0.099/+0.092/+0.111).'
Burada once yeniden uretilir, sonra SAAT ve GUNxSAAT esitlenmis kiyas yapilir.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from engine import DATA, add_indicators, asof_features, load_bars, resample_from
from geometry_apply import replay_atr, atr_series, split_of, MODELS

KTP, KSL = 2.0, 1.0
RNG = np.random.default_rng(3)

b1 = load_bars("1m")
ts1m = b1["ts"].values
arr = b1[["open", "high", "low", "close"]].to_numpy()
af = atr_series(b1)

s = pd.read_csv(DATA / "signals.csv")
s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
s = s[s.model_type.isin(MODELS) & s.ml_direction.isin(["BUY", "SELL"])]
s = s[(s.ts >= b1.ts.min()) & (s.ts <= b1.ts.max() - pd.Timedelta(days=2))]
s = s[["id", "ts", "model_type", "ml_direction"]].sort_values("ts")
s = asof_features(s, af.assign(ts=af["known_at"])).drop(columns=["known_at"])

step = resample_from(b1, "15m")
grid = pd.DataFrame({"ts": step["ts"] + pd.Timedelta(minutes=15)})
grid = grid[(grid.ts >= b1.ts.min() + pd.Timedelta(days=12)) &
            (grid.ts <= b1.ts.max() - pd.Timedelta(days=2))]
grid = asof_features(grid, af.assign(ts=af["known_at"])).drop(columns=["known_at"])


def run(src, is_grid):
    rows = []
    for r in src.itertuples(index=False):
        atr = getattr(r, "H1_atr", np.nan)
        if not np.isfinite(atr) or atr <= 0:
            continue
        tp, sl = KTP * atr, KSL * atr
        dirs = ("BUY", "SELL") if is_grid else (r.ml_direction,)
        for d in dirs:
            res = replay_atr(arr, ts1m, np.datetime64(r.ts), d, tp, sl)
            if res is None:
                continue
            rows.append(dict(ts=r.ts, direction=d, **res))
    return pd.DataFrame(rows)


print("replay: izgara…", flush=True)
G = run(grid, True)
print("replay: sinyaller…", flush=True)
S = run(s, False)

# epizod kurali
eps = []
for d in ("BUY", "SELL"):
    sub = S[S.direction == d].sort_values("ts")
    ou = None
    for r in sub.itertuples(index=False):
        if ou is not None and r.ts < ou:
            continue
        ou = b1["ts"].iloc[int(r.exit_i)]
        eps.append(r._asdict())
E = pd.DataFrame(eps)

for df in (G, E):
    df["hour"] = df.ts.dt.hour; df["date"] = df.ts.dt.date
    df["month"] = df.ts.dt.to_period("M").astype(str)
    df["split"] = split_of(df.ts)
lo, hi = G.ts.min(), G.ts.max()
E = E[(E.ts >= lo) & (E.ts <= hi)]

print(f"\nATR {KTP}/{KSL} — HAM (yeniden uretim)")
for d in ("BUY", "SELL"):
    gx, ex = G[G.direction == d], E[E.direction == d]
    print(f"  {d}: izgara n={len(gx)} WR={gx.outcome.mean()*100:.1f} EV={gx.r.mean():+.4f} | "
          f"pulse n={len(ex)} WR={ex.outcome.mean()*100:.1f} EV={ex.r.mean():+.4f} → Δ{ex.r.mean()-gx.r.mean():+.4f}")


def matched(ex, gx, keys):
    ec = ex.groupby(keys).agg(pev=("r", "mean"), k=("r", "size")).reset_index()
    gc = gx.groupby(keys).agg(ev=("r", "mean")).reset_index()
    m = ec.merge(gc, on=keys, how="inner")
    w = m.k.values
    return float((m.ev * w).sum() / w.sum()), float((m.pev * w).sum() / w.sum()), m


print(f"\nATR {KTP}/{KSL} — ESITLENMIS")
for keys, nm in ((["hour"], "saat"), (["month"], "ay"), (["date"], "gun"),
                 (["date", "hour"], "gun x saat")):
    line = f"  {nm:12s} "
    for d in ("BUY", "SELL"):
        gev, pev, _ = matched(E[E.direction == d], G[G.direction == d], keys)
        line += f"{d}: izg{gev:+.4f} pls{pev:+.4f} Δ{pev-gev:+.4f}   "
    print(line)

print(f"\nATR {KTP}/{KSL} — SPLIT bazinda (ham vs saat-esit vs gunxsaat-esit)")
for d in ("BUY", "SELL"):
    for sp in ("train", "val", "test"):
        gx = G[(G.direction == d) & (G.split == sp)]
        ex = E[(E.direction == d) & (E.split == sp)]
        if len(ex) < 5:
            continue
        gh, ph, _ = matched(ex, gx, ["hour"])
        gd, pd_, _ = matched(ex, gx, ["date", "hour"])
        print(f"  {d} {sp:5s} n={len(ex):4d}  ham Δ={ex.r.mean()-gx.r.mean():+.4f}  "
              f"saat Δ={ph-gh:+.4f}  gun×saat Δ={pd_-gd:+.4f}")

# gun-bloklu bootstrap (gun x saat esit)
print(f"\nATR {KTP}/{KSL} — GUN-BLOKLU BOOTSTRAP (gun x saat esitlenmis, B=4000)")
for d in ("BUY", "SELL"):
    gev, pev, m = matched(E[E.direction == d], G[G.direction == d], ["date", "hour"])
    days = m.date.unique()
    grp = {k: (np.repeat(v.pev.values, v.k.values), np.repeat(v.ev.values, v.k.values))
           for k, v in m.groupby("date")}
    out = np.empty(4000)
    for b in range(4000):
        pick = RNG.choice(len(days), size=len(days), replace=True)
        p = np.concatenate([grp[days[i]][0] for i in pick])
        q = np.concatenate([grp[days[i]][1] for i in pick])
        out[b] = p.mean() - q.mean()
    l5, h95 = np.percentile(out, [5, 95])
    print(f"  {d}: gun={len(days)} nokta={pev-gev:+.4f} %5-95=[{l5:+.4f},{h95:+.4f}] P(>0)={(out>0).mean()*100:.1f}%")

# ham fark icin de gun-bloklu
print(f"\nATR {KTP}/{KSL} — HAM fark icin gun-bloklu bootstrap (izgara sabit)")
for d in ("BUY", "SELL"):
    ex = E[E.direction == d]; gref = G[G.direction == d].r.mean()
    days = ex.date.unique(); grp = {k: v.r.values for k, v in ex.groupby("date")}
    out = np.empty(4000)
    for b in range(4000):
        pick = RNG.choice(len(days), size=len(days), replace=True)
        out[b] = np.concatenate([grp[days[i]] for i in pick]).mean() - gref
    l5, h95 = np.percentile(out, [5, 95])
    print(f"  {d}: gun={len(days)} nokta={ex.r.mean()-gref:+.4f} %5-95=[{l5:+.4f},{h95:+.4f}] P(>0)={(out>0).mean()*100:.1f}%")

# ay bazinda
print(f"\nATR {KTP}/{KSL} — AY BAZINDA")
rows = []
for d in ("BUY", "SELL"):
    for mo in sorted(E.month.unique()):
        ex = E[(E.direction == d) & (E.month == mo)]; gx = G[(G.direction == d) & (G.month == mo)]
        if len(ex) < 3:
            continue
        rows.append(dict(yon=d, ay=mo, n=len(ex), pulseEV=ex.r.mean(), izgaraEV=gx.r.mean(),
                         delta=ex.r.mean() - gx.r.mean()))
print(pd.DataFrame(rows).round(4).to_string(index=False))

G.to_parquet(DATA / "audit_atr_grid.parquet", index=False)
E.to_parquet(DATA / "audit_atr_epi.parquet", index=False)
