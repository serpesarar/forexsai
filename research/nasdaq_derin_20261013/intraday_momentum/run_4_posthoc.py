"""Adım 4 — POST-HOC (ön-kayıt DIŞI): keşifteki saat plasebosu tablosunda 15:00 diliminin (sinyal: önceki 16:00 → 15:00,
işlem 15:00–15:30) perm p≈0 çıkması. Tek bir sınama: aynı kural N1m keşifte, kasada (30m/1m) ve DAX'ta (16:30–17:00).
Kanıt değeri sınırlı (11 dilim arasından seçildi → seçim yükü); yalnız yön teyidi.
"""
import json
import pandas as pd
from imcore import LOCK, RES, perm_p, summarize, trades
from run_1_discovery import build
from run_3_lockbox_dax import dax_table, ndx_lock

rows = []
for nm, T in [("N30_kesif", build("30m", 30)), ("N1m_kesif", build("1m", 1)), ("N30_kasa", ndx_lock("30m", 30)),
              ("N1m_kasa", ndx_lock("1m", 1))]:
    X = trades(T, T.P900 / T.C0 - 1, "O900", "P930", opt_col="P900")
    r = summarize(X, f"ROD60->15:00-15:30 @{nm}"); r["perm_p"] = round(perm_p(X)[0], 4); rows.append(r)
D = dax_table()
D2 = D.copy()
X = trades(D2, D2.P990 / D2.C0 - 1, "O990", "P1020", opt_col="P990")
for lab, Xs in [("tum", X), ("<2026-07", X[X.index < LOCK]), (">=2026-07", X[X.index >= LOCK])]:
    r = summarize(Xs, f"DAX ROD(16:30)->16:30-17:00 {lab}"); r["perm_p"] = round(perm_p(Xs)[0], 4); rows.append(r)
json.dump(rows, open(RES / "posthoc_1500.json", "w"), ensure_ascii=False, indent=1, default=str)
pd.set_option("display.width", 250)
print(pd.DataFrame(rows)[["id", "n", "ortR", "ort_puan", "WR", "P_EV>0", "yari1", "yari2", "hepAL_ortR", "fark_hepAL", "perm_p"]].to_string(index=False))
