"""Rastgele giriş maliyet/fizibilite sınırı.

Girdi: out/hits.npz (01_hits.py). Çıktılar out/*.csv.
Kurallar: giriş sonraki 1m açılışı; aynı barda TP+SL → SL; SL dolumu boşluk-duyarlı; zaman stopu = bar e+H-1 kapanışı.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

OUT = lib.OUT
Z = np.load(f"{OUT}/hits.npz")
E = Z["e"].astype(np.int64)
P0 = Z["p0"]
G = lib.load_grid()
OPEN, CFF = G["open"], G["close_ff"]
TS = lib.T0 + pd.to_timedelta(E, unit="m")
YEAR = TS.year.to_numpy()
HOUR = TS.hour.to_numpy()
DOW = TS.dayofweek.to_numpy()
DAY = (E // 1440).astype(np.int64)
WEEKEND = DOW >= 5
ATR1_BP = Z["atr1"] / P0 * 1e4
ATR5_BP = Z["atr5"] / P0 * 1e4
RV = Z["rv"]
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

LEVELS = [3, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 40, 50, 60, 75, 100, 150, 200]
HS = [1, 5, 15, 30, 60, 240, 1440]
ASYM = [5, 10, 20, 30, 50, 100]
VENUES = ["PEP_PCT", "PEP_STRESS", "PEP_FIX15", "BIN_TAKER", "BIN_MAKER", "BIN_MIX", "BIN_MIXTP"]


def venue_cost(v: str, cls: np.ndarray) -> np.ndarray | float:
    """Gidiş-dönüş maliyet (bp). cls: 1=TP, -1=SL, 0=zaman."""
    if v == "PEP_PCT":
        return 1.85
    if v == "PEP_STRESS":
        return 1.85 * 1.5
    if v == "PEP_FIX15":
        return 15.0 / P0 * 1e4
    if v == "BIN_TAKER":
        return 10.0
    if v == "BIN_MAKER":
        return 4.0
    if v == "BIN_MIX":
        return 7.0
    if v == "BIN_MIXTP":
        return np.where(cls == 1, 4.0, 7.0)
    raise ValueError(v)


def outcome(k_tp, k_sl, tp_bp, sl_bp, H: int, side: int):
    """side=+1 long, -1 short. Dönüş: ret_bp, cls, tau(dk), amb."""
    k_tp = k_tp.astype(np.int64)
    k_sl = k_sl.astype(np.int64)
    tp_first = (k_tp < k_sl) & (k_tp < H)
    sl_first = (k_sl <= k_tp) & (k_sl < H)
    amb = (k_tp == k_sl) & (k_tp < H)
    cls = np.zeros(len(k_tp), dtype=np.int8)
    cls[tp_first] = 1
    cls[sl_first] = -1
    ret = np.empty(len(k_tp))
    ret[tp_first] = np.broadcast_to(tp_bp, ret.shape)[tp_first]
    hit_open = OPEN[np.minimum(E + np.minimum(k_sl, lib.LMAX - 1), lib.N - 1)]
    gap_r = side * (hit_open / P0 - 1) * 1e4
    ret_sl = np.minimum(-np.broadcast_to(sl_bp, ret.shape), gap_r)
    ret[sl_first] = ret_sl[sl_first]
    ts = cls == 0
    ret[ts] = side * (CFF[E[ts] + H - 1] / P0[ts] - 1) * 1e4
    tau = np.where(cls == 1, k_tp + 1, np.where(cls == -1, k_sl + 1, H))
    return ret, cls, tau, amb


def hits_for(side: int, tp_key: str, sl_key: str):
    """long: TP yukarı, SL aşağı; short: tersi."""
    if side == 1:
        return Z[f"k_up_{tp_key}"], Z[f"k_dn_{sl_key}"]
    return Z[f"k_dn_{tp_key}"], Z[f"k_up_{sl_key}"]


def summarize(mask, ret, cls, tau, amb, sl_bp, tp_bp) -> dict:
    r = ret[mask]
    c = cls[mask]
    slb = np.broadcast_to(sl_bp, ret.shape)[mask]
    tpb = np.broadcast_to(tp_bp, ret.shape)[mask]
    d = DAY[mask]
    cnt = np.bincount(d)
    sm = np.bincount(d, weights=r)
    dm = sm[cnt > 0] / cnt[cnt > 0]
    out = {
        "n": int(mask.sum()),
        "days": int(len(dm)),
        "gross_bp": r.mean(),
        "gross_bp_se": dm.std(ddof=1) / np.sqrt(len(dm)) if len(dm) > 1 else np.nan,
        "gross_R": (r / slb).mean(),
        "wr_tp": (c == 1).mean(),
        "sl_share": (c == -1).mean(),
        "ts_share": (c == 0).mean(),
        "amb_rate": amb[mask].mean(),
        "tau_mean": tau[mask].mean(),
        "tau_med": float(np.median(tau[mask])),
        "sl_bp_med": float(np.median(slb)),
        "tp_bp_med": float(np.median(tpb)),
    }
    for v in VENUES:
        cost = venue_cost(v, cls)
        cost = np.broadcast_to(cost, ret.shape)[mask]
        out[f"net_R_{v}"] = ((r - cost) / slb).mean()
        out[f"costR_{v}"] = (cost / slb).mean()
    return out


def run_sym_grid() -> pd.DataFrame:
    rows = []
    for b in LEVELS:
        for H in HS:
            for side in (1, -1):
                ktp, ksl = hits_for(side, str(b), str(b))
                ret, cls, tau, amb = outcome(ktp, ksl, b, b, H, side)
                for y in YEARS + ["ALL"]:
                    m = np.ones(len(E), bool) if y == "ALL" else (YEAR == y)
                    s = summarize(m, ret, cls, tau, amb, b, b)
                    rows.append({"tp_bp": b, "sl_bp": b, "H": H, "side": "L" if side == 1 else "S", "year": y, **s})
    return pd.DataFrame(rows)


def run_asym_grid() -> pd.DataFrame:
    rows = []
    for tp in ASYM:
        for sl in ASYM:
            for H in [1, 5, 15, 30, 60]:
                for side in (1, -1):
                    ktp, ksl = hits_for(side, str(tp), str(sl))
                    ret, cls, tau, amb = outcome(ktp, ksl, tp, sl, H, side)
                    for y in YEARS + ["ALL"]:
                        m = np.ones(len(E), bool) if y == "ALL" else (YEAR == y)
                        s = summarize(m, ret, cls, tau, amb, sl, tp)
                        rows.append({"tp_bp": tp, "sl_bp": sl, "H": H, "side": "L" if side == 1 else "S", "year": y, **s})
    return pd.DataFrame(rows)


def run_atr_grid() -> pd.DataFrame:
    rows = []
    for name, abp in [("a1", ATR1_BP), ("a5", ATR5_BP)]:
        valid = ~np.isnan(abp)
        for m in [0.5, 1.0, 2.0, 3.0]:
            key = f"{name}_{m}"
            bp = m * abp
            for H in [1, 5, 15, 30, 60, 240]:
                for side in (1, -1):
                    ktp, ksl = hits_for(side, key, key)
                    ret, cls, tau, amb = outcome(ktp, ksl, bp, bp, H, side)
                    for y in YEARS + ["ALL"]:
                        mk = valid & (np.ones(len(E), bool) if y == "ALL" else (YEAR == y))
                        s = summarize(mk, ret, cls, tau, amb, bp, bp)
                        rows.append({"bracket": f"{m}xATR{name[1]}m", "H": H, "side": "L" if side == 1 else "S",
                                     "year": y, **s})
    return pd.DataFrame(rows)


def tau_dist() -> pd.DataFrame:
    rows = []
    for b in LEVELS:
        ku, kd = Z[f"k_up_{b}"].astype(np.int64), Z[f"k_dn_{b}"].astype(np.int64)
        kmin = np.minimum(ku, kd)
        res = kmin < lib.LMAX
        tau = kmin + 1
        amb_any = (ku == kd) & res  # her iki yön için de aynı bar
        for y in YEARS + ["ALL"]:
            m = np.ones(len(E), bool) if y == "ALL" else (YEAR == y)
            t = tau[m & res]
            rows.append({"bp": b, "year": y, "unresolved_1440": 1 - res[m].mean(),
                         "tau_p10": np.percentile(t, 10), "tau_p25": np.percentile(t, 25),
                         "tau_med": np.median(t), "tau_p75": np.percentile(t, 75), "tau_p90": np.percentile(t, 90),
                         "amb_rate": amb_any[m].mean(),
                         "atr1_bp_med": np.nanmedian(ATR1_BP[m]), "atr5_bp_med": np.nanmedian(ATR5_BP[m]),
                         "b_over_atr1": b / np.nanmedian(ATR1_BP[m]), "b_over_atr5": b / np.nanmedian(ATR5_BP[m])})
    return pd.DataFrame(rows)


def seq_counts(tau_full: np.ndarray) -> np.ndarray:
    """Ardışık örtüşmesiz işlemler: giriş e, çözüm e+tau-1, sonraki giriş >= e+tau. Giriş indeksleri döner."""
    picks = []
    i = 0
    n = len(E)
    while i < n:
        picks.append(i)
        nxt = E[i] + tau_full[i]
        j = np.searchsorted(E, nxt, side="left")
        i = int(j)
    return np.array(picks, dtype=np.int64)


def opp_per_day() -> pd.DataFrame:
    rows = []
    for b in LEVELS:
        ku, kd = Z[f"k_up_{b}"].astype(np.int64), Z[f"k_dn_{b}"].astype(np.int64)
        tau = np.minimum(np.minimum(ku, kd) + 1, lib.LMAX)
        for tsname, tt in [("noTS", tau), ("TS60", np.minimum(tau, 60))]:
            pk = seq_counts(tt)
            resolved = (np.minimum(ku, kd)[pk] < (lib.LMAX if tsname == "noTS" else 60))
            dd = pd.DataFrame({"day": DAY[pk], "year": YEAR[pk], "res": resolved})
            per = dd.groupby(["year", "day"]).agg(n=("res", "size"), nres=("res", "sum")).reset_index()
            for y in YEARS + ["ALL"]:
                p = per if y == "ALL" else per[per["year"] == y]
                rows.append({"bp": b, "ts": tsname, "year": y, "trades_day_med": p["n"].median(),
                             "trades_day_p10": p["n"].quantile(0.1), "trades_day_p90": p["n"].quantile(0.9),
                             "resolved_day_med": p["nres"].median()})
    return pd.DataFrame(rows)


def loglog_interp(x, xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    return float(np.exp(np.interp(np.log(x), np.log(xs), np.log(ys))))


def frontier(td: pd.DataFrame, op: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y in YEARS + ["ALL"]:
        m = np.ones(len(E), bool) if y == "ALL" else (YEAR == y)
        fix15 = float(np.median(15.0 / P0[m] * 1e4))
        costs = {"PEP_PCT (1,85 bp)": 1.85, "PEP_STRESS (2,78 bp)": 2.775, "PEP_FIX15 ($15)": fix15,
                 "BIN_TAKER (10 bp)": 10.0, "BIN_MIX (7 bp)": 7.0, "BIN_MAKER (4 bp)": 4.0}
        tdy = td[td["year"] == y].sort_values("bp")
        on = op[(op["year"] == y) & (op["ts"] == "noTS")].sort_values("bp")
        o60 = op[(op["year"] == y) & (op["ts"] == "TS60")].sort_values("bp")
        a5 = float(np.nanmedian(ATR5_BP[m]))
        a1 = float(np.nanmedian(ATR1_BP[m]))
        for vn, c in costs.items():
            for frac in (0.10, 0.20):
                b = c / frac
                rows.append({"year": y, "venue": vn, "cost_bp": round(c, 2), "cost_frac_R": frac, "min_bp": round(b, 1),
                             "min_bp_in_ATR1m": round(b / a1, 2), "min_bp_in_ATR5m": round(b / a5, 2),
                             "tau_med_min": round(loglog_interp(b, tdy["bp"], tdy["tau_med"]), 1),
                             "tau_p90_min": round(loglog_interp(b, tdy["bp"], tdy["tau_p90"]), 1),
                             "opp_day_med_noTS": round(loglog_interp(b, on["bp"], on["trades_day_med"]), 1),
                             "opp_day_med_TS60": round(loglog_interp(b, o60["bp"], o60["trades_day_med"]), 1),
                             "resolved_in60_day_med": round(loglog_interp(b, o60["bp"], o60["resolved_day_med"].clip(lower=0.1)), 1)})
    return pd.DataFrame(rows)


def by_group() -> pd.DataFrame:
    rows = []
    rvbin = pd.cut(RV, [0, 0.35, 0.60, 0.90, 10], labels=["RV<35%", "RV35-60%", "RV60-90%", "RV>90%"]).astype(str)
    groups = {"hour": HOUR.astype(str), "weekend": np.where(WEEKEND, "haftasonu", "haftaici"), "rv": rvbin,
              "year_weekend": np.char.add(YEAR.astype(str), np.where(WEEKEND, "_hs", "_hi"))}
    specs = [("10bp", "10", 10.0), ("20bp", "20", 20.0), ("50bp", "50", 50.0), ("1xATR5m", "a5_1.0", ATR5_BP)]
    for nm, key, bp in specs:
        for side in (1, -1):
            ktp, ksl = hits_for(side, key, key)
            ret, cls, tau, amb = outcome(ktp, ksl, bp, bp, 60, side)
            kmin = np.minimum(ktp, ksl).astype(np.int64)
            for gname, gv in groups.items():
                for lev in np.unique(gv):
                    m = (gv == lev) & ~np.isnan(np.broadcast_to(bp, ret.shape))
                    if m.sum() < 1000:
                        continue
                    s = summarize(m, ret, cls, tau, amb, bp, bp)
                    s["res_in60"] = float((kmin[m] < 60).mean())
                    s["tau_nots_med"] = float(np.median(np.minimum(kmin[m] + 1, lib.LMAX)))
                    s["atr5_bp_med"] = float(np.nanmedian(ATR5_BP[m]))
                    s["atr1_bp_med"] = float(np.nanmedian(ATR1_BP[m]))
                    rows.append({"bracket": nm, "side": "L" if side == 1 else "S", "group": gname, "level": lev, **s})
    return pd.DataFrame(rows)


def main() -> None:
    td = tau_dist(); td.to_csv(f"{OUT}/tau_dist.csv", index=False); print("tau ok", flush=True)
    op = opp_per_day(); op.to_csv(f"{OUT}/opp_per_day.csv", index=False); print("opp ok", flush=True)
    fr = frontier(td, op); fr.to_csv(f"{OUT}/frontier_min_bracket.csv", index=False); print("frontier ok", flush=True)
    run_sym_grid().to_csv(f"{OUT}/grid_sym_year.csv", index=False); print("sym ok", flush=True)
    run_asym_grid().to_csv(f"{OUT}/grid_asym_year.csv", index=False); print("asym ok", flush=True)
    run_atr_grid().to_csv(f"{OUT}/grid_atr_year.csv", index=False); print("atr ok", flush=True)
    by_group().to_csv(f"{OUT}/by_group.csv", index=False); print("group ok", flush=True)


if __name__ == "__main__":
    main()
