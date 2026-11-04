"""Kaldıraç / risk matematiği + Monte Carlo (varsayımsal net kenarlar).

- Pozisyon boyu: notional/özsermaye L = risk% / SL%. Kaldıraç girdi değil ÇIKTIDIR.
- Pepperstone BTCUSD marjin %5 (1:20); perakende stop-out marjin seviyesi %50 → tek pozisyonda
  stop-out mesafesi d* = 1/L − 0.05×0.5.
- Binance izole marjin (açıklayıcı): tasfiye ≈ 1/lev − MMR (MMR 0,4% varsayım; resmi tablo doğrulanmadı).
- MC: bağımsız işlemler, sabit kesirli risk, bileşik; net R kenarı +0,03/+0,05/+0,10 (ve 0, −0,05 kontrol).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

OUT = lib.OUT
MARGIN_RATE = 0.05
STOPOUT_LEVEL = 0.50
MMR = 0.004
rng = np.random.default_rng(20261021)

# ---------------------------------------------------------------- kaldıraç tablosu
lev_rows = []
for sl in [5, 10, 20, 30, 50, 100]:
    for r in [0.25, 0.5, 1.0, 2.0]:
        L = (r / 100) / (sl / 1e4)
        d_star = 1 / L - MARGIN_RATE * STOPOUT_LEVEL
        lev_rows.append({"sl_bp": sl, "risk_pct": r, "notional_x_equity": round(L, 2),
                         "pep_margin_used_pct_equity": round(100 * MARGIN_RATE * L, 1),
                         "pep_cap_ok(L<=20)": L <= 1 / MARGIN_RATE,
                         "pep_stopout_dist_bp": round(d_star * 1e4, 0) if d_star > 0 else 0,
                         "stopout_over_SL": round(d_star * 1e4 / sl, 1) if d_star > 0 else 0,
                         "fee_per_trade_pct_eq_BIN_TAKER": round(r * 10 / sl, 3),
                         "fee_per_trade_pct_eq_PEP_PCT": round(r * 1.85 / sl, 3)})
lev = pd.DataFrame(lev_rows)
lev.to_csv(f"{OUT}/leverage_table.csv", index=False)

liq_rows = []
for lv in [5, 10, 20, 50, 75, 100, 125]:
    liq_rows.append({"binance_isolated_leverage": lv, "liq_dist_bp_approx": round((1 / lv - MMR) * 1e4, 0)})
liq = pd.DataFrame(liq_rows)
liq.to_csv(f"{OUT}/binance_isolated_liq.csv", index=False)

# ---------------------------------------------------------------- Monte Carlo
GEOMS = {"1:1": 1.0, "1.5:1": 1.5}
EDGES = [-0.05, 0.0, 0.03, 0.05, 0.10]
FREQ = [5, 20]
DAYS = 365
RISKS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
NPATH = 4000
mc_rows = []
for gname, bwin in GEOMS.items():
    for e in EDGES:
        p = (1 + e) / (bwin + 1)
        sd = np.sqrt(p * bwin ** 2 + (1 - p) - e ** 2)
        kelly = e / bwin
        for fq in FREQ:
            nt = fq * DAYS
            wins = rng.random((NPATH, nt)) < p
            R = np.where(wins, bwin, -1.0)
            for r in RISKS:
                f = r / 100
                logeq = np.cumsum(np.log1p(f * R), axis=1)
                peak = np.maximum.accumulate(np.concatenate([np.zeros((NPATH, 1)), logeq], axis=1), axis=1)[:, 1:]
                dd = 1 - np.exp(logeq - peak)
                maxdd = dd.max(axis=1)
                fin = np.exp(logeq[:, -1])
                mc_rows.append({"geom": gname, "edge_R": e, "wr": round(p, 4), "trades_day": fq, "n_trades": nt,
                                "risk_pct": r, "kelly_pct": round(100 * kelly, 2),
                                "risk_over_kelly": round(f / kelly, 2) if kelly > 0 else np.nan,
                                "final_med": np.median(fin), "final_p05": np.percentile(fin, 5),
                                "final_p95": np.percentile(fin, 95), "P_loss": (fin < 1).mean(),
                                "maxdd_med": np.median(maxdd), "maxdd_p95": np.percentile(maxdd, 95),
                                "P_dd20": (maxdd >= 0.2).mean(), "P_dd50": (maxdd >= 0.5).mean(),
                                "P_dd90": (maxdd >= 0.9).mean()})
        mc_rows_sd = sd
mc = pd.DataFrame(mc_rows)
mc.to_csv(f"{OUT}/mc_risk.csv", index=False)

# kenarı istatistiksel olarak görmek için gereken işlem sayısı (2σ, bağımsız varsayım)
det = []
for gname, bwin in GEOMS.items():
    for e in [0.03, 0.05, 0.10]:
        p = (1 + e) / (bwin + 1)
        sd = np.sqrt(p * bwin ** 2 + (1 - p) - e ** 2)
        n2 = (2 * sd / e) ** 2
        det.append({"geom": gname, "edge_R": e, "sd_R": round(sd, 3), "n_trades_2sigma": int(n2),
                    "days_at_5_per_day": round(n2 / 5, 0), "days_at_20_per_day": round(n2 / 20, 0)})
pd.DataFrame(det).to_csv(f"{OUT}/edge_detection_n.csv", index=False)

pd.set_option("display.width", 250)
print(lev.to_string())
print(liq.to_string())
print(pd.DataFrame(det).to_string())
sel = mc[(mc["trades_day"] == 20)]
print(sel.round(3).to_string())
print(mc[mc["trades_day"] == 5].round(3).to_string())
