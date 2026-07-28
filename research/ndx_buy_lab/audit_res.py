"""audit_res.py — COZUNURLUK YANLILIGI OLCUMU.

Iddia geometry_sweep_1h.py'den geliyor: 1h barlarda TP ve SL AYNI barda vurulursa
kod SL'i once sayiyor. Dusuk RR'de TP ve SL birbirine yakin (0.73 ATR vs 1.0 ATR)
=> tek bir 1h bar ikisini de kapsayabilir. Yuksek RR'de TP 3-4 ATR uzakta =>
ayni bar ikisini birden kapsayamaz. Yani belirsizlik-cezasi RR ile ters orantili
DAGILIYOR olabilir.

Bu dosya: AYNI giris zamanlari, AYNI tp/sl mesafeleri, AYNI duvar-saati ufku;
tek degisken = yolu cozen barlarin cozunurlugu (1h vs 15m vs 1m).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DATA = "data/"
FRIC = 1.0 / 29000


def load(name: str) -> pd.DataFrame:
    d = pd.read_csv(DATA + name, parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    return d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def h1_atr(d1h: pd.DataFrame) -> pd.Series:
    pc = d1h["close"].shift(1)
    tr = pd.concat([d1h.high - d1h.low, (d1h.high - pc).abs(),
                    (d1h.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    return (atr / d1h["close"]).shift(1)      # karar aninda BILINEN


def resolve(bars: pd.DataFrame, entry_ts: np.ndarray, entry_px: np.ndarray,
            tp: np.ndarray, sl: np.ndarray, horizon_h: float, direction: str,
            tie: str = "sl"):
    """Duvar-saati ufku: [entry_ts, entry_ts + horizon_h saat).
    tie: ayni bar icinde ikisi de vurulursa 'sl' | 'tp' | 'split' (0.5/0.5).
    Doner: win, loss, opn, end_ret, amb (belirsiz bar orani icin maske)."""
    bts = bars["ts"].values
    bh = bars["high"].to_numpy()
    bl = bars["low"].to_numpy()
    bc = bars["close"].to_numpy()
    i0 = np.searchsorted(bts, entry_ts, side="left")
    i1 = np.searchsorted(bts, entry_ts + np.timedelta64(int(horizon_h * 60), "m"), side="left")
    width = int((i1 - i0).max())
    n = len(entry_ts)
    cols = np.arange(width)[None, :]
    idx = np.minimum(i0[:, None] + cols, len(bts) - 1)
    valid = cols < (i1 - i0)[:, None]
    up = np.where(valid, bh[idx] / entry_px[:, None] - 1.0, -np.inf)
    dn = np.where(valid, bl[idx] / entry_px[:, None] - 1.0, np.inf)
    if direction == "BUY":
        hit_tp, hit_sl = up >= tp[:, None], dn <= -sl[:, None]
    else:
        hit_tp, hit_sl = dn <= -tp[:, None], up >= sl[:, None]
    any_tp, any_sl = hit_tp.any(1), hit_sl.any(1)
    BIG = 10 ** 7
    t_tp = np.where(any_tp, hit_tp.argmax(1), BIG)
    t_sl = np.where(any_sl, hit_sl.argmax(1), BIG)
    amb = any_tp & any_sl & (t_tp == t_sl)          # AYNI barda ikisi de -> belirsiz
    if tie == "sl":
        win = any_tp & (t_tp < t_sl)
    elif tie == "tp":
        win = any_tp & (t_tp <= t_sl)
    else:
        win = any_tp & (t_tp < t_sl)                 # 'split' asagida ayri islenir
    loss = any_sl & ~win & (t_sl <= t_tp)
    opn = ~win & ~loss
    last = np.where((i1 - i0) > 0, i1 - 1, i0)
    end_ret = bc[np.minimum(last, len(bts) - 1)] / entry_px - 1.0
    return win, loss, opn, end_ret, amb


def ev(win, loss, opn, end_ret, amb, tp, sl, direction, fric, tie="sl"):
    sgn = 1.0 if direction == "BUY" else -1.0
    r = np.where(win, (tp - fric) / sl, np.where(loss, -(sl + fric) / sl, 0.0))
    r = np.where(opn, (sgn * end_ret - fric) / sl, r)
    if tie == "split":                # belirsizleri yari kazanc/yari kayip say
        r = np.where(amb, 0.5 * (tp - fric) / sl + 0.5 * (-(sl + fric) / sl), r)
    return r
