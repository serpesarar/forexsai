"""features.py — madencilikte KULLANILABİLİR özellikler (ve neden diğerleri yasak).

YASAK: mutlak fiyat/seviye kolonları (*_close, *_ema20/50/200, *_atr, mx_NDXCASH,
mx_QQQ, mx_SPX, mx_HYG, mx_TLT, mx_DXY).
Neden: NDX 5 ayda 30.300 → 28.400 gitti. "M15_close < 29.000" gibi bir eşik,
yükseliş rejimini düşüş rejiminden MÜKEMMEL ayırır → TRAIN'de muhteşem görünür,
ama bu bir kural değil, TARİHİ EZBERLEMEKTİR. Ölçeksiz (ATR/yüzde/oran/bounded)
özellikler bu tuzağa düşmez.

VIX / VIX3M / US10Y seviyeleri İSTİSNA: ortalamaya dönen, sınırlı büyüklükler,
fiyat seviyesiyle mekanik olarak bağlı değiller.
"""
from __future__ import annotations

import re

import pandas as pd

BANNED_PATTERNS = [
    r"^[MH]\d+_close$", r"^[MH]\d+_ema\d+$", r"^[MH]\d+_atr$",
    r"^mx_(NDXCASH|QQQ|SPX|HYG|TLT|DXY)$",
]
NON_FEATURE = {"ts", "direction", "outcome", "exit_i", "r", "pnl", "ambiguous",
               "bars_held", "mfe_r", "mae_r", "entry_px", "timeout", "day", "split",
               "sig_id", "model", "conf", "backend_status", "entry_ts", "known_at"}


def is_allowed(col: str) -> bool:
    if col in NON_FEATURE:
        return False
    return not any(re.match(p, col) for p in BANNED_PATTERNS)


def allowed(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if is_allowed(c)]


# ── hipotez aileleri (madenci ajanlar bunları paylaşır) ──────────────────────
FAMILIES: dict[str, list[str]] = {
    "trend_yapisi": [
        "M15_dist_ema20_atr", "M15_dist_ema50_atr", "M15_dist_ema200_atr",
        "M30_dist_ema20_atr", "M30_dist_ema50_atr", "M30_dist_ema200_atr",
        "H1_dist_ema20_atr", "H1_dist_ema50_atr", "H1_dist_ema200_atr",
        "H4_dist_ema20_atr", "H4_dist_ema50_atr", "H4_dist_ema200_atr",
        "M15_ema20_slope_atr", "M15_ema50_slope_atr", "M30_ema20_slope_atr",
        "M30_ema50_slope_atr", "H1_ema20_slope_atr", "H1_ema50_slope_atr",
        "H4_ema20_slope_atr", "H4_ema50_slope_atr",
        "M15_sar_dist_atr", "M30_sar_dist_atr", "H1_sar_dist_atr", "H4_sar_dist_atr",
        "M15_adx", "M30_adx", "H1_adx", "H4_adx",
        "M15_di_diff", "M30_di_diff", "H1_di_diff", "H4_di_diff",
    ],
    "geri_donus_gerilme": [
        "M1_dist_ema20_atr", "M5_dist_ema20_atr", "M5_dist_ema50_atr",
        "M1_rsi", "M5_rsi", "M15_rsi", "M30_rsi", "H1_rsi", "H4_rsi",
        "M1_stoch_k", "M5_stoch_k", "M15_stoch_k", "M30_stoch_k", "H1_stoch_k", "H4_stoch_k",
        "M5_bb_pos", "M15_bb_pos", "M30_bb_pos", "H1_bb_pos", "H4_bb_pos",
        "M5_pos_in_range50", "M15_pos_in_range50", "M30_pos_in_range50",
        "H1_pos_in_range50", "H4_pos_in_range50",
        "M15_dist_ll50_atr", "M15_dist_hh50_atr", "H1_dist_ll50_atr", "H1_dist_hh50_atr",
    ],
    "volatilite_rejimi": [
        "M5_atr_pct", "M15_atr_pct", "M30_atr_pct", "H1_atr_pct", "H4_atr_pct",
        "M5_atr_ratio", "M15_atr_ratio", "M30_atr_ratio", "H1_atr_ratio", "H4_atr_ratio",
        "M15_bb_width_atr", "M30_bb_width_atr", "H1_bb_width_atr", "H4_bb_width_atr",
        "M15_range_atr", "M30_range_atr", "H1_range_atr",
        "mx_ndx_rvol20", "mx_VIX", "mx_VIX3M", "mx_vix_term", "mx_VIX_chg1", "mx_VIX_chg5",
    ],
    "seans_zaman": [
        "et_hour", "utc_hour", "dow", "min_since_open", "is_rth",
        "day_ret_pct", "pos_in_day_range", "day_range_vs_adr", "gap_pct",
        "above_prev_high", "below_prev_low", "prev_ret",
    ],
    "makro_capraz": [
        "mx_VIX", "mx_VIX_chg1", "mx_VIX_chg5", "mx_vix_term",
        "mx_DXY_chg1", "mx_DXY_chg5", "mx_US10Y", "mx_US10Y_chg1", "mx_US10Y_chg5",
        "mx_QQQ_chg1", "mx_QQQ_chg5", "mx_SPX_chg1", "mx_SPX_chg5",
        "mx_HYG_chg1", "mx_HYG_chg5", "mx_TLT_chg1", "mx_TLT_chg5", "mx_hyg_tlt",
    ],
    "mikroyapi_mum": [
        "M1_body_frac", "M5_body_frac", "M15_body_frac", "M30_body_frac",
        "M1_up_frac20", "M5_up_frac20", "M15_up_frac20", "M30_up_frac20", "H1_up_frac20",
        "M1_vol_ratio", "M5_vol_ratio", "M15_vol_ratio", "M30_vol_ratio", "H1_vol_ratio",
        "M1_ret5_atr", "M5_ret5_atr", "M15_ret5_atr", "M30_ret5_atr", "H1_ret5_atr",
        "M1_ret20_atr", "M5_ret20_atr", "M15_ret20_atr", "M30_ret20_atr", "H1_ret20_atr",
        "M5_macd_hist_atr", "M15_macd_hist_atr", "M30_macd_hist_atr", "H1_macd_hist_atr",
        "H4_macd_hist_atr",
    ],
    "gunluk_rejim": [
        "ret5d", "ret20d", "dist_d_ema20_pct", "dist_d_ema50_pct", "d_trend_up",
        "d_up_frac10", "mx_ndx_above_ema50d", "mx_ndx_above_ema200d",
        "mx_ndx_dd_from_ath60", "mx_ndx_rvol20",
        "H4_ret5_atr", "H4_ret20_atr", "H4_up_frac20", "H4_pos_in_range50",
    ],
}
