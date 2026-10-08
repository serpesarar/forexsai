"""Geçmiş benzerleri (analog) — bir işlemi, ondan ÖNCE kapanmış aynı sembol-yön işlemleriyle kıyaslar.

İki soru:
  1. "Bu işleme en çok benzeyen geçmiş işlemler nasıl bitti?" — karar-anı özellikleri üzerinde
     sağlam z-skorlu (medyan/IQR) en yakın k komşu. Yalnız çıkışı hedef işlemin GİRİŞİNDEN önce
     olanlar aday → sızıntısız (o an bilinebilecek geçmiş).
  2. "Ortak noktası ne?" — her özellik için hedefin değeri geçmiş SL'lerin ve geçmiş TP'lerin
     dağılımında hangi yüzdelikte; SL'lere belirgin yakın / TP'lere belirgin yakın olanlar listelenir.

Komşu sayısı küçüktür (k=10) → sonuç bir ipucudur; "komşuların %70'i SL" tek başına kapı gerekçesi DEĞİLDİR.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .compare import LOSS, WIN

ANALOG_FEATURES = [
    "pre_ret_15", "pre_ret_60", "pre_dist_ema20_1m", "pre_dist_ema50_1h", "pre_slope_ema50_1h", "pre_rsi5",
    "pre_range_pos_4h", "pre_day_move_pct", "pre_vol_seas_15", "pre_atr_regime", "pre_sl_struct_margin",
    "pre_mtf_agree", "pre_div_rsi_against", "geo_sl_atr5", "geo_rr",
]
FEATURE_LABELS = {
    "pre_ret_15": "son 15 dk hareket (ATR5, + = lehte)", "pre_ret_60": "son 60 dk hareket (ATR5)",
    "pre_dist_ema20_1m": "1m EMA20'den uzaklık", "pre_dist_ema50_1h": "1h EMA50'den uzaklık",
    "pre_slope_ema50_1h": "1h EMA50 eğimi (yönle)", "pre_rsi5": "5m RSI (yönle)",
    "pre_range_pos_4h": "4s aralıkta konum (1 = yön ucunda)", "pre_day_move_pct": "günlük hareket % (yönle)",
    "pre_vol_seas_15": "giriş öncesi hacim (saatine göre)", "pre_atr_regime": "volatilite rejimi (ATR5/5g medyan)",
    "pre_sl_struct_margin": "SL'nin yapı ucundan payı (ATR1)", "pre_mtf_agree": "uyumlu zaman dilimi (0–4)",
    "pre_div_rsi_against": "aleyhte RSI diverjansı", "geo_sl_atr5": "SL mesafesi (×ATR5)", "geo_rr": "RR",
}
K = 10
MIN_POOL = 20
MIN_GROUP = 8
NEAR_PCT_GAP = 25.0              # SL ve TP yüzdeliği arasında ≥25 puan → "belirgin yakın"


def _pool(t: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    p = t[(t["side"] == target["side"]) & (t["exit_utc"] < target["entry_utc"]) & t["outcome"].isin([LOSS, WIN])]
    return p.sort_values("entry_utc").drop_duplicates("decision_id")


def nearest(t: pd.DataFrame, target: pd.Series, k: int = K) -> pd.DataFrame:
    pool = _pool(t, target)
    if len(pool) < MIN_POOL:
        return pd.DataFrame()
    cols = [c for c in ANALOG_FEATURES if c in pool and pool[c].notna().mean() > 0.8 and np.isfinite(target.get(c, np.nan))]
    X = pool[cols].astype(float)
    med = X.median()
    iqr = (X.quantile(0.75) - X.quantile(0.25)).replace(0, np.nan).fillna(X.std()).replace(0, 1.0)
    Z = (X - med) / iqr
    z0 = (target[cols].astype(float) - med) / iqr
    diff = (Z - z0).abs().clip(upper=3.0)          # tek aykırı özellik mesafeyi ele geçirmesin
    dist = np.sqrt((diff ** 2).mean(axis=1, skipna=True))
    out = pool.assign(mesafe=dist).nsmallest(k, "mesafe")
    return out[["pid", "entry_utc", "family", "outcome", "r_exit", "net", "ana_neden_kod", "mesafe"]]


def feature_position(t: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    """Hedefin her özelliği geçmiş SL'ler ve TP'ler içinde hangi yüzdelikte → hangisine benziyor."""
    pool = _pool(t, target)
    L, W = pool[pool["outcome"] == LOSS], pool[pool["outcome"] == WIN]
    if len(L) < MIN_GROUP or len(W) < MIN_GROUP:
        return pd.DataFrame()
    rows = []
    for c in ANALOG_FEATURES:
        v = target.get(c, np.nan)
        if c not in pool or not np.isfinite(v):
            continue
        ls, ws = L[c].dropna(), W[c].dropna()
        if len(ls) < MIN_GROUP or len(ws) < MIN_GROUP:
            continue
        p_l, p_w = 100 * (ls <= v).mean(), 100 * (ws <= v).mean()
        # "tipiklik": değerin grubun medyanına yüzdelik uzaklığı (0 = tam medyanında)
        d_l, d_w = abs(p_l - 50), abs(p_w - 50)
        verdict = ("SL'lere benziyor" if d_w - d_l >= NEAR_PCT_GAP else
                   "TP'lere benziyor" if d_l - d_w >= NEAR_PCT_GAP else "ayırt etmiyor")
        rows.append({"özellik": FEATURE_LABELS.get(c, c), "değer": float(v), "SL medyanı": float(ls.median()),
                     "TP medyanı": float(ws.median()), "SL yüzdeliği": p_l, "TP yüzdeliği": p_w, "hüküm": verdict})
    return pd.DataFrame(rows)


def summary_line(nb: pd.DataFrame, pool_sl_rate: float) -> str:
    if nb.empty:
        return "geçmişte yeterli benzer işlem yok"
    n_sl = int((nb["outcome"] == LOSS).sum())
    return (f"en benzer {len(nb)} geçmiş işlemin {n_sl}'i SL (bu sembol-yönde taban SL oranı "
            f"%{pool_sl_rate * 100:.0f}), ort R {nb['r_exit'].mean():+.2f}")


def pool_sl_rate(t: pd.DataFrame, target: pd.Series) -> float:
    p = _pool(t, target)
    return float((p["outcome"] == LOSS).mean()) if len(p) else np.nan
