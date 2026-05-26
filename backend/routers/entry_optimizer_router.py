"""
Entry Optimizer — test ve dış-API endpoint'leri.

Endpoint:
  POST /api/entry-optimizer/optimize  → tam karar (signal payload ile)
  GET  /api/entry-optimizer/test       → canlı fiyatla hızlı test

Trade bot bunu çağırmak için POST /optimize'ı kullanır:
  body: {symbol, direction, price?, tp?, sl?, atr?}
  response: {action, entry_price, sl_price, tp_price, structure_type, ...}
"""
from __future__ import annotations

import logging
from typing import Optional

from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/entry-optimizer", tags=["Entry Optimizer"])


@router.post("/optimize")
async def optimize(body: dict):
    """Trade pipeline'da Stage 4 sonrası çağrılır. Beklenen body:
      {symbol, direction (BUY|SELL), price, tp (opsiyonel), sl (opsiyonel),
       atr (opsiyonel)}

    Döndürdüğü JSON sözleşmesi entry_optimizer.optimize_entry'de
    belgelenmiştir — action ∈ {EXECUTE_NOW, LIMIT_ORDER, REJECT}."""
    if not isinstance(body, dict):
        raise HTTPException(400, "body must be JSON object")
    direction = (body.get("direction") or "").upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(400, "direction must be BUY or SELL")
    if not body.get("symbol"):
        raise HTTPException(400, "symbol required")
    body["direction"] = direction
    try:
        from services.entry_optimizer import optimize_entry
        return await optimize_entry(body)
    except Exception as e:
        logger.exception("[entry-optimizer] optimize hata")
        raise HTTPException(500, f"optimize: {e}")


@router.get("/test")
async def test_endpoint(
    symbol: str = Query("XAUUSD"),
    direction: str = Query("BUY"),
    timeframe: str = Query("15m"),
    price: Optional[float] = Query(None, description=
        "Test fiyatı — boşsa canlı fiyat çekilir"),
):
    """Self-test — canlı fiyatla optimize_entry çalıştırır, sonucu döndürür.
    Trade pipeline'a dokunmaz; sadece kararı gösterir."""
    direction = direction.upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(400, "direction must be BUY or SELL")

    use_price = price
    if use_price is None:
        try:
            from services.data_fetcher import fetch_latest_price
            use_price = await fetch_latest_price(symbol)
        except Exception as e:
            raise HTTPException(503, f"canlı fiyat alınamadı: {e}")
        if not use_price:
            raise HTTPException(503, f"{symbol} fiyat yok")

    signal = {"symbol": symbol, "direction": direction,
              "price": float(use_price), "timeframe": timeframe}
    try:
        from services.entry_optimizer import optimize_entry, DEFAULT_CONFIG
        cfg = {**DEFAULT_CONFIG, "timeframe": timeframe}
        decision = await optimize_entry(signal, config=cfg)
        return {"input": signal, "decision": decision,
                "config_summary": {
                    "ob_min_score": cfg["ob_min_score"],
                    "ob_max_age_candles": cfg["ob_max_age_candles"],
                    "inside_tolerance_atr": cfg["inside_tolerance_atr"],
                    "limit_max_pullback_atr": cfg["limit_max_pullback_atr"],
                    "default_rr": cfg["default_rr"],
                }}
    except Exception as e:
        logger.exception("[entry-optimizer] test hata")
        raise HTTPException(500, f"test: {e}")


# ─── 90 günlük replay backtest ────────────────────────────────────────────────
_BACKTEST_STATUS: dict = {"running": False, "started_at": None,
                           "finished_at": None, "result": None, "error": None}


@router.post("/backtest")
async def backtest(bg: BackgroundTasks,
                    days: int = Query(90, ge=14, le=180),
                    sample_per_scope: int = Query(300, ge=0, le=5000)):
    """Entry Optimizer'ı son N günün resolved sinyalleri üzerinde point-in-time
    simüle eder. Her sinyal için:
      - signal_created_at anına kadar 15m candle slice → MarketStructureAnalyzer
      - Entry Optimizer kararı (EXECUTE_NOW/LIMIT_ORDER/REJECT)
      - 1m walk-forward outcome simülasyonu

    Karşılaştırma: original (mevcut TP/SL config) vs entry_optimizer (kendi SL/TP'si).
    REJECT'lerin gerçek WR'i + LIMIT fill rate + toplam P&L delta.

    ~10-15 dk. Status endpoint ile takip et."""
    if _BACKTEST_STATUS["running"]:
        return {"status": "already_running",
                "started_at": _BACKTEST_STATUS["started_at"]}
    _BACKTEST_STATUS.update({"running": True,
                              "started_at": datetime.now(timezone.utc).isoformat(),
                              "finished_at": None, "result": None, "error": None})

    async def _do():
        try:
            from services.entry_optimizer_backtest import backtest_entry_optimizer
            res = await backtest_entry_optimizer(days=days,
                                                  sample_per_scope=sample_per_scope)
            _BACKTEST_STATUS["result"] = res
        except Exception as e:
            logger.exception("[entry-bt] hata: %s", e)
            _BACKTEST_STATUS["error"] = str(e)[:500]
        finally:
            _BACKTEST_STATUS["running"] = False
            _BACKTEST_STATUS["finished_at"] = datetime.now(timezone.utc).isoformat()

    bg.add_task(_do)
    return {"status": "scheduled", "days": days,
            "sample_per_scope": sample_per_scope,
            "poll": "/api/entry-optimizer/backtest/status",
            "estimated_minutes": "10-15"}


@router.get("/backtest/status")
async def backtest_status():
    return {**_BACKTEST_STATUS}


@router.get("/config")
async def show_config():
    """Mevcut default config — eşikleri görmek için."""
    from services.entry_optimizer import DEFAULT_CONFIG
    return {"config": DEFAULT_CONFIG,
            "note": "ATR-relative thresholds — sembol bağımsız"}
