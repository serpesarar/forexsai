"""Ön-dokunuş olasılığı testi (dolum varsayımından bağımsız): sürekli martingalde
P(+TP'ye -SL'den önce) = ln(1-s)/(ln(1-s)-ln(1+t)) ≈ SL/(TP+SL). Gerçek BTC 1m (ufuk 1440, aynı-bar → ayrı sayılır)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa
Z = np.load(f"{lib.OUT}/hits.npz")
E = Z["e"].astype(np.int64)
year = (lib.T0 + pd.to_timedelta(E, unit="m")).year.to_numpy()
rows = []
for tp, sl in [(100, 5), (50, 5), (50, 10), (20, 5), (10, 5), (5, 5), (10, 10), (5, 10), (5, 20), (5, 50), (10, 50), (5, 100)]:
    for side in ("L", "S"):
        if side == "L":
            kt, ks = Z[f"k_up_{tp}"].astype(int), Z[f"k_dn_{sl}"].astype(int)
            theo = -np.log(1 - sl / 1e4) / (np.log(1 + tp / 1e4) - np.log(1 - sl / 1e4))
        else:
            kt, ks = Z[f"k_dn_{tp}"].astype(int), Z[f"k_up_{sl}"].astype(int)
            theo = np.log(1 + sl / 1e4) / (np.log(1 + sl / 1e4) - np.log(1 - tp / 1e4))
        res = (np.minimum(kt, ks) < lib.LMAX) & (kt != ks)
        for y in [2021, 2022, 2023, 2024, 2025, 2026, "ALL"]:
            m = res & ((year == y) if y != "ALL" else True)
            p = (kt[m] < ks[m]).mean()
            rows.append({"tp": tp, "sl": sl, "side": side, "year": y, "n": int(m.sum()), "p_tp_first": p,
                         "p_theory": theo, "diff_pp": 100 * (p - theo), "implied_gross_bp": p * tp - (1 - p) * sl})
df = pd.DataFrame(rows)
df.to_csv(f"{lib.OUT}/gamblers_ruin.csv", index=False)
pd.set_option("display.width", 200)
a = df[df.year == "ALL"]
print(a.round(4).to_string())
print(df[(df.tp == 100) & (df.sl == 5)].round(4).to_string())
