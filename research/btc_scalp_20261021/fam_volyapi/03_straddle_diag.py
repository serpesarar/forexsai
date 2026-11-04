"""ST-H teşhisi (prereg §3 ST): NY 10:00 long+short, SL 1×ATR14(1h), çıkış NY 15:59 kapanışı.
(a) saat plasebosu (24 NY tam saat çapası, 6 s tutuş), (b) sentetik martingal (aynı ay × aynı NY dakika-of-gün içinde
göreli OHLC dörtlüsü karıştırma; 20 tekrar), (c) gün-blok bootstrap, (d) varyans oranı."""
import json
import warnings

import numpy as np
import pandas as pd

import common as C

warnings.simplefilter("ignore")
g = C.Grid()
COST = C.COSTS["PEP"]


def h1_atr(H, L, Cc):
    n1 = len(H) // 60
    h = np.nanmax(H[:n1 * 60].reshape(n1, 60), axis=1)
    l = np.nanmin(L[:n1 * 60].reshape(n1, 60), axis=1)
    c = pd.DataFrame(Cc[:n1 * 60].reshape(n1, 60)).ffill(axis=1).iloc[:, -1].to_numpy()
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    return pd.Series(tr).rolling(14, min_periods=10).mean().to_numpy()


def run(O, H, L, CF, atr1, anchors, hold, slip, bad=None):
    """Her çapa için L ve S: R (net, PEP), brüt R, stop bayrağı, stop sonrası kalan hareket (R)."""
    A = anchors[(anchors + hold < len(O))]
    W = A[:, None] + np.arange(hold)[None, :]
    if bad is not None:
        okb = ~bad[W].any(axis=1)
        A, W = A[okb], W[okb]
    a = atr1[A // 60 - 1]
    ent = O[A]
    ok = np.isfinite(a) & np.isfinite(ent) & (a > 0)
    A, W, a, ent = A[ok], W[ok], a[ok], ent[ok]
    s_bp = a / ent * 1e4
    out = {"A": A, "s_bp": s_bp}
    hw, lw, ow = H[W], L[W], O[W]
    xc = CF[W[:, -1]]
    for d, nm in ((1, "L"), (-1, "S")):
        sl = ent - d * a
        hitm = (lw <= sl[:, None]) if d == 1 else (hw >= sl[:, None])
        has = hitm.any(axis=1)
        k = hitm.argmax(axis=1)
        j = W[np.arange(len(A)), k]
        oj = ow[np.arange(len(A)), k]
        fill = np.minimum(sl, oj) if d == 1 else np.maximum(sl, oj)
        sl_bp = d * (fill / ent - 1) * 1e4 - slip[j]
        t_bp = d * (xc / ent - 1) * 1e4
        gb = np.where(has, sl_bp, t_bp)
        out[f"g_{nm}"] = gb / s_bp
        out[f"R_{nm}"] = (gb - COST) / s_bp
        out[f"stop_{nm}"] = has
        out[f"rem_{nm}"] = np.where(has, d * (xc - sl) / a, np.nan)  # stop sonrası pozisyon yönünde kalan
    return out


def split_of(A):
    return g.split[A]


def summarize(o, label):
    rows = []
    sp = split_of(o["A"])
    for spn in ("DISC", "OOS", "BLIND", "POST", "ALL"):
        mk = (sp != "") if spn == "ALL" else (((sp == "OOS") | (sp == "BLIND")) if spn == "POST" else sp == spn)
        if mk.sum() == 0:
            continue
        RL, RS = o["R_L"][mk], o["R_S"][mk]
        avg = (RL + RS) / 2
        day = o["A"][mk] // 1440
        p, lo, hi = C.day_boot(avg, day)
        rows.append({"cell": label, "split": spn, "n": int(mk.sum()), "R_L": RL.mean(), "R_S": RS.mean(),
                     "LS_avg": avg.mean(), "LS_ci_lo": lo, "LS_ci_hi": hi, "P_LS_gt0": p,
                     "g_L": o["g_L"][mk].mean(), "g_S": o["g_S"][mk].mean(),
                     "stop_L": o["stop_L"][mk].mean(), "stop_S": o["stop_S"][mk].mean(),
                     "rem_L": np.nanmean(o["rem_L"][mk]), "rem_S": np.nanmean(o["rem_S"][mk]),
                     "s_bp_med": float(np.median(o["s_bp"][mk]))})
    return rows


atr1 = h1_atr(g.H, g.L, g.C)
anch10 = np.where((g.ny_mod == 600) & (g.ny_wd < 5))[0]
# gerçek ST-H: 10:00 → 15:59 kapanışı (360 dk)
real = run(g.O, g.H, g.L, g.CF, atr1, anch10, 360, g.slip_bp, g.bad)
rows = summarize(real, "ST-H real 10:00")

# (a) saat plasebosu
hour_rows = []
for h in range(24):
    A = np.where((g.ny_mod == 60 * h) & (g.ny_wd < 5))[0]
    o = run(g.O, g.H, g.L, g.CF, atr1, A, 360, g.slip_bp, g.bad)
    for r_ in summarize(o, f"hour{h:02d}"):
        r_["hour"] = h
        hour_rows.append(r_)
hr = pd.DataFrame(hour_rows)

# (b) sentetik martingal
cprev = np.concatenate([[np.nan], g.CF[:-1]])
rat = np.vstack([g.O / cprev, g.H / cprev, g.L / cprev, g.C / cprev])
nanm = ~np.isfinite(rat).all(axis=0)
rat[:, nanm] = 1.0
rat[:, 0] = 1.0
ym = (g.year - 2021) * 12 + pd.DatetimeIndex(C.T0 + pd.to_timedelta(np.arange(g.N), unit="min")).month.to_numpy()
grpkey = ym * 1440 + g.ny_mod
orig = np.lexsort((np.arange(g.N), grpkey))
syn_rows = []
syn_hour = []
for rep in range(20):
    rng = np.random.default_rng(1000 + rep)
    shuf = np.lexsort((rng.random(g.N), grpkey))
    src = np.empty(g.N, dtype=np.int64)
    src[orig] = shuf
    rr = rat[:, src]
    c = g.CF[0] * np.cumprod(rr[3])
    cp = np.concatenate([[g.CF[0]], c[:-1]])
    o_, h_, l_ = cp * rr[0], cp * rr[1], cp * rr[2]
    h_ = np.maximum.reduce([h_, o_, c]); l_ = np.minimum.reduce([l_, o_, c])
    at = h1_atr(h_, l_, c)
    o = run(o_, h_, l_, c, at, anch10, 360, g.slip_bp, g.bad)
    for r_ in summarize(o, f"syn{rep:02d}"):
        syn_rows.append(r_)
syn = pd.DataFrame(syn_rows)

# (d) varyans oranı NY 10→16 (6 saatlik getiri vs saatlik bileşenler)
def vr(anchor_mod):
    A = np.where((g.ny_mod == anchor_mod) & (g.ny_wd < 5))[0]
    A = A[A + 361 < g.N]
    P = np.log(g.CF[A[:, None] - 1 + 60 * np.arange(7)[None, :]])
    r = np.diff(P, axis=1)
    ok = np.isfinite(r).all(axis=1)
    out = {}
    sp = g.split[A]
    for spn in ("DISC", "OOS", "BLIND", "POST"):
        mk = ok & ((((sp == "OOS") | (sp == "BLIND")) if spn == "POST" else sp == spn))
        rk = r[mk]
        v = np.var(rk.sum(axis=1), ddof=1) / np.var(rk, axis=0, ddof=1).sum()
        rng = np.random.default_rng(9)
        bs = []
        for _ in range(1000):
            ii = rng.integers(0, len(rk), len(rk))
            x = rk[ii]
            bs.append(np.var(x.sum(axis=1), ddof=1) / np.var(x, axis=0, ddof=1).sum())
        out[spn] = {"VR": float(v), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)), "n": int(mk.sum())}
    return out

vrs = {f"{h:02d}:00": vr(60 * h) for h in range(24)}

pd.DataFrame(rows).to_csv(f"{C.RES}/st_h_real.csv", index=False)
hr.to_csv(f"{C.RES}/st_h_hours.csv", index=False)
syn.to_csv(f"{C.RES}/st_h_synth.csv", index=False)
json.dump(vrs, open(f"{C.RES}/st_h_vr.json", "w"), indent=1)
print(pd.DataFrame(rows).round(3).to_string())
for spn in ("DISC", "OOS", "BLIND", "POST", "ALL"):
    s = hr[hr.split == spn].sort_values("LS_avg", ascending=False).reset_index(drop=True)
    rk = int(np.where(s.hour == 10)[0][0]) + 1
    ss = syn[syn.split == spn]
    print(f"{spn}: 10:00 saat-plasebo sırası {rk}/24, (L+S)/2 ={s[s.hour==10].LS_avg.values[0]:+.3f}; "
          f"24 saat medyanı {s.LS_avg.median():+.3f}; sentetik ort {ss.LS_avg.mean():+.3f} [min {ss.LS_avg.min():+.3f}, maks {ss.LS_avg.max():+.3f}]")
print(json.dumps({k: vrs[k] for k in ("10:00", "02:00", "20:00")}, indent=1))
