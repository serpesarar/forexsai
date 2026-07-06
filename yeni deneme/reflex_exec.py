"""Reflex Engine execution hook for the MT5 bot.

Consumes the backend's validated NDX momentum-continuation signals
(GET /api/reflex/live) and executes them with the ONLY validated exit: a 15-minute
time-stop, plus the signal's catastrophic 1.5×ATR SL as a broker-side backstop.

Isolated slot: its own magic (MAGIC_NUMBER + 3), so it never collides with the
momentum / channel / VIX scopes.

SHADOW by default: REFLEX_LIVE (env or config) must be True to place real orders;
otherwise it only logs what it *would* do. This mirrors the bot's LIVE_TRADING
discipline — nothing trades live without an explicit switch.

Wire-in (forexsai_demo_bot.py main loop, once per tick):
    import reflex_exec
    reflex_exec.poll_reflex(log)
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import requests

try:
    import MetaTrader5 as mt5
except Exception:  # allows import on non-MT5 boxes (shadow analysis)
    mt5 = None

import config

REFLEX_MAGIC = config.MAGIC_NUMBER + 3
REFLEX_SYMBOL = "NDX.INDX"
REFLEX_MT5_SYMBOL = config.SYMBOL_MAP.get(REFLEX_SYMBOL, "USTEC")
TIME_STOP_MIN = 15
MAX_OPEN = 2                      # cap concurrent reflex positions
# Live switch: env REFLEX_LIVE=1 OR config.REFLEX_LIVE=True. Default SHADOW.
REFLEX_LIVE = os.environ.get("REFLEX_LIVE", "").strip() == "1" or getattr(config, "REFLEX_LIVE", False)

_seen: set[int] = set()          # signal ids already acted on (dedup within run)


def _mk_comment(sig_id: int) -> str:
    return f"fxs-rfx {sig_id}".encode("ascii", "ignore").decode()[:28]


def _fetch_live() -> list[dict]:
    try:
        url = config.FOREXSAI_API.rstrip("/") + "/api/reflex/live"
        r = requests.get(url, params={"symbol": REFLEX_SYMBOL}, timeout=15)
        if r.status_code == 200:
            return (r.json() or {}).get("active", []) or []
    except Exception:
        pass
    return []


def _reflex_positions() -> list:
    if mt5 is None:
        return []
    return [p for p in (mt5.positions_get(symbol=REFLEX_MT5_SYMBOL) or [])
            if getattr(p, "magic", 0) == REFLEX_MAGIC]


def _open(sig: dict, log) -> None:
    direction = sig["direction"]
    sl = float(sig.get("sl_price") or 0.0)
    sid = int(sig["id"])
    line = f"REFLEX {direction} {REFLEX_MT5_SYMBOL} sl={sl} (id={sid}, {TIME_STOP_MIN}dk time-stop)"

    if not REFLEX_LIVE:
        log.info("[GÖZLEM] Reflex açardım → %s", line)
        _seen.add(sid)
        return
    if mt5 is None:
        log.error("Reflex: MT5 yok, canlı emir atlanıyor"); return

    tick = mt5.symbol_info_tick(REFLEX_MT5_SYMBOL)
    info = mt5.symbol_info(REFLEX_MT5_SYMBOL)
    if tick is None or info is None:
        log.error("Reflex tick/info alınamadı"); return
    price = tick.ask if direction == "BUY" else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    sl = round(sl, info.digits)
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": REFLEX_MT5_SYMBOL,
        "volume": config.LOT_SIZE, "type": order_type, "price": round(price, info.digits),
        "sl": sl, "tp": 0.0,                      # NO TP — exit is the 15-min time-stop
        "deviation": config.DEVIATION_POINTS, "magic": REFLEX_MAGIC,
        "comment": _mk_comment(sid),
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result is None:
        log.error("Reflex order_send None: %s", mt5.last_error()); return
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        _seen.add(sid)
        log.info("[CANLI] ✅ Reflex açıldı ticket=%s → %s", result.order, line)
    else:
        log.error("[CANLI] ❌ Reflex reddedildi retcode=%s → %s", result.retcode, line)


def _close(pos, log) -> None:
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return
    is_buy = pos.type == mt5.ORDER_TYPE_BUY
    price = tick.bid if is_buy else tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "position": pos.ticket,
        "volume": pos.volume, "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
        "price": price, "deviation": config.DEVIATION_POINTS, "magic": REFLEX_MAGIC,
        "comment": "fxs-rfx timestop", "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result is not None and result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info("♻️ Reflex time-stop kapandı ticket=%s", pos.ticket)
    else:
        log.error("Reflex kapatma hatası ticket=%s: %s", pos.ticket,
                  mt5.last_error() if mt5 else "n/a")


def poll_reflex(log) -> None:
    """One reflex cycle: close positions past the 15-min time-stop, then open new signals."""
    try:
        # 1) TIME-STOP: close reflex positions older than TIME_STOP_MIN
        if REFLEX_LIVE and mt5 is not None:
            now = int(time.time())
            for pos in _reflex_positions():
                age_min = (now - int(pos.time)) / 60.0
                if age_min >= TIME_STOP_MIN:
                    _close(pos, log)

        # 2) ENTRIES: open new active signals not already acted on
        active = _fetch_live()
        if not active:
            return
        open_count = len(_reflex_positions()) if (REFLEX_LIVE and mt5 is not None) else 0
        for sig in active:
            sid = int(sig.get("id", 0))
            if sid in _seen or open_count >= MAX_OPEN:
                continue
            # only trade genuinely fresh signals (avoid stale entries on restart)
            try:
                ev_t = datetime.fromisoformat(str(sig["entry_time"]).replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - ev_t).total_seconds() > 120:
                    _seen.add(sid); continue      # too old to enter cleanly
            except Exception:
                pass
            _open(sig, log)
            open_count += 1
    except Exception as e:
        log.exception("Reflex poll hatası: %s", e)
