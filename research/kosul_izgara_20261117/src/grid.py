"""grid.py — PROTOCOL: giriş anı × tutuş × yön × koşul ızgarası; KEŞİF 2018–21 maxT seçimi, KÖR-1 2022–23, KÖR-2 2024–26.
Çıktı results/returns.parquet, results/conds.parquet, results/grid.json"""
from __future__ import annotations

import itertools
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
ANCH = {"A01_1800": -360, "A02_2000": -240, "A03_0300": 180, "A04_0830": 510, "A05_0930": 570, "A06_1000": 600, "A07_1100": 660,
        "A08_1200": 720, "A09_1300": 780, "A10_1400": 840, "A11_1500": 900, "A12_1530": 930, "A13_1600": 960}
HOLDS = ("h60", "h120", "h240", "seans", "g1")
PER = {"KESIF": (date(2018, 1, 1), date(2021, 12, 31)), "KOR1": (date(2022, 1, 1), date(2023, 12, 31)),
       "KOR2": (date(2024, 1, 1), date(2026, 12, 31))}


def returns(m1, D) -> pd.DataFrame:
    days = D.d.tolist(); full = dict(zip(D.d, D.full))
    t = m1.t
    rows = []
    for i, d in enumerate(days):
        if not full.get(d) or i + 1 >= len(days):
            continue
        nd = days[i + 1]
        for a, mn in ANCH.items():
            j = m1.idx_from(lib.utc(d, mn), 300)
            if j is None:
                continue
            exits = {"h60": t[j] + 3600, "h120": t[j] + 7200, "h240": t[j] + 14400,
                     "seans": lib.utc(d, 570) if mn < 570 else (lib.utc(d, 955) if mn < 960 else lib.utc(nd, 570)),
                     "g1": lib.utc(nd, mn) if mn >= 0 else lib.utc(nd, mn)}
            for hname, te in exits.items():
                if te <= t[j]:
                    continue
                k = int(np.searchsorted(t, te))
                if k >= len(t) or t[k] - te > 3 * 3600:
                    continue
                nights = (pd.Timestamp(t[k], unit="s").date() - pd.Timestamp(t[j], unit="s").date()).days
                fin = lib.FIN_BP_PER_DAY * nights
                ask_in, bid_in = m1.o[j] + m1.spr[j], m1.o[j]
                bid_out, ask_out = m1.o[k], m1.o[k] + m1.spr[k]
                rows.append({"d": d, "a": a, "h": hname,
                             "L": (bid_out / ask_in - 1) * 1e4 - fin, "S": -(ask_out / bid_in - 1) * 1e4,
                             "L15": (bid_out / ask_in - 1) * 1e4 - fin - 0.5 * (m1.spr[j] + m1.spr[k]) / m1.o[j] * 1e4,
                             "S15": -(ask_out / bid_in - 1) * 1e4 - 0.5 * (m1.spr[j] + m1.spr[k]) / m1.o[j] * 1e4,
                             "above_open": (m1.o[j] > (D.open930.iloc[i] if np.isfinite(D.open930.iloc[i]) else np.nan)) if mn >= 600 else np.nan})
    return pd.DataFrame(rows)


def conditions(D, vixp) -> pd.DataFrame:
    full = D[D.full & D.close.notna()].reset_index(drop=True)
    cl = full.set_index("d").close
    out = pd.DataFrame(index=pd.Index(D.d, name="d"))
    prev_close = cl.reindex(D.d).ffill().shift(1)
    v = pd.Series({d: vixp.get(d, np.nan) for d in D.d})
    out["VIX<15"] = v < 15; out["VIX15-18"] = (v >= 15) & (v < 18.4); out["VIX18-25"] = (v >= 18.4) & (v < 25); out["VIX>=25"] = v >= 25
    for n in (20, 50, 200):
        ema = cl.ewm(span=n, adjust=False).mean().reindex(D.d).ffill().shift(1)
        sma = cl.rolling(n).mean().reindex(D.d).ffill().shift(1)
        out[f"ust_EMA{n}"] = prev_close > ema; out[f"alt_EMA{n}"] = prev_close < ema
        out[f"ust_SMA{n}"] = prev_close > sma; out[f"alt_SMA{n}"] = prev_close < sma
    pc2 = cl.reindex(D.d).ffill().shift(2)
    out["dun_yukari"] = prev_close > pc2; out["dun_asagi"] = prev_close < pc2
    for k, nm in enumerate(("Pzt", "Sal", "Car", "Per", "Cum")):
        out[nm] = [d.weekday() == k for d in D.d]
    op = pd.Series(D.open930.values, index=D.d)
    out["bosluk_yukari"] = op > prev_close; out["bosluk_asagi"] = op < prev_close
    return out.fillna(False).astype(bool)


FAM = {"VIX": ["VIX<15", "VIX15-18", "VIX18-25", "VIX>=25"],
       "MA": [f"{s}_{m}{n}" for s in ("ust", "alt") for m in ("EMA", "SMA") for n in (20, 50, 200)],
       "DUN": ["dun_yukari", "dun_asagi"], "GUN": ["Pzt", "Sal", "Car", "Per", "Cum"],
       "BOSLUK": ["bosluk_yukari", "bosluk_asagi"], "GICI": ["ustu_acilis", "alti_acilis"]}


def cond_matrix(R: pd.DataFrame, Cd: pd.DataFrame, a: str) -> tuple[np.ndarray, list[str]]:
    """Bir giriş anının gün satırları için koşul matrisi (gün × koşul). Tekli + farklı ailelerden ikili."""
    base = Cd.reindex(R.d).reset_index(drop=True)
    mn = ANCH[a]
    if mn >= 600:
        base["ustu_acilis"] = R.above_open.fillna(False).astype(bool).values
        base["alti_acilis"] = (~R.above_open.fillna(True).astype(bool)).values & R.above_open.notna().values
    fams = {f: [c for c in cs if c in base] for f, cs in FAM.items()}
    if mn < 570:
        fams.pop("BOSLUK", None)
    fams = {f: cs for f, cs in fams.items() if cs}
    cols, names = [np.ones(len(base), bool)], ["KOSULSUZ"]
    for f, cs in fams.items():
        for c in cs:
            cols.append(base[c].values); names.append(c)
    for f1, f2 in itertools.combinations(fams, 2):
        for c1 in fams[f1]:
            for c2 in fams[f2]:
                cols.append(base[c1].values & base[c2].values); names.append(f"{c1}&{c2}")
    return np.array(cols).T, names


def tstats(M: np.ndarray, r: np.ndarray, ok: np.ndarray):
    rr = np.where(ok, r, 0.0)
    n = M.T.astype(float) @ ok.astype(float)
    s = M.T.astype(float) @ rr
    s2 = M.T.astype(float) @ (rr ** 2)
    mean = s / np.maximum(n, 1)
    var = (s2 - n * mean ** 2) / np.maximum(n - 1, 1)
    t = mean / np.sqrt(np.maximum(var, 1e-12) / np.maximum(n, 1))
    return n, mean, t


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1); vixp = lib.vix_prev_map(D.d.tolist())
    rp = OUT / "returns.parquet"
    R = pd.read_parquet(rp) if rp.exists() else returns(m1, D)
    R.to_parquet(rp)
    Cd = conditions(D, vixp)
    per = R.d.map(lambda d: next((k for k, (a, b) in PER.items() if a <= d <= b), "?"))
    R["per"] = per
    rng = np.random.default_rng(11)
    cells, perm_max = [], np.zeros(200)
    for a in ANCH:
        for h in HOLDS:
            Rk = R[(R.a == a) & (R.h == h)].reset_index(drop=True)
            if len(Rk) < 300:
                continue
            M, names = cond_matrix(Rk, Cd, a)
            kes = (Rk.per == "KESIF").values
            for side in ("L", "S"):
                r = Rk[side].values
                n, mean, t = tstats(M[kes], r[kes], np.isfinite(r[kes]))
                for ci, nm in enumerate(names):
                    if n[ci] >= 60:
                        cells.append({"a": a, "h": h, "yon": side, "kosul": nm, "ci": ci, "n_K": int(n[ci]), "ort_K": float(mean[ci]), "t_K": float(t[ci])})
                # permütasyon: koşul satırlarını KEŞİF günleri arasında karıştır
                Mk, rk, okk = M[kes], r[kes], np.isfinite(r[kes])
                for p in range(200):
                    pm = Mk[rng.permutation(len(Mk))]
                    n2, _, t2 = tstats(pm, rk, okk)
                    t2 = np.where(n2 >= 60, t2, 0)
                    perm_max[p] = max(perm_max[p], t2.max())
    C = pd.DataFrame(cells)
    Tstar = float(np.percentile(perm_max, 95))
    sel = C[C.t_K >= Tstar].copy()
    res = {"n_hucre": int(len(C)), "T_yildiz": Tstar, "perm_max_ort": float(perm_max.mean()), "n_secilen": int(len(sel)),
           "t_K_ust10": C.nlargest(10, "t_K")[["a", "h", "yon", "kosul", "n_K", "ort_K", "t_K"]].to_dict("records")}
    # kör doğrulama
    rows = []
    for r_ in sel.itertuples():
        Rk = R[(R.a == r_.a) & (R.h == r_.h)].reset_index(drop=True)
        M, names = cond_matrix(Rk, Cd, r_.a)
        mask = M[:, r_.ci]
        row = {"a": r_.a, "h": r_.h, "yon": r_.yon, "kosul": r_.kosul, "n_K": r_.n_K, "ort_K": r_.ort_K, "t_K": r_.t_K}
        for p in ("KOR1", "KOR2"):
            g = Rk[mask & (Rk.per == p).values]
            x = g[r_.yon].dropna()
            mo = pd.to_datetime(g.loc[x.index, "d"]).dt.to_period("M").astype(str).values
            row[f"n_{p}"] = int(len(x)); row[f"ort_{p}"] = float(x.mean()) if len(x) else np.nan
            row[f"P_{p}"] = lib.block_boot_p(x.values, mo) if len(x) > 5 else np.nan
            row[f"ort15_{p}"] = float(g[r_.yon + "15"].dropna().mean()) if len(x) else np.nan
        row["gecti"] = bool(all(row[f"ort_{p}"] > 0 and row[f"P_{p}"] >= 0.9 and row[f"ort15_{p}"] > 0 for p in ("KOR1", "KOR2")))
        rows.append(row)
    V = pd.DataFrame(rows)
    V.to_csv(OUT / "secilenler.csv", index=False)
    res["gecen"] = V[V.gecti].to_dict("records") if len(V) else []
    res["secilen_ozet"] = V.sort_values("t_K", ascending=False).head(40).to_dict("records") if len(V) else []
    C.to_parquet(OUT / "cells.parquet")
    (OUT / "grid.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("hücre", len(C), "T*", round(Tstar, 2), "seçilen", len(sel), "geçen", len(res["gecen"]))
    if len(V):
        print(V.sort_values("t_K", ascending=False).head(30).round(3).to_string())


if __name__ == "__main__":
    main()
