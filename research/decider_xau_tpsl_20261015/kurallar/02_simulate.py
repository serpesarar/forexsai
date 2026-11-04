"""Adım 2: ön-kayıtlı 3 geometride R'ler.
 (1) decider OPEN analiz kümesi — gecikme 0 ve +1 bar
 (2) C3 tetik popülasyonu (free mod danışmaları, extremity ≥ 1,6) — BUY simülasyonu
 (3) C2 zaman-plasebo havuzu: her decider işlemi için aynı UTC dakikası, ±10 gün içindeki diğer günler
Çıktı: sim_decider.pkl, sim_c3.pkl, sim_c2_pool.pkl"""
import numpy as np
import pandas as pd
import rules_lib as L

HERE = L.HERE
core = L.core
b1 = core.load_1m(); P = core.Paths(b1)
BF = L.BarFeatures(b1)
J = pd.read_pickle(HERE / "data_features_journal.pkl")
A = pd.read_pickle(L.ROOT / "data" / "grid_set.pkl")[["id", "executed", "day", "lot", "source"]]
GN = list(L.GEOMS)


def sim_row(direction, T, spread, delay=0):
    i0, dl = L.entry_index(P, T, delay)
    if dl > 30 or i0 >= len(P.t):
        return None
    atr = BF.features(core.to64(T)).get("atr5_closed", np.nan)   # kapalı-bar ATR (karar anında)
    r = L.sim_one(P, direction, i0, spread, atr)
    r["gap240"] = L.gap_in_window(P, i0)
    r["atr_used"] = atr
    r["entry_delay_min"] = dl
    return r


# ---- (1) decider
D = J.merge(A, on="id", how="inner")
rows = []
for x in D.itertuples(index=False):
    s = x.spread if np.isfinite(x.spread) else L.DEFAULT_SPREAD
    r0 = sim_row(x.direction, x.ts, s, 0); r1 = sim_row(x.direction, x.ts, s, 1)
    s15 = sim_row(x.direction, x.ts, s * 1.5, 0)
    rec = {"id": x.id}
    for g in GN:
        rec[g] = r0[g] if r0 else np.nan
        rec[g + "_usd_oz"] = r0[g + "_usd_oz"] if r0 else np.nan
        rec[g + "_exit"] = r0[g + "_exit"] if r0 else pd.NaT
        rec[g + "_entry"] = pd.Timestamp(P.t[L.entry_index(P, x.ts, 0)[0]], tz="UTC") if r0 else pd.NaT
        rec[g + "_d1"] = r1[g] if r1 else np.nan
        rec[g + "_sp15"] = s15[g] if s15 else np.nan
    rows.append(rec)
S = D.merge(pd.DataFrame(rows), on="id")
S["spread_used"] = S.spread.fillna(L.DEFAULT_SPREAD)
S["lot_rule"] = S.size_factor.map(L.lot_from_size)
S.to_pickle(HERE / "sim_decider.pkl")
print("decider:", S.groupby("direction").size().to_dict(), "| NaN G1:", int(S[GN[0]].isna().sum()))

# ---- (2) C3 tetik popülasyonu
C = J[(J["mode"] == "free") & (J.extremity >= 1.6)].sort_values("ts").copy()
gap = C.ts.diff().dt.total_seconds()
C = C[~(gap < 10)]
rows = []
for x in C.itertuples(index=False):
    s = x.spread if np.isfinite(x.spread) else L.DEFAULT_SPREAD
    r0 = sim_row("BUY", x.ts, s, 0)
    if r0 is None:
        continue
    rows.append({"id": x.id, **{g: r0[g] for g in GN}, "gap240": r0["gap240"]})
C3 = C.merge(pd.DataFrame(rows), on="id")
C3["day"] = C3.ts.dt.tz_convert("UTC").dt.strftime("%Y-%m-%d")
C3.to_pickle(HERE / "sim_c3.pkl")
print("C3:", len(C3), C3.action.value_counts().to_dict(), "sahte WAIT", int(C3.fake_wait.sum()))

# ---- (3) C2 havuzu
pool = []
for x in S.itertuples(index=False):
    t = pd.Timestamp(x.ts)
    for dd in range(-10, 11):
        if dd == 0:
            continue
        T2 = t + pd.Timedelta(days=dd)
        if T2.weekday() >= 5:
            continue
        r = sim_row(x.direction, T2, x.spread_used, 0)
        if r is None or r["entry_delay_min"] > 2 or r["gap240"] or not np.isfinite(r[GN[0]]):
            continue
        pool.append({"id": x.id, "dd": dd, **{g: r[g] for g in GN}})
C2 = pd.DataFrame(pool)
C2.to_pickle(HERE / "sim_c2_pool.pkl")
print("C2 havuzu:", len(C2), "| işlem başına aday medyan", C2.groupby("id").size().median())
