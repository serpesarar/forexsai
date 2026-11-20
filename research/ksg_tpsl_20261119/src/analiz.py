"""analiz.py — PROTOCOL.md seçim + geçme: T, R, A (Duka KEŞİF'te 2 hücre dondur), M; isabet/beklenti tablosu. python analiz.py"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import motor as M

FEEDS = ["DUKA_NDX", "MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000", "DUKA_M30_2016_17", "EET30", "NQ"]
BLIND = ["MT5_US500", "MT5_US30", "MT5_US2000"]
INDEP = ["DUKA_M30_2016_17", "EET30"]
POOL = ["MT5_NAS100", "EET30", "NQ"]          # + Duka TEST
KESIF_SON = pd.Timestamp("2021-10-31")
NB = 3000
RNG = np.random.default_rng(61)
T_CELLS = [f"T_{k}_{s}" for k in M.TP_K for s in M.SL_S]
R_CELLS = [f"R_{k}_{h}" for k in M.R_K for h in M.R_H]
A_CELLS = [(t, k) for t in M.A_T for k in M.A_K]


def boot_pos(v: np.ndarray, blk: np.ndarray) -> float:
    ub = np.unique(blk)
    idx = {u: np.flatnonzero(blk == u) for u in ub}
    return round(float(np.mean([v[np.concatenate([idx[u] for u in RNG.choice(ub, len(ub))])].mean() > 0 for _ in range(NB)])), 4)


def sharpe(d: pd.Series, pnl: pd.Series) -> float:
    days = pd.bdate_range(d.min(), d.max())
    s = pnl.groupby(d.values).sum().reindex(days).fillna(0)
    return round(float(s.mean() / s.std() * np.sqrt(252)), 3) if s.std() > 0 else np.nan


def a_inc(K: pd.DataFrame, t: str, k: int) -> pd.Series:
    """Eklenen birimin gece başına katkısı (eklenmeyen gece 0)."""
    add = K[f"pnl_{t}"] <= -k
    return pd.Series(np.where(add, K[f"inc_{t}"].fillna(0), 0.0), index=K.index)


def variant(K: pd.DataFrame, cell) -> pd.Series:
    """Varyantın gece başına net'i (A için iki birim toplamı)."""
    if isinstance(cell, tuple):
        return K.base + a_inc(K, *cell)
    return K[cell]


def cell_stats(K: pd.DataFrame, cell) -> dict:
    v = variant(K, cell)
    out = {"n": len(K), "ort": round(float(v.mean()), 2), "fark": round(float((v - K.base).mean()), 2),
           "isabet": round(float((v > 0).mean()), 3), "sharpe": sharpe(K.d, v), "sharpe_taban": sharpe(K.d, K.base)}
    if isinstance(cell, tuple):
        add = K[f"pnl_{cell[0]}"] <= -cell[1]
        out |= {"eklenen": int(add.sum()), "ek_birim_ort": round(float(K.loc[add, f"inc_{cell[0]}"].mean()), 2) if add.any() else None}
    return out


def ksg(N: pd.DataFrame, name: str) -> pd.DataFrame:
    K = N[N.ksg].copy()
    if name == "MT5_US500":
        K = K[K.d >= "2018-06-01"]
    return K.reset_index(drop=True)


def select(D: pd.DataFrame, cells: list, by: str) -> list:
    k = D[D.d <= KESIF_SON]
    sc = {c: cell_stats(k, c) for c in cells}
    key = (lambda c: sc[c]["sharpe"] - sc[c]["sharpe_taban"]) if by == "sharpe" else (lambda c: sc[c]["fark"])
    return sorted(cells, key=key, reverse=True)[:2]


def judge(K: dict, cell) -> dict:
    D = K["DUKA_NDX"]
    test = D[D.d > KESIF_SON]
    res = {f: cell_stats(x, cell) for f, x in K.items()} | {"DUKA_TEST": cell_stats(test, cell), "DUKA_KESIF": cell_stats(D[D.d <= KESIF_SON], cell)}
    parts = [test] + [K[f] for f in POOL]
    diff = np.concatenate([(variant(x, cell) - x.base).values for x in parts])
    blk = np.concatenate([x.blk.values for x in parts])
    P = boot_pos(diff, blk)
    a = isinstance(cell, tuple)
    better = (lambda s: s["sharpe"] > s["sharpe_taban"] and s["fark"] > 0) if a else (lambda s: s["fark"] > 0)
    ok = {"test": better(res["DUKA_TEST"]), "mt5": better(res["MT5_NAS100"]), "havuz_P": P >= 0.975,
          "kor_2_3": sum(res[f]["fark"] > 0 for f in BLIND) >= 2, "bagimsiz": all(res[f]["fark"] > 0 for f in INDEP),
          "sharpe": all(res[f]["sharpe"] > res[f]["sharpe_taban"] for f in ("DUKA_NDX", "MT5_NAS100"))}
    h = "B" if all(ok.values()) else ("X" if not (ok["test"] and ok["mt5"]) else "C")
    return {"hucre": str(cell), "olcum": res, "havuz_P": P, "olcut": ok, "hukum": h}


def m_family(K: dict) -> dict:
    out, parts = {}, []
    for f in ("DUKA_NDX", "NQ"):
        x = K[f].dropna(subset=["m"])
        segs = {"tum": x} if f == "NQ" else {"KESIF": x[x.d <= KESIF_SON], "TEST": x[x.d > KESIF_SON]}
        for s, z in segs.items():
            hi, lo = z[z.m >= 0.5].base, z[z.m < 0.5].base
            out[f"{f}_{s}"] = {"m>=0.5": [len(hi), round(float(hi.mean()), 2)], "m<0.5": [len(lo), round(float(lo.mean()), 2)],
                               "fark": round(float(hi.mean() - lo.mean()), 2),
                               "tertil": {str(q): round(float(g.base.mean()), 2) for q, g in z.groupby(pd.qcut(z.m.clip(-2, 3), 3, labels=False))}}
        parts.append(x)
    x = pd.concat(parts)
    hi, lo = x[x.m >= 0.5], x[x.m < 0.5]
    diffs = []
    blks = x.blk.unique()
    idx = {u: np.flatnonzero(x.blk.values == u) for u in blks}
    for _ in range(NB):
        ii = np.concatenate([idx[u] for u in RNG.choice(blks, len(blks))])
        z = x.iloc[ii]
        diffs.append(z[z.m >= 0.5].base.mean() - z[z.m < 0.5].base.mean())
    out["havuz"] = {"fark": round(float(hi.base.mean() - lo.base.mean()), 2), "P": round(float(np.mean(np.array(diffs) > 0)), 4)}
    ok = out["DUKA_NDX_KESIF"]["fark"] > 0 and out["DUKA_NDX_TEST"]["fark"] > 0 and out["NQ_tum"]["fark"] > 0 and out["havuz"]["P"] >= 0.95
    out["hukum"] = "B" if ok else ("C" if out["havuz"]["fark"] > 0 else "X")
    return out


def counter_arm(N: dict) -> dict:
    """E116: KSG-olmayan gecelerde aynı düşüş koşulunda eklenen birim (betimleyici)."""
    out = {}
    for f in ("DUKA_NDX", "MT5_NAS100"):
        x = N[f][~N[f].ksg]
        out[f] = {f"{t}|{k}": round(float(x.loc[x[f"pnl_{t}"] <= -k, f"inc_{t}"].mean()), 2) for t, k in A_CELLS}
    return out


def main() -> None:
    N = {f: M.add_rescue(M.table(f)) for f in FEEDS}
    K = {f: ksg(N[f], f) for f in FEEDS}
    for f in FEEDS:
        print(f, "gece", len(K[f]), "taban", round(K[f].base.mean(), 2), "isabet", round((K[f].base > 0).mean(), 3), flush=True)
    res = {"taban": {f: cell_stats(K[f], "base") for f in FEEDS}}
    res["tablo_duka"] = {str(c): cell_stats(K["DUKA_NDX"], c) for c in T_CELLS + R_CELLS + A_CELLS}
    res["tablo_mt5"] = {str(c): cell_stats(K["MT5_NAS100"], c) for c in T_CELLS + R_CELLS + A_CELLS}
    for fam, cells, by in (("T", T_CELLS, "fark"), ("R", R_CELLS, "fark"), ("A", A_CELLS, "sharpe")):
        sel = select(K["DUKA_NDX"], cells, by)
        res[fam] = [judge(K, c) for c in sel]
        for j in res[fam]:
            print(fam, j["hucre"], j["hukum"], j["olcut"], "P", j["havuz_P"], flush=True)
    res["M"] = m_family(K)
    print("M", json.dumps(res["M"], ensure_ascii=False))
    res["A_karsi_kol"] = counter_arm(N)
    (M.HERE / "results/analiz.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
