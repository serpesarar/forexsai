"""
MT5 trader bot için TEK endpoint — tüm pipeline kararlarını birleştirir.

forexsai_demo_bot.py şu an PULSE 1/2/3 endpoint'lerinden sadece DIRECTION
alıyor; TP/SL config.py'dan sabit; lot config.LOT_SIZE sabit.

Bu endpoint Stage 4 percentile sizing + Entry Optimizer + Precision Veto
kararlarını birleştirip BOT'un kullanabileceği tek paket döndürür.

Sözleşme:
  POST /api/bot/trade-signal
  body: {symbol, direction, confidence, model_type?, timeframe?}
  resp: should_trade, lot_multiplier, entry/sl/tp, action, veto_reason, ...

Bot'un yapması gereken:
  1. PULSE 1/2/3'ten direction al (var olan voting mantığı)
  2. Bu endpoint'i çağır → optimized trade plan
  3. should_trade=false ise atla
  4. lot = config.LOT_SIZE * lot_multiplier
  5. mt5.order_send(entry=entry_price, sl=sl_price, tp=tp_price, vol=lot)

Cache: yok — her sinyalde fresh karar. Bot çağrı sıklığı düşük (PULSE
cycle'ına bağlı, dakikada birkaç çağrı), yük sorun yok.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bot", tags=["MT5 Bot"])


@router.post("/trade-signal")
async def trade_signal(body: dict):
    """Bot için tüm trade kararı paketi.

    Body:
      symbol      (str)  zorunlu — "XAUUSD", "NDX.INDX", vb.
      direction   (str)  zorunlu — "BUY" | "SELL"
      confidence  (float) ops    — voter consensus skoru (0-100)
      model_type  (str)  ops     — "pulse2" / "ensemble" / vb. (log için)
      timeframe   (str)  ops     — default "15m"

    Response anahtarları (executor'da hepsi okunabilir):
      should_trade        bool   false ise BOT EMİR AÇMASIN
      direction_out       str    "BUY"|"SELL"|"HOLD" (precision veto override edebilir)
      veto_reason         str?   bloklanma sebebi
      lot_multiplier      float  0.0=veto, 0.25/1.0/1.2/1.5 — config.LOT_SIZE ile çarp
      entry_price         float  market entry için referans (current price)
      sl_price            float  stop loss fiyatı
      tp_price            float  take profit fiyatı
      action              str    EXECUTE_NOW|LIMIT_ORDER|FALLBACK_MARKET|PASSTHROUGH
      max_wait_candles    int    LIMIT için bekleme (timeframe başına mum)
      structure_type      str?   bullish_order_block|bearish_fvg|none
      adjusted_confidence float  precision_veto sonrası
      priority_score      int    0-100 (yüksek = güçlü sinyal)
      enforce_mode        bool   ENTRY_OPTIMIZER_MODE=enforce mi (bot bu bilgiyi
                                  kendi A/B karşılaştırması için kullanabilir)
      original            dict   bot'un gönderdiği orijinal istek (echo)
    """
    if not isinstance(body, dict):
        raise HTTPException(400, "JSON body gerekli")
    symbol = body.get("symbol") or ""
    direction = (body.get("direction") or "").upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(400, "direction BUY veya SELL olmalı")
    if not symbol:
        raise HTTPException(400, "symbol zorunlu")

    confidence = float(body.get("confidence") or 70.0)
    model_type = body.get("model_type") or "bot"
    timeframe = body.get("timeframe") or "15m"

    # Canlı fiyat
    try:
        from services.data_fetcher import fetch_latest_price
        price = await fetch_latest_price(symbol)
    except Exception as e:
        raise HTTPException(503, f"fiyat alınamadı: {e}")
    if not price or price <= 0:
        raise HTTPException(503, f"{symbol} canlı fiyat yok")

    signal = {
        "symbol": symbol, "direction": direction,
        "confidence": confidence, "model_type": model_type,
        "timeframe": timeframe, "price": float(price),
    }

    # ── 1) Precision Veto + Stage 4 sizing ──────────────────────────────────
    veto_reason = None
    direction_out = direction
    lot_multiplier = 1.0
    adjusted_confidence = confidence
    sizing_action = ""
    stage4_predicted_r = None
    try:
        from services.precision_veto_service import check_signal
        vr = await check_signal(signal)
        if vr.vetoed or vr.would_veto:
            veto_reason = vr.reason
        if vr.converted_to_hold or vr.vetoed:
            direction_out = "HOLD"
        if vr.position_size_multiplier is not None:
            lot_multiplier = float(vr.position_size_multiplier)
        if vr.adjusted_confidence:
            adjusted_confidence = float(vr.adjusted_confidence)
        sizing_action = vr.sizing_action or ""
        stage4_predicted_r = (vr.features or {}).get("meta_predicted_r")
    except Exception as e:
        logger.warning("[bot] precision_veto hata: %s", e)

    # ── 2) Entry Optimizer ──────────────────────────────────────────────────
    entry_price = float(price)
    sl_price = float(price)
    tp_price = float(price)
    action = "FALLBACK_MARKET"
    max_wait = 0
    structure_type = "none"
    priority_score = 0
    optimizer_details: dict = {}
    try:
        from services.entry_optimizer import optimize_entry
        decision = await optimize_entry(dict(signal))
        action = decision.get("action") or "FALLBACK_MARKET"
        entry_price = float(decision.get("entry_price") or price)
        sl_price = float(decision.get("sl_price") or price)
        tp_price = float(decision.get("tp_price") or price)
        max_wait = int(decision.get("max_wait_candles") or 0)
        structure_type = decision.get("structure_type") or "none"
        priority_score = int(decision.get("priority_score") or 0)
        optimizer_details = decision.get("details") or {}
    except Exception as e:
        logger.warning("[bot] entry_optimizer hata: %s", e)

    # ── 3) Mode (shadow / enforce) — bot'un karar mantığına yardım için ────
    import os as _os
    mode = (_os.getenv("ENTRY_OPTIMIZER_MODE") or "off").lower()
    enforce = (mode == "enforce")

    # should_trade — net karar
    # - precision_veto vetolanmışsa HAYIR
    # - Stage 4 sizing 0 (hard veto) HAYIR
    # - direction HOLD'a düşmüşse HAYIR
    should_trade = (
        not veto_reason
        and lot_multiplier > 0
        and direction_out in ("BUY", "SELL")
    )

    # Shadow mode'da bot LOT'u değiştirmesin önerisi — sadece raporla
    # (enforce'a geçince bot çarpanı uygular)
    effective_lot_mult = (lot_multiplier if enforce else 1.0)

    return {
        "should_trade": should_trade,
        "direction_out": direction_out,
        "veto_reason": veto_reason,
        "lot_multiplier": round(lot_multiplier, 3),
        "effective_lot_multiplier": round(effective_lot_mult, 3),
        "entry_price": round(entry_price, 5),
        "sl_price": round(sl_price, 5),
        "tp_price": round(tp_price, 5),
        "action": action,
        "max_wait_candles": max_wait,
        "structure_type": structure_type,
        "priority_score": priority_score,
        "adjusted_confidence": round(adjusted_confidence, 2),
        "sizing_action": sizing_action,
        "stage4_predicted_r": stage4_predicted_r,
        "enforce_mode": enforce,
        "optimizer_mode": mode,
        "current_market_price": round(float(price), 5),
        "original": {
            "symbol": symbol, "direction": direction,
            "confidence": confidence, "model_type": model_type,
        },
        "notes": {
            "shadow_safe": (not enforce),
            "shadow_safe_note": (
                "Mode shadow — lot_multiplier ve optimizer entry/sl/tp "
                "SADECE raporlanıyor; bot'un mevcut hesabını uygula ve "
                "sonuçları karşılaştır. Enforce'a geçince effective_lot_"
                "multiplier ile çarp + entry/sl/tp kullan."
                if not enforce
                else "Mode enforce — bot effective_lot_multiplier ile çarpsın "
                "ve entry/sl/tp'yi uygulasın."),
            "optimizer_details": optimizer_details,
        },
    }


@router.get("/trade-signal/preview")
async def trade_signal_preview(symbol: str, direction: str,
                                  confidence: float = 70.0,
                                  model_type: str = "preview"):
    """GET versiyonu — manuel test için. Aynı output."""
    return await trade_signal({
        "symbol": symbol, "direction": direction.upper(),
        "confidence": confidence, "model_type": model_type,
    })


@router.get("/status")
async def bot_status():
    """Bot endpoint sağlık + mevcut konfigürasyon."""
    import os as _os
    return {
        "endpoint": "/api/bot/trade-signal",
        "method": "POST",
        "optimizer_mode": (_os.getenv("ENTRY_OPTIMIZER_MODE") or "off"),
        "excluded_symbols": list(__import__(
            "services.entry_optimizer", fromlist=["EXCLUDED_SYMBOLS"]
        ).EXCLUDED_SYMBOLS),
        "rr_per_symbol": __import__(
            "services.entry_optimizer", fromlist=["_RR_BY_SYMBOL"]
        )._RR_BY_SYMBOL,
        "note": (
            "Bot tek endpoint çağırsın, response'da her şey var. "
            "Mode shadow'da sadece veri toplanır; enforce'a geçince "
            "lot_multiplier + optimized entry/sl/tp uygulanır."),
    }
