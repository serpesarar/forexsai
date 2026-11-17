"""EK-1 F1 / EK-1b — SMT ızgarası: seans × seviye × teyit × hedef × gün, NAS100 vs US500 broker (M30 + M5)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT.parent
OUT = ROOT / "results"
SRC = {"M30": RES / "c1_turev_20261105" / "data" / "mt5", "M5": RES / "yon_lab_20261114" / "data" / "mt5"}
SERVER_MINUS_NY = 7 * 3600
NAS_POINT = 0.1
M30_START = pd.Timestamp("2021-01-01")
TEST_START = pd.Timestamp("2023-07-01")
M5_START = pd.Timestamp("2025-06-18")
CONF_BARS = {"M30": 4, "M5": 12}
R60_BARS = {"M30": 2, "M5": 12}
WINDOWS = {"Asya": (18 * 60, 2 * 60), "Londra": (120, 480), "NYsabah": (570, 720), "ogle": (720, 810), "NYoglen": (810, 960)}
LEVELS_FOR = {"Asya": ("PD", "R60"), "Londra": ("PD", "ASYA", "R60"), "NYsabah": ("PD", "ON", "ASYA", "LON", "R60"),
              "ogle": ("PD", "ON", "AM", "R60"), "NYoglen": ("PD", "ON", "AM", "R60")}
TARGETS = (1.0, 2.0, 3.0, None)
FRACTAL_K = 2
N_NULL = 200
RNG = np.random.default_rng(20261117)
DOW = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]


def load(tf: str) -> pd.DataFrame:
    a = pd.read_csv(SRC[tf] / f"NAS100_{tf}.csv.gz")
    b = pd.read_csv(SRC[tf] / f"US500_{tf}.csv.gz")
    d = a.merge(b[["t", "h", "l", "c"]], on="t", suffixes=("", "_s")).sort_values("t").reset_index(drop=True)
    d["et"] = pd.to_datetime(d.t - SERVER_MINUS_NY, unit="s")
    lo, hi = (M30_START, M5_START) if tf == "M30" else (M5_START, pd.Timestamp("2100-01-01"))
    d = d[(d.et >= lo) & (d.et < hi)].reset_index(drop=True)
    d["mins"] = d.et.dt.hour * 60 + d.et.dt.minute
    d["sdate"] = (d.et + pd.Timedelta(hours=6)).dt.normalize()  # 18:00 → ertesi seans günü
    d["spr"] = d.sp * NAS_POINT
    return d


def in_window(mins: np.ndarray, w: str) -> np.ndarray:
    a, b = WINDOWS[w]
    return (mins >= a) | (mins < b) if a > b else (mins >= a) & (mins < b)


def session_levels(d: pd.DataFrame) -> pd.DataFrame:
    """Seans günü başına iki sembolün statik seviyeleri (yalnız ilgili pencereden önce biten barlardan)."""
    def hl(mask, suffix=""):
        g = d[mask].groupby("sdate")
        return g["h" + suffix].max(), g["l" + suffix].min()
    rth = (d.mins >= 570) & (d.mins < 960)
    parts = {}
    for name, mask in (("RTH", rth), ("ON", (d.mins >= 1080) | (d.mins < 570)), ("ASYA", in_window(d.mins.to_numpy(), "Asya")),
                       ("LON", in_window(d.mins.to_numpy(), "Londra")), ("AM", (d.mins >= 570) & (d.mins < 720))):
        for sfx, tag in (("", ""), ("_s", "s")):
            h, l = hl(mask, sfx)
            parts[f"{name}_H{tag}"], parts[f"{name}_L{tag}"] = h, l
    lv = pd.DataFrame(parts).sort_index()
    for tag in ("", "s"):
        lv[f"PD_H{tag}"] = lv[f"RTH_H{tag}"].shift(1)
        lv[f"PD_L{tag}"] = lv[f"RTH_L{tag}"].shift(1)
    return lv


def fractal_known(h: np.ndarray, l: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n, k = len(h), FRACTAL_K
    lo_k, hi_k = np.full(n, np.nan), np.full(n, np.nan)
    cl = ch = np.nan
    for i in range(n):
        j = i - k
        if j >= k:
            wl, wh = l[j - k:j + k + 1], h[j - k:j + k + 1]
            if l[j] == wl.min() and (wl == l[j]).sum() == 1:
                cl = l[j]
            if h[j] == wh.max() and (wh == h[j]).sum() == 1:
                ch = h[j]
        lo_k[i], hi_k[i] = cl, ch
    return lo_k, hi_k


def find_events(d: pd.DataFrame, lv: pd.DataFrame, tf: str) -> list[dict]:
    out = []
    H, L, Hs, Ls = (d[c].to_numpy() for c in ("h", "l", "h_s", "l_s"))
    nr = R60_BARS[tf]
    r60 = {"H": pd.Series(H).rolling(nr).max().shift(1).to_numpy(), "L": pd.Series(L).rolling(nr).min().shift(1).to_numpy(),
           "Hs": pd.Series(Hs).rolling(nr).max().shift(1).to_numpy(), "Ls": pd.Series(Ls).rolling(nr).min().shift(1).to_numpy()}
    mins = d.mins.to_numpy()
    for sd, grp in d.groupby("sdate"):
        if sd not in lv.index:
            continue
        r = lv.loc[sd]
        for w in WINDOWS:
            idx = grp.index[in_window(grp.mins.to_numpy(), w)].to_numpy()
            if len(idx) < 3:
                continue
            for lvl in LEVELS_FOR[w]:
                for side in ("H", "L"):
                    if lvl == "R60":
                        la, ls = r60[side][idx], r60[side + "s"][idx]
                    else:
                        key = "PD" if lvl == "PD" else lvl
                        la, ls = r[f"{key}_{side}"], r[f"{key}_{side}s"]
                        if not (np.isfinite(la) and np.isfinite(ls)):
                            continue
                    ax = (H[idx] > la) if side == "H" else (L[idx] < la)
                    sx = (Hs[idx] > ls) if side == "H" else (Ls[idx] < ls)
                    ax, sx = np.asarray(ax) & np.isfinite(la), np.asarray(sx) & np.isfinite(ls)
                    if not (ax.any() or sx.any()):
                        continue
                    fa = int(np.argmax(ax)) if ax.any() else 10 ** 9
                    fs = int(np.argmax(sx)) if sx.any() else 10 ** 9
                    f = min(fa, fs)
                    kind = "CTRL" if fa == fs else "SMT"
                    lead = "ikisi" if fa == fs else ("NAS" if fa < fs else "SPX")
                    lvl_a = float(la[f]) if np.ndim(la) else float(la)
                    lvl_s = float(ls[f]) if np.ndim(ls) else float(ls)
                    out.append(dict(sdate=sd, w=w, level=lvl, side=side, kind=kind, lead=lead, i=int(idx[f]),
                                    end=int(idx[-1]), dir=-1 if side == "H" else 1, lvl_a=lvl_a, lvl_s=lvl_s))
    return out


def entry_for(ev: dict, conf: str, d: pd.DataFrame, lo_k, hi_k, W: int) -> int | None:
    i, end = ev["i"], ev["end"]
    C, Cs = d.c.to_numpy(), d.c_s.to_numpy()
    if conf == "U":
        return i + 1 if i + 1 <= end else None
    if conf == "F":
        ref = lo_k[i] if ev["dir"] < 0 else hi_k[i]
        if not np.isfinite(ref):
            return None
        for j in range(i + 1, min(i + W, end) + 1):
            if (ev["dir"] < 0 and C[j] < ref) or (ev["dir"] > 0 and C[j] > ref):
                return j + 1 if j + 1 <= end else None
        return None
    # IN: süpüren sembol seviyesinin içine geri kapanır (olay barı dahil)
    use_s = ev["lead"] == "SPX"
    cc, lv = (Cs, ev["lvl_s"]) if use_s else (C, ev["lvl_a"])
    for j in range(i, min(i + W, end) + 1):
        if (ev["dir"] < 0 and cc[j] < lv) or (ev["dir"] > 0 and cc[j] > lv):
            return j + 1 if j + 1 <= end else None
    return None


def simulate(ev: dict, e_i: int, tgt: float | None, d: pd.DataFrame) -> tuple[float, float] | None:
    H, L, O, C, S = (d[c].to_numpy() for c in ("h", "l", "o", "c", "spr"))
    s, e = ev["dir"], O[e_i]
    stop = H[ev["i"]:e_i].max() if s < 0 else L[ev["i"]:e_i].min()
    risk = (stop - e) if s < 0 else (e - stop)
    if risk <= 2 * S[e_i]:
        return None
    cost = S[e_i] / risk
    for j in range(e_i, ev["end"] + 1):
        if (s < 0 and H[j] >= stop) or (s > 0 and L[j] <= stop):
            return -1.0 - cost, cost
        if tgt is not None and ((s < 0 and L[j] <= e - tgt * risk) or (s > 0 and H[j] >= e + tgt * risk)):
            return tgt - cost, cost
    return s * (C[ev["end"]] - e) / risk - cost, cost


def build_events_only(tf: str) -> tuple[pd.DataFrame, list[dict]]:
    d = load(tf)
    return d, find_events(d, session_levels(d), tf)


def build(tf: str) -> pd.DataFrame:
    d = load(tf)
    lv = session_levels(d)
    lo_k, hi_k = fractal_known(d.h.to_numpy(), d.l.to_numpy())
    rows = []
    for ev in find_events(d, lv, tf):
        for conf in ("U", "F", "IN"):
            e_i = entry_for(ev, conf, d, lo_k, hi_k, CONF_BARS[tf])
            if e_i is None:
                continue
            for tgt in TARGETS:
                r = simulate(ev, e_i, tgt, d)
                if r is None:
                    continue
                rows.append(dict(sdate=ev["sdate"], w=ev["w"], level=ev["level"], kind=ev["kind"], conf=conf,
                                 tgt="S" if tgt is None else f"{tgt:.0f}R", R=r[0], cost=r[1]))
    t = pd.DataFrame(rows)
    t["dow"] = [DOW[x] for x in pd.to_datetime(t.sdate).dt.dayofweek]
    t["per"] = np.where(tf == "M5", "B", np.where(pd.to_datetime(t.sdate) < TEST_START, "K", "T"))
    return t


def expand(t: pd.DataFrame) -> pd.DataFrame:
    """Seviye ve gün için 'hepsi' satırlarını ekler (her olay kendi + birleşik hücrelere girer)."""
    a = t.assign(level="hepsi")
    b = pd.concat([t, a])
    return pd.concat([b, b.assign(dow="hepsi")])


KEYS = ["w", "level", "conf", "tgt", "dow", "kind"]


def cell_stats(x: pd.DataFrame, col: str = "R") -> pd.DataFrame:
    g = x.groupby(KEYS + ["per"])[col].agg(["count", "mean", "std"])
    g["t"] = g["mean"] / g["std"] * np.sqrt(g["count"])
    return g.unstack("per")


def passing(c: pd.DataFrame) -> pd.Series:
    tK, tT, nT, nK = c[("t", "K")], c[("t", "T")], c[("count", "T")], c[("count", "K")]
    return (tK.abs() >= 2) & (nK >= 15) & (nT >= 30) & (np.sign(tT) == np.sign(tK)) & (tT.abs() >= 1.65)


def main() -> None:
    t = pd.concat([build("M30"), build("M5")], ignore_index=True)
    t.to_parquet(OUT / "smt_grid_islemler.parquet")
    x = expand(t)
    c = cell_stats(x)
    ok = passing(c)
    days = x.sdate.unique()
    null = []
    for _ in range(N_NULL):
        flip = pd.Series(RNG.choice([-1.0, 1.0], size=len(days)), index=days)
        xn = x.assign(Rn=flip.reindex(x.sdate).to_numpy() * (x.R + x.cost) - x.cost)
        null.append(int(passing(cell_stats(xn, "Rn")).sum()))
    flat = c.copy()
    flat.columns = [f"{a}_{b}" for a, b in flat.columns]
    flat["gecer"] = ok
    flat = flat.reset_index()
    flat.to_csv(OUT / "smt_grid_hucreler.csv", index=False)
    elig = flat[(flat.count_K >= 15) & (flat.count_T >= 30)]
    top = elig.reindex(elig.t_K.abs().sort_values(ascending=False).index).head(20)
    smt = flat[flat.kind == "SMT"].set_index(KEYS[:-1])
    ctl = flat[flat.kind == "CTRL"].set_index(KEYS[:-1])
    diff = (smt[["mean_K", "mean_T", "mean_B"]] - ctl[["mean_K", "mean_T", "mean_B"]]).dropna(subset=["mean_K", "mean_T"])
    main_cells = flat[(flat.level == "hepsi") & (flat.dow == "hepsi") & (flat.tgt == "2R")]
    res = dict(islem=len(t), hucre=len(flat), uygun=len(elig), gecen=int(ok.sum()), null_ort=float(np.mean(null)),
               null_p95=float(np.percentile(null, 95)), gecenler=flat[flat.gecer].to_dict("records"),
               ilk20=top.to_dict("records"),
               ilk20_TEST_ayni_isaret=float((np.sign(top.t_K) == np.sign(top.t_T)).mean()),
               ilk20_B_ayni_isaret=float((np.sign(top.t_K) == np.sign(top.mean_B)).mean()),
               ana_hucreler=main_cells.to_dict("records"),
               smt_eksi_kontrol_ozet=dict(n=len(diff), K_ort=float(diff.mean_K.mean()), T_ort=float(diff.mean_T.mean()),
                                          ayni_isaret=float((np.sign(diff.mean_K) == np.sign(diff.mean_T)).mean())))
    (OUT / "smt_grid.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
    print({k: res[k] for k in ("islem", "hucre", "uygun", "gecen", "null_ort", "null_p95", "ilk20_TEST_ayni_isaret",
                               "ilk20_B_ayni_isaret", "smt_eksi_kontrol_ozet")})


if __name__ == "__main__":
    main()
