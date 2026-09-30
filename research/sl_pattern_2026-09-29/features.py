"""Giriş anı özellikleri — yalnız giriş anından ÖNCE kapanmış barlar (sızıntısız)."""
import numpy as np
import pandas as pd

TFMIN = {"5m": 5, "15m": 15, "1h": 60}
KEYS = ["rsi14", "adx14", "dist_ema20_atr", "dist_ema50_atr", "above_ema200", "ema_stack_up",
        "ema_stack_dn", "bb_pct_b", "vwap_z", "macd_hist", "stoch_k", "atr14", "atr_pct",
        "plus_di", "minus_di", "sar_dist_atr"]

df = pd.read_pickle("paths_stats.pkl")
df = df[df.exit.isin(["tp", "sl"])].copy()
syms = df.sym.unique()
B = {(s, tf): pd.read_pickle(f"fx_{s}_{tf}.pkl") for s in syms for tf in ["1m", "5m", "15m", "1h"]}

feat = []
for r in df.itertuples():
    sgn = 1 if r.dir == "BUY" else -1
    f = {}
    for tf, mins in TFMIN.items():
        m = B[(r.sym, tf)]
        cutoff = r.open_utc - pd.Timedelta(minutes=mins)      # bar açılışı ≤ giriş−tf → kapanmış
        sub = m.loc[:cutoff]
        if not len(sub):
            continue
        ind = sub["ind"].iloc[-1] or {}
        for k in KEYS:
            v = ind.get(k)
            f[f"{tf}_{k}"] = float(v) if v is not None else np.nan
        # yön-göreli sürümler
        for k in ("dist_ema20_atr", "dist_ema50_atr", "macd_hist", "vwap_z", "sar_dist_atr"):
            if f.get(f"{tf}_{k}") is not None:
                f[f"{tf}_{k}_dir"] = f[f"{tf}_{k}"] * sgn
        f[f"{tf}_rsi_dir"] = (f.get(f"{tf}_rsi14", np.nan) - 50) * sgn
        f[f"{tf}_trend_with"] = float(bool(ind.get("ema_stack_up") if sgn > 0 else ind.get("ema_stack_dn")))
        f[f"{tf}_trend_against"] = float(bool(ind.get("ema_stack_dn") if sgn > 0 else ind.get("ema_stack_up")))
        f[f"{tf}_ema200_with"] = float(bool(ind.get("above_ema200")) == (sgn > 0))
    m1 = B[(r.sym, "1m")].loc[:r.open_utc - pd.Timedelta(minutes=1)]
    atr1h = f.get("1h_atr14", np.nan)
    if len(m1) > 240:
        c = m1["close"].values
        for mins in (15, 60, 240):
            f[f"chg{mins}_atr_dir"] = (c[-1] - c[-mins]) * sgn / atr1h if atr1h else np.nan
        hi, lo = m1["high"].values[-240:].max(), m1["low"].values[-240:].min()
        pos = (r.open_price - lo) / (hi - lo) if hi > lo else 0.5
        f["wave_pos_dir"] = pos if sgn > 0 else 1 - pos            # 1 = yön tarafında tepede (kovalama)
        f["range4h_atr"] = (hi - lo) / atr1h if atr1h else np.nan
    f["sl_atr1h"] = r.risk / atr1h if atr1h else np.nan
    f["tp_atr1h"] = r.reward / atr1h if atr1h else np.nan
    pass
    f["hour"] = r.open_utc.hour
    f["dow"] = r.open_utc.dayofweek
    f["is_limit"] = float(r.entry_kind == "limit")
    f["n_voters"] = len([v for v in str(r.voters).replace(",", "|").split("|") if v.strip()])
    f["family"] = (r.scope.split(":")[2] if isinstance(r.scope, str) and r.scope.count(":") >= 2
                   else ("SR" if r.entry_kind == "limit" else "MOM"))
    feat.append(f)

F = pd.DataFrame(feat, index=df.index)
out = df.join(F)
out.to_pickle("feat.pkl")
print(out.shape)
print(out.family.value_counts())
print(out[out.position_id == 390567007][["sl_atr1h", "tp_atr1h", "chg60_atr_dir", "chg240_atr_dir",
                                         "wave_pos_dir", "1h_rsi14", "5m_ema200_with", "1h_trend_with",
                                         "15m_adx14", "family", "n_voters"]].T)
