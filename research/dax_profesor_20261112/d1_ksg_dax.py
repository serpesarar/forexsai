"""D1 — DAX-KSG: 16:30→17:30 Berlin < 0 → 17:30 AL → ertesi işlem günü 09:00 SAT (PROTOCOL.md §D1, donmuş)."""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "research/dax_profesor_20261112")
from data_load import load

SWAP_BP_NIGHT = 4.94 / 365 * 100      # %/yıl → bp/gece
SPREAD_MULT = 1.5
RNG = np.random.default_rng(20261112)
OUT = Path("research/dax_profesor_20261112/results"); OUT.mkdir(exist_ok=True)

def nights(d: pd.DataFrame, sig_start="16:30", entry="17:30", exit_="09:00", spread_mult=SPREAD_MULT) -> pd.DataFrame:
    d = d.assign(day=d["ber"].dt.date, hm=d["ber"].dt.strftime("%H:%M"))
    full = d.groupby(d["ber"].dt.strftime("%Y-%m"))["ber"].transform(lambda s: (s.dt.minute == 30).mean() >= 0.45)
    d = d[full]
    piv = {k: d[d.hm == k].set_index("day") for k in (sig_start, entry, exit_)}
    days = sorted(set(piv[entry].index) & set(piv[sig_start].index))
    exit_days = sorted(piv[exit_].index)
    rows = []
    for dy in days:
        nxt = [x for x in exit_days[np.searchsorted(exit_days, dy, side="right"):][:1]]
        if not nxt: continue
        nx = nxt[0]
        if (pd.Timestamp(nx) - pd.Timestamp(dy)).days > 4: continue      # tatil boşluğu
        s0, e0, x0 = piv[sig_start].loc[dy], piv[entry].loc[dy], piv[exit_].loc[nx]
        sig = e0["o"] / s0["o"] - 1
        gross = (x0["o"] / e0["o"] - 1) * 1e4
        cost = spread_mult * e0["sp"] * 0.1 / e0["o"] * 1e4
        n_nights = 3 if pd.Timestamp(dy).weekday() == 4 else (pd.Timestamp(nx) - pd.Timestamp(dy)).days
        net = gross - cost - SWAP_BP_NIGHT * n_nights
        rows.append(dict(day=dy, sig=sig, gross=gross, net=net, cost=cost, fri=pd.Timestamp(dy).weekday() == 4))
    return pd.DataFrame(rows)

def boot_p(x: np.ndarray, blocks: np.ndarray, n=4000) -> float:
    ub = np.unique(blocks); idx = {b: np.where(blocks == b)[0] for b in ub}
    m = []
    for _ in range(n):
        pick = RNG.choice(ub, len(ub)); m.append(np.concatenate([x[idx[b]] for b in pick]).mean())
    return float((np.array(m) > 0).mean())

def summarize(t: pd.DataFrame) -> dict:
    rule = t[t.sig < 0]; ctr = t[t.sig >= 0]
    mb = pd.to_datetime(rule.day).dt.strftime("%Y-%m").values
    half = len(rule) // 2
    yrs = rule.groupby(pd.to_datetime(rule.day).dt.year)["net"].mean()
    # Δ bootstrap: ay-blok, iki kol birlikte
    t2 = t.assign(m=pd.to_datetime(t.day).dt.strftime("%Y-%m"), r=(t.sig < 0))
    ub = t2.m.unique(); g = {m: t2[t2.m == m] for m in ub}; ds = []
    for _ in range(3000):
        s = pd.concat([g[m] for m in RNG.choice(ub, len(ub))]); ds.append(s[s.r].net.mean() - s[~s.r].net.mean())
    # plasebo: aynı sayıda rastgele gece
    plc = np.array([t.net.values[RNG.choice(len(t), len(rule), replace=False)].mean() for _ in range(2000)])
    return dict(n=len(rule), net=rule.net.mean(), gross=rule.gross.mean(), hit=(rule.net > 0).mean(),
                P=boot_p(rule.net.values, mb), half1=rule.net.iloc[:half].mean(), half2=rule.net.iloc[half:].mean(),
                ctr_n=len(ctr), ctr_net=ctr.net.mean(), delta=rule.net.mean() - ctr.net.mean(), P_delta=float((np.array(ds) > 0).mean()),
                placebo_p=float((plc >= rule.net.mean()).mean()), years_pos=f"{(yrs > 0).sum()}/{len(yrs)}",
                years={int(k): round(v, 1) for k, v in yrs.items()}, worst=rule.net.min(), first=str(rule.day.min()), last=str(rule.day.max()))

if __name__ == "__main__":
    d = load()
    t = nights(d); res = {"ana": summarize(t)}
    t3 = nights(d, spread_mult=3.0); res["spread_x3"] = {"net": t3[t3.sig < 0].net.mean()}
    for name, kw in {"cikis_08": dict(exit_="08:00"), "cikis_10": dict(exit_="10:00"), "giris_18": dict(entry="18:00")}.items():
        tt = nights(d, **kw); r = tt[tt.sig < 0]; res[name] = {"n": len(r), "net": r.net.mean()}
    r = t[(t.sig < 0) & ~t.fri]; res["cuma_haric"] = {"n": len(r), "net": r.net.mean()}
    t.to_csv(OUT / "d1_nights.csv", index=False)
    print(json.dumps(res, indent=1, default=lambda x: round(float(x), 3)))
    json.dump(res, open(OUT / "d1_ozet.json", "w"), indent=1, default=lambda x: round(float(x), 3))
