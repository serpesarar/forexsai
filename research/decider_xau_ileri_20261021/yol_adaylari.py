"""PROTOCOL_ILERI.md §B — B1 erken kesme (5/10 dk, R ≤ −0,5) ve B3 giriş gecikmesi (+3 dk), G1 geometrisi.
Keşif kaynağı icralar (otopsi); sınama: gölge BUY kararları (icra edilmemiş), iki yarı, ileri alt küme.
Sadakat: taban simülasyon `sim_decider.pkl` G1 sütununu yeniden üretmeli.
python3 research/decider_xau_ileri_20261021/yol_adaylari.py"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CUT = pd.Timestamp("2026-10-15", tz="UTC")
TP_X, SL_X = 1.0, 1.5
HORIZON_MIN = 48 * 60
CUT_R = -0.5
N_BOOT = 4000
RNG = np.random.default_rng(1021)


def load_bars() -> pd.DataFrame:
    b = pd.read_csv(HERE / "data" / "xau_1m_utc.csv.gz")
    b["t_utc"] = pd.to_datetime(b.t_utc, utc=True)
    return b.set_index("t_utc").sort_index()


def sim(b: pd.DataFrame, ts: pd.Timestamp, atr: float, spread: float, delay: int = 0,
        cut_min: int | None = None) -> float:
    idx = b.index
    j = idx.searchsorted(ts, side="right")            # karar ts'sinden SONRA açılan ilk bar
    j += delay
    if j >= idx.size - 2 or not np.isfinite(atr) or atr <= 0:
        return np.nan
    if (idx[j] - ts) > pd.Timedelta(minutes=delay + 5):
        return np.nan
    e = float(b.open.iloc[j]) + spread
    sl, tp = e - SL_X * atr, e + TP_X * atr
    risk = SL_X * atr
    hi, lo, cl = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    end = min(idx.size, j + HORIZON_MIN)
    for k in range(j, end):
        if lo[k] <= sl:
            return -1.0
        if hi[k] >= tp:
            return TP_X / SL_X
        if cut_min is not None and k == j + cut_min - 1:
            r = (cl[k] - e) / risk
            if r <= CUT_R:
                return float(r)
    return float((cl[end - 1] - e) / risk)


def stats(x: np.ndarray, base: np.ndarray, days: np.ndarray) -> dict:
    d = x - base
    ud = np.unique(days)
    idx = {u: np.flatnonzero(days == u) for u in ud}
    bs = [d[np.concatenate([idx[u] for u in RNG.choice(ud, ud.size)])].mean() for _ in range(N_BOOT)]
    h = np.arange(d.size) < d.size // 2
    return {"ortR aday": x.mean(), "ortR taban": base.mean(), "fark": d.mean(), "P(fark>0)": float(np.mean(np.array(bs) > 0)),
            "yarılar": f"{d[h].mean():+.3f}/{d[~h].mean():+.3f}"}


def main() -> None:
    S = pd.read_pickle(HERE / "kurallar" / "sim_decider.pkl")
    S = S[(S.direction == "BUY") & S.in_analysis_set.astype(bool)].copy()
    S["ts"] = pd.to_datetime(S.ts, utc=True)
    S = S.sort_values("ts").reset_index(drop=True)
    b = load_bars()
    sp = S.spread_used.fillna(0.14).to_numpy(float)
    atr = S.atr5_closed.to_numpy(float)
    base = np.array([sim(b, t, a, s) for t, a, s in zip(S.ts, atr, sp)])
    ok = np.isfinite(base) & np.isfinite(S["G1_tp1.0_sl1.5"].to_numpy(float))
    fid = float(np.mean(np.isclose(base[ok], S["G1_tp1.0_sl1.5"].to_numpy(float)[ok], atol=1e-6)))
    variants = {"B1 kes 5dk": dict(cut_min=5), "B1 kes 10dk": dict(cut_min=10), "B3 gecikme +3dk": dict(delay=3)}
    res = {k: np.array([sim(b, t, a, s, **v) for t, a, s in zip(S.ts, atr, sp)]) for k, v in variants.items()}
    rows = []
    for grp, m in (("tümü", np.ones(len(S), bool)), ("gölge (icra edilmemiş)", ~S.executed.astype(bool).to_numpy()),
                   ("icra", S.executed.astype(bool).to_numpy()), ("ileri ≥10-15", (S.ts >= CUT).to_numpy())):
        for k, x in res.items():
            mm = m & np.isfinite(x) & np.isfinite(base)
            if mm.sum() < 10:
                continue
            rows.append({"küme": grp, "aday": k, "n": int(mm.sum()),
                         **stats(x[mm], base[mm], S.day.astype(str).to_numpy()[mm])})
    t = pd.DataFrame(rows)
    t.to_csv(HERE / "results" / "yol_adaylari.csv", index=False)
    txt = (f"# §B yol adayları (G1; sadakat: taban sim, DX G1 sütununu %{100 * fid:.1f} oranında birebir üretti, n={int(ok.sum())})\n\n"
           + t.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    (HERE / "results" / "yol_adaylari.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
