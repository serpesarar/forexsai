"""EK-1 F5 (düşüş/yükseliş günü × dilim × gün) ve F4 (açılış / 10:00 devamı / Judas) — vektörize, plasebolu."""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from derin_lib import (CLOSE, DOW_NAMES, OPEN, OUT, RNG, VIX_TH, Mat, load_mat, passes, prev_rth_close,
                       price_close_before, price_open)

SLICES = {"0930-1000": (570, 600), "1000-1100": (600, 660), "1100-1200": (660, 720), "1200-1330": (720, 810),
          "1330-1500": (810, 900), "1500-1600": (900, 960), "AM": (570, 720), "PM": (810, 960), "GUN": (570, 960)}
PTS = (150, 250, 400, 600)
PCT = (0.005, 0.01, 0.016, 0.025)
ZS = (1.0, 1.5, 2.5)
N_NULL = 200
T0S = {"0945": 585, "1000": 600, "1015": 615, "1030": 630}
T1S = {"1100": 660, "1200": 720, "1600": 960}
MIN_N_K = 15


def slice_returns(m: Mat) -> np.ndarray:
    out = np.full((len(m.days), len(SLICES)), np.nan)
    for j, (a, b) in enumerate(SLICES.values()):
        po, pc = price_open(m, a), price_close_before(m, b)
        cost = m.S[:, a] / po * 1e4
        out[:, j] = (pc / po - 1) * 1e4 - cost
    return out


def sd20(m: Mat) -> np.ndarray:
    c = price_close_before(m, CLOSE)
    r = pd.Series(c).pct_change()
    return r.rolling(20).std().shift(1).to_numpy()


def f5_conditions(m: Mat) -> tuple[np.ndarray, list[str]]:
    o = price_open(m, OPEN)
    pc = prev_rth_close(m)
    p18 = price_open_prev(m, 1080)
    s = sd20(m)
    cols, names = [], []
    for meas, ref in (("kap", pc), ("18", p18)):
        pts, pct = o - ref, o / ref - 1
        z = pct / s
        for sgn, lab in ((-1, "dus"), (1, "yuk")):
            for th in PTS:
                cols.append(sgn * pts >= th); names.append(f"{meas}|{lab}|{th}p")
            for th in PCT:
                cols.append(sgn * pct >= th); names.append(f"{meas}|{lab}|{th*100:.1f}%")
            for th in ZS:
                cols.append(sgn * z >= th); names.append(f"{meas}|{lab}|z{th}")
    return np.column_stack(cols).astype(float), names


def price_open_prev(m: Mat, minute: int) -> np.ndarray:
    blk = m.prevO[:, minute:minute + 15]
    ok = np.isfinite(blk)
    j = ok.argmax(1)
    v = blk[np.arange(len(blk)), j]
    v[~ok.any(1)] = np.nan
    return v


def moments(M: np.ndarray, R: np.ndarray, V: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    Rz = np.where(V, R, 0.0)
    return M.T @ V.astype(float), M.T @ Rz, M.T @ (Rz ** 2)


def welch_from(n1, s1, q1, n2, s2, q2) -> tuple[np.ndarray, np.ndarray]:
    with np.errstate(divide="ignore", invalid="ignore"):
        m1, m2 = s1 / n1, s2 / n2
        v1 = (q1 - n1 * m1 ** 2) / (n1 - 1)
        v2 = (q2 - n2 * m2 ** 2) / (n2 - 1)
        d = m1 - m2
        t = d / np.sqrt(v1 / n1 + v2 / n2)
    return d, t


def f5_stats(cond: np.ndarray, R: np.ndarray, m: Mat) -> dict[str, np.ndarray]:
    V = np.isfinite(R)
    groups = [np.ones(len(m.days), bool)] + [m.dow == k for k in range(5)]
    res = {}
    for per, pm in (("K", m.kesif), ("T", ~m.kesif)):
        D, T, N = [], [], []
        for g in groups:
            sel = (g & pm).astype(float)[:, None]
            Mc = cond * sel
            Mn = (1 - cond) * sel
            n1, s1, q1 = moments(Mc, R, V)
            n2, s2, q2 = moments(Mn, R, V)
            d, t = welch_from(n1, s1, q1, n2, s2, q2)
            D.append(d); T.append(t); N.append(n1)
        res[f"d{per}"], res[f"t{per}"], res[f"n{per}"] = np.stack(D), np.stack(T), np.stack(N)
    return res  # şekil: grup × koşul × dilim


def count_pass(st: dict) -> np.ndarray:
    ok = ((np.abs(st["tK"]) >= 2) & (st["nK"] >= MIN_N_K) & (st["nT"] >= 30)
          & (np.sign(st["tT"]) == np.sign(st["tK"])) & (np.abs(st["tT"]) >= 1.65))
    return ok


def permute_within_year(cond: np.ndarray, years: np.ndarray) -> np.ndarray:
    out = cond.copy()
    for y in np.unique(years):
        ix = np.flatnonzero(years == y)
        out[ix] = cond[RNG.permutation(ix)]
    return out


def run_f5(m: Mat) -> dict:
    R = slice_returns(m)
    cond, names = f5_conditions(m)
    st = f5_stats(cond, R, m)
    ok = count_pass(st)
    years = pd.to_datetime(m.days).year.to_numpy()
    null = [int(count_pass(f5_stats(permute_within_year(cond, years), R, m)).sum()) for _ in range(N_NULL)]
    rows = []
    gnames = ["hepsi"] + DOW_NAMES
    for gi, ci, si in itertools.product(range(6), range(len(names)), range(len(SLICES))):
        rows.append(dict(gun=gnames[gi], kosul=names[ci], dilim=list(SLICES)[si],
                         nK=int(st["nK"][gi, ci, si]), dK=st["dK"][gi, ci, si], tK=st["tK"][gi, ci, si],
                         nT=int(st["nT"][gi, ci, si]), dT=st["dT"][gi, ci, si], tT=st["tT"][gi, ci, si],
                         gecer=bool(ok[gi, ci, si])))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "f5_hucreler.csv", index=False)
    elig = t[(t.nK >= MIN_N_K) & (t.nT >= 30)]
    top = elig.reindex(elig.tK.abs().sort_values(ascending=False).index).head(20)
    same = (np.sign(top.tK) == np.sign(top.tT)).mean()
    return dict(hucre=len(t), uygun=len(elig), gecen=int(ok.sum()), null_ort=float(np.mean(null)),
                null_p95=float(np.percentile(null, 95)), gecenler=t[t.gecer].sort_values("tK").to_dict("records"),
                ilk20_TEST_ayni_isaret=float(same),
                ilk20_TEST_ort_fark_isaretli=float((np.sign(top.tK) * top.dT).mean()),
                ilk20=top[["gun", "kosul", "dilim", "nK", "dK", "tK", "nT", "dT", "tT"]].to_dict("records"))


def f4_returns(m: Mat) -> tuple[np.ndarray, list[tuple[str, str]], np.ndarray]:
    o930 = price_open(m, OPEN)
    o945 = price_open(m, 585)
    d1 = np.sign(o945 - o930)
    cols, keys, judas = [], [], []
    for (n0, t0), (n1, t1) in itertools.product(T0S.items(), T1S.items()):
        p0 = price_open(m, t0)
        dr = np.sign(p0 - o930)
        cost = m.S[:, t0] / p0 * 1e4
        r = dr * (price_close_before(m, t1) / p0 - 1) * 1e4 - cost
        r[dr == 0] = np.nan
        cols.append(r); keys.append((n0, n1))
        judas.append((t0 > 585) & (dr == -d1) & (d1 != 0))
    return np.column_stack(cols), keys, np.column_stack(judas)


def f4_masks(m: Mat, judas_col: np.ndarray) -> list[tuple[str, np.ndarray]]:
    o = price_open(m, OPEN)
    gz = (o / prev_rth_close(m) - 1) / sd20(m)
    js = {"hepsi": np.ones(len(o), bool), "Judas": judas_col, "Judas-yok": ~judas_col}
    gs = {"hepsi": np.ones(len(o), bool), "bosluk+": gz > 0.5, "bosluk-": gz < -0.5, "duz": np.abs(gz) <= 0.5}
    vs = {"hepsi": np.ones(len(o), bool), "VIX>=": m.vix_prev >= VIX_TH, "VIX<": m.vix_prev < VIX_TH}
    ds = {"hepsi": np.ones(len(o), bool), **{DOW_NAMES[k]: m.dow == k for k in range(5)}}
    out = []
    for (a, ma), (b, mb), (c, mc), (e, me) in itertools.product(js.items(), gs.items(), vs.items(), ds.items()):
        out.append((f"{a}|{b}|{c}|{e}", ma & mb & mc & me))
    return out


def f4_table(R: np.ndarray, keys, J: np.ndarray, m: Mat, flip: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    for k, (n0, n1) in enumerate(keys):
        r = R[:, k] if flip is None else R[:, k] * flip
        for name, mk in f4_masks(m, J[:, k]):
            if name.startswith("Judas|") and n0 == "0945":
                continue
            out = {"T0": n0, "T1": n1, "kosul": name}
            for per, pm in (("K", m.kesif), ("T", ~m.kesif)):
                x = r[mk & pm]
                x = x[np.isfinite(x)]
                n = len(x)
                mu = x.mean() if n > 2 else np.nan
                sd = x.std(ddof=1) if n > 2 else np.nan
                out.update({f"n{per}": n, f"m{per}": mu, f"t{per}": mu / sd * np.sqrt(n) if n > 2 and sd > 0 else np.nan})
            rows.append(out)
    t = pd.DataFrame(rows)
    t["gecer"] = [passes(a, b, int(n)) and nk >= MIN_N_K for a, b, n, nk in zip(t.tK, t.tT, t.nT, t.nK)]
    return t


def run_f4(m: Mat) -> dict:
    R, keys, J = f4_returns(m)
    t = f4_table(R, keys, J, m)
    t.to_csv(OUT / "f4_hucreler.csv", index=False)
    null = [int(f4_table(R, keys, J, m, RNG.choice([-1.0, 1.0], size=len(m.days))).gecer.sum()) for _ in range(N_NULL)]
    elig = t[(t.nK >= MIN_N_K) & (t.nT >= 30)]
    top = elig.reindex(elig.tK.abs().sort_values(ascending=False).index).head(20)
    return dict(hucre=len(t), uygun=len(elig), gecen=int(t.gecer.sum()), null_ort=float(np.mean(null)),
                null_p95=float(np.percentile(null, 95)), gecenler=t[t.gecer].to_dict("records"),
                ilk20_TEST_ayni_isaret=float((np.sign(top.tK) == np.sign(top.tT)).mean()),
                ilk20_TEST_ort_isaretli=float((np.sign(top.tK) * top.mT).mean()),
                ilk20=top.to_dict("records"),
                hepsi=t[t.kosul == "hepsi|hepsi|hepsi|hepsi"].to_dict("records"))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    m = load_mat()
    res = {"gun": len(m.days), "kesif_gun": int(m.kesif.sum()), "F5": run_f5(m), "F4": run_f4(m)}
    (OUT / "derin_f45.json").write_text(json.dumps(res, indent=1, default=float, ensure_ascii=False))
    for f in ("F5", "F4"):
        r = res[f]
        print(f, {k: r[k] for k in ("hucre", "uygun", "gecen", "null_ort", "null_p95")})


if __name__ == "__main__":
    main()
