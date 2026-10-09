"""islem_otopsi sabitleri — tüm eşikler burada, isimli (CLAUDE.md: magic number yasak).

Eşikler SONUCA BAKILMADAN sabitlendi (2026-10-07, ilk sürüm). Bir eşiği sonuç
gördükten sonra değiştirmek o koşunun kanıt değerini bitirir (defter §0.4).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "output" / "islem_otopsi"
CACHE_DIR = OUT_ROOT / "_cache"

# ── Strateji aileleri: magic − MAGIC_BASE → aile (yeni deneme/config.py + bot) ──
MAGIC_BASE = 52890969
FAMILY_BY_OFFSET = {
    0: "MOMSR",      # momentum / S/R (bot ana slot)
    1: "CHREV",      # kanal-sınır dönüşü
    2: "VIXREG",     # VIX rejimi → NDX yönü
    3: "REFLEX",     # reflex motoru (gölge)
    4: "DAYCOMBO",
    5: "USOIL_BRK",  # USOIL breakout (gölge)
    6: "REENTRY",
    7: "CAPREV",     # CAPREV portföyü NDX+DAX canlı (2026-10-09, kart 6/6)
    20: "DECIDER",   # claude_decider demo icrası
}
MANUAL_MAGIC = 0

# ── Semboller ────────────────────────────────────────────────────────────────
SYMBOL_ALIASES = {
    "NDX": "NDX.INDX", "NAS": "NDX.INDX", "NAS100": "NDX.INDX", "NASDAQ": "NDX.INDX",
    "NDX.INDX": "NDX.INDX", "USTEC": "NDX.INDX",
    "DAX": "GDAXI.INDX", "GER40": "GDAXI.INDX", "GDAXI": "GDAXI.INDX", "GDAXI.INDX": "GDAXI.INDX",
    "USOIL": "USOIL.FOREX", "OIL": "USOIL.FOREX", "WTI": "USOIL.FOREX", "PETROL": "USOIL.FOREX",
    "SPOTCRUDE": "USOIL.FOREX", "USOIL.FOREX": "USOIL.FOREX",
    "XAU": "XAUUSD", "XAUUSD": "XAUUSD", "GOLD": "XAUUSD", "ALTIN": "XAUUSD",
}
# Fiyat eşleştirme toleransı (fiyat birimi) — saat ekseni ve bariyer dokunuşu.
PRICE_TOL = {"NDX.INDX": 3.0, "GDAXI.INDX": 3.0, "XAUUSD": 0.5, "USOIL.FOREX": 0.05}
# Tipik spread (mumlar BID; SELL bariyerleri ASK ile tetiklenir).
TYPICAL_SPREAD = {"NDX.INDX": 1.5, "GDAXI.INDX": 1.5, "XAUUSD": 0.25, "USOIL.FOREX": 0.03}
DEFAULT_PRICE_TOL_FRAC = 0.0002

# ── Saat ekseni ──────────────────────────────────────────────────────────────
# indicator_snapshots 2026-07-28 18:00 UTC öncesi BROKER saatinde (+3s) yazılmış;
# 18:00–21:00 arası belirsiz → atılır (bot_loss_veto PROTOCOL + hafıza).
SNAPSHOT_BROKER_UNTIL = "2026-07-28T18:00:00+00:00"
SNAPSHOT_AMBIGUOUS_UNTIL = "2026-07-28T21:00:00+00:00"
SNAPSHOT_BROKER_SHIFT_H = 3
# bot_trades zamanları broker saati (UTC+2/+3) — işlem başına aranacak kaymalar (saat).
TRADE_OFFSET_CANDIDATES_H = (-3, -2, 0, -4, -1, 1)
MIN_ALIGNED_FRAC = 0.75          # bunun altı → MISALIGNED, dur

# ── Veri pencereleri ─────────────────────────────────────────────────────────
WARMUP_DAYS = 14                 # 1h EMA50 + 10 günlük mevsimsel hacim tabanı
POST_EXIT_MIN = 240              # çıkış sonrası karşı-olgu penceresi
POST_EXIT_SHORT_MIN = 60
REPLAY_MAX_HOLD_MIN = 3 * 24 * 60
DEFAULT_FOCUS_DAYS = 14
DEFAULT_BASE_DAYS = 120
SUPABASE_PAGE = 1000
CACHE_REFRESH_TAIL_H = 2         # önbelleğin son 2 saati her koşuda yeniden çekilir

# ── Gösterge parametreleri ───────────────────────────────────────────────────
EMA_FAST, EMA_SLOW = 20, 50
RSI_N = ATR_N = ADX_N = 14
BB_N, BB_K = 20, 2.0
STRUCT_LOOKBACK = 30             # yapı uç noktası (1m bar)
RANGE_LOOKBACK = 240             # 4 saatlik aralık konumu
VOL_BASE_BARS = 60               # giriş öncesi hacim tabanı
SEASONAL_DAYS = 10               # mevsimsel hacim tabanı: aynı saat dilimi, önceki 10 gün
SEASONAL_MIN_DAYS = 4
SEASONAL_BUCKET_MIN = 15
DIV_WINDOW_A = (60, 20)          # diverjans: eski pencere [t-60, t-20)
DIV_RSI_MARGIN = 2.0
VOLDIV_FRAC = 0.8
REGIME_DAYS = 5
EARLY_MARKS_MIN = (5, 15)
EVENT_ENTRY_MAX_MIN = 120
EVENT_EXIT_PRE_MIN = 30

# ── Sınıflandırma / etiket eşikleri ──────────────────────────────────────────
FULL_SL_R = -0.8                 # R ≤ bu → tam SL
BE_BAND_R = 0.2                  # |R| < bu ve reason=SL → başabaş stop
FAST_SL_MIN = 10
SLOW_TRADE_MIN = 120
NEVER_WORKED_MFE_R = 0.15
WENT_GREEN_R = 0.3
NEAR_TP_FRAC = 0.7
CLEAN_TP_MAE_R = 0.25
PAINFUL_TP_MAE_R = 0.6
EARLY_TP_RUN_R = 1.0             # TP sonrası ≥1R daha gitti → hedef erken
WRONG_DIR_EXTRA_R = 1.0          # SL'den sonra ≥1R daha ters → yön yanlış
CHASE_RET15_ATR5 = 1.5           # son 15 dk ≥1,5 ATR5 lehte hareket → kovalama
DIP_RET15_ATR5 = -1.5            # ≤ −1,5 ATR5 → dönüş/dip alımı
VOL_SHOCK_SEAS = 2.5             # mevsimsel-düzeltilmiş hacim şoku
VOL_LOW_SEAS = 0.6
VOL_FADE_RATIO = 0.75            # son üçte bir / ilk üçte bir < bu → hacim sönümü
SPIKE_STOP_RANGE_ATR = 2.0
SLIP_R = 0.15
FIRST_HIT_R = 0.5
TIGHT_SL_ATR5 = 1.0              # SL < 1×ATR5 → gürültü içinde stop
GEO_ANOMALY_RR = (0.4, 3.0)      # RR bu aralık dışı → kurulum/besleme hatası şüphesi (defter E21)
GEO_ANOMALY_SL_ATR5 = 12.0       # SL > 12×ATR5 → olağan dışı geniş stop
RANGE_EDGE = 0.85                # 4s aralığın yön tarafındaki %15'lik ucu
MTF_WEAK = 1                     # 4 zaman diliminden ≤1 uyumlu → çelişki
LEG_VOL_HEAVY = 1.3              # çıkışa götüren bacak ilk bacaktan ≥%30 hacimli
VOL_HIGH_SEAS = 2.0
REVENGE_WINDOW_MIN = 60
DECISION_CLUSTER_MIN = 2         # aynı sembol+yön, 2 dk içinde → tek karar (E9)
VIX_REGIME_THRESHOLD = 18.4

# ── İstatistik ───────────────────────────────────────────────────────────────
PERMUTATIONS = 2000
MIN_GROUP_N = 8                  # SL ve TP gruplarının her biri en az bu kadar
FDR_Q = 0.10
TOP_FEATURES = 25
CANDIDATE_MAX = 6
INTERACTION_TOP = 6
RNG_SEED = 20261007
GEOMETRY_SL_MULTS = (0.75, 1.0, 1.25, 1.5, 2.0)
GEOMETRY_TP_MULTS = (0.75, 1.0, 1.5)
REPLAY_MIN_CALIB = 20
REPLAY_MIN_AGREE = 0.85
DIVERGENCE_GAP_R = 0.25
DIVERGENCE_T = 2.0

# ── Defter çapraz bağları: özellik → docs/KAPI_KAYIT_DEFTERI.md kimlikleri ──
REGISTRY_HINTS = {
    "pre_trend_align_1h": "B4 TREND_GATE (AKTİF, A−) · K9",
    "pre_dist_ema50_1h": "B4 TREND_GATE (AKTİF, A−)",
    "pre_slope_ema50_1h": "B4 TREND_GATE (AKTİF, A−)",
    "pre_range_pos_4h": "B5 POSITION_GATE (AKTİF, C/B) · B13 POS_TIGHT (X, E6)",
    "pre_ret_15": "GF-15 kovalama endeksi (C+, bota özgü)",
    "pre_ret_60": "GF-15 kovalama endeksi (C+)",
    "pre_consec": "GF-15 kovalama endeksi (C+)",
    "pre_vol_seas_15": "GF-14 T3 hacim patlaması (C+) · SY H2 hacim vetosu (reddedildi)",
    "pre_vol_ratio_5_60": "GF-14 T3 (C+) · SY H2/H3 (reddedildi)",
    "pre_rsi5": "B16 SELL_RSI (GÖLGE, C)",
    "pre_atr_regime": "B14 SQZ (GÖLGE, B)",
    "pre_bbw_pct5": "B14 SQZ (GÖLGE, B)",
    "pre_day_move_pct": "GF-10/11 K5b stres (GÖLGE) · GF-16 CAPREV",
    "pre_vix_favors": "VIXREG · K1 VIX_REGIME_GATE (AKTİF, A) · D3",
    "geo_sl_atr5": "OLD-20 sorun geometri · M8 · M11",
    "geo_rr": "OLD-20 · M8 (WR↑ para↓, E14)",
    "e5_mae_r": "M9 BE/kilit/erken çıkış (ELENDİ) · M7 zaman stopu (X)",
    "e15_mae_r": "M9 (ELENDİ) · M7 (X)",
    "e15_close_r": "M9 (ELENDİ) · M6 koşullu BE",
    "hour_utc": "B2/B3/B6 seans-gün kapıları · GF-03 saat takvimi taşınmaz (X)",
}
