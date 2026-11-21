"""kq6_analiz.py — KQ-06 (PROTOCOL.md): giriş yeri (E0–E4) × tutuş şartı (U0–U3) × tutuş payı h, korumasız kâr çıkışı.

python kq6_analiz.py → results/analiz6.json
"""
from __future__ import annotations

import itertools
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import kq3_analiz as K3  # noqa: E402
import kq4_analiz as K4  # noqa: E402

B, A, CA, K2 = K3.B, K3.A, K3.CA, K4.K2
V, FIN = K2.V, B.FIN
STOP_K, MAXC = 3.0, 5
FRESH_MKT = ["FCHI", "AEX", "SSMI", "IBEX", "GSPTSE", "AXJO", "KS11", "BVSP", "TWII", "MXX"]
for n in FRESH_MKT:
    V.G.KOR[n] = HERE / f"data/{n}.csv"
    K2.Q.DAILY[n] = V.daily(n)
ENTRIES = ["E0", "E1", "E2", "E3a", "E3b", "E4"]
ELIG = ["U0", "U1", "U2", "U3"]
HS = (0.5, 1.0)
CELLS = {f"{e}_{u}_h{h}": (e, u, h) for e, u, h in itertools.product(ENTRIES, ELIG, HS)}
FF: dict[str, pd.DataFrame] = {}


def feats(idx: str) -> pd.DataFrame:
    if idx not in FF:
        FF[idx] = V.FF[idx] if idx in V.FF else V.feat_frame(idx)
    return FF[idx]


def eligible(ev: dict, u: str) -> bool:
    if u == "U0":
        return True
    f = feats(ev["idx"])
    d = pd.Timestamp(ev["d"]).normalize()
    k = int(f.index.searchsorted(d))
    if k >= len(f) or f.index[k] != d:
        return True
    row = f.iloc[k]
    val = {"U1": row["sma200"] > 0, "U2": row["vix"] < 30, "U3": row["dd252"] > -0.15}[u]
    return bool(val) if pd.notna(row[{"U1": "sma200", "U2": "vix", "U3": "dd252"}[u]]) else True


# ───────── tek yarım/tam pozisyon yolu ─────────
def _walk(ev: dict, E: float, start: int, first_check: int, h: float, daily: bool, entry_is_open: bool = False) -> tuple[float, int]:
    """start: stop denetiminin başladığı bar (feed) / gün (daily); first_check: ilk kâr kontrol kapanışı."""
    dv, lo, op, dd, seg, cl = ev["dvol"], ev["lo"], ev["op"], ev["dd"], ev["seg"], ev["cl"]
    fac = ev["fac"]
    S = E * (1 - STOP_K * dv)
    n = len(cl)
    locked, w = 0.0, 1.0
    pos = start
    for s in range(first_check, n):
        end = seg[s] if not daily else s + 1
        seg_lo, seg_op = lo[pos:end], op[pos:end]
        hit = np.flatnonzero(seg_lo <= S)
        if hit.size:
            j = pos + int(hit[0])
            o = seg_op[int(hit[0])]
            if daily and (j == 0 or (entry_is_open and j == start)):
                o = np.inf                                   # gün içi giriş: açılış girişten önce
            fill = min(S, o) * fac
            return locked + w * ((fill / E - 1) * 1e4 - FIN * dd[j]), s
        pos = end
        r = (cl[s] / E - 1) * 1e4 - FIN * (dd[s] if daily else _cal_days(ev, s))
        if cl[s] >= E or s - first_check >= MAXC or s == n - 1:
            return locked + w * r, s
        if s == first_check and h < 1.0:
            locked += (1 - h) * r
            w = h
    return locked, n - 1


def _cal_days(ev: dict, s: int) -> float:
    """Feed: kapanış s'nin takvim günü farkı = res'ten geri çöz (res = (cl/E0−1)·1e4 − FIN·gün)."""
    return ((ev["cl"][s] / ev["E"] - 1) * 1e4 - ev["res"][s]) / FIN if FIN else 0.0


def sim(ev: dict, cell: tuple) -> tuple[float, int]:
    e, u, h = cell
    if not eligible(ev, u):
        return B.simulate(ev, B.BASE)[0], 0
    daily = ev["feed"].startswith("G_")
    E0 = ev["E"]
    if daily:
        ask = 2 - ev["fac"]
        c0_ask = ev["cl"][0] / ev["fac"] * ask
        d1_ask = ev["op"][1] * ask if len(ev["op"]) > 1 else np.nan
    else:
        sp = ev.get("sp_bp", 0.0) / 1e4
        c0_ask = ev["cl"][0] * (1 + sp)
        d1_ask = np.nan
    if e == "E0":
        return _walk(ev, E0, 0, 0, h, daily)
    if e == "E1":
        return _walk(ev, c0_ask, 1 if daily else ev["seg"][0], 1, h, daily)
    if e == "E2":
        a, sa = _walk(ev, E0, 0, 0, h, daily)
        b, sb = _walk(ev, c0_ask, 1 if daily else ev["seg"][0], 1, h, daily)
        return 0.5 * a + 0.5 * b, max(sa, sb)
    if e in ("E3a", "E3b"):
        k = 0.5 if e == "E3a" else 1.0
        lim = E0 * (1 - k * ev["dvol"])
        d0 = ev["lo"][0:1] if daily else ev["lo"][0:ev["seg"][0]]
        hit = np.flatnonzero(d0 <= lim)
        if not hit.size:
            return 0.0, 0
        j = 0 if daily else int(hit[0])
        return _walk(ev, lim, j, 0, h, daily)
    if e == "E4":
        if not daily:
            return np.nan, 0
        if not np.isfinite(d1_ask):
            return np.nan, 0
        return _walk(ev, d1_ask, 1, 1, h, daily, entry_is_open=True)
    raise ValueError(e)


def frame(P: list[dict]) -> pd.DataFrame:
    rows = []
    for ev in P:
        r = {"set": ev["set"], "idx": ev["idx"], "feed": ev["feed"], "d": pd.Timestamp(ev["d"]), "base": B.simulate(ev, B.BASE)[0],
             "kar": B.simulate(ev, B.KAR)[0], "sp_bp": ev.get("sp_bp", np.nan),
             "opt_bp": (ev["E"] / ev["e_opt"] - 1) * 1e4 if ev.get("e_opt") else np.nan}
        for c, cell in CELLS.items():
            r[c], r[c + "#s"] = sim(ev, cell)
        rows.append(r)
    T = pd.DataFrame(rows)
    T["grp"] = np.where(T.set == "G2016", "G2016_" + T.idx, T.set)
    T["blk"] = T.grp + "|" + T.d.dt.to_period("M").astype(str)
    return T


def fresh_markets(cells: list[str]) -> dict:
    out = {"kapsam": {}, "hucre": {}}
    parts = []
    for n in FRESH_MKT:
        k = K2.daily_paths(n, "1990-01-01", "2015-12-31", "KESIF")
        if sum(e["cl"][0] < e["E"] for e in k) < 20:
            k = K2.daily_paths(n, "1990-01-01", "2009-12-31", "KESIF")
        rate = K4.recovery(k)
        t = K2.daily_paths(n, "2016-01-01", "2026-12-31", "YENI")
        out["kapsam"][n] = {"kesif_olay": len(k), "toparlanma": round(rate, 3) if np.isfinite(rate) else None,
                            "kapsam_ici": bool(np.isfinite(rate) and rate >= K4.SCOPE_MIN), "test_olay": len(t)}
        if out["kapsam"][n]["kapsam_ici"] and t:
            parts.append(t)
    P = [e for p in parts for e in p]
    if not P:
        return out
    rows = []
    for ev in P:
        r = {"idx": ev["idx"], "d": pd.Timestamp(ev["d"]), "base": B.simulate(ev, B.BASE)[0], "kar": B.simulate(ev, B.KAR)[0]}
        for c in cells:
            r[c] = sim(ev, CELLS[c])[0]
        rows.append(r)
    T = pd.DataFrame(rows)
    T["blk"] = T.idx + "|" + T.d.dt.to_period("M").astype(str)
    for c in cells + ["kar"]:
        x = T.dropna(subset=[c])
        o = {"n": len(x), "fark": round(float((x[c] - x.base).mean()), 1), "P": CA.boot((x[c] - x.base).values, x.blk.values),
             "isabet": [round(float((x.base > 0).mean()), 3), round(float((x[c] > 0).mean()), 3)],
             "cvar5": [round(CA.cvar5(x.base), 0), round(CA.cvar5(x[c]), 0)],
             "endeks_fark": {n: round(float((g[c] - g.base).mean()), 1) for n, g in x.groupby("idx")}}
        o["ok"] = o["fark"] > 0 and o["P"] >= 0.90 and o["cvar5"][1] >= 2 * o["cvar5"][0]
        out["hucre"][c] = o
    return out


def main() -> None:
    P = [e for e in pickle.load(open(HERE / "cache/yollar2.pkl", "rb")) if e["idx"] != "GDAXI" and (e["set"] != "KESIF" or e["idx"] in K3.US)]
    T = frame(P)
    K3.CELLS = dict(CELLS) | {"KAR_korumasiz": None}      # select() referans satırı ister; E0_U0_h1.0 ile aynı hücre
    K = T[T.set == "KESIF"]
    T["KAR_korumasiz"] = T.kar
    sel = K3.select(T)
    sel["secilen"] = list(dict.fromkeys("E0_U0_h1.0" if c == "KAR_korumasiz" else c for c in sel["secilen"]))
    K3.CELLS = CELLS
    chosen = sel["secilen"]
    fm = fresh_markets(chosen)
    out = {"secim": sel, "taze_piyasa": fm, "hucre": {},
           "kesif_tum": {c: {"fark": round(float((K[c] - K.base).mean()), 1), "isabet": round(float((K[c] > 0).mean()), 3),
                             "cvar5": round(CA.cvar5(K[c]), 0)} for c in CELLS}}
    for c in chosen:
        x = T.copy()
        x[c] = x[c].fillna(x.base) if c.startswith("E4") else x[c]
        j = K3.judge(x, c)
        j["kart"] = K3.card(x, c)
        ok_new = fm["hucre"].get(c, {}).get("ok", False)
        j["hukum_kq06"] = "B" if all(j["olcut"].values()) and ok_new and j["kart"]["verdikt"] == "LIVE" else (
            "X" if j["olcum"]["DUKA_NDX"]["fark"] <= 0 else "C")
        out["hucre"][c] = j
    json.dump(out, open(HERE / "results/analiz6.json", "w"), ensure_ascii=False, indent=1, default=float)
    T.to_pickle(HERE / "cache/sonuc6.pkl")
    out["tutarlilik_E0_U0_h1_eq_kar"] = {g: round(float((T[T.grp == g]["E0_U0_h1.0"] - T[T.grp == g].kar).abs().max()), 3)
                                         for g in ["KESIF", "DUKA_NDX", "MT5_NAS100", "EET30"]}
    print("tutarlilik", out["tutarlilik_E0_U0_h1_eq_kar"])
    print(json.dumps({"secilen": chosen, "uygun": sel["uygun"], "kapsam": fm["kapsam"],
                      "hukum": {c: (v["hukum_kq06"], v["olcut"], v["havuz_P"], v["kart"]["verdikt"]) for c, v in out["hucre"].items()},
                      "ndx": {c: v["olcum"]["DUKA_NDX"] for c, v in out["hucre"].items()},
                      "taze": fm["hucre"]}, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
