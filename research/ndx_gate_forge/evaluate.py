"""Ön-kayıtlı hipotezlerin 4 dönem × geometri × zaman dilimi değerlendirmesi."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from common import DATA, OUT, block_boot

PER = ["D25a", "D25b", "C26", "M26", "S26"]
GEOMS = ["G80", "GS", "GR"]


def load(tf: int = 1) -> pd.DataFrame:
    L = pd.read_parquet(DATA / "labels.parquet")
    f = pd.read_parquet(DATA / f"feat_tf{tf}.parquet")
    f = f.iloc[L.i.to_numpy()].reset_index(drop=True)
    d = pd.concat([f, L.drop(columns=["i"])], axis=1)
    d["i"] = L.i.to_numpy()
    # Bot evreni: Pzt–Per, 07:00–21:59 UTC
    d = d[(d.wd <= 3) & d.utc_h.between(7, 21) & d.period.isin(PER)].reset_index(drop=True)
    for s in "BS":
        for H in (60, 240):
            d[f"f{H}n_{s}"] = d[f"f{H}_{s}"] / d.D
    return d


def macro() -> pd.DataFrame:
    m = pd.read_csv(DATA / "macro_daily_patched.csv", parse_dates=["date"])
    m["ts_ratio"] = m.VIX_close / m.VIX3M_close
    return m.set_index("date")


def conditions(d: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Her hipotez → (BUY'ı bloklayan maske, SELL'i bloklayan maske)."""
    H: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    nym = d.ny_min.to_numpy()
    p = d.price.to_numpy()
    z = np.zeros(len(d), bool)
    r = d.ret_prevclose.to_numpy()
    for thr, k in [(0.01, "H1a"), (0.005, "H1b")]:
        w = (nym >= 900) & (nym <= 950)
        H[k] = (w & (r <= -thr), w & (r >= thr))
    w = (nym >= 120) & (nym < 300)
    H["H2a"] = (z, w)
    H["H2b"] = (z, w & (d.prev_day_ret.to_numpy() < 0))
    g = d.gap.to_numpy()
    w = (nym >= 571) & (nym <= 615)
    H["H3a_fade"] = (w & (g >= .005), w & (g <= -.005))
    H["H3b_go"] = (w & (g <= -.005), w & (g >= .005))
    pm = p / d.p0400.to_numpy() - 1
    w = (nym >= 540) & (nym < 570)
    H["H4a"] = (w & (pm >= .003), w & (pm <= -.003))
    H["H4b"] = (w & (pm > 0), w & (pm < 0))
    m10 = d.p1000.to_numpy() / d.rth_open.to_numpy() - 1
    w = (nym >= 600) & (nym <= 630)
    H["H5"] = (w & (m10 >= .004), w & (m10 <= -.004))
    ru, dp = d.range_used.to_numpy(), d.day_pos.to_numpy()
    for thr, k in [(1.0, "H6a"), (1.3, "H6b")]:
        H[k] = ((ru >= thr) & (dp >= .8), (ru >= thr) & (dp <= .2))
    vr = d.vr15.to_numpy()
    H["H7a_vr_hi"] = (vr > 1.2, vr > 1.2)
    H["H7b_vr_lo"] = (vr < 0.7, vr < 0.7)
    for off in (0, 25, 50, 75):
        up = (np.ceil((p - off) / 100) * 100 + off) - p
        dn = p - (np.floor((p - off) / 100) * 100 + off)
        H[f"H8_round+{off}"] = ((up > 0) & (up <= 40), (dn > 0) & (dn <= 40))
    v, rg, tr = d.v15_rel.to_numpy(), d.rng15_rel.to_numpy(), d.tr60.to_numpy()
    for thr, k in [(2.0, "H9a"), (1.5, "H9b")]:
        a = (v >= thr) & (rg < 1.0)
        H[k] = (a & (tr > 0), a & (tr < 0))
    rv = d.rv30_rel.to_numpy()
    H["H10a"] = (rv < .6, rv < .6)
    H["H10b"] = (rv < .5, rv < .5)
    vw, sd = d.vwap.to_numpy(), d.vwap_sd.to_numpy()
    w = (nym >= 600) & (sd > 0)
    for k_, kk in [(2.0, "H11a"), (1.5, "H11b")]:
        H[kk] = (w & (p > vw + k_ * sd), w & (p < vw - k_ * sd))
    for off, k in [(0, "H12_pdhl"), (37, "H12_pdhl+37"), (-37, "H12_pdhl-37")]:
        up = d.pdh.to_numpy() + off - p
        dn = p - (d.pdl.to_numpy() - off)
        H[k] = ((up > 0) & (up <= 40), (dn > 0) & (dn <= 40))
    sk = d.skew120.to_numpy()
    H["H13"] = (sk > 1, sk < -1)
    # ---- gün düzeyi (takvim) ----
    days = pd.Series(sorted(d.tday.unique()))
    dd = pd.to_datetime(days)
    mon = dd.dt.to_period("M")
    pos = days.groupby(mon).cumcount()
    rev = days.groupby(mon).cumcount(ascending=False)
    tom = set(days[(pos < 3) | (rev == 0)])
    H["H14_tom"] = (z, d.tday.isin(tom).to_numpy())
    # OPEX: ayın 3. Cuma'sı
    third_fri = {}
    for y in range(2024, 2027):
        for mth in range(1, 13):
            fr = pd.date_range(f"{y}-{mth:02d}-01", periods=31, freq="D")
            fr = fr[(fr.month == mth) & (fr.weekday == 4)]
            third_fri[(y, mth)] = fr[2]
    tdd = pd.to_datetime(d.tday)
    tf_ = np.array([third_fri[(a, b_)] for a, b_ in zip(tdd.dt.year, tdd.dt.month)], dtype="datetime64[ns]")
    delta = (tf_ - tdd.to_numpy().astype("datetime64[ns]")).astype("timedelta64[D]").astype(int)
    opex_week = (delta >= 0) & (delta <= 4)
    after = (delta >= -7) & (delta <= -3)
    H["H15a_opexwk"] = (z, opex_week)
    H["H15b_postopex"] = (after, z)
    m = macro()
    prevday = pd.to_datetime(d.tday) - pd.Timedelta(days=1)
    tsr = m.ts_ratio.reindex(pd.date_range(m.index.min(), m.index.max())).ffill()
    vix = m.VIX_close.reindex(tsr.index).ffill()
    tr_ = tsr.reindex(prevday).to_numpy()
    vx = vix.reindex(prevday).to_numpy()
    H["H16a_ts_back"] = (z, tr_ >= 1.0)
    H["H16b_ts_contango"] = (tr_ <= .85, z)
    H["K1_vix_level(ref)"] = (vx < 18.4, vx >= 18.4)
    rng = np.random.default_rng(11)
    key = pd.Series(d.tday.astype(str) + d.utc_h.astype(str))
    u = pd.Series(rng.random(key.nunique()), index=key.unique())
    pr = key.map(u).to_numpy()
    H["PLACEBO_rand10"] = (pr < .1, pr > .9)
    H["PLACEBO_rand30"] = (pr < .3, pr > .7)
    H["REF_trend_gate"] = (d.h1_trend.to_numpy() < 0, d.h1_trend.to_numpy() > 0)
    H["REF_pos_gate"] = (d.pos4.to_numpy() > .6, d.pos4.to_numpy() < .4)
    return H


DAYLEVEL = {"H14_tom", "H15a_opexwk", "H15b_postopex", "H16a_ts_back", "H16b_ts_contango", "K1_vix_level(ref)"}


def demean(d: pd.DataFrame, col: str, key: list[str]) -> np.ndarray:
    return (d[col] - d.groupby(key)[col].transform("mean")).to_numpy()


def score(d: pd.DataFrame, H: dict, universe_b: np.ndarray, universe_s: np.ndarray, metrics: list[str]) -> list[dict]:
    rows = []
    cache: dict[str, np.ndarray] = {}
    for s in "BS":
        for mt in metrics:
            col = f"R_{mt}_{s}" if mt in GEOMS else f"{mt}_{s}"
            dm = d[[col, "tday", "period"]].copy()
            u = universe_b if s == "B" else universe_s
            dm.loc[~u, col] = np.nan
            dm["utc_h"] = d.utc_h.to_numpy()
            # Gün-içi ortalama GELECEĞE BAKAR (günün kalan yolu) → kullanılmaz.
            # Taban: aynı dönem × aynı yön × aynı UTC saati (≈60 gün ortalaması).
            cache[f"{mt}_{s}_day"] = demean(dm, col, ["period", "utc_h"])
            cache[f"{mt}_{s}_per"] = demean(dm, col, ["period"])
            cache[f"{mt}_{s}_raw"] = dm[col].to_numpy()
    per = d.period.to_numpy()
    days = d.tday.to_numpy()
    for name, (mb, ms) in H.items():
        mode = "per" if name in DAYLEVEL else "day"
        for mt in metrics:
            rec = {"hyp": name, "metric": mt, "mode": mode}
            for P in PER + ["DISC", "VAL"]:
                sel_p = np.isin(per, {"DISC": ["D25a", "D25b"], "VAL": ["C26", "M26"]}.get(P, [P]))
                vals, grp, raw = [], [], []
                for s, m in [("B", mb), ("S", ms)]:
                    u = (universe_b if s == "B" else universe_s)
                    k = m & sel_p & u
                    x = cache[f"{mt}_{s}_{mode}"][k]
                    ok = ~np.isnan(x)
                    vals.append(x[ok]); grp.append(days[k][ok]); raw.append(cache[f"{mt}_{s}_raw"][k][ok])
                v = np.concatenate(vals); g = np.concatenate(grp); rw = np.concatenate(raw)
                rec[f"{P}_lift"] = float(np.mean(v)) if len(v) else np.nan
                rec[f"{P}_ev"] = float(np.mean(rw)) if len(rw) else np.nan
                rec[f"{P}_n"] = int(len(v))
                rec[f"{P}_days"] = int(len(np.unique(g)))
                if P in ("DISC", "VAL") and len(v) > 0:
                    bs = block_boot(v, g, 2000)
                    rec[f"{P}_p_lt0"] = float(np.mean(bs < 0))
                    rec[f"{P}_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            rec["sign_all4_neg"] = all(rec[f"{P}_lift"] < 0 for P in PER if rec[f"{P}_n"] > 0) and all(rec[f"{P}_n"] > 0 for P in PER)
            rows.append(rec)
    return rows


def main(tf: int = 1, incremental: bool = False) -> pd.DataFrame:
    d = load(tf)
    H = conditions(d)
    if incremental:
        ub = (d.h1_trend.to_numpy() > 0) & (d.pos4.to_numpy() <= .6)
        us = (d.h1_trend.to_numpy() < 0) & (d.pos4.to_numpy() >= .4)
    else:
        ub = us = np.ones(len(d), bool)
    rows = score(d, H, ub, us, ["G80", "GS", "GR", "f60n", "f240n"])
    tag = f"tf{tf}{'_inc' if incremental else ''}"
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / f"hyp_{tag}.json").write_text(json.dumps(rows, indent=1))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    tf = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    inc = len(sys.argv) > 2 and sys.argv[2] == "inc"
    r = main(tf, inc)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 500)
    cols = ["hyp", "metric"] + [f"{P}_lift" for P in PER] + ["DISC_p_lt0", "VAL_p_lt0", "VAL_ev", "VAL_days", "D25a_days", "sign_all4_neg"]
    print(r[cols].round(3).to_string())
