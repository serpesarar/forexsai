"""Zaman alt-aileleri: Q (21-23 UTC), HOD, DOW/WE, USC (+H12), FUND (H10), TOC (H11). Ön-kayıt: prereg.md."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import common as c

NDAY = c.N // 1440
DAYS = np.arange(NDAY)
D0 = DAYS * 1440
DOW_ = ((pd.Timestamp(c.T0).dayofweek + DAYS) % 7)  # 0=Pzt
YEAR = np.array([(c.T0 + pd.Timedelta(days=int(d))).year for d in DAYS])
rng = np.random.default_rng(7)


def run_cell(name, t, x, direction, swap=True, placebo="hour", fam=""):
    t = np.asarray(t, np.int64)
    x = np.asarray(x, np.int64)
    real = c.window_trades(t, x, direction, swap=swap)
    stress = c.window_trades(t, x, direction, s_frac=c.S_STRESS, swap=swap)
    opt = c.window_trades(t, x, direction, swap=swap, optimistic=True)
    a15 = c.window_trades(t, x, direction, s_abs=c.S_ABS, swap=swap)
    for d in (real, stress, opt, a15):
        d["per"] = c.period_of(d["t"].to_numpy())
    real = real[real["per"] != ""]
    keep = set(real["t"])
    stress, opt, a15 = (d[d["t"].isin(keep)] for d in (stress, opt, a15))
    # plasebo
    tt, xx = real["t"].to_numpy(), real["x"].to_numpy()
    tx = x[np.searchsorted(t, tt)] if np.all(np.diff(t) > 0) else None
    L = (tx - tt) if tx is not None else (xx - tt)
    n = len(tt)
    per = real["per"].to_numpy()
    sums = {k: np.zeros(c.N_PLAC) for k in ["TAM", *c.PERIODS]}
    cnts = {k: np.zeros(c.N_PLAC) for k in ["TAM", *c.PERIODS]}
    nd = c.N_PLAC if placebo != "minute" else 1
    loops = 1 if placebo != "minute" else c.N_PLAC
    for lp in range(loops):
        if placebo == "hour":
            hh = rng.integers(0, 24, size=(nd, n))
            tp = (tt // 1440 * 1440)[None, :] + hh * 60 + (tt % 60)[None, :]
        elif placebo == "day":
            yrs = YEAR[tt // 1440]
            tp = np.empty((nd, n), np.int64)
            for y in np.unique(yrs):
                pool = DAYS[(YEAR == y) & (DAYS * 1440 + L.max() < c.N)]
                mk = yrs == y
                tp[:, mk] = pool[rng.integers(0, len(pool), size=(nd, mk.sum()))] * 1440 + (tt[mk] % 1440)[None, :]
        elif placebo == "minute":
            tp = (tt // 60 * 60 + rng.integers(0, 60, size=n))[None, :]
        xp = tp + L[None, :]
        pr = c.window_trades(tp.ravel(), np.minimum(xp.ravel(), c.N - 1), direction, swap=swap)
        di = pr.index.to_numpy() // n + lp
        ei = pr.index.to_numpy() % n
        Rv = pr["R"].to_numpy()
        for k in sums:
            mk = np.ones(len(ei), bool) if k == "TAM" else per[ei] == k
            sums[k] += np.bincount(di[mk], weights=Rv[mk], minlength=c.N_PLAC)[:c.N_PLAC]
            cnts[k] += np.bincount(di[mk], minlength=c.N_PLAC)[:c.N_PLAC]
    pp = {}
    for k in sums:
        act = real["R"].mean() if k == "TAM" else real.loc[real["per"] == k, "R"].mean()
        with np.errstate(invalid="ignore", divide="ignore"):
            pp[k] = c.plac_percentile(act, sums[k] / cnts[k])
        pp[k + "_mean"] = float(np.nanmean(sums[k] / cnts[k]))
    row = c.card_row(name, real, stress, opt, a15, pp, {"fam": fam, "dir": direction})
    return row, real


def build_cells():
    cells = []  # (name, fam, t, x, dir, swap, placebo)
    dst = c.DAY_DST
    # --- Q
    t21 = D0 + 21 * 60
    x23 = D0 + 22 * 60 + 59
    roll = c.ROLL[:NDAY]
    cells.append(("Q_A_swap_L", "Q", t21, x23, 1, True, "hour"))
    cells.append(("Q_A_noswap_L", "Q", t21, x23, 1, False, "hour"))
    cells.append(("Q_B_postroll_L", "Q", roll + 1, x23, 1, True, "hour"))
    xc = np.where((roll > t21) & (roll <= x23 + 1), roll - 2, x23)
    cells.append(("Q_C_preexit_L", "Q", t21, xc, 1, True, "hour"))
    # --- HOD
    for h in range(24):
        for d, s in ((1, "L"), (-1, "S")):
            cells.append((f"HOD_{h:02d}_{s}", "HOD", D0 + h * 60, D0 + h * 60 + 59, d, True, "hour"))
    # --- DOW
    names = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]
    for k in range(7):
        dd = DAYS[DOW_ == k]
        for d, s in ((1, "L"), (-1, "S")):
            cells.append((f"DOW_{names[k]}_{s}", "DOW", dd * 1440, dd * 1440 + 1439, d, True, "day"))
    sat = DAYS[(DOW_ == 5) & (DAYS + 2 < NDAY)]
    for d, s in ((1, "L"), (-1, "S")):
        cells.append((f"WE_CmtPaz_{s}", "DOW", sat * 1440, sat * 1440 + 2 * 1440 - 1, d, True, "day"))
    # --- USC (hafta içi NY 09:30-16:00)
    wd = DAYS[DOW_ < 5]
    off = np.where(dst[wd], 13 * 60 + 30, 14 * 60 + 30)
    for d, s in ((1, "L"), (-1, "S")):
        cells.append((f"USC_{s}", "USC", wd * 1440 + off, wd * 1440 + off + 389, d, True, "hour"))
    # --- FUND
    for h in (0, 8, 16):
        st = D0 + h * 60 - 15
        st, ok = st[st >= 61], None
        for d, s in ((1, "L"), (-1, "S")):
            cells.append((f"FUND_{h:02d}_{s}", "FUND", st, st + 29, d, True, "hour"))
    # --- TOC
    mins = np.arange(61, c.N)
    mins = mins[mins % 15 == 0]
    for d, s in ((1, "L"), (-1, "S")):
        cells.append((f"TOC_{s}", "TOC", mins, mins, d, True, "minute"))
    return cells


def hod_maxz(n_rep=500):
    """KEŞİF günlerinde 48 HOD hücresinin max t'si için dairesel kaydırma boş dağılımı."""
    a, b = c.PER_BOUNDS["KESIF"]
    dd = DAYS[(D0 >= a) & (D0 + 1440 <= b)]
    M = {}
    for d in (1, -1):
        m = np.full((len(dd), 24), np.nan)
        for h in range(24):
            w = c.window_trades(dd * 1440 + h * 60, dd * 1440 + h * 60 + 59, d)
            pos = np.searchsorted(dd * 1440 + h * 60, w["t"].to_numpy())
            m[pos, h] = w["R"].to_numpy()
        M[d] = m

    def tstat(m):
        n = np.isfinite(m).sum(0)
        mu = np.nanmean(m, 0)
        sd = np.nanstd(m, 0, ddof=1)
        return mu / (sd / np.sqrt(n))
    obs = np.concatenate([tstat(M[1]), tstat(M[-1])])
    r = np.random.default_rng(99)
    null = np.empty(n_rep)
    rows = np.arange(len(dd))[:, None]
    for i in range(n_rep):
        k = r.integers(0, 24, size=len(dd))
        cols = (np.arange(24)[None, :] + k[:, None]) % 24
        null[i] = max(np.nanmax(tstat(M[1][rows, cols])), np.nanmax(tstat(M[-1][rows, cols])))
    names = [f"HOD_{h:02d}_L" for h in range(24)] + [f"HOD_{h:02d}_S" for h in range(24)]
    p = {nm: float((null >= o).mean()) for nm, o in zip(names, obs)}
    return p, float(np.percentile(null, 95))


def dow_maxz(n_rep=500):
    a, b = c.PER_BOUNDS["KESIF"]
    mon = DAYS[(DOW_ == 0) & (D0 >= a) & (D0 + 7 * 1440 <= b)]
    M = {}
    for d in (1, -1):
        m = np.full((len(mon), 7), np.nan)
        for k in range(7):
            w = c.window_trades((mon + k) * 1440, (mon + k) * 1440 + 1439, d)
            pos = np.searchsorted((mon + k) * 1440, w["t"].to_numpy())
            m[pos, k] = w["R"].to_numpy()
        M[d] = m

    def tstat(m):
        n = np.isfinite(m).sum(0)
        return np.nanmean(m, 0) / (np.nanstd(m, 0, ddof=1) / np.sqrt(n))
    names = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]
    obs = np.concatenate([tstat(M[1]), tstat(M[-1])])
    r = np.random.default_rng(98)
    rows = np.arange(len(mon))[:, None]
    null = np.empty(n_rep)
    for i in range(n_rep):
        k = r.integers(0, 7, size=len(mon))
        cols = (np.arange(7)[None, :] + k[:, None]) % 7
        null[i] = max(np.nanmax(tstat(M[1][rows, cols])), np.nanmax(tstat(M[-1][rows, cols])))
    nm = [f"DOW_{x}_L" for x in names] + [f"DOW_{x}_S" for x in names]
    return {a_: float((null >= o).mean()) for a_, o in zip(nm, obs)}


def h12():
    f = pd.read_parquet(f"{c.DATA}/btc_5m.parquet", columns=["ts", "close"])
    f["r"] = np.log(f["close"]).diff().abs()
    f = f.iloc[1:]
    f["day"] = f["ts"].dt.floor("D")
    mod = f["ts"].dt.hour * 60 + f["ts"].dt.minute
    f["us"] = (mod >= 13 * 60 + 30) & (mod < 21 * 60)
    g = f.groupby("day").apply(lambda x: x.loc[x["us"], "r"].sum() / x["r"].sum(), include_groups=False)
    g = g[g.index.dayofweek < 5]
    pre = g[(g.index >= "2022-01-01") & (g.index < "2024-01-01")].to_numpy()
    post = g[g.index >= "2024-01-11"].to_numpy()
    r = np.random.default_rng(5)
    bs = np.array([r.choice(post, len(post)).mean() - r.choice(pre, len(pre)).mean() for _ in range(5000)])
    yr = g.groupby(g.index.year).mean().round(4).to_dict()
    return {"pre_mean": float(pre.mean()), "post_mean": float(post.mean()),
            "diff_pp": float((post.mean() - pre.mean()) * 100),
            "ci95_pp": [float(np.percentile(bs, 2.5) * 100), float(np.percentile(bs, 97.5) * 100)],
            "n_pre": len(pre), "n_post": len(post), "uniform_share": 7.5 / 24,
            "by_year": {str(k): v for k, v in yr.items()}}


def fund_kill():
    """24 saatin merkezli 30 dk penceresi brüt getirisi (bp, mid, maliyetsiz) — TAM ve dönemler."""
    out = []
    for h in range(24):
        st = D0 + h * 60 - 15
        st = st[st >= 61]
        e = c.NXT[st]
        x = c.PRV[st + 29]
        ok = (e - st <= 10) & (x >= e) & ~c.bad_in(e, np.maximum(x, e))
        g = (c.C[x[ok]] / c.O[e[ok]] - 1) * 1e4
        per = c.period_of(st[ok])
        row = {"hour": h, "n": len(g), "mean_bp": g.mean(), "t": g.mean() / (g.std(ddof=1) / np.sqrt(len(g))),
               "mean_abs_bp": np.abs(g).mean()}
        for k in c.PERIODS:
            gg = g[per == k]
            row[f"{k}_bp"] = gg.mean()
            row[f"{k}_t"] = gg.mean() / (gg.std(ddof=1) / np.sqrt(len(gg)))
        out.append(row)
    d = pd.DataFrame(out)
    d["p2"] = [2 * c.norm_sf(abs(z)) for z in d["t"]]
    d["p_bonf"] = np.minimum(1, d["p2"] * 24)
    return d


def toc_gross():
    m = np.arange(61, c.N)
    ok = c.TRAD[m]
    m = m[ok]
    g = (c.C[m] / c.O[m] - 1) * 1e4
    turn = (m % 15) == 0
    yr = YEAR[m // 1440]
    rows = []
    for y in np.unique(yr):
        k = yr == y
        rows.append({"year": int(y), "turn_bp": g[k & turn].mean(), "other_bp": g[k & ~turn].mean(),
                     "n_turn": int((k & turn).sum())})
    rows.append({"year": 0, "turn_bp": g[turn].mean(), "other_bp": g[~turn].mean(), "n_turn": int(turn.sum())})
    return pd.DataFrame(rows)


def q_subreports(real: pd.DataFrame, name: str):
    d = real.copy()
    day = d["t"].to_numpy() // 1440
    d["dow"] = DOW_[day]
    d["dst"] = c.DAY_DST[day]
    d["year"] = YEAR[day]
    rows = []
    for lab, mk in [("Pzt-Cum", d["dow"] < 5), ("Cmt-Paz", d["dow"] >= 5), ("yaz(DST)", d["dst"]),
                    ("kis", ~d["dst"]), ("ETF-oncesi", d["t"] < c.tmin("2024-01-11")),
                    ("ETF-sonrasi", d["t"] >= c.tmin("2024-01-11"))] + \
                   [(str(y), d["year"] == y) for y in sorted(d["year"].unique())]:
        s = d[mk]
        P, _ = c.boot_day(s["t"].to_numpy(), s["R"].to_numpy())
        rows.append({"cell": name, "sub": lab, "n": len(s), "meanR": s["R"].mean(), "bp": s["bp"].mean(),
                     "wr": (s["R"] > 0).mean(), "P": P})
    return rows


def main():
    cells = build_cells()
    rows, qsub = [], []
    for (name, fam, t, x, d, sw, pl) in cells:
        row, real = run_cell(name, t, x, d, swap=sw, placebo=pl, fam=fam)
        rows.append(row)
        if fam == "Q":
            qsub += q_subreports(real, name)
        print(name, row["n"], round(row["meanR"], 4), round(row["bp"], 2), row.get("KESIF_t"), row["card_pass"],
              flush=True)
    df = pd.DataFrame(rows)
    hp, hcrit = hod_maxz()
    dp = dow_maxz()
    df["maxz_p"] = df["cell"].map({**hp, **dp})
    df.to_csv(f"{c.OUT}/timing_cells.csv", index=False)
    pd.DataFrame(qsub).to_csv(f"{c.OUT}/q_subreports.csv", index=False)
    fk = fund_kill()
    fk.to_csv(f"{c.OUT}/fund_kill_24h.csv", index=False)
    toc_gross().to_csv(f"{c.OUT}/toc_gross_by_year.csv", index=False)
    with open(f"{c.OUT}/h12_us_share.json", "w") as f:
        json.dump({**h12(), "hod_maxz_t95": hcrit}, f, indent=1)
    print("bitti")


if __name__ == "__main__":
    main()
