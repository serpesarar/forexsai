"""duka.py — Dukascopy NDX 1m: C3b adayları, gün sonu işaretli $ kitabı (canlı lot 2,0, OPEX ×0,5), G1/G2/G5.

python duka.py → results/duka.json, cache/duka_trades.parquet
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/ndx_10y_1m_20261116/src"))
import lib  # noqa: E402
import motor as M  # noqa: E402

LIVE_LOT = 2.0
MONTHS = pd.period_range("2018-01", "2026-11", freq="M")
N_PLACEBO = 2000


class Duka:
    def __init__(self) -> None:
        self.m1 = lib.load_m1()
        D = lib.daily_table(self.m1)
        self.all_days = list(D.d)
        s = D[D.S.notna() & D.E.notna() & ~D.early].reset_index(drop=True)
        self.days = list(s.d)
        self.S = s.S.values.astype(float)
        vixp = lib.vix_prev_map(self.days)
        self.vix = np.array([vixp.get(d, np.nan) for d in self.days], float)
        self.stress = self.vix >= M.VIX_TH
        dd = self.m1.d
        self.ends = np.r_[np.where(dd[1:] != dd[:-1])[0], len(dd) - 1]
        self.end_d = np.array([pd.Timestamp(dd[k]).date() for k in self.ends])

    def px_in(self, i: int, entry_min: int = 930) -> float:
        k, bid = lib.entry_ix(self.m1, lib.utc(self.days[i], entry_min))
        return bid + self.m1.spr[min(k, len(self.m1.t) - 1)] if k is not None else np.nan

    def trades(self, cand: str) -> pd.DataFrame:
        entry_min = 960 if M.entry16(cand) else 930
        tr = M.simulate(self.S, self.stress, M.mode_of(cand), entry_ref=lambda i: self.px_in(i), vix=self.vix)
        ek, re = M.exit_kind(cand), M.reentry_flags(tr)
        rows = []
        for t, r_ in zip(tr, re):
            d0, d1 = self.days[t.i], self.days[t.j]
            t_out = lib.utc(d1, 930)
            if ek == "1600" or (ek == "next0930" and r_):
                t_out = lib.utc(d1, 960) if ek == "1600" else t_out
            elif ek == "next0930":
                nxt = self.all_days[self.all_days.index(d1) + 1] if self.all_days.index(d1) + 1 < len(self.all_days) else None
                if nxt is None:
                    continue
                t_out = lib.utc(nxt, 570)
            x = lib.time_trade(self.m1, "C3B", d0, lib.utc(d0, entry_min), t_out, +1)
            if x is None:
                continue
            rows.append({"d": d0, "d_out": self.ny_out(x.t_out), "t_in": x.t_in, "t_out": x.t_out, "px_in": x.px_in, "bp": x.net_bp(),
                         "hold": t.j - t.i, "vd": t.vd, "stress": t.stress, "deep": t.deep, "w": M.weight(t, cand),
                         "opex": M.opex_week(d0)})
        return pd.DataFrame(rows)

    def ny_out(self, t: int):
        i = min(int(np.searchsorted(self.m1.t, t, side="right")) - 1, len(self.m1.t) - 1)
        return pd.Timestamp(self.m1.d[max(i, 0)]).date()

    def marks(self, T: pd.DataFrame) -> list[pd.Series]:
        """İşlem başına 1 lotluk gün sonu işaretli $ serisi (çıkış günü kalan = toplam − işaretler)."""
        m1, out = self.m1, []
        for x in T.itertuples():
            usd = x.px_in * x.bp / 1e4
            i_in, i_out = int(np.searchsorted(m1.t, x.t_in)), int(np.searchsorted(m1.t, x.t_out))
            a, b = int(np.searchsorted(self.ends, i_in)), int(np.searchsorted(self.ends, i_out))
            prev, acc, rows = x.px_in, 0.0, {}
            for k in range(a, b):
                if self.end_d[k] >= x.d_out:
                    break
                v = m1.c[self.ends[k]] - prev
                rows[self.end_d[k]] = rows.get(self.end_d[k], 0.0) + v
                acc += v
                prev = m1.c[self.ends[k]]
            rows[x.d_out] = rows.get(x.d_out, 0.0) + usd - acc
            out.append(pd.Series(rows))
        return out


def book(marks: list[pd.Series], lots: np.ndarray, days: list) -> pd.Series:
    s = pd.Series(0.0, index=sorted(set(days)))
    for m, l in zip(marks, lots):
        if l > 0:
            s = s.add(m * l, fill_value=0.0)
    return s.sort_index()


def lots_of(T: pd.DataFrame) -> np.ndarray:
    return LIVE_LOT * np.where(T.opex, M.OPEX_MULT, 1.0) * T.w.values


def summary(s: pd.Series, T: pd.DataFrame, lots: np.ndarray, base_mdd: float) -> dict:
    st = M.stats(s)
    idx = pd.Index(s.index)
    st["ESKI"] = M.stats(s[idx <= lib.ESKI_END])
    st["YENI"] = M.stats(s[idx > lib.ESKI_END])
    f = base_mdd / st["maks_dusus"] if st["maks_dusus"] < 0 else np.nan     # eşit maks. düşüşe ölçek
    usd = T.px_in.values * T.bp.values / 1e4 * lots
    st["esit_risk"] = {"olcek": f, "toplam": st["toplam"] * f, "zarar_toplam": float(usd[usd < 0].sum() * f),
                       "kar_toplam": float(usd[usd > 0].sum() * f), "en_kotu_10": st["en_kotu_10"] * f,
                       "en_kotu_gun": st["en_kotu_gun"] * f}
    st["n"] = int((lots > 0).sum())
    st["ort_bp_lotlu"] = float(np.average(T.bp.values, weights=lots)) if lots.sum() > 0 else np.nan
    st["isabet"] = float((T.bp.values[lots > 0] > 0).mean()) if (lots > 0).any() else np.nan
    return st


def placebo(marks: list[pd.Series], T: pd.DataFrame, cand: str, days: list, obs: float, rng) -> dict:
    """Etiketleri yıl içinde karıştır (aynı ağır işlem sayısı); D1/K1 vd, D2/K2 (stres, derin) çifti."""
    yrs = pd.to_datetime(T.d).dt.year.values
    M1 = np.array([m.reindex(sorted(set(days)), fill_value=0.0).values for m in marks])   # işlem × gün
    base_l = LIVE_LOT * np.where(T.opex, M.OPEX_MULT, 1.0)
    vals = []
    for _ in range(N_PLACEBO):
        perm = np.arange(len(T))
        for y in np.unique(yrs):
            k = np.flatnonzero(yrs == y)
            perm[k] = rng.permutation(k)
        if cand in ("D1", "K1"):
            w = np.where(T.vd.values[perm], 1.0, 1 / 3)
        elif cand in ("D2", "K2"):
            w = 0.25 + 0.375 * T.stress.values[perm] + 0.375 * T.deep.values[perm]
        else:
            w = np.where(T.vd.values[perm], 1.0, 0.0)
        s = (M1 * (base_l * w)[:, None]).sum(0)
        eq = np.cumsum(s)
        mdd = (eq - np.maximum.accumulate(eq)).min()
        vals.append(s.sum() / abs(mdd) if mdd < 0 else np.nan)
    vals = np.array(vals)
    return {"yuzdelik": float(np.nanmean(vals < obs)), "plasebo_medyan": float(np.nanmedian(vals)),
            "plasebo_p95": float(np.nanpercentile(vals, 95))}


def main() -> None:
    tur2 = "tur2" in sys.argv
    tur3 = "tur3" in sys.argv
    cands = M.CANDS3 if tur3 else (M.CANDS2 if tur2 else M.CANDS)
    dk = Duka()
    rng = np.random.default_rng(11)
    res, store = {}, []
    base_s = None
    for cand in cands:
        T = dk.trades(cand)
        mk = dk.marks(T)
        lots = lots_of(T)
        s = book(mk, lots, dk.days)
        if cand == "BASE":
            base_s, base_mdd = s, M.stats(s)["maks_dusus"]
            print("taban n", len(T), "ort bp", round(T.bp.mean(), 2))
        r = summary(s, T, lots, base_mdd)
        r["P_sharpe"] = M.boot_sr(M.monthly(s, MONTHS), M.monthly(base_s, MONTHS))
        if cand in ("D1", "D2", "D3", "K1", "K2"):
            r["plasebo"] = placebo(mk, T, cand, dk.days, r["calmar"], rng)
        res[cand] = r
        T["cand"] = cand
        T["lot"] = lots
        store.append(T)
        print(cand, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items() if not isinstance(v, dict)})
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / f"results/duka{'_tur3' if tur3 else ('_tur2' if tur2 else '')}.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
    pd.concat(store).to_parquet(HERE / f"cache/duka_trades{'_tur3' if tur3 else ('_tur2' if tur2 else '')}.parquet")


if __name__ == "__main__":
    main()
