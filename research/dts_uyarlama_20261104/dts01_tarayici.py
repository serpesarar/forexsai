"""DTS-01 — repo tarayıcısının 5 kurulumu × 4 sembol × {1h, 4h, 1d} × h {1,5,10}. Ön-kayıt: PROTOCOL.md."""
import json, math, zlib
from multiprocessing import Pool
import numpy as np
import pandas as pd
from common import SYMS, SPREAD, load, month_boot, clusters

TFS, HS = ("1h", "4h", "1d"), (1, 5, 10)
SETUPS = ("breakout_20d", "bull_flag", "reclaim_ma20", "oversold", "oversold_bounce")


def wilder_rsi(c: np.ndarray, n: int = 14) -> np.ndarray:
    d = np.diff(c, prepend=c[0]); g, l = np.maximum(d, 0), np.maximum(-d, 0)
    out = np.full(len(c), np.nan); ag = al = None
    for i in range(1, len(c)):
        if i == n:
            ag, al = g[1:n + 1].mean(), l[1:n + 1].mean()
        elif i > n:
            ag, al = (ag * (n - 1) + g[i]) / n, (al * (n - 1) + l[i]) / n
        if i >= n:
            out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def setups(c: np.ndarray) -> dict:
    s = pd.Series(c)
    hi20 = s.shift(1).rolling(20).max().to_numpy()
    ma20 = s.rolling(20).mean().to_numpy(); ma20p = np.r_[np.nan, ma20[:-1]]
    run = s.shift(5) / s.shift(15) - 1
    rng5 = (s.rolling(5).max() - s.rolling(5).min()) / s
    r = wilder_rsi(c); rp = np.r_[np.nan, r[:-1]]; cp = np.r_[np.nan, c[:-1]]
    ok = np.arange(len(c)) >= 30
    return {"breakout_20d": ok & (c > hi20), "bull_flag": ok & (run.to_numpy() > 0.10) & (rng5.to_numpy() < 0.05),
            "reclaim_ma20": ok & (cp < ma20p) & (c > ma20), "oversold": ok & (r < 30),
            "oversold_bounce": ok & (rp < 30) & (c > cp)}


def run(arg):
    sym, tf = arg
    d = load(sym, tf); c, o = d.close.to_numpy(), d.open.to_numpy(); n = len(c)
    months = d.ts.dt.strftime("%Y-%m").to_numpy(); mid = d.ts.iloc[n // 2]
    first = (d.ts < mid).to_numpy(); sig = setups(c); sp = SPREAD[sym]; rows = []
    for h in HS:
        fwd = np.full(n, np.nan); valid = np.arange(n) + h < n
        e = np.r_[o[1:], np.nan] + sp
        fwd[valid] = 1e4 * (c[np.arange(n)[valid] + h] / e[valid] - 1)        # bp, spreadli, giriş t+1 açılış
        base = np.nanmean(fwd)
        for st in SETUPS:
            m = sig[st] & np.isfinite(fwd); k = np.flatnonzero(m)
            ex = fwd[k] - base
            lab = clusters(k, h)
            ep = pd.Series(ex).groupby(lab).mean().to_numpy() if len(k) else np.array([])
            seed = zlib.crc32(f"{sym}|{tf}|{h}|{st}".encode())
            rows.append({"sym": sym, "tf": tf, "h": h, "setup": st, "n": int(len(k)), "olay": int(len(ep)),
                         "net_bp": float(np.mean(fwd[k])) if len(k) else math.nan, "fazla_bp": float(np.mean(ex)) if len(k) else math.nan,
                         "P": month_boot(ex, months[k], seed) if len(k) else math.nan,
                         "y1": float(np.mean(ex[first[k]])) if first[k].any() else math.nan,
                         "y2": float(np.mean(ex[~first[k]])) if (~first[k]).any() else math.nan,
                         "olay_medyan": float(np.median(ep)) if len(ep) else math.nan})
    return rows


def main():
    with Pool(6) as p:
        rows = sum(p.map(run, [(s, t) for s in SYMS for t in TFS]), [])
    df = pd.DataFrame(rows)
    df["gecti"] = (df.fazla_bp > 0) & (df.P >= 0.975) & (df.y1 > 0) & (df.y2 > 0) & (df.olay >= 30) & (df.net_bp > 0)
    df["ters"] = (df.P <= 0.025) & (df.olay >= 30)
    df["bonf"] = df.gecti & (df.P >= 1 - 0.025 / 180)
    df.to_csv("dts01_hucreler.csv", index=False)
    k = int(df.gecti.sum()); N = len(df)
    pbin = sum(math.comb(N, j) * 0.025 ** j * 0.975 ** (N - j) for j in range(k, N + 1))
    rep = df[df.gecti].groupby(["setup", "tf", "h"]).sym.nunique()
    out = {"hucre": N, "gecen": k, "ters_anlamli": int(df.ters.sum()), "bonferroni": int(df.bonf.sum()), "binom_p": pbin,
           "iki_sembolde_tekrar": {f"{a}|{b}|{c}": int(v) for (a, b, c), v in rep.items() if v >= 2}}
    json.dump(out, open("dts01_ozet.json", "w"), indent=1)
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 300)
    print(json.dumps(out, indent=1))
    print(df[df.gecti | df.ters].round(3).to_string(index=False))
    print(df.groupby(["setup", "tf"]).apply(lambda g: pd.Series({"ort_fazla_bp": g.fazla_bp.mean(), "pozitif_hucre": int((g.fazla_bp > 0).sum()), "hucre": len(g)})).round(2).to_string())


if __name__ == "__main__":
    main()
