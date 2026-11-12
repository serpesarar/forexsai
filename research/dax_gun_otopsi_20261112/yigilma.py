"""Y1/Y2/Y3 — aileler arası yığılma. Ön kayıt PROTOCOL.md. Salt-okuma."""
import json, numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent
t = pd.read_csv(HERE.parents[1] / "output/islem_otopsi/2026-11-12_2142_all/islemler.csv", parse_dates=["entry_utc", "exit_utc"])
t = t[np.isfinite(t.r_exit)].sort_values("entry_utc").reset_index(drop=True)
rng = np.random.default_rng(7)

def ctx(i, r):
    o = t[(t.symbol == r.symbol) & (t.direction == r.direction) & (t.entry_utc < r.entry_utc) & (t.exit_utc > r.entry_utc)]
    if o.empty: return 0, 0, 0
    s = 1 if r.direction == "BUY" else -1
    # o andaki fiyat ≈ bu işlemin giriş fiyatı
    under = int((s * (r.open_price - o.open_price) < 0).sum())
    return len(o), under, int((o.family != r.family).sum())
c = np.array([ctx(i, r) for i, r in t.iterrows()])
t["n_same"], t["n_under"], t["n_other_fam"] = c[:, 0], c[:, 1], c[:, 2]
t["Y1"] = t.n_same > 0; t["Y2"] = t.n_under > 0
t["day"] = t.entry_utc.dt.date

def delta(df, flag):
    a, b = df[df[flag]].r_exit, df[~df[flag]].r_exit
    return a.mean() - b.mean() if len(a) and len(b) else np.nan

def boot(df, flag, n=5000):
    g = df.groupby("day").agg(sf=("r_exit", lambda x: x[df.loc[x.index, flag]].sum()), nf=(flag, "sum"),
                              sa=("r_exit", "sum"), na=("r_exit", "size"))
    g["sr"], g["nr"] = g.sa - g.sf, g.na - g.nf
    w = rng.multinomial(len(g), np.ones(len(g)) / len(g), size=n)
    sf, nf, sr, nr = (w @ g[c].values for c in ["sf", "nf", "sr", "nr"])
    with np.errstate(invalid="ignore", divide="ignore"):
        out = sf / nf - sr / nr
    return float(np.nanmean(out < 0)), np.nanpercentile(out, [2.5, 97.5]).round(3).tolist()

def strat(df, flag):
    w, s = 0, 0
    for _, g in df.groupby("family"):
        if g[flag].sum() >= 3 and (~g[flag]).sum() >= 3:
            n = len(g); w += n; s += n * delta(g, flag)
    return s / w if w else np.nan

res = {}
for flag in ["Y1", "Y2"]:
    for name, df in [("tumu", t), ("GDAXI", t[t.symbol == "GDAXI.INDX"])]:
        h = len(df) // 2; d1, d2 = df.iloc[:h], df.iloc[h:]
        p, ci = boot(df, flag)
        res[f"{flag}_{name}"] = dict(n_flag=int(df[flag].sum()), n_rest=int((~df[flag]).sum()),
            r_flag=round(df[df[flag]].r_exit.mean(), 3), r_rest=round(df[~df[flag]].r_exit.mean(), 3),
            usd_flag=round(df[df[flag]].net.sum()), delta=round(delta(df, flag), 3), P_neg=round(p, 3), ci=ci,
            yari1=round(delta(d1, flag), 3), yari2=round(delta(d2, flag), 3), tabakali=round(strat(df, flag), 3))
# Y1 sembol × aile kırılımı
res["Y1_sembol"] = t.groupby(["symbol", "Y1"]).r_exit.agg(["count", "mean"]).round(3).reset_index().to_dict("records")
res["Y1_aile"] = t.groupby(["family", "Y1"]).r_exit.agg(["count", "mean"]).round(3).reset_index().to_dict("records")
# Y3 CHREV GER40 $ risk
ch = t[(t.family == "CHREV") & (t.symbol == "GDAXI.INDX")].copy()
ch["sl_pts"] = (ch.open_price - ch.sl0).abs(); ch["risk_usd"] = (ch.net.abs() / ch.r_exit.abs()).where(ch.r_exit.abs() > 0.2)
res["Y3"] = dict(n=len(ch), sl_pts_q=ch.sl_pts.quantile([.1, .5, .9]).round(1).tolist(), risk_usd_q=ch.risk_usd.quantile([.1, .5, .9]).round(0).tolist(),
                 last=ch.tail(1)[["entry_utc", "sl_pts", "risk_usd", "volume", "r_exit"]].astype(str).to_dict("records"),
                 sl_pts_pct=round(float((ch.sl_pts < ch.sl_pts.iloc[-1]).mean()), 3),
                 lots=ch.volume.value_counts().to_dict())
(HERE / "results").mkdir(exist_ok=True)
(HERE / "results/yigilma.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
