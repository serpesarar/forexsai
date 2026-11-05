"""S1–S5 makro sürpriz + S6 haberli/habersiz şok + S8 konu sözlüğü (NDX). KEŞİF 2025; `--acik` ile doğrulama/kör, yalnız adaylar için."""
from __future__ import annotations
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
A = int(pd.Timestamp("2025-01-01", tz="UTC").timestamp()); Z = int(pd.Timestamp("2026-01-01", tz="UTC").timestamp())
HZ = (5, 15, 60, 240)
N = 1000
SIGN = {"infl": -1, "grow": -1, "grow_inv": 1}   # NDX: sıcak enflasyon/güçlü büyüme → satış (öncül)
B = O.Bars("NDX")

def events() -> pd.DataFrame:
    e = O.macro_events(); e["u"] = e.ts.astype("int64") // 10**9
    e = e[e.kind.isin(SIGN)].dropna(subset=["z"]).sort_values(["u", "order"])
    e["m"] = e.u // 60
    return e.drop_duplicates("m").reset_index(drop=True)

def reaction(t: int, lb_min: int) -> float:
    a = np.searchsorted(B.t, t - t % 60); b = np.searchsorted(B.t, t - t % 60 + lb_min * 60)
    if a >= len(B.t) or b >= len(B.t) or a == b or B.t[a] - t > 120: return np.nan
    return (B.c[b - 1] / B.o[a] - 1) * 1e4

def cells_for(e: pd.DataFrame, tag: str, mask, side, lb: int = 0) -> list[dict]:
    x = e[mask].copy(); s = np.asarray(side)[np.asarray(mask)]
    ts = (x.u.to_numpy() - x.u.to_numpy() % 60 + lb * 60 - 1).astype(float) if lb else x.u.to_numpy().astype(float)
    return [{"name": f"{tag} {h}dk", "ts": ts, "side": s, "h": h} for h in HZ]

def main() -> None:
    e = events(); e = e[(e.u >= A) & (e.u < Z)].reset_index(drop=True)
    print("olay", len(e), e.family.value_counts().to_dict()); print("|z|≥1", int((e.z.abs() >= 1).sum()))
    if "--sayim" in sys.argv: return
    pri = np.array([SIGN[k] for k in e.kind]) * np.sign(e.z.to_numpy())
    r1 = np.array([reaction(u, 1) for u in e.u]); r5 = np.array([reaction(u, 5) for u in e.u]); atr = pd.Series(np.abs(B.ret)).rolling(600, min_periods=100).mean().to_numpy() * 1e4
    a0 = atr[np.minimum(np.searchsorted(B.t, e.u.to_numpy()), len(atr) - 1)]
    big = e.z.abs().to_numpy() >= 1; small = e.z.abs().to_numpy() < 0.5; shock = np.abs(r1) >= 1.5 * a0
    # S2 öğrenilen işaret: aile için son 12 olayın r5·z işareti
    lr = np.full(len(e), np.nan)
    for fam, g in e.groupby("family"):
        hist: list[float] = []
        for i in g.index:
            if len(hist) >= 6: lr[i] = np.sign(np.sum(hist[-12:]))
            if np.isfinite(r5[i]): hist.append(np.sign(e.z.at[i]) * np.sign(r5[i]))
    learned = lr * np.sign(e.z.to_numpy())
    fam = {
        "S1": cells_for(e, "S1 öncül yön |z|≥1", big, pri),
        "S2": cells_for(e, "S2 öğrenilen işaret", big & np.isfinite(learned), np.nan_to_num(learned)),
        "S3": cells_for(e, "S3 tepkiye uy", big & shock, np.sign(np.nan_to_num(r1)), lb=1),
        "S4": cells_for(e, "S4 sürprizsiz tepki söndür", small & shock, -np.sign(np.nan_to_num(r1)), lb=1),
        "S5": cells_for(e, "S5 reddedilen haber", big & (np.sign(np.nan_to_num(r5)) == -pri), np.sign(np.nan_to_num(r5)), lb=5),
    }
    for k, c in fam.items():
        print(f"\n== {k}"); print(O.family(B, c, N=N).to_string(index=False))
    # ailelere göre S1
    for name in ("US_CORE_CPI_MOM", "US_CPI_MOM", "US_NFP", "US_ISM_SVC", "US_ISM_MFG", "US_RETAIL", "US_CLAIMS"):
        m = (e.family == name).to_numpy() & big
        if m.sum() >= 5:
            print(O.family(B, cells_for(e, f"S1 {name}", m, pri), N=300).to_string(index=False, header=False))
    # S6 + S8
    fj = O.load_channel("FinancialJuice"); wb = O.load_channel("WalterBloomberg")
    nw = pd.concat([fj, wb]); nw["u"] = nw.ts.astype("int64") // 10**9; nw = nw[(nw.u >= A) & (nw.u < Z)].sort_values("u")
    REL = re.compile(r"\b(?:fed|fomc|powell|tariffs?|trump|cpi|inflation|payrolls?|nasdaq|nvidia|apple|microsoft|china|iran|war|strike|attack|treasury|yields?)\b", re.I)
    rel = nw[nw.text.str.contains(REL)].u.to_numpy()
    ret5 = np.full(len(B.t), np.nan); ret5[5:] = np.log(B.c[5:] / B.c[:-5]) * 1e4
    hr = ((B.t // 3600) % 24).astype(int); med = np.array([np.nanmedian(np.abs(ret5[(hr == h) & (B.t >= A) & (B.t < Z)])) for h in range(24)])
    sh = np.flatnonzero((B.t >= A) & (B.t < Z) & (np.abs(ret5) >= 5 * med[hr]))
    keep, last = [], 0
    for i in sh:
        if B.t[i] - last >= 1800: keep.append(i); last = B.t[i]
    ix = np.array(keep); t0 = B.t[ix] + 60
    has = np.array([((rel >= t - 600) & (rel <= t)).any() for t in t0]); sd = np.sign(ret5[ix]).astype(int)
    print("\n== S6 şok", len(ix), "haberli", int(has.sum()))
    c = []
    for h in (15, 60, 240):
        c += [{"name": f"S6 haberli devam {h}", "ts": t0[has].astype(float), "side": sd[has], "h": h}, {"name": f"S6 habersiz söndür {h}", "ts": t0[~has].astype(float), "side": -sd[~has], "h": h}]
    print(O.family(B, c, N=N).to_string(index=False))
    TOP = {"tarife_art": (r"\b(?:raises?|impose[sd]?|hikes?|new|additional)\b.{0,40}\btariffs?\b", -1), "tarife_anlas": (r"\b(?:tariff|trade)\b.{0,40}\b(?:pause|delay|deal|truce|exempt|agreement|reduce)", 1),
           "fed_guvercin": (r"\b(?:fed|powell|fomc)\b.{0,60}\b(?:rate cuts?|dovish|ease)\b", 1), "fed_sahin": (r"\b(?:fed|powell|fomc)\b.{0,60}\b(?:hawkish|higher for longer|no rush|rate hikes?)\b", -1)}
    c = []
    for k, (rx, sg) in TOP.items():
        x = nw[nw.text.str.contains(rx, case=False, regex=True)]; x = x[x.u.diff().fillna(1e9) >= 1800]
        for h in (15, 60, 240):
            c.append({"name": f"S8 {k} {h}", "ts": x.u.to_numpy().astype(float), "side": np.full(len(x), sg), "h": h})
    print("\n== S8"); print(O.family(B, c, N=N).to_string(index=False))

if __name__ == "__main__":
    main()
