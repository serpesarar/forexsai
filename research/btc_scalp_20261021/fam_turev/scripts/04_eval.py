"""prereg.md §6–§8: tüm hücreler, DISC seçimi, max-z, plasebolar, kart, verdikt → out/

Kullanım: python -I 04_eval.py [n_null=500]
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 500
NBOOT = 2000
RNG = np.random.default_rng(20261022)
MIN_N_DISC = 50
SB_MAX = 0.005
GROSS_EDGE_R = 0.15
GROSS_EDGE_BP = 2 * C.COSTS["PEP"]

OUTS: dict = {}
BASE = np.load(C.CACHE / "base.npz")
OPEN = BASE["o"]
PREVC = np.concatenate([[np.nan], BASE["c"][:-1]])


def arr(H: int, name: str) -> np.ndarray:
    k = (H, name)
    if k not in OUTS:
        if H not in OUTS:
            OUTS[H] = np.load(C.CACHE / f"out_H{H}.npz")
        OUTS[k] = OUTS[H][name]
    return OUTS[k]


def trades(e: np.ndarray, d: int, r: float, H: int, cost: float | str = "PEP") -> dict:
    """Geçerli girişlerin sonuçları (e sıralı)."""
    v = arr(H, "valid")[e]
    e = e[v]
    key = f"d{d}_r{r}"
    s = arr(H, "s_bp")[e].astype(np.float64)
    gb = arr(H, f"gb_{key}")[e].astype(np.float64)
    slip = arr(H, f"slip_{key}")[e].astype(np.float64)
    cb = 15.0 / OPEN[e] * 1e4 if cost == "FIX15" else (C.COSTS[cost] if isinstance(cost, str) else cost)
    R = (gb - cb - slip) / s
    return {"e": e, "R": R, "s": s, "gb": gb, "slip": slip, "bp": gb - cb - slip,
            "xt": arr(H, f"xt_{key}")[e], "xo": arr(H, f"xo_{key}")[e].astype(np.int64), "sb": arr(H, f"sb_{key}")[e],
            "gbo": arr(H, f"gbo_{key}")[e].astype(np.float64), "gbh": arr(H, f"gbh_{key}")[e].astype(np.float64),
            "sliph": arr(H, f"sliph_{key}")[e].astype(np.float64)}


def cz(e: np.ndarray, R: np.ndarray) -> tuple[float, float, float]:
    """ort, gün-kümeli SE, z."""
    n = len(R)
    if n < 2:
        return (float(R.mean()) if n else np.nan), np.nan, np.nan
    m = R.mean()
    day = e // 1440
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=R - m)
    se = np.sqrt((S ** 2).sum()) / n
    return float(m), float(se), float(m / se) if se > 0 else np.nan


def boot(e: np.ndarray, R: np.ndarray) -> tuple[float, float, float]:
    if len(R) < 5:
        return np.nan, np.nan, np.nan
    day = e // 1440
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=R)
    n = np.bincount(inv)
    D = len(u)
    w = RNG.multinomial(D, np.full(D, 1 / D), size=NBOOT)
    mb = (w @ S) / (w @ n)
    return float((mb > 0).mean()), float(np.percentile(mb, 2.5)), float(np.percentile(mb, 97.5))


def single_pos(t: dict) -> np.ndarray:
    keep = []
    free = -1
    for i, (e, xo) in enumerate(zip(t["e"], t["xo"])):
        if e >= free:
            keep.append(i)
            free = e + xo + 1
    return np.asarray(keep, dtype=np.int64)


def seg_mask(e: np.ndarray, segs: tuple[str, ...]) -> np.ndarray:
    sg = C.seg_of(e)
    want = [["DISC", "OOS", "BLIND"].index(x) for x in segs]
    return np.isin(sg, want)


# ---------- plasebo havuzları (yıl × UTC saati × bölme, yön/geometri aynı) ----------
POOLS: dict = {}


def pool(H: int):
    if H not in POOLS:
        ev = np.where(arr(H, "valid"))[0]
        key = C.seg_of(ev).astype(np.int64) * 10**6 + C.year_of(ev).astype(np.int64) * 100 + (ev % 1440) // 60
        o = np.argsort(key, kind="stable")
        ev, key = ev[o], key[o]
        uk, st, cnt = np.unique(key, return_index=True, return_counts=True)
        POOLS[H] = (ev, uk, st, cnt)
    return POOLS[H]


def placebo_hour(e: np.ndarray, d: int, r: float, H: int, real_mean: float, nrep: int = NREP):
    ev, uk, st, cnt = pool(H)
    key = C.seg_of(e).astype(np.int64) * 10**6 + C.year_of(e).astype(np.int64) * 100 + (e % 1440) // 60
    j = np.searchsorted(uk, key)
    assert np.all(uk[j] == key)
    idx = st[j][:, None] + (RNG.random((len(e), nrep)) * cnt[j][:, None]).astype(np.int64)
    ep = ev[idx]
    key2 = f"d{d}_r{r}"
    s = arr(H, "s_bp")[ep]
    gb = arr(H, f"gb_{key2}")[ep]
    R = (gb - C.COSTS["PEP"] - arr(H, f"slip_{key2}")[ep]) / s
    mR = R.mean(axis=0)
    mG = (gb / s).mean(axis=0)
    return float((mR < real_mean).mean()), float(mR.mean()), float(mG.mean())


def shift_e(e: np.ndarray, a: int, b: int, D: int) -> np.ndarray:
    return a + ((e - a + D * 1440) % (b - a))


def placebo_circ(e_all_t: np.ndarray, d: int, r: float, H: int, segs: tuple[str, ...], real_mean: float, nrep: int = NREP):
    """Koşul serisinin tam-gün dairesel kaydırması; her bölme kendi içinde sarılır."""
    out = np.full(nrep, np.nan)
    days_ = {nm: (C.seg_bounds(nm)) for nm in segs}
    for i in range(nrep):
        Rs = []
        for nm, (a, b) in days_.items():
            nd = (b - a) // 1440
            D = int(RNG.integers(30, max(31, nd - 30)))
            ee = e_all_t[(e_all_t >= a) & (e_all_t < b)]
            if len(ee) == 0:
                continue
            es = np.sort(shift_e(ee, a, b, D))
            Rs.append(trades(es, d, r, H)["R"])
        if Rs:
            out[i] = np.concatenate(Rs).mean()
    return float((out < real_mean).mean()), float(np.nanmean(out))


def describe(t: dict, mask: np.ndarray) -> dict:
    e, R = t["e"][mask], t["R"][mask]
    n = len(R)
    if n == 0:
        return {"n": 0}
    m, se, z = cz(e, R)
    days = len(np.unique(e // 1440))
    return {"n": n, "days": days, "WR": float((R > 0).mean()), "meanR": m, "bp": float(t["bp"][mask].mean()),
            "grossR": float((t["gb"][mask] / t["s"][mask]).mean()), "grossbp": float(t["gb"][mask].mean()),
            "se": se, "z": z, "sb_rate": float(t["sb"][mask].mean()), "s_bp_med": float(np.median(t["s"][mask])),
            "tp_share": float((t["xt"][mask] == 1).mean()), "sl_share": float((t["xt"][mask] == -1).mean())}


def main() -> None:
    sig = pickle.load(open(C.CACHE / "signals.pkl", "rb"))
    a_d, b_d = C.seg_bounds("DISC")
    # ---------- 1) tüm hücreler ----------
    cells = []
    for si, s in enumerate(sig):
        e_all = s["t"] + 1
        for H in s["Hset"]:
            for r in C.RS:
                t = trades(e_all, s["dir"], r, H)
                row = {"si": si, "hid": s["hid"], "par": s["par"], "dir": s["dir"], "kind": s["kind"], "r": r, "H": H}
                for nm in ("DISC", "OOS", "BLIND"):
                    dsc = describe(t, seg_mask(t["e"], (nm,)))
                    for k_ in ("n", "meanR", "bp", "z", "sb_rate", "grossR"):
                        row[f"{nm}_{k_}"] = dsc.get(k_, np.nan)
                dsc = describe(t, seg_mask(t["e"], ("OOS", "BLIND")))
                for k_ in ("n", "meanR", "bp", "z"):
                    row[f"POST_{k_}"] = dsc.get(k_, np.nan)
                row["p_DISC"] = float(1 - norm.cdf(row["DISC_z"])) if np.isfinite(row["DISC_z"]) else 1.0
                cells.append(row)
    cdf = pd.DataFrame(cells)
    # DISC Holm (468 hücre)
    p = cdf["p_DISC"].to_numpy()
    o = np.argsort(p)
    m_ = len(p)
    adj = np.maximum.accumulate((m_ - np.arange(m_)) * p[o])
    holm = np.empty(m_)
    holm[o] = np.minimum(adj, 1)
    cdf["holm_DISC"] = holm
    print("hücre sayısı", len(cdf), "DISC Holm<0,05:", int((cdf["holm_DISC"] < 0.05).sum()))

    # ---------- 2) max-z null (DISC, tüm aile, ortak tam-gün kaydırma) ----------
    nd = (b_d - a_d) // 1440
    maxz = np.full(NREP, -np.inf)
    for i in range(NREP):
        D = int(RNG.integers(30, nd - 30))
        for si, s in enumerate(sig):
            ee = s["t"] + 1
            ee = ee[(ee >= a_d) & (ee < b_d)]
            es = np.sort(shift_e(ee, a_d, b_d, D))
            for H in s["Hset"]:
                for r in C.RS:
                    t = trades(es, s["dir"], r, H)
                    if len(t["R"]) < MIN_N_DISC or t["sb"].mean() >= SB_MAX:
                        continue
                    z = cz(t["e"], t["R"])[2]
                    if np.isfinite(z) and z > maxz[i]:
                        maxz[i] = z
        if i % 50 == 0:
            print("max-z kopya", i, round(maxz[i], 2), flush=True)
    np.save(C.OUT / "maxz_null.npy", maxz)

    # ---------- 3) ID başına seçim ve tam rapor ----------
    elig = (cdf["DISC_n"] >= MIN_N_DISC) & (cdf["DISC_sb_rate"] < SB_MAX)
    cdf["eligible"] = elig
    cdf["p_sel_cell"] = [float((maxz >= z).mean()) if np.isfinite(z) else 1.0 for z in cdf["DISC_z"]]
    cdf.to_csv(C.OUT / "cells.csv", index=False)
    sel_rows = []
    hids = list(dict.fromkeys(s["hid"] for s in sig))
    for hid in hids:
        sub = cdf[(cdf["hid"] == hid) & cdf["eligible"]]
        if len(sub) == 0:
            sel_rows.append({"hid": hid, "evaluable": False})
            continue
        best = sub.loc[sub["DISC_z"].idxmax()]
        s = sig[int(best["si"])]
        r, H, d = float(best["r"]), int(best["H"]), int(best["dir"])
        e_all = s["t"] + 1
        t = trades(e_all, d, r, H)
        post = seg_mask(t["e"], ("OOS", "BLIND"))
        res = {"hid": hid, "evaluable": True, "par": s["par"], "dir": d, "r": r, "H": H, "kind": s["kind"],
               "DISC": describe(t, seg_mask(t["e"], ("DISC",))), "OOS": describe(t, seg_mask(t["e"], ("OOS",))),
               "BLIND": describe(t, seg_mask(t["e"], ("BLIND",))), "POST": describe(t, post),
               "ALL": describe(t, seg_mask(t["e"], ("DISC", "OOS", "BLIND")))}
        res["p_sel"] = float((maxz >= best["DISC_z"]).mean())
        P = res["POST"]
        if P["n"] > 0:
            eP, RP = t["e"][post], t["R"][post]
            res["P_EV"], res["CI_lo"], res["CI_hi"] = boot(eP, RP)
            h = len(RP) // 2
            res["half1"], res["half2"] = float(RP[:h].mean()) if h else np.nan, float(RP[h:].mean())
            ts = trades(e_all, d, r, H, "PEP_STRESS")
            res["stress"] = float(ts["R"][seg_mask(ts["e"], ("OOS", "BLIND"))].mean())
            for cn in ("FIX15", "BIN_MAKER", "BIN_TAKER"):
                tc = trades(e_all, d, r, H, cn)
                res[f"net_{cn}"] = float(tc["R"][seg_mask(tc["e"], ("OOS", "BLIND"))].mean())
            opt = float((t["gbo"][post] / t["s"][post]).mean())
            res["optR"] = opt
            res["exec_gap"] = opt - P["meanR"]
            res["heurR"] = float(((t["gbh"][post] - C.COSTS["PEP"] - t["sliph"][post]) / t["s"][post]).mean())
            tp = {k: v[post] for k, v in t.items()}
            sp = single_pos(tp)
            res["single_n"], res["single_R"] = int(len(sp)), float(tp["R"][sp].mean()) if len(sp) else np.nan
            res["plc_hour_pct"], res["plc_hour_R"], res["plc_hour_grossR"] = placebo_hour(eP, d, r, H, P["meanR"])
            res["plc_circ_pct"], res["plc_circ_R"] = placebo_circ(e_all, d, r, H, ("OOS", "BLIND"), P["meanR"], nrep=200)
            res["gross_edge_R"] = P["grossR"] - res["plc_hour_grossR"]
            res["p_post"] = float(1 - norm.cdf(P["z"])) if np.isfinite(P["z"]) else 1.0
            ndays_post = (C.seg_bounds("OOS")[1] - C.seg_bounds("OOS")[0] + C.seg_bounds("BLIND")[1] - C.seg_bounds("BLIND")[0]) / 1440
            res["trades_per_day"] = P["n"] / ndays_post
            yrs = C.year_of(t["e"])
            res["years"] = {int(y): {"n": int((yrs == y).sum()), "R": float(t["R"][yrs == y].mean()),
                                     "bp": float(t["bp"][yrs == y].mean())} for y in np.unique(yrs)}
            # sağlamlık: +1 dk gecikme
            t1 = trades(e_all + 1, d, r, H)
            res["lag1_POST_R"] = float(t1["R"][seg_mask(t1["e"], ("OOS", "BLIND"))].mean())
            # mod aynası
            tm = trades(e_all, -d, r, H)
            res["mirror_POST_R"] = float(tm["R"][seg_mask(tm["e"], ("OOS", "BLIND"))].mean())
            if hid.startswith("DV03d") and res["BLIND"]["n"] > 0:
                eb = t["e"][seg_mask(t["e"], ("BLIND",))]
                Rb = t["R"][seg_mask(t["e"], ("BLIND",))]
                est = BASE["fl_est"][eb - 1] == 1
                res["BLIND_R_noest"] = float(Rb[~est].mean()) if (~est).any() else np.nan
        sel_rows.append(res)

    # POST Holm (40 ID; değerlendirilemeyen p=1)
    pv = np.array([x.get("p_post", 1.0) for x in sel_rows])
    o = np.argsort(pv)
    m_ = len(pv)
    adj = np.maximum.accumulate((m_ - np.arange(m_)) * pv[o])
    hp = np.empty(m_)
    hp[o] = np.minimum(adj, 1)
    for x, h_ in zip(sel_rows, hp):
        x["holm_post"] = float(h_)
        if not x.get("evaluable") or x["POST"]["n"] == 0:
            x["verdict"] = "RED (değerlendirilemez)" if not x.get("evaluable") else "RED (POST olay yok)"
            x["card"] = 0
            continue
        P = x["POST"]
        primary_plc = x["plc_circ_pct"] if x["kind"] == "regime" else x["plc_hour_pct"]
        x["plc_primary_pct"] = primary_plc
        c1 = P["n"] >= 150
        c2 = P["meanR"] > 0 and x["P_EV"] >= 0.90
        c3 = x["half1"] >= 0 and x["half2"] >= 0
        c4 = x["stress"] > 0
        c5 = abs(x["exec_gap"]) <= 0.5 * abs(P["meanR"])
        c6 = x["single_R"] > 0
        x["card_flags"] = [bool(c) for c in (c1, c2, c3, c4, c5, c6)]
        x["card"] = int(sum(x["card_flags"]))
        blind_pos = x["BLIND"].get("n", 0) > 0 and x["BLIND"]["meanR"] > 0
        gross_ok = (x["gross_edge_R"] >= GROSS_EDGE_R) or (P["grossbp"] >= GROSS_EDGE_BP)
        sb_ok = P["sb_rate"] < SB_MAX
        x["blind_pos"], x["gross_ok"], x["sb_ok"] = bool(blind_pos), bool(gross_ok), bool(sb_ok)
        if x["card"] == 6 and primary_plc >= 0.95 and blind_pos and gross_ok and sb_ok and x["holm_post"] < 0.05 and x["p_sel"] <= 0.10:
            x["verdict"] = "LIVE-aday"
        elif P["meanR"] > 0 and x["P_EV"] >= 0.90 and x["card"] >= 5 and primary_plc >= 0.90 and blind_pos and sb_ok:
            x["verdict"] = "GÖLGE-aday"
        elif not sb_ok:
            x["verdict"] = "RED (aynı-bar ≥ %0,5 → hücre geçersiz, prereg §3)"
        else:
            x["verdict"] = "RED"
    json.dump(sel_rows, open(C.OUT / "selected.json", "w"), indent=1, default=float)
    # özet tablo
    rows = []
    for x in sel_rows:
        if not x.get("evaluable"):
            rows.append({"hid": x["hid"], "verdict": x["verdict"]})
            continue
        P, D_, O_, Bl = x["POST"], x["DISC"], x["OOS"], x["BLIND"]
        rows.append({
            "hid": x["hid"], "cell": f"{x['par']} r{x['r']} H{x['H']}", "dir": x["dir"],
            "DISC_n": D_["n"], "DISC_R": D_["meanR"], "DISC_z": D_["z"], "p_sel": x["p_sel"],
            "POST_n": P.get("n"), "WR": P.get("WR"), "POST_R": P.get("meanR"), "POST_bp": P.get("bp"),
            "CI": f"[{x.get('CI_lo', np.nan):+.3f}, {x.get('CI_hi', np.nan):+.3f}]", "P_EV": x.get("P_EV"),
            "half1": x.get("half1"), "half2": x.get("half2"), "stress": x.get("stress"), "exec_gap": x.get("exec_gap"),
            "single": x.get("single_R"), "plc_hour": x.get("plc_hour_pct"), "plc_circ": x.get("plc_circ_pct"),
            "OOS_R": O_.get("meanR"), "BLIND_n": Bl.get("n"), "BLIND_R": Bl.get("meanR"),
            "gross_edge_R": x.get("gross_edge_R"), "grossbp": P.get("grossbp"), "sb": P.get("sb_rate"),
            "years": " ".join(f"{y % 100}:{'+' if v['R'] > 0 else '-'}" for y, v in x.get("years", {}).items()),
            "tpd": x.get("trades_per_day"), "holm": x["holm_post"], "card": x["card"], "lag1": x.get("lag1_POST_R"),
            "mirror": x.get("mirror_POST_R"), "fix15": x.get("net_FIX15"), "maker": x.get("net_BIN_MAKER"),
            "taker": x.get("net_BIN_TAKER"), "heur": x.get("heurR"), "verdict": x["verdict"]})
    sdf = pd.DataFrame(rows)
    sdf.to_csv(C.OUT / "summary.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    print(sdf.round(3).to_string())


if __name__ == "__main__":
    main()
