"""
Entry Optimizer Shadow/Enforce Wrapper.

Sinyal pipeline'ına entegrasyon noktası — tek fonksiyon `apply_entry_optimizer`.
Modlar (env: ENTRY_OPTIMIZER_MODE):
  "off"     → optimizer hiç çağrılmaz, signal değişmez (DEFAULT — güvenli)
  "shadow"  → optimizer ÇAĞRILIR + Supabase'e LOGLANIR ama signal DEĞİŞMEZ
  "enforce" → optimizer çağrılır + log + signal entry/sl/tp DEĞİŞTİRİLİR

Önerilen yaşam döngüsü:
  1. Deploy: mode=shadow → 7 gün gözlem
  2. Stats temizse: mode=enforce → optimizer kararları gerçek trade'e uygulanır
  3. Sorun olursa: mode=off → anında geri al

Kullanım (pipeline'da signal_lifecycle veya prediction_logger içinde):

    from services.shadow_executor import apply_entry_optimizer
    signal = await apply_entry_optimizer(signal, stage4_info)
    # signal artık enforce mode'da optimizer'ın entry/sl/tp'siyle gelir
    # diğer modlarda original ile aynı
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _mode() -> str:
    """ENTRY_OPTIMIZER_MODE → off (default) | shadow | enforce."""
    m = (os.getenv("ENTRY_OPTIMIZER_MODE") or "off").strip().lower()
    return m if m in ("off", "shadow", "enforce") else "off"


def _is_eligible(signal: dict) -> bool:
    """Filtre: optimizer hangi sinyaller için çalışsın.

    Sembol exclusion (NDX gibi) ZATEN entry_optimizer içinde işleniyor —
    PASSTHROUGH dönüyor. Burada model_type/timeframe gibi üst filtreler için
    yer. Şimdilik geniş kapsamlı."""
    direction = (signal.get("direction") or "").upper()
    if direction not in ("BUY", "SELL"):
        return False
    if not signal.get("symbol"):
        return False
    if not (signal.get("price") or signal.get("entry_price")):
        return False
    return True


async def apply_entry_optimizer(signal: dict,
                                  stage4_info: Optional[dict] = None,
                                  prediction_id: Optional[str] = None
                                  ) -> dict:
    """Sinyal pipeline'da tek entry noktası.

    Mod=off: signal aynen döner, hiçbir şey yapılmaz.
    Mod=shadow: optimizer çağrılır, Supabase'e loglanır, signal DEĞİŞMEZ.
    Mod=enforce: optimizer çağrılır, loglanır, signal'in entry/sl/tp'si
      decision'ınkilere değiştirilir.

    Args:
      signal: {symbol, direction, price, confidence?, model_type?, ...}
      stage4_info: {sizing_mult?, predicted_r?} — log için (opsiyonel)
      prediction_id: prediction_logs row ID (insert sonrası verilebilir)

    Returns:
      signal dict (orijinal veya modify edilmiş — moda göre)
    """
    mode = _mode()
    if mode == "off":
        return signal
    if not _is_eligible(signal):
        return signal

    # Optimizer'ı çağır
    try:
        from services.entry_optimizer import optimize_entry
        decision = await optimize_entry(dict(signal))
    except Exception as e:
        logger.warning("[shadow-exec] optimize_entry hata: %s", e)
        return signal

    # Log et — shadow ve enforce modlarda ikisinde de
    import asyncio
    try:
        from services.regime_logger import log_signal
        # Candles fetch (opsiyonel — varsa logger ATR hesaplar)
        candles_15m = None
        try:
            from services.data_fetcher import fetch_ohlc_data
            candles_15m = await fetch_ohlc_data(
                signal.get("symbol"), "15m", limit=80)
        except Exception:
            pass
        asyncio.create_task(log_signal(
            signal=signal, decision=decision,
            candles_15m=candles_15m, stage4_info=stage4_info,
            prediction_id=prediction_id,
            enforce_mode=(mode == "enforce")))
    except Exception as e:
        logger.warning("[shadow-exec] log_signal scheduling hata: %s", e)

    # Mode'a göre signal'i değiştir
    if mode == "enforce":
        action = decision.get("action")
        # PASSTHROUGH veya FALLBACK_MARKET → default config korunur, sadece
        # entry/sl/tp güncellenir (optimizer kararındaki değerler).
        # EXECUTE_NOW / LIMIT_ORDER → optimizer'ın özel entry/sl/tp'si uygulanır.
        new_signal = dict(signal)
        new_signal["entry_price"] = decision.get("entry_price")
        new_signal["sl_price"] = decision.get("sl_price")
        new_signal["tp_price"] = decision.get("tp_price")
        new_signal["entry_optimizer_action"] = action
        new_signal["entry_optimizer_priority"] = decision.get("priority_score")
        new_signal["max_wait_candles"] = decision.get("max_wait_candles") or 0
        new_signal["structure_type"] = decision.get("structure_type")
        return new_signal

    # Shadow — signal aynen döner, ama trace için decision iliştirilir
    signal_with_shadow = dict(signal)
    signal_with_shadow["_shadow_decision"] = {
        "action": decision.get("action"),
        "entry": decision.get("entry_price"),
        "sl": decision.get("sl_price"),
        "tp": decision.get("tp_price"),
        "priority": decision.get("priority_score"),
        "structure": decision.get("structure_type"),
    }
    return signal_with_shadow


def get_status() -> dict:
    """Mevcut mod + filter bilgisi — endpoint için."""
    return {
        "mode": _mode(),
        "env_var": "ENTRY_OPTIMIZER_MODE",
        "valid_values": ["off", "shadow", "enforce"],
        "description": {
            "off": "Optimizer hiç çalışmaz (default — güvenli)",
            "shadow": "Çalışır + loglanır, signal değişmez (gözlem mode)",
            "enforce": "Çalışır + loglanır + signal entry/sl/tp değiştirilir",
        },
    }
