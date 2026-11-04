"""fam_trend: ön-kayıtlı (prereg.md) trend/kırılım/momentum hücrelerini koşar.

Çıktı: results/cells.json, results/summary.md
Çalıştır: /Users/melihcanodacioglu/Desktop/panel/.venv/bin/python -I run_trend.py
"""
from __future__ import annotations

import json
import sys
import time
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_trend as lt  # noqa: E402

OUT = lt.ROOT / "results"
N_PLAC = 200
DAYM = 1440
WIN = {"FULL": ("DISC", "OOS", "BLIND"), "POST": ("OOS", "BLIND")}


def mk(df: pd.DataFrame, dirn: int, sl_mult: float, tp_mult: float, end, atr_col="atr",
       sig_col="close", extra: dict | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
        "dec": df["dec"].to_numpy(np.int64),
        "dir": np.full(len(df), dirn, np.int64),
        "sl": sl_mult * df[atr_col].to_numpy(),
        "tp": tp_mult * df[atr_col].to_numpy() if np.isfinite(tp_mult) else np.full(len(df), np.nan),
        "end": np.asarray(end, np.int64),
        "sig": df[sig_col].to_numpy(float),
    })
    if extra:
        for k, v in extra.items():
            out[k] = np.asarray(v)
    out = out[np.isfinite(out["sl"]) & (out["sl"] > 0)].reset_index(drop=True)
    return out


# ───────────────────────── çerçeveler ─────────────────────────
def frames(m1: lt.M1) -> dict:
    D = lt.load_tf("1d", DAYM)
    c, h, l = D["close"].to_numpy(), D["high"].to_numpy(), D["low"].to_numpy()
    D["ema200"] = lt.ema(c, 200)
    for n in (40, 55, 70):
        D[f"hh{n}"], D[f"ll{n}"] = lt.prev_max(h, n), lt.prev_min(l, n)
    for n in (10, 20):
        D[f"cmax{n}"] = pd.Series(c).rolling(n).max().to_numpy()
        D[f"cmin{n}"] = pd.Series(c).rolling(n).min().to_numpy()
    D["ret"] = pd.Series(c).pct_change().to_numpy()
    D["dvol20"] = pd.Series(D["ret"]).rolling(20).std().to_numpy()
    D["atr_med60"] = pd.Series(D["atr"]).rolling(60).median().to_numpy()
    D["date"] = D["ts"].dt.date
    H4 = lt.load_tf("4h", 240)
    for n in (20, 55):
        H4[f"hh{n}"], H4[f"ll{n}"] = lt.prev_max(H4["high"].to_numpy(), n), lt.prev_min(H4["low"].to_numpy(), n)
    a = lt.asof(H4["dec"].to_numpy(), D, ["close", "ema200"])
    H4["d_up"] = (a["close"] > a["ema200"]).to_numpy()
    H4["d_dn"] = (a["close"] < a["ema200"]).to_numpy()
    H1 = lt.load_tf("1h", 60)
    H1["hh20"], H1["ll20"] = lt.prev_max(H1["high"].to_numpy(), 20), lt.prev_min(H1["low"].to_numpy(), 20)
    H1["sar"] = lt.psar(H1["high"].to_numpy(), H1["low"].to_numpy())
    # S2: sinyal barının UTC gününden bir önceki tam gün getirisi + o güne kadarki dvol20
    dmap = pd.DataFrame({"date": D["date"], "pr": D["ret"], "dv": D["dvol20"]})
    dmap["date"] = pd.to_datetime(dmap["date"]) + pd.Timedelta(days=1)  # d-1 değerleri d gününe
    hd = pd.DataFrame({"date": pd.to_datetime(H1["ts"].dt.date)})
    mg = hd.merge(dmap, on="date", how="left")
    H1["prev_ret"], H1["prev_dv"] = mg["pr"].to_numpy(), mg["dv"].to_numpy()
    M15 = lt.load_tf("15m", 15)
    c15 = M15["close"].to_numpy()
    hh = pd.Series(M15["high"]).rolling(14).max().to_numpy()
    ll = pd.Series(M15["low"]).rolling(14).min().to_numpy()
    M15["stoch"] = 100 * (c15 - ll) / np.where(hh - ll > 0, hh - ll, np.nan)
    M15["dist"] = (c15 - lt.ema(c15, 20)) / M15["atr"].to_numpy()
    a = lt.asof(M15["dec"].to_numpy(), H1, ["close", "sar", "atr"])
    M15["h1_close"], M15["h1_sar"], M15["h1_atr"] = a["close"].to_numpy(), a["sar"].to_numpy(), a["atr"].to_numpy()
    M5 = lt.load_tf("5m", 5)
    c5 = M5["close"].to_numpy()
    M5["ema200"] = lt.ema(c5, 200)
    M5["hh48"], M5["ll48"] = lt.prev_max(M5["high"].to_numpy(), 48), lt.prev_min(M5["low"].to_numpy(), 48)
    return dict(D=D, H4=H4, H1=H1, M15=M15, M5=M5)


def h6_end(D: pd.DataFrame, n: int, long: bool) -> np.ndarray:
    """giriş günü d için: d'den sonraki ilk gün e, kapanış = son n kapanışın min (long) / max (short)."""
    c = D["close"].to_numpy()
    flag = (c <= D[f"cmin{n}"].to_numpy()) if long else (c >= D[f"cmax{n}"].to_numpy())
    dec = D["dec"].to_numpy(np.int64)
    nxt = np.full(len(c), -1)
    cur = -1
    for i in range(len(c) - 1, -1, -1):
        nxt[i] = cur
        if flag[i]:
            cur = i
    cap = dec + 20 * DAYM
    e = np.where(nxt >= 0, dec[np.maximum(nxt, 0)], cap)
    return np.minimum(e, cap)


# ───────────────────────── hücreler ─────────────────────────
def cells(F: dict, m1: lt.M1) -> list[dict]:
    C: list[dict] = []
    D, H4, H1, M15, M5 = F["D"], F["H4"], F["H1"], F["M15"], F["M5"]

    def add(name, group, primary, ev, base, window="FULL", note="", extra=None):
        C.append(dict(name=name, group=group, primary=primary, ev=ev, base=base, window=window,
                      note=note, extra=extra or {}))

    # ── GD
    Dv = D[~D["excl"] & D["ema200"].notna() & D["atr"].notna()]
    end20 = lambda df: df["dec"].to_numpy() + 20 * DAYM  # noqa: E731
    baseL = mk(Dv, 1, 2, 4, end20(Dv), extra={"above": (Dv["close"] > Dv["ema200"]).to_numpy()})
    baseS = mk(Dv, -1, 2, 4, end20(Dv))
    for n, prim in ((55, True), (40, False), (70, False)):
        s = Dv[(Dv["close"] >= Dv[f"hh{n}"]) & (Dv["close"] > Dv["ema200"])]
        add(f"GD{n}-L", "GD", prim, mk(s, 1, 2, 4, end20(s)), baseL)
    s = Dv[Dv["close"] >= Dv["hh55"]]
    add("GD55-L-noEMA", "GD", False, mk(s, 1, 2, 4, end20(s)), baseL)
    s = Dv[(Dv["close"] <= Dv["ll55"]) & (Dv["close"] < Dv["ema200"])]
    add("GD55-S", "GD", True, mk(s, -1, 2, 4, end20(s)), baseS)

    # ── MX
    Dm = D[~D["excl"] & D["atr"].notna()]
    e1 = lambda df: df["dec"].to_numpy() + DAYM  # noqa: E731
    bL1, bS1 = mk(Dm, 1, 2, np.nan, e1(Dm)), mk(Dm, -1, 2, np.nan, e1(Dm))
    mx10 = Dm[Dm["close"] >= Dm["cmax10"]]
    mn10 = Dm[Dm["close"] <= Dm["cmin10"]]
    mx20 = Dm[Dm["close"] >= Dm["cmax20"]]
    evL, evS = mk(mx10, 1, 2, np.nan, e1(mx10)), mk(mn10, -1, 2, np.nan, e1(mn10))
    add("MX10-L-1d", "MX", True, evL, bL1)
    add("MN10-S-1d", "MX", True, evS, bS1)
    add("MXMN10-LS-1d", "MX", True, pd.concat([evL, evS], ignore_index=True),
        pd.concat([bL1, bS1], ignore_index=True))
    add("MN10-L-1d", "MX", False, mk(mn10, 1, 2, np.nan, e1(mn10)), bL1)
    add("MX20-L-1d", "MX", False, mk(mx20, 1, 2, np.nan, e1(mx20)), bL1)
    eL6 = pd.Series(h6_end(D, 10, True), index=D.index)
    eS6 = pd.Series(h6_end(D, 10, False), index=D.index)
    bL6 = mk(Dm, 1, 2, np.nan, eL6[Dm.index]); bS6 = mk(Dm, -1, 2, np.nan, eS6[Dm.index])
    add("MX10-L-H6", "MX", False, mk(mx10, 1, 2, np.nan, eL6[mx10.index]), bL6)
    add("MN10-S-H6", "MX", False, mk(mn10, -1, 2, np.nan, eS6[mn10.index]), bS6)

    # ── H4
    Hv = H4[~H4["excl"] & H4["atr"].notna()]
    e30 = lambda df: df["dec"].to_numpy() + 30 * 240  # noqa: E731
    b4L, b4S = mk(Hv, 1, 2, 4, e30(Hv)), mk(Hv, -1, 2, 4, e30(Hv))
    for n in (20, 55):
        for tr in ("", "-T"):
            sL = Hv[(Hv["close"] >= Hv[f"hh{n}"]) & (Hv["d_up"] if tr else True)]
            sS = Hv[(Hv["close"] <= Hv[f"ll{n}"]) & (Hv["d_dn"] if tr else True)]
            prim = (n == 20 and tr == "")
            add(f"H4D{n}{tr}-L", "H4", prim, mk(sL, 1, 2, 4, e30(sL)), b4L)
            add(f"H4D{n}{tr}-S", "H4", prim, mk(sS, -1, 2, 4, e30(sS)), b4S)

    # ── R0B
    Hh = H1[~H1["excl"] & H1["atr"].notna()]
    e20 = lambda df: df["dec"].to_numpy() + 20 * 60  # noqa: E731
    b1L, b1S = mk(Hh, 1, 1.5, np.nan, e20(Hh)), mk(Hh, -1, 1.5, np.nan, e20(Hh))
    sL = Hh[Hh["high"] >= Hh["hh20"]]
    sS = Hh[Hh["low"] <= Hh["ll20"]]
    exL = {"prev_ret": sL["prev_ret"].to_numpy(), "prev_dv": sL["prev_dv"].to_numpy()}
    exS = {"prev_ret": sS["prev_ret"].to_numpy(), "prev_dv": sS["prev_dv"].to_numpy()}
    evL, evS = mk(sL, 1, 1.5, np.nan, e20(sL), extra=exL), mk(sS, -1, 1.5, np.nan, e20(sS), extra=exS)
    add("R0B-L", "R0B", True, evL, b1L)
    add("R0B-S", "R0B", False, evS, b1S)
    for k, nm, prim in ((1.0, "S2s", True), (0.75, "S2s0.75", False), (1.25, "S2s1.25", False)):
        skip = evL["prev_ret"] > k * evL["prev_dv"]
        add(f"R0B-L-{nm}", "R0B", prim, evL[~skip.to_numpy()].reset_index(drop=True), b1L,
            extra={"skip_of": "R0B-L", "k": k})
    skip = evL["prev_ret"] > 0.01
    add("R0B-L-S2lit", "R0B", False, evL[~skip.to_numpy()].reset_index(drop=True), b1L,
        extra={"skip_of": "R0B-L", "k": "lit1%"})
    skip = evS["prev_ret"] < -1.0 * evS["prev_dv"]
    add("R0B-S-S2s", "R0B", False, evS[~skip.to_numpy()].reset_index(drop=True), b1S,
        extra={"skip_of": "R0B-S", "k": -1.0})

    # ── MOM
    Mv = M15[~M15["excl"] & M15["h1_atr"].notna() & M15["dist"].notna() & M15["stoch"].notna()
             & M15["h1_sar"].notna()]
    condL = (Mv["stoch"] > 70) & (Mv["dist"] > 0.8) & (Mv["h1_sar"] < Mv["h1_close"])
    condS = (Mv["stoch"] < 30) & (Mv["dist"] < -0.8) & (Mv["h1_sar"] > Mv["h1_close"])
    # ilk geçiş: önceki 15m barda (gerçek komşu bar) koşul yanlış
    fullL = pd.Series(False, index=M15.index); fullL[Mv.index] = condL
    fullS = pd.Series(False, index=M15.index); fullS[Mv.index] = condS
    firstL = fullL & ~fullL.shift(1, fill_value=False)
    firstS = fullS & ~fullS.shift(1, fill_value=False)
    e24 = lambda df: df["dec"].to_numpy() + DAYM  # noqa: E731
    for g, tp in (("G1", 2.0), ("G2", 0.73)):
        bL = mk(Mv, 1, 1.0, tp, e24(Mv), atr_col="h1_atr")
        bS = mk(Mv, -1, 1.0, tp, e24(Mv), atr_col="h1_atr")
        sl_ = M15[firstL]; ss_ = M15[firstS]
        add(f"MOM-L-{g}", "MOM", g == "G1", mk(sl_, 1, 1.0, tp, e24(sl_), atr_col="h1_atr"), bL)
        add(f"MOM-S-{g}", "MOM", False, mk(ss_, -1, 1.0, tp, e24(ss_), atr_col="h1_atr"), bS)

    # ── H3
    mac = pd.read_parquet(lt.DATA / "macro_daily.parquet")
    days = pd.to_datetime(mac.loc[mac["ndx_close"].notna(), "date"])
    days = days[(days >= "2021-06-01") & (days <= "2026-10-20")]

    def ny(dates, hm):
        return lt.tmin(pd.Series([pd.Timestamp(f"{x.date()} {hm}", tz="America/New_York").tz_convert("UTC")
                                  for x in dates]))
    t930, t1000, t1530, t1600 = ny(days, "09:30"), ny(days, "10:00"), ny(days, "15:30"), ny(days, "16:00")
    T = m1.T

    def at(tt):
        i = np.searchsorted(T, tt)
        i = np.minimum(i, len(T) - 1)
        return i, T[i] == tt
    i0, ok0 = at(t930); i1, ok1 = at(t1000 - 1); ie, oke = at(t1530 - 1); ir, okr = at(t1000 - 1)
    r1 = np.where(ok0 & ok1, m1.C[i1] / m1.O[i0] - 1, np.nan)
    h1a = lt.asof(t1530, H1, ["atr"])["atr"].to_numpy()
    h1r = lt.asof(t1000, H1, ["atr"])["atr"].to_numpy()
    da = lt.asof(t1530, D, ["atr", "atr_med60"])
    hv = (da["atr"] > da["atr_med60"]).to_numpy()
    dfd = pd.DataFrame({"dec": t1530, "atr": h1a, "close": np.where(oke, m1.C[ie], np.nan), "r1": r1, "hv": hv})
    dfd = dfd[np.isfinite(dfd["close"])]
    end30 = dfd["dec"].to_numpy() + 30
    bH3 = pd.concat([mk(dfd, 1, 1.0, np.nan, end30), mk(dfd, -1, 1.0, np.nan, end30)], ignore_index=True)
    sgn = np.sign(dfd["r1"].to_numpy())
    evs = []
    for dd in (1, -1):
        s = dfd[sgn == dd]
        evs.append(mk(s, dd, 1.0, np.nan, s["dec"].to_numpy() + 30, extra={"hv": s["hv"].to_numpy()}))
    ev = pd.concat(evs, ignore_index=True)
    add("H3-L30", "H3", True, ev, bH3, window="POST")
    add("H3-L30-HV", "H3", False, ev[ev["hv"].astype(bool)].reset_index(drop=True), bH3, window="POST")
    dfr = pd.DataFrame({"dec": t1000, "atr": h1r, "close": np.where(okr, m1.C[ir], np.nan), "r1": r1})
    dfr = dfr[np.isfinite(dfr["close"])]
    endr = (t1600[dfr.index.to_numpy()] if False else None)
    t16 = pd.Series(t1600, index=range(len(t1600)))
    endr = t16[dfr.index].to_numpy()
    bR = pd.concat([mk(dfr, 1, 1.0, np.nan, endr), mk(dfr, -1, 1.0, np.nan, endr)], ignore_index=True)
    sg = np.sign(dfr["r1"].to_numpy())
    evr = pd.concat([mk(dfr[sg == dd], dd, 1.0, np.nan, endr[sg == dd]) for dd in (1, -1)], ignore_index=True)
    add("H3-ROD", "H3", False, evr, bR, window="POST")

    # ── N5
    Fv = M5[~M5["excl"] & M5["atr"].notna() & M5["ema200"].notna() & M5["hh48"].notna()]
    c5, hh48, ll48 = M5["close"], M5["hh48"], M5["ll48"]
    a5 = M5["atr"]
    cL = (c5 > hh48) & (c5.shift(1) <= hh48.shift(1)) & (c5 > M5["ema200"]) & ((c5 - hh48) / a5 <= 0.5)
    cS = (c5 < ll48) & (c5.shift(1) >= ll48.shift(1)) & (c5 < M5["ema200"]) & ((ll48 - c5) / a5 <= 0.5)
    sL, sS = M5[cL & M5.index.isin(Fv.index)], M5[cS & M5.index.isin(Fv.index)]
    add("N5-L", "N5", True, mk(sL, 1, 1, 1, e24(sL)), mk(Fv, 1, 1, 1, e24(Fv)))
    add("N5-S", "N5", True, mk(sS, -1, 1, 1, e24(sS)), mk(Fv, -1, 1, 1, e24(Fv)))
    return C


# ───────────────────────── değerlendirme ─────────────────────────
def keycode(dec: np.ndarray, dirn: np.ndarray) -> np.ndarray:
    t = pd.to_datetime(dec * 60, unit="s", utc=True)
    return ((t.year.to_numpy() * 10000 + t.hour.to_numpy() * 100 + t.minute.to_numpy()) * 2
            + (dirn == 1)).astype(np.int64)


def sim_all(m1, ev, variants=("real", "opt", "stress", "abs")) -> dict:
    out = {}
    a = (ev["dec"].to_numpy(), ev["dir"].to_numpy(), ev["sl"].to_numpy(), ev["tp"].to_numpy(),
         ev["end"].to_numpy(), ev["sig"].to_numpy())
    for v in variants:
        if v == "real":
            out[v] = m1.simulate(*a)
        elif v == "opt":
            out[v] = m1.simulate(*a, optimistic=True)
        elif v == "stress":
            out[v] = m1.simulate(*a, spread=lt.SPREAD_STRESS)
        elif v == "abs":
            out[v] = m1.simulate(*a, spread_abs=lt.SPREAD_ABS)
    return out


def mean_or_nan(x):
    x = x[np.isfinite(x)]
    return float(x.mean()) if len(x) else float("nan")


def evaluate(cell, m1, base_cache) -> dict:
    ev = cell["ev"].sort_values("dec").reset_index(drop=True)
    sp = lt.split_of(ev["dec"].to_numpy())
    sims = sim_all(m1, ev)
    R = sims["real"]["R"]
    bkey = id(cell["base"])
    if bkey not in base_cache:
        b = cell["base"]
        bs = sim_all(m1, b, ("real",))["real"]
        bsp = lt.split_of(b["dec"].to_numpy())
        okb = np.isfinite(bs["R"]) & (bsp != "")
        code = keycode(b["dec"].to_numpy()[okb], b["dir"].to_numpy()[okb])
        o = np.argsort(code, kind="stable")
        base_cache[bkey] = dict(code=code[o], R=bs["R"][okb][o], dir=b["dir"].to_numpy()[okb][o],
                                split=bsp[okb][o], extra=b.drop(columns=["dec", "dir", "sl", "tp", "end", "sig"])
                                .loc[okb].iloc[o].reset_index(drop=True) if b.shape[1] > 6 else None)
    BC = base_cache[bkey]
    res = {"name": cell["name"], "group": cell["group"], "primary": cell["primary"], "window": cell["window"]}
    ok_all = np.isfinite(R)
    res["per_split"] = {}
    for s in ("DISC", "OOS", "BLIND"):
        mm = ok_all & (sp == s)
        res["per_split"][s] = {"n": int(mm.sum()), "meanR": mean_or_nan(R[mm]),
                               "pct": mean_or_nan(sims["real"]["pct"][mm])}
    W = np.isin(sp, WIN[cell["window"]]) & ok_all
    res.update(card(ev, sims, W, BC, sp))
    res["note"] = cell.get("note", "")
    return res


def card(ev, sims, W, BC, sp) -> dict:
    R = sims["real"]["R"][W]
    ent = sims["real"]["ent"][W]
    ext = sims["real"]["ext"][W]
    dec = ev["dec"].to_numpy()[W]
    dirn = ev["dir"].to_numpy()[W]
    day = ent // DAYM
    n = len(R)
    r: dict = {"n": n}
    if n == 0:
        return r
    r["n_days"] = int(len(np.unique(day)))
    r["WR"] = float(np.mean(R > 0))
    r["meanR"] = float(R.mean())
    r["pct"] = float(sims["real"]["pct"][W].mean())
    r["beWR"] = lt.be_wr(R)
    P, lo, hi = lt.day_boot(R, day)
    r["P"], r["ci"] = P, [lo, hi]
    h = n // 2
    r["half1"], r["half2"] = (float(R[:h].mean()) if h else np.nan), float(R[h:].mean())
    r["stress"] = mean_or_nan(sims["stress"]["R"][W])
    r["abs15"] = mean_or_nan(sims["abs"]["R"][W])
    r["opt"] = mean_or_nan(sims["opt"]["R"][W])
    r["gap"] = abs(r["opt"] - r["meanR"])
    sel = lt.single_position(ent.astype(float), ext)
    Rs = R[sel]
    r["n_single"] = int(len(sel))
    r["single"] = float(Rs.mean()) if len(sel) else np.nan
    dsum = pd.Series(Rs).groupby(day[sel]).sum().sort_values(ascending=False)
    for k in (5, 20):
        drop = set(dsum.index[:k])
        rest = Rs[~np.isin(day[sel], list(drop))]
        r[f"single_ex{k}"] = float(rest.mean()) if len(rest) else np.nan
    r["types"] = {t: int(np.sum(sims["real"]["typ"][W] == i)) for i, t in enumerate(("SL", "TP", "TIME"))}
    yrs = pd.to_datetime(dec * 60, unit="s", utc=True).year
    r["by_year"] = {int(y): [int((yrs == y).sum()), float(R[yrs == y].mean())] for y in np.unique(yrs)}
    r["blind"] = mean_or_nan(sims["real"]["R"][np.isfinite(sims["real"]["R"]) & (sp == "BLIND")])
    r["z"] = lt.cluster_z(R, day)
    r["p_one"] = float(1 - 0.5 * (1 + erf(r["z"] / sqrt(2)))) if np.isfinite(r["z"]) else np.nan
    # tabanlar
    for d_, nm in ((1, "base_L"), (-1, "base_S")):
        mm = (BC["dir"] == d_) & np.isin(BC["split"], list(set(sp[W])))
        r[nm] = mean_or_nan(BC["R"][mm]) if mm.any() else np.nan
    if BC["extra"] is not None and "above" in BC["extra"]:
        mm = np.isin(BC["split"], list(set(sp[W]))) & BC["extra"]["above"].to_numpy().astype(bool)
        r["base_P2_aboveEMA"] = mean_or_nan(BC["R"][mm])
    # P1 plasebo
    code = keycode(dec, dirn)
    lo_ = np.searchsorted(BC["code"], code, "left")
    hi_ = np.searchsorted(BC["code"], code, "right")
    cnt = hi_ - lo_
    g = cnt > 0
    rng = np.random.default_rng(abs(hash(("p1", n, float(R.sum())))) % (2**32))
    U = rng.random((N_PLAC, int(g.sum())))
    idx = lo_[g] + np.floor(U * cnt[g]).astype(np.int64)
    pm = BC["R"][idx].mean(axis=1)
    r["plac_means"] = pm.tolist()
    r["plac_mean"] = float(pm.mean())
    r["plac_sd"] = float(pm.std(ddof=1))
    r["plac_pct"] = float(np.mean(pm < R[g].mean()) * 100)
    r["real_on_plac_set"] = float(R[g].mean())
    return r


def main() -> None:
    t0 = time.time()
    m1 = lt.M1()
    F = frames(m1)
    print("çerçeveler", round(time.time() - t0, 1))
    CL = cells(F, m1)
    print("hücre", len(CL), round(time.time() - t0, 1))
    base_cache: dict = {}
    results = []
    for c in CL:
        r = evaluate(c, m1, base_cache)
        results.append(r)
        print(f"{r['name']:16s} n={r.get('n',0):6d} meanR={r.get('meanR',np.nan):+.3f} "
              f"P={r.get('P',np.nan):.2f} plac={r.get('plac_pct',np.nan):5.1f} "
              f"DISC={r['per_split']['DISC']['meanR']:+.3f} OOS={r['per_split']['OOS']['meanR']:+.3f} "
              f"BLIND={r['per_split']['BLIND']['meanR']:+.3f}  t={time.time()-t0:.0f}s", flush=True)
    # DISCOVERY seçimi → OOS∪BLIND kartı
    by = {}
    for c, r in zip(CL, results):
        by.setdefault(c["group"], []).append((c, r))
    sel_rows = []
    for g, lst in by.items():
        best = max(lst, key=lambda cr: (cr[1]["per_split"]["DISC"]["meanR"]
                                        if np.isfinite(cr[1]["per_split"]["DISC"]["meanR"]) else -9))
        c, r = best
        r["disc_selected"] = True
        if not c["primary"] or c["window"] != "POST":
            c2 = dict(c); c2["window"] = "POST"; c2["name"] = "SEL:" + c["name"]; c2["primary"] = False
            r2 = evaluate(c2, m1, base_cache); r2["disc_selected"] = True
            sel_rows.append(r2)
            print("SEL", r2["name"], f"{r2.get('meanR', np.nan):+.3f}")
    results += sel_rows
    # S2 atlanan grup analizi
    s2 = s2_analysis(CL, m1)
    # aile düzeltmeleri
    fam = [r for r in results if r.get("n", 0) > 0]
    ps = np.array([r["p_one"] if np.isfinite(r.get("p_one", np.nan)) else 1.0 for r in fam])
    o = np.argsort(ps)
    M = len(ps)
    holm = np.zeros(M, bool)
    for rank, i in enumerate(o):
        if ps[i] <= 0.05 / (M - rank):
            holm[i] = True
        else:
            break
    Z = []
    for r in fam:
        pm = np.array(r["plac_means"])
        sd = r["plac_sd"] if r["plac_sd"] > 0 else np.nan
        r["z_drift"] = (r["real_on_plac_set"] - r["plac_mean"]) / sd
        Z.append((pm - r["plac_mean"]) / sd)
    Z = np.array(Z)  # hücre × tekrar
    maxnull = np.nanmax(Z, axis=0)
    for i, r in enumerate(fam):
        r["holm"] = bool(holm[i])
        r["p_sel_maxz"] = float(np.mean(maxnull >= r["z_drift"])) if np.isfinite(r["z_drift"]) else np.nan
        verdict(r)
    for r in results:
        r.pop("plac_means", None)
    OUT.mkdir(exist_ok=True)
    (OUT / "cells.json").write_text(json.dumps({"cells": results, "s2": s2, "family_size": M},
                                               indent=1, default=float, ensure_ascii=False))
    write_md(results, s2, M)
    print("bitti", round(time.time() - t0, 1), "s")


def verdict(r: dict) -> None:
    c = {
        "c1_n150": r["n"] >= 150,
        "c2_ev": r["meanR"] > 0 and r["P"] >= 0.90,
        "c3_halves": r["half1"] >= 0 and r["half2"] >= 0,
        "c4_stress": r["stress"] > 0,
        "c5_exec": r["gap"] <= 0.5 * abs(r["meanR"]),
        "c6_single": r["single"] > 0,
        "c7_plac95": r["plac_pct"] >= 95,
        "c8_blind": r["blind"] > 0,
        "c9_holm": r["holm"],
        "c10_maxz": r["p_sel_maxz"] <= 0.10,
    }
    r["crit"] = c
    core = ["c2_ev", "c3_halves", "c4_stress", "c5_exec", "c6_single"]
    nfail = sum(not c[k] for k in core)
    if all(c.values()):
        v = "LIVE"
    elif r["meanR"] <= r["plac_mean"] or nfail >= 2:
        v = "RED"
    else:
        v = "SHADOW"
    r["verdict"] = v


def s2_analysis(CL, m1) -> dict:
    """R0B-L olaylarında atlanan (bayraklı) vs kalan grup; tam dönem ve bölme bazında."""
    out = {}
    for src, flag_fn, nm in (("R0B-L", lambda e: e["prev_ret"] > e["prev_dv"], "S2s"),
                             ("R0B-L", lambda e: e["prev_ret"] > 0.75 * e["prev_dv"], "S2s0.75"),
                             ("R0B-L", lambda e: e["prev_ret"] > 1.25 * e["prev_dv"], "S2s1.25"),
                             ("R0B-L", lambda e: e["prev_ret"] > 0.01, "S2lit"),
                             ("R0B-S", lambda e: e["prev_ret"] < -e["prev_dv"], "S2s-mirror")):
        c = [x for x in CL if x["name"] == src][0]
        ev = c["ev"].sort_values("dec").reset_index(drop=True)
        R = sim_all(m1, ev, ("real",))["real"]
        sp = lt.split_of(ev["dec"].to_numpy())
        fl = flag_fn(ev).to_numpy()
        d = {}
        for s in ("DISC", "OOS", "BLIND", "ALL"):
            mm = np.isfinite(R["R"]) & ((sp == s) if s != "ALL" else (sp != ""))
            a, b = R["R"][mm & fl], R["R"][mm & ~fl]
            d[s] = {"n_flag": int(len(a)), "R_flag": mean_or_nan(a), "n_rest": int(len(b)),
                    "R_rest": mean_or_nan(b), "diff": mean_or_nan(a) - mean_or_nan(b)}
            # tek-poz filtreli vs filtresiz
            if s != "ALL":
                ent, ext = R["ent"][mm].astype(float), R["ext"][mm]
                s_all = lt.single_position(ent, ext)
                keep = mm & ~fl
                s_f = lt.single_position(R["ent"][keep].astype(float), R["ext"][keep])
                d[s]["single_unf"] = float(R["R"][mm][s_all].mean()) if len(s_all) else np.nan
                d[s]["single_filt"] = float(R["R"][keep][s_f].mean()) if len(s_f) else np.nan
                d[s]["single_unf_sum"] = float(R["R"][mm][s_all].sum()) if len(s_all) else np.nan
                d[s]["single_filt_sum"] = float(R["R"][keep][s_f].sum()) if len(s_f) else np.nan
        out[f"{src}:{nm}"] = d
    return out


def f(x, k=3):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{k}f}"


def write_md(results, s2, M) -> None:
    L = ["# fam_trend sonuç tablosu (otomatik)", "",
         f"Aile büyüklüğü (Holm/max-z): {M} hücre. Pencere FULL = DISC∪OOS∪BLIND, POST = OOS∪BLIND.", "",
         "| hücre | birincil | pencere | n | gün | n_tekpoz | WR | başabaş WR | ortR | %95 GA | P(EV>0) | yarı1 | yarı2 | "
         "stres | 15$ | iyimser | icra farkı | tek-poz | tek-poz −en iyi 5g | −20g | plasebo yüzd. | P1 ort | taban L | "
         "taban S | DISC | OOS | BLIND | ort % | Holm | p_sel | verdikt |",
         "|" + "---|" * 31]
    for r in results:
        if r.get("n", 0) == 0:
            L.append(f"| {r['name']} | | {r['window']} | 0 |" + " |" * 27)
            continue
        ps = r["per_split"]
        L.append("| " + " | ".join([
            r["name"] + (" (DISC-seçili)" if r.get("disc_selected") else ""), "★" if r["primary"] else "",
            r["window"], str(r["n"]), str(r["n_days"]), str(r["n_single"]), f"{r['WR']:.1%}",
            f"{r['beWR']:.1%}" if np.isfinite(r["beWR"]) else "—", f(r["meanR"]),
            f"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]", f"{r['P']:.2f}", f(r["half1"]), f(r["half2"]),
            f(r["stress"]), f(r["abs15"]), f(r["opt"]), f"{r['gap']:.3f}", f(r["single"]), f(r["single_ex5"]),
            f(r["single_ex20"]), f"{r['plac_pct']:.1f}", f(r["plac_mean"]), f(r["base_L"]), f(r["base_S"]),
            f"{f(ps['DISC']['meanR'])} ({ps['DISC']['n']})", f"{f(ps['OOS']['meanR'])} ({ps['OOS']['n']})",
            f"{f(ps['BLIND']['meanR'])} ({ps['BLIND']['n']})", f"{r['pct']:+.3f}%",
            "✓" if r.get("holm") else "✗", f"{r.get('p_sel_maxz', np.nan):.3f}", r.get("verdict", "")]) + " |")
    L += ["", "## Kart ölçütleri (✓/✗)", "", "| hücre | " + " | ".join(
        ["1 n", "2 EV", "3 yarı", "4 stres", "5 icra", "6 tekpoz", "7 plasebo", "8 BLIND", "9 Holm", "10 maxz"]) + " |",
          "|" + "---|" * 11]
    for r in results:
        if "crit" in r:
            L.append(f"| {r['name']} | " + " | ".join("✓" if v else "✗" for v in r["crit"].values()) + " |")
    L += ["", "## Yıl bazında ortR (n)", ""]
    for r in results:
        if r.get("by_year"):
            L.append(f"- {r['name']}: " + ", ".join(f"{y}: {v[1]:+.3f} ({v[0]})" for y, v in r["by_year"].items())
                     + f" · çıkış türleri {r['types']}" + (f" · P2(EMA üstü her gün) {r['base_P2_aboveEMA']:+.3f}"
                                                          if "base_P2_aboveEMA" in r else ""))
    L += ["", "## S2 (kovalama atlaması) — atlanan vs kalan", ""]
    for k, d in s2.items():
        L.append(f"### {k}")
        L.append("| bölme | n bayrak | R bayrak | n kalan | R kalan | fark | tek-poz filtresiz | tek-poz filtreli | Σ filtresiz | Σ filtreli |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for s, v in d.items():
            L.append(f"| {s} | {v['n_flag']} | {f(v['R_flag'])} | {v['n_rest']} | {f(v['R_rest'])} | {f(v['diff'])} | "
                     f"{f(v.get('single_unf'))} | {f(v.get('single_filt'))} | {f(v.get('single_unf_sum'),1)} | "
                     f"{f(v.get('single_filt_sum'),1)} |")
    (OUT / "summary.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
