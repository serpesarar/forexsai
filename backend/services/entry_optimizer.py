"""
Entry Optimizer — Pipeline ortasında "fiyat hassasiyet" filtresi.

Pipeline:  EMEL signal → Stage 4 sizing → ENTRY OPTIMIZER → Trade Bot

Sorun: Sinyal geldiğinde fiyat çoktan uçmuş olabiliyor. EMEL "BUY" dediğinde
fiyat zaten 20 pip yukarıda → bot market'tan girer → düzeltme SL'yi vurur.
Yön doğru, giriş kötü → kaybedersin.

Çözüm: Sinyal gelince mevcut Order Block ve FVG dağılımını incele:
  - Fiyat sinyal yönüne uygun GEÇERLİ bir OB/FVG bölgesinde mi?
    → EXECUTE_NOW (market order, normal sizing)
  - Fiyat uçmuş ama yakınlarda geçerli bir OB/FVG var mı?
    → LIMIT_ORDER (o bölgeye, max_wait_candles ile zaman aşımı)
  - Hiç geçerli yapı yok ya da çok uzak mı?
    → REJECT (FOMO sinyali, geç)

Çıktı (sözleşme):
  {
    "action": "EXECUTE_NOW" | "LIMIT_ORDER" | "REJECT",
    "entry_price": float,
    "sl_price": float,
    "tp_price": float,
    "structure_type": "bullish_order_block" | "bearish_order_block" |
                       "bullish_fvg" | "bearish_fvg" | "none",
    "invalidation_reason": str | None,
    "max_wait_candles": int,
    "priority_score": int (0-100),
  }

Bu modül STATELESS. Trade bot kararı kendisi uygular; entegrasyon yeri:
trade executor'da Stage 4 sizing'den SONRA, market order'dan ÖNCE.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Konfigürasyon — env ile override edilebilir ─────────────────────────────
# Tüm mesafe eşikleri ATR cinsinden — sembol bağımsız.
# 2026-05-26: REJECT kaldırıldı (backtest 1834 pip "kaçırılan kazanç"
# göstermişti). Yerine FALLBACK_MARKET: sembolün varsayılan TP/SL config'i
# + market entry. LIMIT timeout'unda da aynı fallback uygulanır.
DEFAULT_CONFIG = {
    "timeframe": "15m",
    "candle_limit": 100,
    # OB filtresi
    "ob_min_score": 50,
    "ob_max_age_candles": 30,    # OB son 30 mum içinde oluşmuşsa "fresh"
    "fvg_max_age_candles": 20,
    # "İçinde mi?" — fiyatın OB/FVG bölgesinde sayılması için tolerans
    "inside_tolerance_atr": 0.10,
    # "Uçmuş mu?" — fiyat OB üstünde/altında bu kadarsa "fled"
    "fled_threshold_atr": 0.30,
    # LIMIT için maksimum geri-çekilme — bunu aşan zone yoksa LIMIT atılmaz
    # → FALLBACK_MARKET (market entry, default config TP/SL)
    "limit_max_pullback_atr": 2.0,
    # LIMIT order için bekleme süresi — TF'e göre default
    "max_wait_candles_default": 5,
    # SL: zone dışına ne kadar uzak (sadece structure-based entry için)
    "sl_buffer_atr": 0.30,
    # R:R hedefi — sembol bazlı override _RR_BY_SYMBOL'da, yoksa bu kullanılır
    "default_rr": 2.0,
}

# Sembol bazlı R:R — backtest 2026-05-26 kalibrasyonu:
# Yüksek volatilite + momentum (NDX/USOIL) → 2.0
# Daha sıkı, oscillating (XAUUSD/GDAXI) → 1.8 (geniş TP'ye ulaşma şansı az)
_RR_BY_SYMBOL = {
    "XAUUSD": 1.8,
    "GDAXI.INDX": 1.8,
    "NDX.INDX": 2.0,
    "USOIL.FOREX": 2.0,
}


def _get_rr(symbol: str, default_rr: float) -> float:
    return _RR_BY_SYMBOL.get(symbol, default_rr)


# 2026-05-26 Validation suite bulguları:
# - NDX walk-forward F1 (0-30d): −155% delta (optimizer ZARAR ETTİRDİ)
# - NDX per-symbol full 90d: −26.4% delta
# - Diğer 3 sembol +246% ile +933% arası net pozitif
# → NDX yapısal optimizasyondan dışlandı. PASSTHROUGH action ile eski sistem
# davranışı korunur (default TP/SL + market entry). Stage 4 sizing ORTHOGONAL
# olarak aynen uygulanır. Env override: ENTRY_OPT_EXCLUDE_SYMBOLS=sym1,sym2.
import os as _os
EXCLUDED_SYMBOLS = {
    s.strip().upper() for s in
    (_os.getenv("ENTRY_OPT_EXCLUDE_SYMBOLS") or "NDX.INDX").split(",")
    if s.strip()
}


@dataclass
class EntryDecision:
    action: str
    entry_price: float
    sl_price: float
    tp_price: float
    structure_type: str
    invalidation_reason: Optional[str]
    max_wait_candles: int
    priority_score: int
    # Açıklayıcı detaylar (test/log için, executor okumayabilir)
    details: dict

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "entry_price": round(float(self.entry_price), 5),
            "sl_price": round(float(self.sl_price), 5),
            "tp_price": round(float(self.tp_price), 5),
            "structure_type": self.structure_type,
            "invalidation_reason": self.invalidation_reason,
            "max_wait_candles": int(self.max_wait_candles),
            "priority_score": int(self.priority_score),
            "details": self.details,
        }


# ─── Yardımcılar ─────────────────────────────────────────────────────────────
def _opposite_direction(direction: str) -> str:
    return "SELL" if direction == "BUY" else "BUY"


def _direction_to_structure_side(direction: str) -> str:
    """BUY → bullish (long), SELL → bearish (short)."""
    return "bullish" if direction == "BUY" else "bearish"


def _is_inside_zone(price: float, zone_low: float, zone_high: float,
                     tolerance: float) -> bool:
    return (zone_low - tolerance) <= price <= (zone_high + tolerance)


def _zone_distance_signed(price: float, zone_low: float, zone_high: float,
                           direction: str) -> float:
    """BUY için: fiyat zone üstündeyse pozitif (uçmuş), zone altındaysa negatif
    (zone'a düşmek lazım — geri çekilme). SELL için tersi.

    Inside ise 0 döner."""
    if zone_low <= price <= zone_high:
        return 0.0
    if direction == "BUY":
        if price > zone_high:
            return price - zone_high     # +: uçmuş
        return price - zone_low          # − : zone altında (yukarı çekilme gerek)
    # SELL
    if price < zone_low:
        return zone_low - price          # +: uçmuş (aşağı)
    return zone_high - price             # −: zone üstünde


def _filter_valid_obs(obs: list[dict], direction: str, current_idx: int,
                       max_age: int, min_score: int) -> list[dict]:
    target = _direction_to_structure_side(direction)
    out = []
    for ob in obs or []:
        if ob.get("type") != target:
            continue
        if ob.get("mitigated"):
            continue
        if int(ob.get("score") or 0) < min_score:
            continue
        idx = int(ob.get("index") or -1)
        if current_idx > 0 and max_age > 0 and (current_idx - idx) > max_age:
            continue
        if not (ob.get("zone_low") and ob.get("zone_high")):
            continue
        out.append(ob)
    return out


def _filter_valid_fvgs(fvgs: list[dict], direction: str, current_idx: int,
                        max_age: int) -> list[dict]:
    target = _direction_to_structure_side(direction)
    out = []
    for f in fvgs or []:
        if f.get("direction") != target:
            continue
        if f.get("filled"):
            continue
        idx = int(f.get("index") or -1)
        if current_idx > 0 and max_age > 0 and (current_idx - idx) > max_age:
            continue
        if f.get("high") is None or f.get("low") is None:
            continue
        out.append(f)
    return out


def _structure_to_zone(s: dict, kind: str) -> tuple[float, float, str]:
    """OB veya FVG dict'inden (zone_low, zone_high, structure_type) çıkar."""
    if kind == "ob":
        return (float(s.get("zone_low") or 0),
                float(s.get("zone_high") or 0),
                "bullish_order_block" if s.get("type") == "bullish"
                else "bearish_order_block")
    # fvg
    return (float(s.get("low") or 0),
            float(s.get("high") or 0),
            "bullish_fvg" if s.get("direction") == "bullish" else "bearish_fvg")


def _priority_score(structure_score: int, freshness_ratio: float,
                     inside: bool, rr: float) -> int:
    """Karma skor — OB skoru + tazelik + giriş kalitesi + R:R.
    0-100. EXECUTE_NOW kararları yüksek, LIMIT_ORDER orta, REJECT skor None."""
    s = 0.4 * (structure_score or 0)
    s += 25 * max(0.0, min(1.0, freshness_ratio))
    s += 20 if inside else 8
    s += 15 * max(0.0, min(1.0, (rr - 1.0) / 2.0))  # rr 1→0, 3→1
    return int(round(max(0, min(100, s))))


def _candle_atr(candles: list[dict], period: int = 14) -> float:
    """Basit ATR (TR=max(H-L, |H-Cp|, |L-Cp|))."""
    n = len(candles)
    if n < period + 1:
        return 0.0
    trs = []
    for i in range(n - period, n):
        h = float(candles[i].get("high") or candles[i].get("h") or 0)
        l = float(candles[i].get("low") or candles[i].get("l") or 0)
        cp = float(candles[i - 1].get("close") or candles[i - 1].get("c") or 0)
        trs.append(max(h - l, abs(h - cp), abs(l - cp)))
    return sum(trs) / len(trs) if trs else 0.0


# ─── Ana karar fonksiyonu ────────────────────────────────────────────────────
async def optimize_entry(signal: dict,
                          config: Optional[dict] = None) -> dict:
    """Sinyali analiz et, EXECUTE_NOW / LIMIT_ORDER / REJECT döndür.

    signal: {symbol, direction (BUY|SELL), price (current/desired entry),
             tp (opsiyonel — yoksa hesaplanır), atr (opsiyonel)}
    config: DEFAULT_CONFIG override
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    symbol = signal.get("symbol")
    direction = (signal.get("direction") or "").upper()
    current_price = float(signal.get("price") or signal.get("entry_price") or 0)
    signal_tp = signal.get("tp") or signal.get("tp_price")
    signal_sl = signal.get("sl") or signal.get("sl_price")

    if direction not in ("BUY", "SELL") or current_price <= 0 or not symbol:
        return EntryDecision(
            action="REJECT", entry_price=current_price,
            sl_price=signal_sl or 0, tp_price=signal_tp or 0,
            structure_type="none",
            invalidation_reason="invalid_input",
            max_wait_candles=0, priority_score=0,
            details={"symbol": symbol, "direction": direction,
                      "current_price": current_price}).to_dict()

    # ── Order block + FVG yapısını al ────────────────────────────────────────
    try:
        from services.order_block_service import OrderBlockService
        from order_block_detector import OrderBlockConfig
    except Exception as e:
        logger.warning("[entry-optimizer] OB import: %s", e)
        return EntryDecision(
            action="EXECUTE_NOW", entry_price=current_price,
            sl_price=signal_sl or current_price, tp_price=signal_tp or current_price,
            structure_type="none",
            invalidation_reason="ob_service_unavailable",
            max_wait_candles=0, priority_score=30,
            details={"fallback": "passthrough",
                      "error": str(e)[:120]}).to_dict()

    try:
        svc = OrderBlockService()
        ob_payload = await svc.detect(symbol=symbol, timeframe=cfg["timeframe"],
                                       limit=cfg["candle_limit"],
                                       config=OrderBlockConfig(),
                                       use_cache=True, log_signals=False)
    except Exception as e:
        logger.warning("[entry-optimizer] detect hata %s: %s", symbol, e)
        return EntryDecision(
            action="EXECUTE_NOW", entry_price=current_price,
            sl_price=signal_sl or current_price, tp_price=signal_tp or current_price,
            structure_type="none",
            invalidation_reason="ob_detect_failed",
            max_wait_candles=0, priority_score=30,
            details={"error": str(e)[:120], "fallback": "passthrough"}).to_dict()

    return decide_from_payload(signal, ob_payload, cfg)


def decide_from_payload(signal: dict, ob_payload: dict,
                          cfg: Optional[dict] = None) -> dict:
    """Saf karar mantığı — ob_payload önceden hesaplanmış olarak verilir.
    Backtest, simülasyon ve canlı optimize_entry hep buraya iner."""
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}
    direction = (signal.get("direction") or "").upper()
    current_price = float(signal.get("price") or signal.get("entry_price") or 0)
    signal_tp = signal.get("tp") or signal.get("tp_price")
    signal_sl = signal.get("sl") or signal.get("sl_price")
    sym_upper = (signal.get("symbol") or "").upper()

    # ── EXCLUSION: NDX gibi yapısal optimizasyondan dışlanan semboller ───────
    # Hiç yapı incelemesi yapmadan default config ile market entry'ye yönlendir.
    # Backtest'te delta_pct ~0 olur (orig ile aynı davranış) — Stage 4 sizing
    # bağımsız uygulanır.
    if sym_upper in EXCLUDED_SYMBOLS:
        atr_default = float(signal.get("atr") or 0)
        if atr_default <= 0:
            atr_default = max(current_price * 0.001, 1e-6)
        return _fallback_market(direction, current_price, sym_upper,
                                  signal_sl, signal_tp, atr_default, cfg,
                                  reason="symbol_excluded_from_optimization",
                                  action_override="PASSTHROUGH",
                                  extra={"note":
                                          "Walk-forward F1 negative + "
                                          "per-symbol delta -26% — excluded"})

    # ── Veri çıkar ───────────────────────────────────────────────────────────
    obs = ob_payload.get("order_blocks") or []
    fvgs = ob_payload.get("fvg_list") or []
    # Current index — son mumun index'i (OB'lerin index'iyle aynı koordinat)
    current_idx = (ob_payload.get("structure", {}).get("counts", {}).get("ob")  # fallback
                    or 0)
    # En güvenilir: structure içinde candle sayısı ya da swing_points
    sp = ob_payload.get("swing_points") or []
    if sp:
        current_idx = max((int(s.get("index", 0)) for s in sp), default=0) + 5

    atr = float(signal.get("atr") or 0) or _structure_atr(ob_payload)
    if atr <= 0:
        # Son çare — current_price'ın %0.1'i (mantıksız ama bölme hatası önler)
        atr = max(current_price * 0.001, 1e-6)

    # ── Geçerli yapıları filtrele ────────────────────────────────────────────
    valid_obs = _filter_valid_obs(obs, direction, current_idx,
                                    cfg["ob_max_age_candles"], cfg["ob_min_score"])
    valid_fvgs = _filter_valid_fvgs(fvgs, direction, current_idx,
                                      cfg["fvg_max_age_candles"])

    # Her yapı için (zone_low, zone_high, type, score, raw)
    candidates: list[dict] = []
    for ob in valid_obs:
        zl, zh, stype = _structure_to_zone(ob, "ob")
        candidates.append({"zone_low": zl, "zone_high": zh, "type": stype,
                           "score": int(ob.get("score") or 0),
                           "index": int(ob.get("index") or 0),
                           "kind": "ob", "raw": ob})
    for fv in valid_fvgs:
        zl, zh, stype = _structure_to_zone(fv, "fvg")
        # FVG için "score" yok — size & freshness'ten türetelim
        size = float(fv.get("size") or 0)
        size_score = int(min(80, max(40, size / max(atr, 1e-9) * 30)))
        candidates.append({"zone_low": zl, "zone_high": zh, "type": stype,
                           "score": size_score,
                           "index": int(fv.get("index") or 0),
                           "kind": "fvg", "raw": fv})

    inside_tol = cfg["inside_tolerance_atr"] * atr

    # ── KARAR 1: Fiyat İÇERİDE mi? ───────────────────────────────────────────
    inside_cands = [c for c in candidates
                     if _is_inside_zone(current_price, c["zone_low"],
                                          c["zone_high"], inside_tol)]
    if inside_cands:
        # En yüksek skorlu zone — sembol kalitesini önceler
        best = max(inside_cands, key=lambda c: c["score"])
        sl, tp, rr = _compute_levels(direction, current_price, best,
                                      signal_sl, signal_tp, atr, cfg,
                                      symbol=signal.get("symbol") or "")
        fresh_ratio = _freshness(best["index"], current_idx,
                                  cfg["ob_max_age_candles"] if best["kind"] == "ob"
                                  else cfg["fvg_max_age_candles"])
        return EntryDecision(
            action="EXECUTE_NOW",
            entry_price=current_price,
            sl_price=sl, tp_price=tp,
            structure_type=best["type"],
            invalidation_reason=None,
            max_wait_candles=0,
            priority_score=_priority_score(best["score"], fresh_ratio, True, rr),
            details={
                "zone": {"low": best["zone_low"], "high": best["zone_high"]},
                "score": best["score"], "kind": best["kind"],
                "age_candles": current_idx - best["index"],
                "rr": round(rr, 2),
                "valid_ob_count": len(valid_obs),
                "valid_fvg_count": len(valid_fvgs),
                "current_idx": current_idx, "atr": round(atr, 5),
            }).to_dict()

    # ── KARAR 2: Fiyat UÇMUŞ, geri-çekilme için zone var mı? ─────────────────
    # Sinyal yönünde "geriye" düşen zone'lar (BUY için fiyat altında, SELL için üstünde)
    pullback_cands = []
    for c in candidates:
        d = _zone_distance_signed(current_price, c["zone_low"], c["zone_high"],
                                    direction)
        # d > 0 = fiyat zone'un ÖTE TARAFINDA (uçmuş) — bu zone'a pullback gerek
        if d > 0 and d <= cfg["limit_max_pullback_atr"] * atr:
            pullback_cands.append({**c, "distance": d})

    if pullback_cands:
        # En yakın + en yüksek skor karması — yakınlık ağırlığı daha yüksek
        best = min(pullback_cands,
                    key=lambda c: c["distance"] / atr - 0.01 * c["score"])
        # Limit girişi zone'un ortasına (BUY için zone_high — alıcının ulaşabileceği üst)
        if direction == "BUY":
            entry = best["zone_high"]   # pullback'in geleceği üst sınır
        else:
            entry = best["zone_low"]
        sl, tp, rr = _compute_levels(direction, entry, best,
                                      None, signal_tp, atr, cfg,
                                      symbol=signal.get("symbol") or "")
        fresh = _freshness(best["index"], current_idx,
                            cfg["ob_max_age_candles"] if best["kind"] == "ob"
                            else cfg["fvg_max_age_candles"])
        # Bekleme süresi — daha uzak = daha fazla bekleme
        wait = max(3, min(15, int(math.ceil(
            best["distance"] / max(atr, 1e-9) * 3 +
            cfg["max_wait_candles_default"]))))
        return EntryDecision(
            action="LIMIT_ORDER",
            entry_price=entry, sl_price=sl, tp_price=tp,
            structure_type=best["type"],
            invalidation_reason=None,
            max_wait_candles=wait,
            priority_score=_priority_score(best["score"], fresh, False, rr),
            details={
                "zone": {"low": best["zone_low"], "high": best["zone_high"]},
                "distance_atr": round(best["distance"] / atr, 2),
                "score": best["score"], "kind": best["kind"],
                "age_candles": current_idx - best["index"],
                "rr": round(rr, 2), "atr": round(atr, 5),
                "valid_ob_count": len(valid_obs),
                "valid_fvg_count": len(valid_fvgs),
                "current_idx": current_idx,
            }).to_dict()

    # ── KARAR 3: Yapısal entry mümkün değil → FALLBACK_MARKET ────────────────
    # REJECT yerine: sembolün varsayılan TP/SL config'i + market entry.
    # 2026-05-26 backtest: REJECT 601 sinyal × WR %74.9 = ortalama signal'le
    # aynı kalitede idi → seçici eleyici değildi. Fallback bu kazançları korur.
    reason = "no_valid_structure"
    extra: dict = {}
    if candidates:
        nearest = min(candidates,
                       key=lambda c: abs(_zone_distance_signed(
                           current_price, c["zone_low"], c["zone_high"], direction)))
        d = abs(_zone_distance_signed(current_price, nearest["zone_low"],
                                        nearest["zone_high"], direction))
        extra["nearest_zone_dist_atr"] = round(d / atr, 2)
        extra["nearest_zone_type"] = nearest["type"]
        reason = ("zones_on_wrong_side_for_signal" if d <= 0.10 * atr
                   else "price_too_far_or_misaligned")
    elif not (valid_obs or valid_fvgs):
        reason = "no_valid_obs_or_fvgs_in_lookback"
    return _fallback_market(direction, current_price, signal.get("symbol") or "",
                              signal_sl, signal_tp, atr, cfg, reason,
                              extra={**extra,
                                       "valid_ob_count": len(valid_obs),
                                       "valid_fvg_count": len(valid_fvgs),
                                       "candidate_count": len(candidates),
                                       "current_idx": current_idx})


def _fallback_market(direction: str, current_price: float, symbol: str,
                      signal_sl, signal_tp, atr: float, cfg: dict,
                      reason: str, extra: Optional[dict] = None,
                      action_override: Optional[str] = None) -> dict:
    """FALLBACK_MARKET: sembolün varsayılan TP/SL config'iyle market entry.

    Stage 4 sizing dışarıda uygulanır (executor); bu fonksiyon sadece
    entry/sl/tp belirler. Yapı bulunamadığında veya limit timeout sonrası
    çağrılır."""
    sl_price = None
    tp_price = None
    try:
        from services.target_config import (
            calculate_target_prices, calculate_stoploss_price)
        targets = calculate_target_prices(current_price, direction, symbol, "15m")
        # Default config'te TP2 daha geniş hedef → R:R uyumlu (TP1 sığ)
        tp_price = (targets.get("TP2") or targets.get("TP1")
                     or targets.get("TP3"))
        sl_price = calculate_stoploss_price(current_price, direction, symbol, "15m")
    except Exception as e:
        logger.debug("[entry-opt] target_config fallback: %s", e)
        # Ultra-safe: ATR tabanlı 1×SL, 2×TP (default R:R)
        off = atr * 1.0
        if direction == "BUY":
            sl_price = current_price - off
            tp_price = current_price + off * cfg["default_rr"]
        else:
            sl_price = current_price + off
            tp_price = current_price - off * cfg["default_rr"]
    # Signal override — eğer caller signal_sl/tp koymuşsa onları kullan
    if signal_sl: sl_price = float(signal_sl)
    if signal_tp: tp_price = float(signal_tp)
    return EntryDecision(
        action=action_override or "FALLBACK_MARKET",
        entry_price=current_price,
        sl_price=sl_price or current_price,
        tp_price=tp_price or current_price,
        structure_type="none",
        invalidation_reason=reason,
        max_wait_candles=0,
        priority_score=35,
        details={"fallback_reason": reason,
                  "tp_source": "symbol_default",
                  "atr": round(atr, 5),
                  **(extra or {})}).to_dict()


def _structure_atr(ob_payload: dict) -> float:
    """OB payload'undan ATR çıkar — combined_signal veya support_resistance
    içinde olabilir; yoksa 0 döndür."""
    cs = ob_payload.get("combined_signal") or {}
    for key in ("atr", "atr_14"):
        v = cs.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    # support_resistance içindeki swing range'in 14'te biri çoğu zaman ATR'ye yakın
    sr = ob_payload.get("support_resistance") or {}
    rh = sr.get("range_high")
    rl = sr.get("range_low")
    if rh and rl:
        return max(0.0, float(rh) - float(rl)) / 20.0
    return 0.0


def _freshness(idx: int, current_idx: int, max_age: int) -> float:
    if max_age <= 0 or current_idx <= 0:
        return 0.5
    age = max(0, current_idx - idx)
    return max(0.0, 1.0 - age / float(max_age))


def _compute_levels(direction: str, entry: float, best_zone: dict,
                     signal_sl: Optional[float], signal_tp: Optional[float],
                     atr: float, cfg: dict,
                     symbol: str = "") -> tuple[float, float, float]:
    """SL ve TP belirle. SL = zone dışına buffer kadar; TP = signal varsa o,
    yoksa R:R = sembol bazlı (XAUUSD/GDAXI 1.8, NDX/USOIL 2.0). R döndürür."""
    buf = cfg["sl_buffer_atr"] * atr
    rr_target = _get_rr(symbol, cfg["default_rr"])
    if direction == "BUY":
        sl = best_zone["zone_low"] - buf
        risk = max(1e-9, entry - sl)
        tp = float(signal_tp) if signal_tp else entry + risk * rr_target
        rr = (tp - entry) / risk if risk > 0 else 0.0
    else:
        sl = best_zone["zone_high"] + buf
        risk = max(1e-9, sl - entry)
        tp = float(signal_tp) if signal_tp else entry - risk * rr_target
        rr = (entry - tp) / risk if risk > 0 else 0.0
    return sl, tp, rr
