"""PROTOCOL.md hüküm koşucusu: 8 birincil hipotez + keşif ızgarası (seçim düzeltmeli) + seçilen hücre TEST'i + tanılar."""
from __future__ import annotations

import itertools
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import engine as E  # noqa: E402

S_GRID, W_GRID, K_GRID = (0.4, 0.5, 0.6), (0.3, 0.5, 0.8), (0, 1, 2, 3)
N_MIN = 40
N_PERM = 200
SIDE_NAME = {0: "üst fitil→SAT", 1: "alt fitil→AL"}
PRIMARY = [("H1", 60, 0, 0), ("H2", 60, 1, 0), ("H3", 240, 0, 0), ("H4", 240, 1, 0),
           ("H5", 60, 0, 2), ("H6", 60, 1, 2), ("H7", 240, 0, 2), ("H8", 240, 1, 2)]
P_CELL = dict(s=0.5, w=0.5, di=E.DELAYS.index(5), si=0, ti=E.TPS.index(1.0))


def boot(r: np.ndarray, days: np.ndarray, n: int = 5000, seed: int = 7) -> float:
    """Gün-blok bootstrap P(EV>0)."""
    if len(r) == 0:
        return np.nan
    u, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=r, minlength=len(u))
    c = np.bincount(inv, minlength=len(u)).astype(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(u), size=(n, len(u)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return float((m > 0).mean())


def hour_base(Rcol: np.ndarray, hours: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Her mum için aynı saatte TÜM mumların ort. R'si (taban)."""
    out = np.full(len(Rcol), np.nan)
    for h in np.unique(hours):
        m = (hours == h) & valid & np.isfinite(Rcol)
        if m.any():
            out[hours == h] = Rcol[m].mean()
    return out


def trades(B: E.Base, F: pd.DataFrame, T: np.ndarray, mask: np.ndarray, side: int, di: int, si: int, ti: int,
           tf: int, mirror: bool = False, single: bool = False) -> pd.DataFrame:
    rows, busy = [], -1
    hold = E.HOLD[tf] * tf
    for bi in np.flatnonzero(mask):
        e = T[bi, di]
        if e < 0:
            continue
        if single and e <= busy:
            continue
        px = B.o[e] if side == 0 else B.o[e] + B.spo[e]
        d = E.sl_dist(F, bi, side, si, px)
        if not d > 0:
            continue
        sd = 1 - side if mirror else side
        r, x = E.simulate_one(B, e, sd, d, E.TPS[ti], hold)
        busy = x
        rows.append({"bi": bi, "e": e, "R": r, "day": F.day.iat[bi], "hour": F.hour.iat[bi], "year": F.year.iat[bi],
                     "ny_min": F.ny_min.iat[bi], "kesif": F.kesif.iat[bi]})
    return pd.DataFrame(rows)


def summarize(x: pd.DataFrame, base: np.ndarray | None = None) -> dict:
    if len(x) == 0:
        return {"n": 0}
    out = {"n": len(x), "ort_R": round(x.R.mean(), 4), "P": round(boot(x.R.to_numpy(), x.day.to_numpy()), 3),
           "isabet": round((x.R > 0).mean(), 3), "gun": int(x.day.nunique())}
    if base is not None:
        out["taban"] = round(float(np.nanmean(base[x.bi.to_numpy()])), 4)
        out["fark"] = round(out["ort_R"] - out["taban"], 4)
    return out


def grid_cols():
    return list(itertools.product(range(len(E.DELAYS)), range(len(E.SL_MODES)), range(len(E.TPS))))


def grid_t(F: pd.DataFrame, Rm: np.ndarray, side: int, sel: np.ndarray, perm: np.ndarray | None = None):
    """sel alt kümesinde 36 maske × 100 sütun için fark t-istatistiği. perm: özellik satırlarının yeni sırası."""
    cols = grid_cols()
    hours = F.hour.to_numpy()
    X = np.stack([Rm[:, side, di, si, ti] for di, si, ti in cols], 1)[sel]       # N × 100
    h = hours[sel]
    base = np.full_like(X, np.nan)
    for hh in np.unique(h):
        m = h == hh
        base[m] = np.nanmean(X[m], 0)
    Ex = X - base
    V = np.isfinite(Ex)
    Ex0 = np.where(V, Ex, 0.0)
    Fs = F[sel].reset_index(drop=True)
    if perm is not None:
        Fs = Fs.iloc[perm].reset_index(drop=True)
    masks, keys = [], []
    for s, w, k in itertools.product(S_GRID, W_GRID, K_GRID):
        masks.append(E.event_mask(Fs, side, s, w, k))
        keys.append((s, w, k))
    Mk = np.stack(masks).astype(float)
    n = Mk @ V
    s1 = Mk @ Ex0
    s2 = Mk @ (Ex0 ** 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = s1 / n
        sd = np.sqrt(np.maximum(s2 / n - mu ** 2, 0) * n / np.maximum(n - 1, 1))
        t = mu / (sd / np.sqrt(n))
    t[n < N_MIN] = np.nan
    return t, mu, n, keys, cols


def perm_within_hour(hours: np.ndarray, rng) -> np.ndarray:
    idx = np.arange(len(hours))
    out = idx.copy()
    for h in np.unique(hours):
        m = np.flatnonzero(hours == h)
        out[m] = rng.permutation(m)
    return out


def main() -> None:
    B = E.load_1m()
    B15 = E.load_1m(1.5)
    BL = E.load_long1h()
    res: dict = {"birincil": [], "izgara": [], "secilen": []}
    data = {}
    for tf in (60, 240):
        F, Rm, T = E.build(tf, B)
        data[tf] = (F, Rm, T)
    FL, RL, TL = E.build(60, BL, "long1h")

    # ---------- birincil hipotezler ----------
    for hid, tf, side, k in PRIMARY:
        F, Rm, T = data[tf]
        m = E.event_mask(F, side, P_CELL["s"], P_CELL["w"], k)
        col = Rm[:, side, P_CELL["di"], P_CELL["si"], P_CELL["ti"]]
        x = trades(B, F, T, m, side, P_CELL["di"], P_CELL["si"], P_CELL["ti"], tf)
        row = {"id": hid, "tf": tf, "yon": SIDE_NAME[side], "k": k}
        for per, flag in (("KESIF", True), ("TEST", False)):
            valid = (F.kesif.to_numpy() == flag) & F.full.to_numpy()
            base = hour_base(col, F.hour.to_numpy(), valid)
            row[per] = summarize(x[x.kesif == flag], base)
        xs = trades(B15, E.htf_bars(B15, tf), T, m, side, P_CELL["di"], P_CELL["si"], P_CELL["ti"], tf)
        row["TEST_sp15"] = summarize(xs[xs.kesif == False])  # noqa: E712
        x1 = trades(B, F, T, m, side, P_CELL["di"], P_CELL["si"], P_CELL["ti"], tf, single=True)
        row["TEST_tek"] = summarize(x1[x1.kesif == False])  # noqa: E712
        xm = trades(B, F, T, m, side, P_CELL["di"], P_CELL["si"], P_CELL["ti"], tf, mirror=True)
        row["TEST_ayna"] = summarize(xm[xm.kesif == False])  # noqa: E712
        if tf == 60:
            mL = E.event_mask(FL, side, P_CELL["s"], P_CELL["w"], k)
            colL = RL[:, side, 0, P_CELL["si"], P_CELL["ti"]]
            baseL = hour_base(colL, FL.hour.to_numpy(), FL.full.to_numpy())
            xl = trades(BL, FL, TL, mL, side, 0, P_CELL["si"], P_CELL["ti"], tf)
            row["BAGIMSIZ"] = summarize(xl, baseL)
        res["birincil"].append(row)
        print(json.dumps(row, ensure_ascii=False, default=str))

    # ---------- keşif ızgarası + seçim düzeltmesi ----------
    rng = np.random.default_rng(11)
    for tf in (60, 240):
        F, Rm, T = data[tf]
        sel = (F.kesif & F.full).to_numpy()
        hours = F.hour.to_numpy()[sel]
        for side in (0, 1):
            t, mu, n, keys, cols = grid_t(F, Rm, side, sel)
            tmax = np.nanmax(t)
            n_good, n_bad = int((t >= 2).sum()), int((t <= -2).sum())
            null_max, null_good, null_bad = [], [], []
            for _ in range(N_PERM):
                tp, *_ = grid_t(F, Rm, side, sel, perm_within_hour(hours, rng))
                null_max.append(np.nanmax(tp)); null_good.append(int((tp >= 2).sum())); null_bad.append(int((tp <= -2).sum()))
            null_max = np.array(null_max)
            p_sel = float((null_max >= tmax).mean())
            i, j = np.unravel_index(np.nanargmax(t), t.shape)
            s, w, k = keys[i]
            di, si, ti = cols[j]
            g = {"tf": tf, "yon": SIDE_NAME[side], "hucre_aktif": int(np.isfinite(t).sum()),
                 "t_max": round(float(tmax), 2), "null_max_p95": round(float(np.percentile(null_max, 95)), 2),
                 "p_sel": round(p_sel, 3), "iyi_t2": n_good, "kotu_t2": n_bad,
                 "null_iyi_ort": round(float(np.mean(null_good)), 1), "null_kotu_ort": round(float(np.mean(null_bad)), 1),
                 "kesif_fark_medyan": round(float(np.nanmedian(np.where(n >= N_MIN, mu, np.nan))), 4),
                 "en_iyi": {"s": s, "w": w, "k": k, "D": E.DELAYS[di], "SL": E.SL_MODES[si], "TP": E.TPS[ti],
                            "kesif_fark": round(float(mu[i, j]), 4), "kesif_n": int(n[i, j])}}
            # seçilen hücre TEST
            m = E.event_mask(F, side, s, w, k)
            col = Rm[:, side, di, si, ti]
            x = trades(B, F, T, m, side, di, si, ti, tf)
            for per, flag in (("KESIF", True), ("TEST", False)):
                valid = (F.kesif.to_numpy() == flag) & F.full.to_numpy()
                g[per] = summarize(x[x.kesif == flag], hour_base(col, F.hour.to_numpy(), valid))
            xs = trades(B15, E.htf_bars(B15, tf), T, m, side, di, si, ti, tf)
            g["TEST_sp15"] = summarize(xs[xs.kesif == False])  # noqa: E712
            g["TEST_tek"] = summarize(trades(B, F, T, m, side, di, si, ti, tf, single=True).query("kesif == False"))
            g["TEST_ayna"] = summarize(trades(B, F, T, m, side, di, si, ti, tf, mirror=True).query("kesif == False"))
            if tf == 60:
                mL = E.event_mask(FL, side, s, w, k)
                baseL = hour_base(RL[:, side, 0, si, ti], FL.hour.to_numpy(), FL.full.to_numpy())
                g["BAGIMSIZ_D60"] = summarize(trades(BL, FL, TL, mL, side, 0, si, ti, tf), baseL)
            # ilk 20 KEŞİF hücresinin TEST ortalaması (aşırı uyum göstergesi)
            order = np.argsort(-np.nan_to_num(t, nan=-99), axis=None)[:20]
            top = []
            selT = (~F.kesif & F.full).to_numpy()
            tT, muT, nT, *_ = grid_t(F, Rm, side, selT)
            for o in order:
                a, b = np.unravel_index(o, t.shape)
                top.append(muT[a, b])
            g["ilk20_TEST_fark_ort"] = round(float(np.nanmean(top)), 4)
            g["ilk20_TEST_pozitif"] = int(np.nansum(np.array(top) > 0))
            g["TEST_tum_hucre_fark_medyan"] = round(float(np.nanmedian(np.where(nT >= N_MIN, muT, np.nan))), 4)
            res["izgara"].append(g)
            print(json.dumps(g, ensure_ascii=False, default=str))
    (E.OUT / "hukum.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
