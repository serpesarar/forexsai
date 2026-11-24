"""dis.py — G3 (MT5 NAS100), G4 (I1 taze 38 ABD aracı), G6 (ABD < 2018, 17 yabancı, diğer broker) — gerçekleşen P&L, bp.

Günlük setlerde karar = kapanış (≈ 16:00), bu yüzden K1 ≡ D1, K2 ≡ D2 (16:00 girişi zaten kapanış). Broker'da K = 16:00 barı girişi.
python bagimsiz.py → results/dis.json, results/dis_arac.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
R = HERE.parent
sys.path.insert(0, str(R / "kt02_derinlik_20261111"))
import kd_ortak as K  # noqa: E402
import motor as M  # noqa: E402

I1_DIR = R / "korku_evren_20261119/data"
VIX = pd.read_csv(R / "geri_cekilme_20261106/data/VIX.csv")
VIX.index = pd.to_datetime(VIX.Date.astype(str).str[:10])
VIXC = VIX.Close.astype(float).sort_index()
US_CUT = pd.Timestamp("2018-05-25")


def vix_prev(days: pd.DatetimeIndex) -> np.ndarray:
    k = np.searchsorted(VIXC.index.values, days.values) - 1
    v = np.where(k >= 0, VIXC.values[np.clip(k, 0, None)], np.nan)
    v[k < 0] = np.nan
    return v


def rv_stress(S: np.ndarray) -> np.ndarray:
    r = pd.Series(S).pct_change()
    rv = r.rolling(20).std().shift(1)
    return (rv > rv.rolling(252, min_periods=120).median().shift(1)).to_numpy()


CANDS = M.CANDS3 if "tur3" in sys.argv else (M.CANDS2 if "tur2" in sys.argv else M.CANDS)


def run(days: pd.DatetimeIndex, S: np.ndarray, stress: np.ndarray, pnl, pnl16=None, vix=None, pnlx=None) -> dict[str, pd.Series]:
    """pnlx(i, j, kind, entry16) → (bp, çıkış günü) çıkış zamanı varyantları için (TUR 3)."""
    """Aday başına gerçekleşen gün serisi (bp × doz × OPEX), çıkış gününe yazılı."""
    out = {}
    for cand in CANDS:
        tr = M.simulate(S, stress, M.mode_of(cand), vix=vix)
        rows = {}
        ek = M.exit_kind(cand)
        for t, r_ in zip(tr, M.reentry_flags(tr)):
            f = pnl16 if (M.entry16(cand) and pnl16 is not None) else pnl
            day_out = days[t.j]
            if ek != "1530" and pnlx is not None and not (ek == "next0930" and r_):
                bp, day_out = pnlx(t.i, t.j, ek, M.entry16(cand))
            else:
                bp = f(t.i, t.j)
            if not np.isfinite(bp):
                continue
            lot = M.weight(t, cand) * (M.OPEX_MULT if M.opex_week(days[t.i].date()) else 1.0)
            rows[day_out] = rows.get(day_out, 0.0) + bp * lot
        out[cand] = pd.Series(rows, dtype=float).sort_index()
    return out


def daily_set(name: str, loader, stress_kind: str, a0=None, a1=None) -> dict[str, pd.Series]:
    x = loader(name)
    S_all = x.Close.astype(float)
    st_all = vix_prev(S_all.index) >= M.VIX_TH if stress_kind == "vix" else rv_stress(S_all.values)
    m = np.ones(len(S_all), bool)
    if a0 is not None:
        m &= S_all.index >= a0
    if a1 is not None:
        m &= S_all.index < a1
    S, st, days = S_all.values[m], np.asarray(st_all)[m], S_all.index[m]
    if stress_kind == "vix":
        st = st & np.isfinite(vix_prev(days))
    pnl = lambda i, j: (S[j] / S[i] - 1) * 1e4 - 3 - 2 * (j - i)
    O = x.Open.astype(float).values[m]

    def pnlx(i, j, ek, e16):
        if ek == "1600" or j + 1 >= len(S):
            return pnl(i, j), days[j]
        return (O[j + 1] / S[i] - 1) * 1e4 - 3 - 2 * (j + 1 - i), days[j + 1]
    return run(days, S, st.astype(bool), pnl, vix=vix_prev(days), pnlx=pnlx)


def i1_loader(name: str) -> pd.DataFrame:
    x = pd.read_parquet(I1_DIR / f"{name}.parquet")
    x.index = pd.to_datetime(x.index)
    return x[x.Close > 0]


def broker_set(sym: str, stress_kind: str) -> dict[str, pd.Series]:
    p = K.broker_panel(sym)
    days = pd.DatetimeIndex(p.days)
    st = vix_prev(days) >= M.VIX_TH if stress_kind == "vix" else rv_stress(p.S)
    mk, bi = p.mk, p.bi
    b16 = np.array([mk.at(d + pd.Timedelta(minutes=960)) for d in days])
    pnl = lambda i, j: mk.pnl(bi[i], bi[j])
    pnl16 = lambda i, j: mk.pnl(b16[i], bi[j]) if b16[i] >= 0 else np.nan
    b930 = np.array([mk.at(d + pd.Timedelta(minutes=570)) for d in days])

    def pnlx(i, j, ek, e16):
        i_in = b16[i] if e16 else bi[i]
        if ek == "1600":
            return (mk.pnl(i_in, b16[j]) if b16[j] >= 0 and i_in >= 0 else np.nan), days[j]
        if j + 1 >= len(days) or b930[j + 1] < 0 or i_in < 0:
            return np.nan, days[j]
        return mk.pnl(i_in, b930[j + 1]), days[j + 1]
    return run(days, p.S, np.asarray(st, bool), pnl, pnl16, vix=vix_prev(days), pnlx=pnlx)


def measure(ser: dict[str, pd.Series]) -> dict:
    allix = sorted(set().union(*[set(s.index) for s in ser.values()]))
    months = pd.period_range(pd.Timestamp(allix[0]).to_period("M"), pd.Timestamp(allix[-1]).to_period("M"), freq="M")
    b = M.monthly(ser["BASE"], months)
    out = {}
    for c, s in ser.items():
        st = M.stats(s)
        mv = M.monthly(s, months)
        st["sharpe"] = M.sr(mv)
        st["P_sharpe"] = M.boot_sr(mv, b) if c != "BASE" else np.nan
        st["n"] = int((s != 0).sum())
        out[c] = st
    for c in out:
        out[c]["sr_x"] = out[c]["sharpe"] / out["BASE"]["sharpe"] if out["BASE"]["sharpe"] else np.nan
        out[c]["cal_x"] = out[c]["calmar"] / out["BASE"]["calmar"] if out["BASE"]["calmar"] else np.nan
    return out


def pool(sets: dict[str, dict[str, pd.Series]]) -> dict[str, pd.Series]:
    """Eşit ağırlık (bp) havuz kitabı: araçların gün serileri toplanır."""
    out = {}
    for c in CANDS:
        out[c] = pd.concat([s[c] for s in sets.values()], axis=1).fillna(0).sum(1).sort_index()
    return out


def main() -> None:
    res, rows = {}, []
    groups: dict[str, dict] = {"G3": {}, "I1": {}, "US_eski": {}, "YABANCI": {}, "BRK_diger": {}}
    groups["G3"]["NAS100"] = broker_set("NAS100", "vix")
    for s in ("US500", "US30", "US2000"):
        groups["BRK_diger"][s] = broker_set(s, "vix")
    groups["BRK_diger"]["GER40"] = broker_set("GER40", "rv")
    for n in sorted(p.stem for p in I1_DIR.glob("*.parquet")):
        groups["I1"][n] = daily_set(n, i1_loader, "vix")
    for n in K.US:
        groups["US_eski"][n] = daily_set(n, K.load_ohlc, "vix", a1=US_CUT)
    for n in K.KOR17:
        groups["YABANCI"][n] = daily_set(n, K.load_ohlc, "rv")
    for g, sets in groups.items():
        for n, ser in sets.items():
            m = measure(ser)
            for c, v in m.items():
                rows.append({"grup": g, "arac": n, "aday": c, **{k: v[k] for k in ("n", "toplam", "maks_dusus", "calmar", "sharpe",
                                                                                     "sr_x", "cal_x", "P_sharpe")}})
        if len(sets) > 1:
            res[g + "_havuz"] = measure(pool(sets))
            if g == "I1":
                res["I1_havuz_QQQ_SPY_haric"] = measure(pool({k: v for k, v in sets.items() if k not in ("QQQ", "SPY")}))
        else:
            res[g] = measure(next(iter(sets.values())))
    df = pd.DataFrame(rows)
    SUF = "_tur3" if "tur3" in sys.argv else ("_tur2" if "tur2" in sys.argv else "")
    df.to_csv(HERE / f"results/dis_arac{SUF}.csv", index=False)
    frac = (df[df.aday != "BASE"].assign(iyi=lambda x: x.sr_x > 1).groupby(["grup", "aday"]).iyi.mean().unstack())
    res["sharpe_artan_oran"] = frac.round(3).to_dict()
    (HERE / f"results/dis{SUF}.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
    print(frac.round(2).to_string())
    for g in res:
        if g == "sharpe_artan_oran":
            continue
        print(g, {c: (round(v["cal_x"], 2), round(v["sr_x"], 2), round(v["P_sharpe"], 2) if v["P_sharpe"] == v["P_sharpe"] else None)
                  for c, v in res[g].items()})


if __name__ == "__main__":
    main()
