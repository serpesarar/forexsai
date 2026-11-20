"""cr_gunluk.py — U: ^NDX günlük vekil (PROTOCOL.md 'U'). Tetik gün dibi < önceki gün dibi; giriş min(açılış, önceki dip).

Fiyat sürekliliği: giriş önceki dibin ilk geçildiği an → gün dibi girişten sonra → D0 stop dokunuşu kesin.
Gün içi TP: açılış önceki dibin altındaysa (giriş = açılış) gün yüksek değeri girişten sonradır → kesin; aksi halde yüksek
değer girişten önce olabilir → TP yalnız kapanış ≥ TP ise sayılır (muhafazakâr). Aynı gün stop + TP → stop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cr_motor as M

SRC = M.ROOT / "research/ndx_seri_opex_20261118/data/NDX_1985.parquet"
COST_BP = 1.0                      # taraf başına (gidiş-dönüş 2 bp)


KOR = {"GSPC": M.ROOT / "research/son4_20261118/data/GSPC_1950.parquet",
       "DJI": M.ROOT / "research/geri_cekilme_20261106/data/DJI.csv",
       "RUT": M.ROOT / "research/geri_cekilme_20261106/data/RUT.csv"}


def load_daily(name: str = "NDX") -> pd.DataFrame:
    if name == "NDX":
        d = pd.read_parquet(SRC)
        x = d.xs("^NDX", axis=1, level=1)[["Open", "High", "Low", "Close"]].dropna()
    elif str(KOR[name]).endswith(".csv"):
        x = pd.read_csv(KOR[name], index_col=0)[["Open", "High", "Low", "Close"]].dropna()
        x.index = pd.to_datetime([s[:10] for s in x.index])
    else:
        d = pd.read_parquet(KOR[name])
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        x = d[["Open", "High", "Low", "Close"]].dropna()
    x.index = pd.to_datetime(x.index).tz_localize(None) if getattr(x.index, "tz", None) else pd.to_datetime(x.index)
    x = x[(x.Open > 0) & (x.High >= x.Low)]
    bad = (x.Open == x.Close.shift(1)) | (x.Open == x.Close)          # açılışı olmayan (kapanış kopyası) yılları at
    ok = bad.groupby(x.index.year).mean() < 0.3
    return x[x.index.year.isin(ok[ok].index)]


def table(start: str = "1990-01-01", end: str = "2015-12-31", name: str = "NDX") -> pd.DataFrame:
    x = load_daily(name)
    O, H, L, C = (x[c].values for c in ("Open", "High", "Low", "Close"))
    days = [t.date() for t in x.index]
    rows = []
    for i in range(22, len(days) - 6):
        d = days[i]
        if not (pd.Timestamp(start).date() <= d <= pd.Timestamp(end).date()) or d.weekday() > 3:
            continue
        rets = C[i - 21:i] / C[i - 22:i - 1] - 1
        r1, r5, dvol = rets[-1], C[i - 1] / C[i - 6] - 1, float(np.std(rets[-20:], ddof=1))
        v = M.vix_prev(d)
        if v is None or v < M.VIX_MIN or not (r1 <= M.STRESS_R1 or r5 <= M.STRESS_R5):
            continue
        pdl = L[i - 1]
        if L[i] >= pdl:
            continue
        gap_below = O[i] < pdl
        E = min(O[i], pdl) * (1 + COST_BP / 1e4)

        def bid(p: float) -> float:
            return p * (1 - COST_BP / 1e4)

        def outcome(k, tp_k, exit_rule) -> tuple[float, str]:
            sl = E * (1 - (k * dvol if k is not None else M.EMERG))
            # D0
            if L[i] <= sl:
                return (bid(sl) / E - 1) * 1e4, "stop"
            if tp_k is not None:
                tp = E * (1 + tp_k * dvol)
                if (gap_below and H[i] >= tp) or C[i] >= tp:
                    return (tp / E - 1) * 1e4, "tp"
            j = exit_rule(0)
            if j == 0:
                return (bid(C[i]) / E - 1) * 1e4, "time"
            for s in range(1, 6):
                n = i + s
                fin = M.FIN * (days[n] - d).days
                if O[n] <= sl:
                    return (bid(O[n]) / E - 1) * 1e4 - fin, "stop"
                if j == ("o", s):
                    return (bid(O[n]) / E - 1) * 1e4 - fin, "time"
                if L[n] <= sl:
                    return (bid(sl) / E - 1) * 1e4 - fin, "stop"
                if j == ("c", s):
                    return (bid(C[n]) / E - 1) * 1e4 - fin, "time"
            raise RuntimeError

        xp_s = 0 if bid(C[i]) >= E else next((s for s in range(1, 6) if C[i + s] > C[i + s - 1]), 5)
        rules = {"D0c": lambda _: 0, "D1o": lambda _: ("o", 1), "D1c": lambda _: ("c", 1),
                 "XP": lambda _: 0 if xp_s == 0 else ("c", xp_s), "R0": lambda _: 0 if bid(C[i]) >= E else ("c", 1)}
        base, why = outcome(1.0, None, rules["D0c"])
        r = {"d": pd.Timestamp(d), "feed": f"U_{name}_GUNLUK", "E": E, "dvol": dvol, "r1": r1, "r5": r5, "vix": v,
             "vix_chg": (v / M.vix_prev2(d) - 1) if M.vix_prev2(d) else np.nan, "pre_open": bool(gap_below),
             "trig_h": np.nan, "depth": np.nan, "from_close": (E / C[i - 1] - 1) / dvol,
             "from_hi20": (E / C[i - 20:i].max() - 1) / dvol, "last_hour": np.nan, "wd": d.weekday(), "opex": M._opex(d),
             "base": base, "why": why, "R": base / 1e4 / dvol}
        r["cls"] = "SL" if why == "stop" else ("TP" if base > 0 else "ZK")
        for k in M.S_K:
            r[f"S_{k}"] = outcome(k, None, rules["D0c"])[0]
        for k in M.T_K:
            r[f"T_{k}"] = outcome(1.0, k, rules["D0c"])[0]
        for nm, k in (("st", 1.0), ("ns", None)):
            for x_ in ("D1o", "D1c", "XP", "R0"):
                r[f"H_{x_}_{nm}"] = outcome(k, None, rules[x_])[0]
        r["mae_d0"] = (L[i] / E - 1) * 1e4
        r["d0c_bp_nostop"] = (bid(C[i]) / E - 1) * 1e4
        r["d1c_bp_nostop"] = (bid(C[i + 1]) / E - 1) * 1e4 - M.FIN * (days[i + 1] - d).days
        rows.append(r)
    return pd.DataFrame(rows)
