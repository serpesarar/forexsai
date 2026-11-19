"""evren.py — Eksen A: sektör/sanayi ETF ve mega-cap hissede korku gecesi paketi (V1 + OPEX + XP) + portföy etkisi. python evren.py"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
D, RES = HERE / "data", HERE / "results"
for p in ("research/son_rapor_20261118/src", "research/ndx_10y_1m_20261116/src"):
    sys.path.insert(0, str(ROOT / p))
import rapor as R  # noqa: E402
import lib  # noqa: E402
from indir import HISSE, SANAYI, SEKTOR  # noqa: E402

GRUP = {**{t: "sektor" for t in SEKTOR}, **{t: "sanayi" for t in SANAYI}, **{t: "hisse" for t in HISSE}}
KESIF_SON, CUT = pd.Timestamp("2017-12-31"), pd.Timestamp("2026-11-05")
RNG = np.random.default_rng(23)
K, _ = R.cycle(R.trading_calendar())


def load(t: str) -> pd.DataFrame:
    d = pd.read_parquet(D / f"{t}.parquet")
    x = pd.DataFrame({"o": d.Open, "h": d.High, "l": d.Low, "c": d.Close}).dropna()
    x = x[(x.index <= CUT) & (x.c > 0)]
    x["V1"] = (x.c <= (x.h + x.l) / 2 * 0.995) & (x.c < x.o)
    x["bosluk"] = x.o / x.c.shift(1) - 1
    return x


def xp_net(x: pd.DataFrame, cost: float) -> pd.Series:
    """Her gün için: o gün kapanışta alınsa XP çıkışlı net bp (ilk yükselen kapanış, en geç 5. gün)."""
    c, idx = x.c.values, x.index
    out = np.full(len(c), np.nan)
    for i in range(len(c) - 1):
        prev, j = c[i], None
        last = min(i + 5, len(c) - 1)
        for jj in range(i + 1, last + 1):
            if c[jj] > prev or jj == last:
                j = jj
                break
            prev = c[jj]
        out[i] = (c[j] / c[i] - 1) * 1e4 - cost - lib.FIN_BP_PER_DAY * (idx[j] - idx[i]).days
    return pd.Series(out, index=idx)


def trades() -> pd.DataFrame:
    ref = {t: load(t) for t in ("QQQ", "SPY")}
    idx_v1 = set(ref["QQQ"].index[ref["QQQ"].V1]) | set(ref["SPY"].index[ref["SPY"].V1])
    rows = []
    for t, g in GRUP.items():
        x = load(t)
        x["net"] = xp_net(x, 5.0 if g == "hisse" else 2.0)
        x["opex"] = np.isin(K.reindex(x.index).values, [0, 1, 2])
        x = x.dropna(subset=["net"])
        x = x[x.index >= pd.Timestamp("1999-01-01")]
        z = pd.DataFrame({"t": t, "grup": g, "d": x.index, "net": x.net.values, "V1": x.V1.values, "opex": x.opex.values,
                          "endeks": x.index.isin(idx_v1), "haber": (x.bosluk <= -0.02).values})
        rows.append(z)
    A = pd.concat(rows, ignore_index=True)
    A["donem"] = np.where(A.d <= KESIF_SON, "KESIF", "TEST")
    A["paket"] = A.V1 & ~A.opex
    return A


def boot_P(v: np.ndarray, days: np.ndarray, base: float, n: int = 2000) -> float:
    ud = np.unique(days)
    pos = {u: np.flatnonzero(days == u) for u in ud}
    s = np.empty(n)
    for k in range(n):
        pick = RNG.choice(ud, len(ud))
        s[k] = np.concatenate([v[pos[u]] for u in pick]).mean() - base
    return float((s > 0).mean())


SUBS = {"tum": lambda z: np.ones(len(z), bool), "yeni_gun": lambda z: ~z.endeks.values,
        "yeni_gun_habersiz": lambda z: (~z.endeks & ~z.haber).values, "yeni_gun_haberli": lambda z: (~z.endeks & z.haber).values,
        "endeksle": lambda z: z.endeks.values}


def cell(A: pd.DataFrame, grup: str, sub: str, era: str) -> dict:
    z = A[(A.grup == grup) & (A.donem == era)]
    base = z[~z.V1]                                  # taban: V1 olmayan günler, aynı XP
    p = z[z.paket & SUBS[sub](z)]
    if len(p) < 10:
        return {"n": int(len(p))}
    per = {}
    for t, g in p.groupby("t"):
        b = base[base.t == t].net.mean()
        per[t] = round(float(g.net.mean() - b), 1)
    bmean = float(base.groupby("t").net.mean().reindex(p.t.unique()).mean())
    return {"n": int(len(p)), "yilda": round(len(p) / max(1, p.d.dt.year.nunique()), 1), "ort": round(float(p.net.mean()), 1),
            "taban": round(bmean, 1), "fark": round(float(p.net.mean() - bmean), 1), "isabet_%": round(float((p.net > 0).mean() * 100), 1),
            "en_kotu": round(float(p.net.min()), 1), "P": round(boot_P(p.net.values, p.d.values, bmean), 3),
            "enstruman_arti_%": round(float(np.mean([v > 0 for v in per.values()]) * 100), 1), "enstruman": per}


def verdict(k: dict, t: dict) -> str:
    if t.get("n", 0) < 10 or k.get("n", 0) < 10:
        return "yetersiz"
    if k["fark"] > 0 and t["fark"] > 0 and t["P"] >= 0.95 and t["enstruman_arti_%"] >= 65:
        return "B"
    if t["fark"] > 0 and k["fark"] > 0:
        return "C"
    return "X"


def ndx_package_daily() -> pd.Series:
    I = pd.read_parquet(ROOT / "research/xp_gelistir_20261119/results/islemler.parquet")
    P = I[(I.besleme == "MT5_NAS100") & ~I.opex_k.isin([0, 1, 2]) & (I.d >= "2018-01-01") & (I.d <= CUT)]
    return P.groupby("d").net.sum()


def portfolio(A: pd.DataFrame, grup: str, sub: str) -> dict:
    p = A[(A.grup == grup) & A.paket & (A.donem == "TEST")]
    p = p[SUBS[sub](p)]
    leg = p.groupby("d").net.mean()                  # gün başına 1 birim (aynı günün işlemleri bölüşür)
    ndx = ndx_package_daily()
    days = pd.bdate_range("2018-01-01", CUT)
    L, N = leg.reindex(days).fillna(0), ndx.reindex(days).fillna(0)
    L_nom = L.copy()
    L = L * (N.std() / L.std()) if L.std() > 0 else L      # ön kayıt: EŞİT RİSK (bacak günlük σ'sı NDX paketininkine eşitlenir)

    def sh(s):
        return round(float(s.mean() / s.std() * np.sqrt(252)), 2) if s.std() > 0 else None

    def dd(s):
        c = s.cumsum()
        return round(float((c - c.cummax()).min()), 0)
    both = (L != 0) & (N != 0)
    yrs = len(days) / 252
    return {"islem_yilda": round(len(p) / yrs, 1), "gun_yilda": round(leg.size / yrs, 1),
            "ndx_disi_gun_yilda": round(float((~leg.index.isin(ndx.index)).sum() / yrs), 1),
            "ndx_gun_yilda": round(ndx.size / yrs, 1), "ortak_gun_korelasyon": round(float(L[both].corr(N[both])), 2) if both.sum() > 5 else None,
            "sharpe_ndx": sh(N), "sharpe_bacak": sh(L), "sharpe_birlesik": sh(N + L), "maxdd_ndx": dd(N), "maxdd_birlesik": dd(N + L),
            "toplam_bp_yil_ndx": round(float(N.sum() / yrs), 0), "toplam_bp_yil_birlesik": round(float((N + L).sum() / yrs), 0),
            "bacak_olcek": round(float(L.std() / L_nom.std()), 3) if L_nom.std() > 0 else None,
            "esit_nominal_sharpe_birlesik": sh(N + L_nom), "maxdd_bacak": dd(L)}


def main() -> None:
    A = trades()
    res = {"veri": {f"{g}|{e}": int(v) for (g, e), v in A.groupby(["grup", "donem"]).paket.sum().items()}}
    print("paket işlem sayısı:", res["veri"], flush=True)
    for g in ("sektor", "sanayi", "hisse"):
        for s in SUBS:
            k, t = cell(A, g, s, "KESIF"), cell(A, g, s, "TEST")
            v = verdict(k, t)
            res[f"{g}|{s}"] = {"KESIF": k, "TEST": t, "hukum": v}
            print(f"{g:7s} {s:18s} KEŞİF n {k.get('n')} fark {k.get('fark')} | TEST n {t.get('n')} yılda {t.get('yilda')} ort {t.get('ort')} "
                  f"taban {t.get('taban')} fark {t.get('fark')} P {t.get('P')} isabet {t.get('isabet_%')} enstr+ {t.get('enstruman_arti_%')}% → {v}", flush=True)
            if v == "B":
                res[f"{g}|{s}"]["portfoy"] = pf = portfolio(A, g, s)
                print("        portföy:", pf, flush=True)
    (RES / "evren.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    A.to_parquet(RES / "evren_islemler.parquet")


if __name__ == "__main__":
    main()
