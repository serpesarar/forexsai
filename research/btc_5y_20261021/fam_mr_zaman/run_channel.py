"""CH — kanal-sınır dönüşü (CHREV portu), 32 birincil hücre + tanılar. Ön-kayıt: prereg.md §3 CH."""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

import common as c

NCH = 50
ZT = 2.0
rng = np.random.default_rng(31)
YEARD = np.array([(c.T0 + pd.Timedelta(days=int(i))).year for i in range(c.N // 1440 + 2)])


def load_tf(tf: str, tfm: int):
    b = pd.read_parquet(f"{c.DATA}/btc_{tf}.parquet", columns=["ts", "open", "high", "low", "close"])
    ts = ((b["ts"] - c.T0) / pd.Timedelta(minutes=1)).to_numpy().astype(np.int64)
    o, h, l, cl = (b[k].to_numpy() for k in ["open", "high", "low", "close"])
    nb = len(cl)
    # linreg pencereleri (bitiş indeksi j için j-49..j)
    W = swv(cl, NCH)
    xc = np.arange(NCH) - (NCH - 1) / 2
    a = W @ xc / (xc ** 2).sum()
    yb = W.mean(1)
    res = W - (yb[:, None] + a[:, None] * xc[None, :])
    sd = np.sqrt((res ** 2).mean(1))
    fit_last = np.full(nb, np.nan); fit_last[NCH - 1:] = yb + a * xc[-1]
    fit_next = np.full(nb, np.nan); fit_next[NCH - 1:] = yb + a * (xc[-1] + 1)
    SD = np.full(nb, np.nan); SD[NCH - 1:] = sd
    A = np.full(nb, np.nan); A[NCH - 1:] = a
    pc = np.concatenate([[np.nan], cl[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    atr = pd.Series(tr).rolling(14).mean().to_numpy()
    # Wilder ADX14
    up = h - np.concatenate([[np.nan], h[:-1]])
    dn = np.concatenate([[np.nan], l[:-1]]) - l
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    rma = lambda x: pd.Series(x).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    atrw = rma(np.nan_to_num(tr))
    pdi = 100 * rma(pdm) / atrw
    ndi = 100 * rma(ndm) / atrw
    dx = 100 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-9)
    adx = rma(dx)
    adx[:30] = np.nan
    # geçerlilik: 51 bar kesintisiz ve kötü dakika içermez
    valid = np.zeros(nb, bool)
    j = np.arange(NCH + 1, nb)
    contig = (ts[j] - ts[j - NCH]) == NCH * tfm
    clean = (c.BAD_CS[np.minimum(ts[j] + tfm, c.N)] - c.BAD_CS[ts[j - NCH]]) == 0
    valid[j] = contig & clean & np.isfinite(atr[j])
    dec = ts + tfm  # karar anı = bar kapanışı
    valid &= dec < c.N - 5
    return dict(ts=ts, o=o, h=h, l=l, c=cl, z=(cl - fit_last) / SD, mid_cz=fit_last, mid_rj_raw=fit_next,
                sd=SD, slope_atr=A / atr, atr=atr, adx=adx, valid=valid, dec=dec, tfm=tfm)


def triggers(B, trig: str, d: int, zt: float = ZT):
    cl, l, h = B["c"], B["l"], B["h"]
    if trig == "CZ":
        cond = (B["z"] <= -zt) if d == 1 else (B["z"] >= zt)
        mid = B["mid_cz"]
    else:
        # kanal t-1'de biten pencereden t'ye uzatılmış
        midx = np.concatenate([[np.nan], B["mid_rj_raw"][:-1]])
        sdp = np.concatenate([[np.nan], B["sd"][:-1]])
        rng_ = np.maximum(h - l, 1e-9)
        if d == 1:
            band = midx - zt * sdp
            cond = (l <= band) & (cl > band) & ((cl - l) >= 0.5 * rng_)
        else:
            band = midx + zt * sdp
            cond = (h >= band) & (cl < band) & ((h - cl) >= 0.5 * rng_)
        mid = midx
    cond = np.nan_to_num(cond, nan=0).astype(bool)
    prev = np.concatenate([[False], cond[:-1]])
    ev = cond & ~prev & B["valid"]
    return np.where(ev)[0], mid


def geom(B, idx, g: str, d: int, mid=None, mid_ratio=None):
    cl, atr, tfm = B["c"][idx], B["atr"][idx], B["tfm"]
    n = len(idx)
    if g == "Gbot":
        return 0.0149 * cl, 0.0104 * cl, np.full(n, 1440)
    if g == "Gatr":
        return 1.5 * atr, 1.0 * atr, np.full(n, 48 * tfm)
    if g == "Gtime":
        return 1.5 * atr, np.full(n, np.inf), np.full(n, 12 * tfm)
    if g == "Gmid":
        tpd = d * (mid[idx] - cl) if mid_ratio is None else mid_ratio * atr
        return 1.5 * atr, tpd, np.full(n, 48 * tfm)


def run_events(B, idx, d, g, mid=None, mid_ratio=None, **kw):
    D, T, cap = geom(B, idx, g, d, mid, mid_ratio)
    out = c.bracket_trades(B["dec"][idx], d, D, T, cap, dec_close=B["c"][idx], **kw)
    out["bi"] = idx
    return out


def placebo(B, ev_idx, ev_per, pool_df, actual: pd.DataFrame):
    """aynı yıl × UTC saati havuzundan rastgele bar kapanışı; 200 tekrar."""
    dec = B["dec"]
    dp = dec[pool_df["bi"].to_numpy()]
    key_pool = YEARD[dp // 1440] * 24 + (dp // 60) % 24
    Rp = pool_df["R"].to_numpy()
    okp = np.isfinite(Rp)
    key_pool, Rp = key_pool[okp], Rp[okp]
    key_ev = YEARD[dec[ev_idx] // 1440] * 24 + (dec[ev_idx] // 60) % 24
    sums = {k: np.zeros(c.N_PLAC) for k in ["TAM", *c.PERIODS]}
    cnt = {k: 0 for k in sums}
    o = np.argsort(key_pool)
    kp, Rs = key_pool[o], Rp[o]
    for k in np.unique(key_ev):
        m = key_ev == k
        lo, hi = np.searchsorted(kp, k), np.searchsorted(kp, k, side="right")
        if hi <= lo:
            continue
        dr = Rs[lo + rng.integers(0, hi - lo, size=(c.N_PLAC, m.sum()))]
        sums["TAM"] += dr.sum(1); cnt["TAM"] += m.sum()
        pm = ev_per[m]
        for p in c.PERIODS:
            mm = pm == p
            if mm.any():
                sums[p] += dr[:, mm].sum(1); cnt[p] += mm.sum()
    pp = {}
    for k in sums:
        act = actual["R"].mean() if k == "TAM" else actual.loc[actual["per"] == k, "R"].mean()
        pp[k] = c.plac_percentile(act, sums[k] / max(cnt[k], 1))
        pp[k + "_mean"] = float((sums[k] / max(cnt[k], 1)).mean())
    return pp


def baseline(pool_df):
    p = pool_df[np.isfinite(pool_df["R"])]
    per = c.period_of(p["t"].to_numpy())
    out = {"base_TAM": p["R"][per != ""].mean()}
    for k in c.PERIODS:
        out[f"base_{k}"] = p["R"][per == k].mean()
    return out


def main():
    rows, diag = [], []
    for tf, tfm in (("15m", 15), ("1h", 60)):
        B = load_tf(tf, tfm)
        pool_all = np.where(B["valid"])[0]
        pools = {}
        for d in (1, -1):
            for g in ("Gbot", "Gatr", "Gtime"):
                pools[(d, g)] = run_events(B, pool_all, d, g)
                print(tf, d, g, "havuz", flush=True)
        for trig in ("CZ", "RJ"):
            for d in (1, -1):
                ev, mid = triggers(B, trig, d)
                for g in ("Gbot", "Gatr", "Gtime", "Gmid"):
                    if g == "Gmid":
                        D, T, _ = geom(B, ev, g, d, mid)
                        keep = np.isfinite(T) & (T >= 0.25 * B["atr"][ev])
                        e2 = ev[keep]
                        real = run_events(B, e2, d, g, mid)
                        ratio = float(np.median(T[keep] / B["atr"][e2]))
                        pool = run_events(B, pool_all, d, g, mid_ratio=ratio)
                    else:
                        e2 = ev
                        pool = pools[(d, g)]
                        pos = np.searchsorted(pool_all, e2)
                        real = pool.iloc[pos].reset_index(drop=True)
                        ratio = np.nan
                    stress = run_events(B, e2, d, g, mid, s_frac=c.S_STRESS)
                    opt = run_events(B, e2, d, g, mid, optimistic=True)
                    a15 = run_events(B, e2, d, g, mid, s_abs=c.S_ABS)
                    frames = []
                    for df in (real, stress, opt, a15):
                        df = df[np.isfinite(df["R"])].copy()
                        df["per"] = c.period_of(df["t"].to_numpy())
                        frames.append(df[df["per"] != ""])
                    real, stress, opt, a15 = frames
                    ks = set(real["t"])
                    stress, opt, a15 = (f[f["t"].isin(ks)] for f in (stress, opt, a15))
                    ev_idx = real["bi"].to_numpy()
                    pp = placebo(B, ev_idx, real["per"].to_numpy(), pool, real)
                    name = f"CH_{tf}_{trig}_{'L' if d == 1 else 'S'}_{g}"
                    extra = {"fam": "CH", "dir": d, "mid_ratio": ratio, **baseline(pool),
                             "tp_frac": (real["kind"] == 1).mean(), "sl_frac": (real["kind"] == -1).mean()}
                    row = c.card_row(name, real, stress, opt, a15, pp, extra)
                    rows.append(row)
                    print(name, row["n"], round(row["meanR"], 4), round(row.get("KESIF_t", np.nan), 2),
                          row["card_pass"], flush=True)
                    # tanı: ADX<25 × eğim yönü, zt=2.5 (yalnız bilgi)
                    adx_lo = B["adx"][ev_idx] < 25
                    slope_ok = (B["slope_atr"][ev_idx] * d) >= 0
                    for a_ in (True, False):
                        for s_ in (True, False):
                            m = (adx_lo == a_) & (slope_ok == s_)
                            sub = real[m]
                            dd = {"cell": name, "diag": f"ADX<25={a_},egim_lehte={s_}", "n": len(sub),
                                  "meanR": sub["R"].mean()}
                            for p in c.PERIODS:
                                dd[f"{p}_meanR"] = sub.loc[sub["per"] == p, "R"].mean()
                                dd[f"{p}_n"] = int((sub["per"] == p).sum())
                            diag.append(dd)
                    if g != "Gmid":
                        ev25, _ = triggers(B, trig, d, zt=2.5)
                        pos = np.searchsorted(pool_all, ev25)
                        okk = (pos < len(pool_all)) & (pool_all[np.minimum(pos, len(pool_all) - 1)] == ev25)
                        sub = pool.iloc[pos[okk]].copy()
                        sub = sub[np.isfinite(sub["R"])]
                        sub["per"] = c.period_of(sub["t"].to_numpy())
                        dd = {"cell": name, "diag": "zt=2.5", "n": int((sub["per"] != "").sum()),
                              "meanR": sub.loc[sub["per"] != "", "R"].mean()}
                        for p in c.PERIODS:
                            dd[f"{p}_meanR"] = sub.loc[sub["per"] == p, "R"].mean()
                            dd[f"{p}_n"] = int((sub["per"] == p).sum())
                        diag.append(dd)
    pd.DataFrame(rows).to_csv(f"{c.OUT}/channel_cells.csv", index=False)
    pd.DataFrame(diag).to_csv(f"{c.OUT}/channel_diag.csv", index=False)
    print("bitti")


if __name__ == "__main__":
    main()
