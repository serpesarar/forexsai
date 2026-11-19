"""ihale.py — NA-03 Hazine 10/30 yıl ihaleleri → NDX. python ihale.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fitil_gece_20261118/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gece as G  # noqa: E402
import gunluk as U  # noqa: E402

NY = "America/New_York"
ERA = (("ESKI", "2018-04-01", "2021-10-31"), ("KESIF", "2021-11-01", "2024-06-30"), ("TEST", "2024-07-01", "2026-12-31"))


def auctions() -> pd.DataFrame:
    a = pd.read_csv(U.DATA / "auctions.csv")
    a["d"] = pd.to_datetime(a.auction_date).dt.date
    a["grp"] = np.where(a.security_type == "Bond", "30Y", "10Y")
    a["btc"] = pd.to_numeric(a.bid_to_cover_ratio, errors="coerce")
    a = a.sort_values("d").reset_index(drop=True)
    med = a.groupby("grp").btc.transform(lambda s: s.shift(1).rolling(6, min_periods=4).median())
    a["zayif"] = a.btc < med
    a["guclu"] = a.btc >= med
    return a


def era_of(d) -> str:
    s = pd.Timestamp(d)
    for nm, x, y in ERA:
        if pd.Timestamp(x) <= s <= pd.Timestamp(y):
            return nm
    return "DIS"


def intraday(b: pd.DataFrame, step: int, a: pd.DataFrame) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [780, 782, 960], step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and all(np.isfinite(dp.loc[z, f"o{m}"]) for m in (780, 782, 960))]
    D = dp.loc[days].copy()
    ad = a.groupby("d").agg(zayif=("zayif", "any"), guclu=("guclu", "all"))
    D["ihale"] = D.index.isin(ad.index)
    D["zayif"] = D.index.map(lambda z: bool(ad.zayif.get(z, False)))
    D["guclu"] = D.index.map(lambda z: bool(ad.guclu.get(z, False)) and z in ad.index)
    for e in (780, 782):
        D[f"L{e}"] = (D.o960 / (D[f"o{e}"] + D[f"s{e}"]) - 1) * 1e4
        D[f"S{e}"] = -((D.o960 + D.s960) / D[f"o{e}"] - 1) * 1e4
        D[f"x{e}"] = 0.5 * (D[f"s{e}"] + D.s960) / D[f"o{e}"] * 1e4
    D["era"] = [era_of(z) for z in D.index]
    return D


def cmp(D: pd.DataFrame, m: np.ndarray, col: str, base: np.ndarray, n_boot: int = 3000) -> dict:
    v, w = D[col].values, D[col].values
    a, b = m & np.isfinite(v), base & np.isfinite(w)
    if a.sum() < 5:
        return {"n": int(a.sum())}
    d = np.array([str(z) for z in D.index])
    ex = D[f"x{col[1:]}"].values
    return {"n": int(a.sum()), "tetik": round(float(v[a].mean()), 1), "taban": round(float(w[b].mean()), 1),
            "fark": round(float(v[a].mean() - w[b].mean()), 1), "s15": round(float((v[a] - ex[a]).mean()), 1),
            "isabet": round(float((v[a] > 0).mean()), 3), "P": round(float(G.KS.diff_p(v[a], d[a], w[b], d[b], n=n_boot)), 4)}


def run_intraday(b: pd.DataFrame, step: int, a: pd.DataFrame, eras: tuple[str, ...]) -> dict:
    D = intraday(b, step, a)
    out = {}
    for e in eras:
        z = D[D.era == e]
        ih, non = z.ihale.values, ~z.ihale.values
        out[e] = {"HI1_AL": cmp(z, ih, "L780", non), "HI1_SAT": cmp(z, ih, "S780", non),
                  "HI2_zayif_SAT": cmp(z, z.zayif.values, "S782", non), "HI2_guclu_AL": cmp(z, z.guclu.values, "L782", non),
                  "HI2_zayif_AL": cmp(z, z.zayif.values, "L782", non), "HI2_guclu_SAT": cmp(z, z.guclu.values, "S782", non)}
    return out


def daily(a: pd.DataFrame) -> dict:
    out = {}
    for nm in ("NDX", "QQQ"):
        px = U.load(nm)
        r = (px / px.shift(1) - 1) * 1e4
        ad = set(pd.to_datetime(pd.Series(sorted(set(a.d)))))
        idx = px.index
        isd = pd.Series(idx.isin(list(ad)), index=idx)
        pre, post = isd, isd.shift(1).fillna(False).astype(bool)
        rec = {}
        for e, x, y in (("KESIF", "1990-01-01", "2021-10-31"), ("TEST", "2021-11-01", "2026-12-31")):
            sel = (idx >= x) & (idx <= y) & r.notna().values
            for k, m in (("HI3_ihale_gunu", pre), ("HI3_ertesi_gun", post)):
                mm = m.values & sel
                rec[f"{e}_{k}"] = {"n": int(mm.sum()), "ort": round(float(r[mm].mean()), 1), "taban": round(float(r[sel].mean()), 1),
                                   "P_fark_pozitif": round(U.ath.bboot(r.values[mm], r.values[sel], 1), 4)}
        out[nm] = rec
    return out


def main() -> None:
    a = auctions()
    a = a[a.closing_time_comp.fillna("01:00 PM").eq("01:00 PM") | (pd.to_datetime(a.auction_date) < "2000-01-01")]
    out = {"duka": run_intraday(G.ndx_bars(), 60, a[pd.to_datetime(a.auction_date) >= "2018-01-01"], ("ESKI", "KESIF", "TEST"))}
    sys.path.insert(0, str(ROOT / "research/moc_pencere_20261118/src"))
    import moc  # noqa: E402
    b2, st2 = moc.mt5_2m()
    out["mt5"] = run_intraday(b2, st2, a, ("ESKI", "KESIF", "TEST"))
    out["gunluk"] = daily(a)
    (U.RES / "ihale.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for src in ("duka", "mt5"):
        for e, cs in out[src].items():
            for c, v in cs.items():
                print(src, e, c, v)
    for nm, r in out["gunluk"].items():
        for k, v in r.items():
            print(nm, k, v)


if __name__ == "__main__":
    main()
