"""
Entry Optimizer regime/outcome logger.

Her sinyalde Supabase'e yazar:
  - Sinyal bağlamı (symbol, direction, price, confidence)
  - Optimizer kararı (action, entry/sl/tp, structure, priority)
  - Market context (ATR, regime, volatilite oranı)
  - Stage 4 sizing (ortogonal)

Trade kapandığında outcome_backfill ile:
  - optimizer_outcome (kazandı/kaybetti)
  - market_outcome (eski sistem ne yapardı — A/B)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def _compute_atr(candles: list[dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    trs = []
    for i in range(len(candles) - period, len(candles)):
        h = float(candles[i].get("high") or 0)
        l = float(candles[i].get("low") or 0)
        cp = float(candles[i - 1].get("close") or 0)
        trs.append(max(h - l, abs(h - cp), abs(l - cp)))
    return sum(trs) / len(trs) if trs else 0.0


async def log_signal(signal: dict, decision: dict,
                       candles_15m: Optional[list[dict]] = None,
                       stage4_info: Optional[dict] = None,
                       prediction_id: Optional[str] = None,
                       enforce_mode: bool = False) -> Optional[str]:
    """Sinyal + optimizer kararını entry_optimizer_logs'a yaz.

    Hata atmaz — exception'da uyarı loglar, None döner. Production flow'u
    bloklamaz.

    Returns: log row ID (varsa)
    """
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return None
        client = get_supabase_client()

        # ATR + regime hesabı (15m candles verildiyse)
        atr_14 = atr_50 = None
        atr_ratio = None
        if candles_15m and len(candles_15m) >= 50:
            atr_14 = _compute_atr(candles_15m, 14)
            atr_50 = _compute_atr(candles_15m, 50)
            if atr_50 > 1e-9:
                atr_ratio = round(atr_14 / atr_50, 3)

        # Regime — opsiyonel, day_structure_service'ten okumayı dene
        regime = None
        regime_eff = None
        try:
            from services.day_structure_service import compute_day_structure
            ds = await compute_day_structure(signal.get("symbol"), "15m")
            if ds:
                regime = ds.regime
                regime_eff = round(ds.regime_efficiency, 3)
        except Exception as e:
            logger.debug("[regime-log] day_structure fail: %s", e)

        details = decision.get("details") or {}
        row = {
            "prediction_id": prediction_id,
            "signal_model": signal.get("model_type") or signal.get("model"),
            "symbol": signal.get("symbol"),
            "signal_direction": (signal.get("direction") or "").upper(),
            "current_price": float(signal.get("price")
                                      or signal.get("entry_price") or 0),
            "signal_confidence": (float(signal["confidence"])
                                    if signal.get("confidence") is not None
                                    else None),
            # Optimizer
            "optimizer_action": decision.get("action"),
            "optimizer_entry": float(decision.get("entry_price") or 0),
            "optimizer_sl": float(decision.get("sl_price") or 0),
            "optimizer_tp": float(decision.get("tp_price") or 0),
            "optimizer_priority": int(decision.get("priority_score") or 0),
            "max_wait_candles": int(decision.get("max_wait_candles") or 0),
            "structure_type": decision.get("structure_type"),
            "invalidation_reason": decision.get("invalidation_reason"),
            # Stage 4
            "stage4_sizing_mult": (float(stage4_info["sizing_mult"])
                                     if stage4_info and "sizing_mult" in stage4_info
                                     else None),
            "stage4_predicted_r": (float(stage4_info["predicted_r"])
                                     if stage4_info and "predicted_r" in stage4_info
                                     else None),
            # Market context
            "atr_14": round(atr_14, 5) if atr_14 else None,
            "atr_50": round(atr_50, 5) if atr_50 else None,
            "atr_ratio": atr_ratio,
            "regime": regime,
            "regime_efficiency": regime_eff,
            # Mode
            "enforce_mode": enforce_mode,
            "notes": {"details": details} if details else None,
        }
        # None değerli alanları temizleme — Supabase nullable kabul ediyor
        # NOT: özel REST istemcisinde insert() ANINDA çalışır ve dict döner.
        # Eski hasattr'lı ternary, denetim amaçlı insert'i de gerçekten çalıştırıp
        # HER KAYDI ÇİFT yazıyordu — tek çağrıya indirildi (2026-07-16).
        res = client.table("entry_optimizer_logs").insert(row)
        data = (res.data if hasattr(res, "data")
                  else (res.get("data") if isinstance(res, dict) else None)) or []
        if data and isinstance(data, list) and data[0].get("id"):
            return str(data[0]["id"])
        return None
    except Exception as e:
        logger.warning("[regime-log] log_signal hata: %s", e)
        return None


async def backfill_outcome(prediction_id: str) -> dict:
    """Trade kapandığında çağrılır. prediction_logs + signal_replay'den
    outcome'ları çekip entry_optimizer_logs'a yazar.

    A/B karşılaştırma için:
      optimizer_outcome   = kendi SL/TP'siyle ne oldu (replay simülasyonu)
      market_outcome      = mevcut SL/TP'yle ne oldu (prediction_logs status)
    """
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return {"status": "db_unavailable"}
        client = get_supabase_client()

        # 1) Log row'unu bul
        q = (client.table("entry_optimizer_logs")
              .select("id,optimizer_action,optimizer_entry,optimizer_sl,"
                      "optimizer_tp,symbol,signal_direction")
              .eq("prediction_id", prediction_id).limit(1))
        res = q.execute() if hasattr(q, "execute") else q
        rows = (res.data if hasattr(res, "data")
                  else (res.get("data") if isinstance(res, dict) else [])) or []
        if not rows:
            return {"status": "no_log_row"}
        log_row = rows[0]

        # 2) prediction_logs'tan market outcome
        q2 = (client.table("prediction_logs")
               .select("status,exit_price,exit_time")
               .eq("id", prediction_id).limit(1))
        res2 = q2.execute() if hasattr(q2, "execute") else q2
        pls = (res2.data if hasattr(res2, "data")
                 else (res2.get("data") if isinstance(res2, dict) else [])) or []
        if not pls:
            return {"status": "no_prediction"}
        pred = pls[0]
        if pred.get("status") not in ("completed", "stopped", "expired"):
            return {"status": "not_resolved_yet"}

        market_outcome = pred.get("status")
        market_exit = float(pred.get("exit_price") or 0)
        market_realized = _pips_signed(
            log_row["symbol"], log_row["signal_direction"],
            float(log_row["optimizer_entry"]), market_exit)

        # 3) Optimizer outcome — kendi SL/TP'siyle ne olurdu?
        # Bunu hesaplamak için signal_created_at sonrasındaki 1m bars walk gerek.
        # Daha hafif: signal_replay_1m'den prediction_id ile çek
        q3 = (client.table("prediction_replay_corrections")
               .select("corrected_status,corrected_exit_price,signal_created_at")
               .eq("prediction_id", prediction_id).limit(1))
        res3 = q3.execute() if hasattr(q3, "execute") else q3
        rcs = (res3.data if hasattr(res3, "data")
                 else (res3.get("data") if isinstance(res3, dict) else [])) or []
        opt_outcome = opt_exit = opt_realized = None
        if rcs:
            rc = rcs[0]
            # Burada gerçek walk-forward simülasyonu için ayrı bir fonksiyon
            # gerekirdi; şimdilik market outcome'u optimizer outcome'a kopya
            # (enforce sonrası bu farklılaşacak). Şimdilik basit:
            # Eğer optimizer entry/sl/tp ≈ market'ınkilerle aynıysa outcome aynı,
            # farklıysa not_implemented
            if (abs(float(log_row["optimizer_entry"])
                      - float(rc["corrected_exit_price"] or 0)) < 1e-6):
                opt_outcome = rc["corrected_status"]
                opt_exit = float(rc["corrected_exit_price"])
                opt_realized = market_realized
            else:
                # Tam simülasyon — TODO: 1m bar walk
                opt_outcome = "pending"

        # 4) Update
        update_data = {
            "market_outcome": market_outcome,
            "market_exit_price": round(market_exit, 5),
            "market_realized_pips": round(market_realized, 3),
            "optimizer_outcome": opt_outcome,
            "optimizer_exit_price": (round(opt_exit, 5) if opt_exit else None),
            "optimizer_realized_pips": (round(opt_realized, 3)
                                          if opt_realized is not None else None),
            "optimizer_resolved_at": datetime.now(timezone.utc).isoformat(),
        }
        u = (client.table("entry_optimizer_logs")
              .update(update_data).eq("id", log_row["id"]))
        u.execute() if hasattr(u, "execute") else None
        return {"status": "ok", "log_id": log_row["id"],
                "market_outcome": market_outcome,
                "optimizer_outcome": opt_outcome}
    except Exception as e:
        logger.warning("[regime-log] backfill hata: %s", e)
        return {"status": "error", "error": str(e)[:200]}


def _pips_signed(symbol: str, direction: str, entry: float, exit_p: float
                   ) -> float:
    if entry <= 0 or exit_p <= 0:
        return 0.0
    diff = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
    try:
        from services.target_config import pips_from_price_change
        mag = abs(pips_from_price_change(abs(diff), symbol))
        return mag if diff >= 0 else -mag
    except Exception:
        return diff


async def shadow_stats(days: int = 7) -> dict:
    """Shadow mode'daki son N gün özeti — A/B karşılaştırma için."""
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return {"status": "db_unavailable"}
        client = get_supabase_client()
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        q = (client.table("entry_optimizer_logs")
              .select("optimizer_action,optimizer_outcome,market_outcome,"
                      "optimizer_realized_pips,market_realized_pips,"
                      "symbol,atr_ratio,regime")
              .gte("created_at", since)
              .limit(20000))
        res = q.execute() if hasattr(q, "execute") else q
        rows = (res.data if hasattr(res, "data")
                  else (res.get("data") if isinstance(res, dict) else [])) or []
        # Aggregate
        by_action: dict = {}
        by_symbol: dict = {}
        high_vol_count = 0
        total_resolved = 0
        for r in rows:
            act = r.get("optimizer_action") or "UNKNOWN"
            sym = r.get("symbol") or "UNKNOWN"
            by_action[act] = by_action.get(act, 0) + 1
            by_symbol[sym] = by_symbol.get(sym, 0) + 1
            if (r.get("atr_ratio") or 0) > 1.3:
                high_vol_count += 1
            if r.get("optimizer_outcome") in ("completed", "stopped"):
                total_resolved += 1
        return {
            "status": "ok",
            "days": days,
            "total_signals": len(rows),
            "by_action": by_action,
            "by_symbol": by_symbol,
            "high_volatility_count": high_vol_count,
            "high_volatility_pct": (round(100 * high_vol_count / len(rows), 1)
                                       if rows else 0),
            "resolved": total_resolved,
            "unresolved": len(rows) - total_resolved,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}
