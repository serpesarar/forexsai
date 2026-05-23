"""
Precision Veto Engine
=====================
ForexSAI'nin 6 sinyal jeneratörü (ML, EMEL, PULSE 1/2/3, SMC) sinyal üretir
ama "doğru fiyat noktası mı?" sorusunu cevaplayan tek merci yoktu — sistem
tepelerden alıp diplerden satıyordu. Bu motor, her sinyal prediction_logs'a
yazılMADAN ÖNCE 4 aşamadan geçirir:

  Aşama 1 — Yapısal vetolar (hard, fail-fast): likidite bölgesi + MTF teyit
  Aşama 2 — Mum yapısı: fitil reddi + formasyon tespiti
  Aşama 3 — İstatistiksel filtre (soft): Bollinger + z-score penaltıları
  Aşama 4 — Meta sentezleyici (LightGBM) — model dosyası varsa

Hard veto → sinyal bloklanır, sebep signal_vetoes'a yazılır.
Soft penalty → confidence düşürülür; kümülatif 30+ ise HOLD'a çevrilir.

Public API:
    await check_signal(signal: dict) -> VetoResult
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Konfigürasyon ───────────────────────────────────────────────────────────
PRECISION_VETO_CONFIG: dict[str, Any] = {
    "enabled": True,
    # shadow_mode=True: veto HESAPLANIR ve loglanır ama sinyal BLOKLANMAZ.
    # Güvenli açılış — backtest ile etkiyi gör, sonra False yap (enforce).
    "shadow_mode": True,
    "stage_1_enabled": True,
    "stage_2_enabled": True,
    "stage_3_enabled": True,
    "stage_1c_enabled": True,         # Day Structure veto katmanı
    "stage_4_enabled": True,
    # Stage 1c eşikleri — profesör review'inden sonra konservatif
    "stage1c_memory_min_rejections": 4,
    "stage1c_memory_min_freshness": 0.6,
    "stage1c_memory_distance_atr": 0.15,
    "stage1c_pdh_pdl_distance_atr": 0.10,
    "stage1c_pdh_pdl_min_rejections_today": 2,
    "stage1c_pivot_penalty_distance_atr": 0.10,
    "stage1c_pivot_penalty": 10,
    "liquidity_lookback": 50,
    "liquidity_premium_threshold": 0.85,   # son 50 mumun %15 tepesi
    "liquidity_discount_threshold": 0.15,
    "wick_ratio_threshold": 0.60,
    "wick_single_extreme_threshold": 0.70,
    "wick_count_in_last_n": 2,
    "wick_lookback": 5,
    "wick_price_zone": 0.25,               # fiyat son 20 mumun %25 uç bölgesinde
    "bb_period": 20,
    "bb_std": 2.0,
    "bb_extreme_threshold": 0.95,
    "z_score_period": 50,
    "z_score_threshold": 2.0,
    "soft_veto_penalty_cap": 30,           # kümülatif penaltı bu değere ulaşırsa HOLD
    "mtf_single_opposition_penalty": 15,
    "meta_classifier_threshold": 0.55,
    "meta_confidence_blend_weight": 0.3,
}

# Sembol bazlı override — XAUUSD'nin volatilitesi farklı.
_SYMBOL_OVERRIDES: dict[str, dict[str, Any]] = {
    "XAUUSD": {
        # Altın daha gürültülü — uç bölge eşiklerini biraz gevşet.
        "liquidity_premium_threshold": 0.88,
        "liquidity_discount_threshold": 0.12,
        "wick_ratio_threshold": 0.62,
        "z_score_threshold": 2.3,
    },
    "USOIL.FOREX": {
        "wick_ratio_threshold": 0.62,
        "z_score_threshold": 2.3,
    },
}

_META_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models",
                                 "precision_meta_classifier.joblib")
_meta_model = None
_meta_model_loaded = False


def _cfg(symbol: str, key: str) -> Any:
    """Sembol-spesifik override varsa onu, yoksa global değeri döndür."""
    ov = _SYMBOL_OVERRIDES.get(symbol, {})
    if key in ov:
        return ov[key]
    return PRECISION_VETO_CONFIG.get(key)


def _env_enabled() -> bool:
    """Env ile master kapatma: PRECISION_VETO_ENABLED=0."""
    return (os.getenv("PRECISION_VETO_ENABLED", "1") != "0"
            and PRECISION_VETO_CONFIG.get("enabled", True))


def _env_shadow() -> bool:
    """Env ile enforce moduna geçiş: PRECISION_VETO_SHADOW=0 → gerçek bloklama."""
    env = os.getenv("PRECISION_VETO_SHADOW")
    if env is not None:
        return env != "0"
    return bool(PRECISION_VETO_CONFIG.get("shadow_mode", True))


# ─── Sonuç tipi ──────────────────────────────────────────────────────────────
@dataclass
class VetoResult:
    """Bir sinyalin veto motorundan geçiş sonucu."""
    vetoed: bool = False                 # enforce modunda gerçekten bloklandı mı
    would_veto: bool = False             # shadow dahil: veto edilirdi mi
    stage: int = 0
    reason: str = ""
    direction: str = ""                  # nihai yön (HOLD'a çevrilmiş olabilir)
    original_confidence: float = 0.0
    adjusted_confidence: float = 0.0
    total_penalty: float = 0.0
    converted_to_hold: bool = False
    shadow_mode: bool = True
    details: dict = field(default_factory=dict)
    features: dict = field(default_factory=dict)   # signal_vetoes kolonları

    def to_log_dict(self, signal: dict) -> dict:
        f = self.features
        return {
            "symbol": signal.get("symbol"),
            "model_type": signal.get("model_type") or "unknown",
            "signal_direction": signal.get("direction"),
            "signal_confidence": float(signal.get("confidence") or 0),
            "veto_stage": self.stage,
            "veto_reason": self.reason,
            "veto_details": self.details,
            "liquidity_zone_position": f.get("liquidity_zone_position"),
            "mtf_agreement_score": f.get("mtf_agreement_score"),
            "wick_rejection_score": f.get("wick_rejection_score"),
            "bb_position": f.get("bb_position"),
            "z_score": f.get("z_score"),
            "meta_classifier_proba": f.get("meta_classifier_proba"),
            "price_at_veto": float(signal.get("price") or signal.get("entry_price") or 0),
            "market_regime": signal.get("market_regime"),
            "outcome": ("shadow" if (self.would_veto and self.shadow_mode)
                        else "veto" if self.vetoed
                        else "penalty" if self.total_penalty > 0
                        else "pass"),
        }


# ─── Mum yardımcıları ────────────────────────────────────────────────────────
def _v(candle: dict, *keys: str) -> float:
    for k in keys:
        if k in candle and candle[k] is not None:
            try:
                return float(candle[k])
            except (TypeError, ValueError):
                pass
    return 0.0


def _o(c): return _v(c, "open", "o")
def _h(c): return _v(c, "high", "h")
def _l(c): return _v(c, "low", "l")
def _c(c): return _v(c, "close", "c")


def _ema(values: list[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return ema


def _trend_direction(candles: list[dict], ema_period: int = 50) -> str:
    """EMA50 eğimi ile trend yönü: UP | DOWN | FLAT."""
    closes = [_c(c) for c in candles if _c(c) > 0]
    if len(closes) < ema_period + 6:
        return "FLAT"
    ema_now = _ema(closes, ema_period)
    ema_prev = _ema(closes[:-5], ema_period)
    if ema_now is None or ema_prev is None or ema_prev == 0:
        return "FLAT"
    slope_pct = (ema_now - ema_prev) / ema_prev * 100.0
    if slope_pct > 0.03:
        return "UP"
    if slope_pct < -0.03:
        return "DOWN"
    return "FLAT"


def _wick_metrics(c: dict) -> dict:
    hi, lo, op, cl = _h(c), _l(c), _o(c), _c(c)
    total = hi - lo
    if total <= 0:
        return {"upper_ratio": 0.0, "lower_ratio": 0.0, "body_ratio": 0.0}
    upper = hi - max(op, cl)
    lower = min(op, cl) - lo
    body = abs(cl - op)
    return {
        "upper_ratio": upper / total,
        "lower_ratio": lower / total,
        "body_ratio": body / total,
    }


# ─── AŞAMA 1 — Yapısal vetolar ───────────────────────────────────────────────
def _stage1_liquidity(symbol: str, direction: str, price: float,
                       candles: list[dict]) -> tuple[Optional[str], float, dict]:
    """1a. Likidite bölgesi. Dönüş: (veto_reason|None, zone_position, details)."""
    look = int(_cfg(symbol, "liquidity_lookback"))
    window = candles[-look:] if len(candles) >= look else candles
    if len(window) < 10:
        return None, 0.5, {"note": "insufficient_candles"}
    hi = max(_h(c) for c in window)
    lo = min(_l(c) for c in window)
    rng = hi - lo
    pos = (price - lo) / rng if rng > 0 else 0.5
    pos = max(0.0, min(1.0, pos))
    prem = _cfg(symbol, "liquidity_premium_threshold")
    disc = _cfg(symbol, "liquidity_discount_threshold")
    details = {"zone_position": round(pos, 3), "range_high": hi, "range_low": lo,
               "premium_thr": prem, "discount_thr": disc}
    if direction == "BUY" and pos >= prem:
        return "premium_zone_buy", pos, details
    if direction == "SELL" and pos <= disc:
        return "discount_zone_sell", pos, details
    return None, pos, details


def _stage1_mtf(direction: str, h1: list[dict], h4: list[dict]
                ) -> tuple[Optional[str], float, float, dict]:
    """1b. MTF teyit. Dönüş: (veto_reason|None, penalty, agreement_score, details)."""
    t1 = _trend_direction(h1)
    t4 = _trend_direction(h4)
    details = {"h1_trend": t1, "h4_trend": t4}

    def opposes(tf_trend: str) -> bool:
        return ((direction == "BUY" and tf_trend == "DOWN")
                or (direction == "SELL" and tf_trend == "UP"))

    def agrees(tf_trend: str) -> bool:
        return ((direction == "BUY" and tf_trend == "UP")
                or (direction == "SELL" and tf_trend == "DOWN"))

    opp = sum(1 for t in (t1, t4) if opposes(t))
    agr = sum(1 for t in (t1, t4) if agrees(t))
    score = (agr - opp) / 2.0   # -1 .. +1

    if opp == 2:
        return "mtf_strong_opposition", 0.0, score, details
    if opp == 1:
        return None, float(PRECISION_VETO_CONFIG["mtf_single_opposition_penalty"]), score, details
    return None, 0.0, score, details


# ─── AŞAMA 2 — Mum yapısı ────────────────────────────────────────────────────
def _price_zone(price: float, candles: list[dict], look: int = 20) -> float:
    """Fiyatın son `look` mumdaki konumu (0=dip, 1=tepe)."""
    window = candles[-look:] if len(candles) >= look else candles
    if len(window) < 5:
        return 0.5
    hi = max(_h(c) for c in window)
    lo = min(_l(c) for c in window)
    rng = hi - lo
    return max(0.0, min(1.0, (price - lo) / rng)) if rng > 0 else 0.5


def _stage2_wick(symbol: str, direction: str, price: float,
                 candles: list[dict]) -> tuple[Optional[str], float, dict]:
    """2a. Fitil ters dönme tespiti. Dönüş: (reason|None, wick_score, details)."""
    look = int(_cfg(symbol, "wick_lookback"))
    thr = float(_cfg(symbol, "wick_ratio_threshold"))
    extreme = float(_cfg(symbol, "wick_single_extreme_threshold"))
    need = int(_cfg(symbol, "wick_count_in_last_n"))
    recent = candles[-look:] if len(candles) >= look else candles
    if len(recent) < 3:
        return None, 0.0, {"note": "insufficient_candles"}

    metrics = [_wick_metrics(c) for c in recent]
    upper_hits = sum(1 for m in metrics if m["upper_ratio"] > thr)
    lower_hits = sum(1 for m in metrics if m["lower_ratio"] > thr)
    max_upper = max(m["upper_ratio"] for m in metrics)
    max_lower = max(m["lower_ratio"] for m in metrics)
    zone = _price_zone(price, candles, 20)
    pz = float(_cfg(symbol, "wick_price_zone"))

    # wick_rejection_score: 0..1, sinyal yönüne karşı reddetme baskısı.
    if direction == "BUY":
        score = min(1.0, (upper_hits / max(need, 1)) * 0.6 + max_upper * 0.4)
    else:
        score = min(1.0, (lower_hits / max(need, 1)) * 0.6 + max_lower * 0.4)

    details = {"upper_hits": upper_hits, "lower_hits": lower_hits,
               "max_upper_ratio": round(max_upper, 3),
               "max_lower_ratio": round(max_lower, 3),
               "price_zone": round(zone, 3)}

    # Çoklu üst fitil + fiyat tepede → BUY veto
    if direction == "BUY" and upper_hits >= need and zone >= (1.0 - pz):
        return "wick_rejection_top", score, details
    # Çoklu alt fitil + fiyat dipte → SELL veto
    if direction == "SELL" and lower_hits >= need and zone <= pz:
        return "wick_rejection_bottom", score, details
    # Tek aşırı üst fitil + premium zone → BUY veto
    if direction == "BUY" and max_upper > extreme and zone >= _cfg(symbol, "liquidity_premium_threshold"):
        return "wick_rejection_top", score, details
    if direction == "SELL" and max_lower > extreme and zone <= _cfg(symbol, "liquidity_discount_threshold"):
        return "wick_rejection_bottom", score, details
    return None, score, details


def _detect_pattern(prev: dict, cur: dict) -> Optional[str]:
    """Saf-Python mum formasyonu tespiti (TA-Lib bağımlılığı yok)."""
    po, ph, pl, pc = _o(prev), _h(prev), _l(prev), _c(prev)
    o, hi, lo, cl = _o(cur), _h(cur), _l(cur), _c(cur)
    rng = hi - lo
    if rng <= 0:
        return None
    body = abs(cl - o)
    upper = hi - max(o, cl)
    lower = min(o, cl) - lo

    # Bearish engulfing: önceki yükseliş, şimdiki düşüş gövdesi onu sarıyor
    if pc > po and cl < o and o >= pc and cl <= po:
        return "bearish_engulfing"
    # Bullish engulfing
    if pc < po and cl > o and o <= pc and cl >= po:
        return "bullish_engulfing"
    # Shooting star: küçük gövde, uzun üst fitil, kısa alt fitil
    if body < rng * 0.35 and upper > body * 2.0 and lower < body:
        return "shooting_star"
    # Hammer: küçük gövde, uzun alt fitil, kısa üst fitil
    if body < rng * 0.35 and lower > body * 2.0 and upper < body:
        return "hammer"
    # Doji: gövde neredeyse yok
    if body < rng * 0.1:
        return "doji"
    return None


def _stage2_pattern(symbol: str, direction: str, price: float,
                     candles: list[dict]) -> tuple[Optional[str], dict]:
    """2b. Formasyon tespiti."""
    if len(candles) < 3:
        return None, {"note": "insufficient_candles"}
    pattern = _detect_pattern(candles[-2], candles[-1])
    zone = _price_zone(price, candles, 20)
    details = {"pattern": pattern, "price_zone": round(zone, 3)}
    if pattern is None:
        return None, details
    prem = _cfg(symbol, "liquidity_premium_threshold")
    disc = _cfg(symbol, "liquidity_discount_threshold")
    bearish_top = pattern in ("bearish_engulfing", "shooting_star")
    bullish_bot = pattern in ("bullish_engulfing", "hammer")
    if direction == "BUY" and bearish_top and zone >= prem:
        return "bearish_pattern_at_high", details
    if direction == "SELL" and bullish_bot and zone <= disc:
        return "bullish_pattern_at_low", details
    return None, details


# ─── AŞAMA 3 — İstatistiksel filtre (soft) ───────────────────────────────────
def _bollinger(closes: list[float], period: int, std_mult: float):
    if len(closes) < period:
        return None
    window = closes[-period:]
    mid = sum(window) / period
    var = sum((x - mid) ** 2 for x in window) / period
    sd = var ** 0.5
    return mid + std_mult * sd, mid, mid - std_mult * sd


def _stage3_meanrev(symbol: str, direction: str, price: float,
                    candles: list[dict]) -> tuple[float, dict]:
    """Bollinger + z-score → confidence penaltısı. Dönüş: (penalty, details)."""
    closes = [_c(c) for c in candles if _c(c) > 0]
    penalty = 0.0
    details: dict = {}
    bb_pos = None
    z = None

    bb = _bollinger(closes, int(_cfg(symbol, "bb_period")),
                    float(_cfg(symbol, "bb_std")))
    if bb:
        upper, mid, lower = bb
        rng = upper - lower
        bb_pos = (price - lower) / rng if rng > 0 else 0.5
        bb_pos = max(-0.5, min(1.5, bb_pos))
        ext = float(_cfg(symbol, "bb_extreme_threshold"))
        if direction == "BUY":
            if price > upper:
                penalty += 20
            elif bb_pos > ext:
                penalty += 10
        else:  # SELL
            if price < lower:
                penalty += 20
            elif bb_pos < (1.0 - ext):
                penalty += 10
        details["bb_position"] = round(bb_pos, 3)

    # Rolling z-score
    zp = int(_cfg(symbol, "z_score_period"))
    if len(closes) >= zp:
        window = closes[-zp:]
        mean = sum(window) / zp
        var = sum((x - mean) ** 2 for x in window) / zp
        sd = var ** 0.5
        if sd > 0:
            z = (price - mean) / sd
            zthr = float(_cfg(symbol, "z_score_threshold"))
            # Sinyal aşırı sapma yönünde mi? (BUY + zaten çok yukarıda)
            if (direction == "BUY" and z > zthr) or (direction == "SELL" and z < -zthr):
                penalty += 15
            details["z_score"] = round(z, 3)

    details["penalty"] = penalty
    details["_bb_pos"] = bb_pos
    details["_z"] = z
    return penalty, details


# ─── AŞAMA 1c — Day Structure (lean v1) ─────────────────────────────────────
async def _stage1c_day_structure(symbol: str, direction: str, price: float,
                                   timeframe: str
                                   ) -> tuple[Optional[str], float, dict]:
    """Day Structure veto katmanı — lean v1 (2 hard, 1 soft).

    HV1: Sinyal yönünde ≥4 reddetme'li memory zone'a ≤0.15 ATR + freshness ≥0.6
    HV2: BUY→PDH ≤0.10 ATR + PDH bugün ≥2 reddedilmiş (likidite avı kanıtı);
         SELL→PDL aynı şart.
    SP1: Pivot karşıt yön (R1/R2 BUY için, S1/S2 SELL için) ≤0.10 ATR → −10

    Dönüş: (veto_reason | None, soft_penalty, details)
    Aşırı-bloklama önlemleri: zone yönü kontrolü, reject-vs-break ayrımı,
    PDH/PDL temiz ilk-temas korunur, freshness şartı."""
    try:
        from services.day_structure_service import compute_day_structure
        ds = await compute_day_structure(symbol, timeframe)
    except Exception as e:
        logger.debug("[stage1c] day structure hata: %s", e)
        return None, 0.0, {"skipped": "compute_failed"}
    if ds is None or ds.atr <= 0:
        return None, 0.0, {"skipped": "no_structure"}

    details: dict = {
        "atr": round(ds.atr, 5),
        "today_atr_ratio": ds.today_atr_ratio,
        "memory_zone_count": len(ds.memory_zones),
    }
    cfg = PRECISION_VETO_CONFIG
    mem_dist = float(cfg["stage1c_memory_distance_atr"])
    mem_min_rej = int(cfg["stage1c_memory_min_rejections"])
    mem_min_fresh = float(cfg["stage1c_memory_min_freshness"])

    # ── HV1: sinyal yönünde strong rejection memory zone ────────────────────
    nearest_zone = ds.nearest_memory_zone_in_direction(direction)
    if nearest_zone is not None:
        dist_atr = abs(nearest_zone.center - price) / ds.atr
        if (dist_atr <= mem_dist
                and nearest_zone.rejections >= mem_min_rej
                and nearest_zone.freshness >= mem_min_fresh):
            details["hv1"] = {
                "zone_center": nearest_zone.center,
                "zone_touches": nearest_zone.touches,
                "zone_rejections": nearest_zone.rejections,
                "zone_freshness": nearest_zone.freshness,
                "distance_atr": round(dist_atr, 3),
            }
            return "memory_zone_rejection_path", 0.0, details

    # ── HV2: PDH/PDL'ye yakın + bugün reddedilmiş ────────────────────────────
    pdh_pdl_dist = float(cfg["stage1c_pdh_pdl_distance_atr"])
    min_today_rej = int(cfg["stage1c_pdh_pdl_min_rejections_today"])
    if direction == "BUY" and ds.pdh is not None:
        d = abs(ds.pdh - price) / ds.atr
        if d <= pdh_pdl_dist and ds.pdh_rejections_today >= min_today_rej:
            details["hv2"] = {"level": "PDH", "value": ds.pdh,
                              "distance_atr": round(d, 3),
                              "touches_today": ds.pdh_touches_today,
                              "rejections_today": ds.pdh_rejections_today}
            return "pdh_rejected_liquidity", 0.0, details
    if direction == "SELL" and ds.pdl is not None:
        d = abs(ds.pdl - price) / ds.atr
        if d <= pdh_pdl_dist and ds.pdl_rejections_today >= min_today_rej:
            details["hv2"] = {"level": "PDL", "value": ds.pdl,
                              "distance_atr": round(d, 3),
                              "touches_today": ds.pdl_touches_today,
                              "rejections_today": ds.pdl_rejections_today}
            return "pdl_rejected_liquidity", 0.0, details

    # ── SP1: karşıt-yön pivot zone yakınlığı → soft penalty ──────────────────
    sp1_dist = float(cfg["stage1c_pivot_penalty_distance_atr"])
    sp1_pen = float(cfg["stage1c_pivot_penalty"])
    opposing = ("R1", "R2", "R3") if direction == "BUY" else ("S1", "S2", "S3")
    nearest_pivot = None
    nearest_d = None
    for name in opposing:
        if name not in ds.pivots:
            continue
        d = abs(ds.pivots[name] - price) / ds.atr
        if d <= sp1_dist and (nearest_d is None or d < nearest_d):
            nearest_d = d
            nearest_pivot = name
    if nearest_pivot:
        details["sp1"] = {"pivot": nearest_pivot,
                          "value": ds.pivots[nearest_pivot],
                          "distance_atr": round(nearest_d, 3),
                          "penalty": sp1_pen}
        return None, sp1_pen, details

    return None, 0.0, details


# ─── AŞAMA 4 — Meta sentezleyici ─────────────────────────────────────────────
def _load_meta_model():
    global _meta_model, _meta_model_loaded
    if _meta_model_loaded:
        return _meta_model
    _meta_model_loaded = True
    try:
        if os.path.exists(_META_MODEL_PATH):
            import joblib
            _meta_model = joblib.load(_META_MODEL_PATH)
            logger.info("[precision-veto] meta classifier yüklendi")
        else:
            logger.info("[precision-veto] meta model yok — Aşama 4 atlanıyor "
                        "(model eğitilince devreye girer)")
    except Exception as e:
        logger.warning("[precision-veto] meta model yüklenemedi: %s", e)
        _meta_model = None
    return _meta_model


def _stage4_meta(symbol: str, signal: dict, features: dict
                 ) -> tuple[Optional[str], Optional[float], dict]:
    """Meta classifier. Model yoksa graceful skip."""
    model = _load_meta_model()
    if model is None:
        return None, None, {"skipped": "no_model"}
    try:
        import numpy as np
        # Feature sırası modelin eğitimiyle aynı olmalı — eğitim scripti
        # bunu precision_meta_features.json'a yazar; yoksa skip.
        feat_vec = features.get("_meta_feature_vector")
        if feat_vec is None:
            return None, None, {"skipped": "no_feature_vector"}
        proba = float(model.predict_proba(np.array([feat_vec]))[0][1])
        thr = float(_cfg(symbol, "meta_classifier_threshold"))
        if proba < thr:
            return "meta_classifier_low_confidence", proba, {"proba": round(proba, 3),
                                                              "threshold": thr}
        return None, proba, {"proba": round(proba, 3), "threshold": thr}
    except Exception as e:
        logger.warning("[precision-veto] meta inference hatası: %s", e)
        return None, None, {"error": str(e)[:120]}


# ─── Ana giriş ───────────────────────────────────────────────────────────────
async def check_signal(signal: dict) -> VetoResult:
    """Bir sinyali 4 aşamadan geçir. signal: symbol, direction, confidence,
    model_type, timeframe, price (zorunlu); market_regime (opsiyonel)."""
    symbol = signal.get("symbol") or ""
    direction = (signal.get("direction") or "").upper()
    conf = float(signal.get("confidence") or 0)
    timeframe = signal.get("timeframe") or "15m"
    price = float(signal.get("price") or signal.get("entry_price") or 0)

    res = VetoResult(direction=direction, original_confidence=conf,
                     adjusted_confidence=conf, shadow_mode=_env_shadow())

    if not _env_enabled() or direction not in ("BUY", "SELL"):
        return res
    if price <= 0:
        res.details["skipped"] = "no_price"
        return res

    # ── Mum verisi ───────────────────────────────────────────────────────────
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, timeframe, limit=120)
        h1 = await fetch_ohlc_data(symbol, "1h", limit=120)
        h4 = await fetch_ohlc_data(symbol, "4h", limit=120)
    except Exception as e:
        logger.warning("[precision-veto] mum verisi alınamadı %s: %s", symbol, e)
        res.details["skipped"] = "no_candle_data"
        return res
    if not candles or len(candles) < 20:
        res.details["skipped"] = "insufficient_candles"
        return res

    def _hard_veto(stage: int, reason: str, det: dict) -> VetoResult:
        res.would_veto = True
        res.stage = stage
        res.reason = reason
        res.details[f"stage{stage}"] = det
        if res.shadow_mode:
            res.vetoed = False          # shadow: bloklamaz, sadece işaretler
        else:
            res.vetoed = True
            res.direction = "HOLD"
        return res

    # ── AŞAMA 1 — Yapısal vetolar (fail-fast) ────────────────────────────────
    if PRECISION_VETO_CONFIG["stage_1_enabled"]:
        reason, zone_pos, det = _stage1_liquidity(symbol, direction, price, candles)
        res.features["liquidity_zone_position"] = round(zone_pos, 3)
        if reason:
            return _hard_veto(1, reason, det)

        reason, penalty, mtf_score, det = _stage1_mtf(direction, h1, h4)
        res.features["mtf_agreement_score"] = round(mtf_score, 3)
        if reason:
            return _hard_veto(1, reason, det)
        if penalty:
            res.total_penalty += penalty
            res.details["stage1_mtf_penalty"] = det

    # ── AŞAMA 2 — Mum yapısı ─────────────────────────────────────────────────
    if PRECISION_VETO_CONFIG["stage_2_enabled"]:
        reason, wick_score, det = _stage2_wick(symbol, direction, price, candles)
        res.features["wick_rejection_score"] = round(wick_score, 3)
        if reason:
            return _hard_veto(2, reason, det)

        reason, det = _stage2_pattern(symbol, direction, price, candles)
        if reason:
            return _hard_veto(2, reason, det)

    # ── AŞAMA 1c — Day Structure (Stage 2'den sonra, Stage 3'ten önce) ──────
    if PRECISION_VETO_CONFIG.get("stage_1c_enabled", True):
        reason, sp_penalty, det = await _stage1c_day_structure(
            symbol, direction, price, timeframe)
        if reason:
            return _hard_veto(1, reason, det)   # rapor aşaması=1 (yapısal)
        if sp_penalty:
            res.total_penalty += sp_penalty
            res.details["stage1c"] = det
        elif det.get("memory_zone_count") is not None:
            # Sessiz pass — sadece feature snapshot (Stage 4 için)
            res.features["day_structure_atr"] = det.get("atr")
            res.features["today_atr_ratio"] = det.get("today_atr_ratio")

    # ── AŞAMA 3 — İstatistiksel filtre (soft) ────────────────────────────────
    if PRECISION_VETO_CONFIG["stage_3_enabled"]:
        penalty, det = _stage3_meanrev(symbol, direction, price, candles)
        res.features["bb_position"] = det.get("_bb_pos")
        res.features["z_score"] = det.get("_z")
        res.total_penalty += penalty
        if penalty:
            res.details["stage3"] = {k: v for k, v in det.items()
                                     if not k.startswith("_")}

    # ── Soft veto kontrolü — kümülatif penaltı ───────────────────────────────
    res.adjusted_confidence = max(0.0, conf - res.total_penalty)
    cap = float(PRECISION_VETO_CONFIG["soft_veto_penalty_cap"])
    if res.total_penalty >= cap:
        res.would_veto = True
        res.stage = 3
        res.reason = "extreme_mean_deviation"
        res.converted_to_hold = True
        if not res.shadow_mode:
            res.vetoed = True
            res.direction = "HOLD"
        return res

    # ── AŞAMA 4 — Meta sentezleyici ──────────────────────────────────────────
    if PRECISION_VETO_CONFIG["stage_4_enabled"]:
        reason, proba, det = _stage4_meta(symbol, signal, res.features)
        if proba is not None:
            res.features["meta_classifier_proba"] = round(proba, 3)
        if reason:
            res.details["stage4"] = det
            return _hard_veto(4, reason, det)
        if proba is not None:
            # Onaylandı — confidence'ı proba ile harmanla.
            w = float(PRECISION_VETO_CONFIG["meta_confidence_blend_weight"])
            res.adjusted_confidence *= (1.0 - w) + w * proba

    return res


# ─── Veto loglama ────────────────────────────────────────────────────────────
async def log_veto(result: VetoResult, signal: dict) -> None:
    """signal_vetoes tablosuna yaz (hard veto, shadow veya penalty)."""
    if not (result.would_veto or result.total_penalty > 0):
        return
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return
        client = get_supabase_client()
        row = result.to_log_dict(signal)
        client.table("signal_vetoes").insert(row)
    except Exception as e:
        logger.warning("[precision-veto] signal_vetoes insert hatası: %s", e)
