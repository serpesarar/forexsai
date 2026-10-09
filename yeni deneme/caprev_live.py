"""caprev_live.py — CAPREV portföyü (NDX + DAX) CANLI icra.

KART: backend/data/evolution/go_live_cards/caprev_portfoy.json — 6/6 LIVE (2026-10-09):
161 işlem / 134 bağımsız gün, ortR +0,217, P(EV>0) %99, iki yarı +, spread ×1,5 +, tek pozisyon +0,160.
KULLANICI KARARI 2026-10-09: 1 lot ile canlıya al. Kapatmak: config.CAPREV_LIVE = False (kutuda).

KURAL (kartla BİREBİR — değiştirmek kanıtı geçersiz kılar; research/ndx_gate_forge/round4.py + cross_market.py):
  * Gün koşulu (gün başında bilinir): önceki işlem günü getirisi ≤ −%1,5 VEYA 5 günlük ≤ −%4 (o piyasanın
    kendi seans kapanışlarından) VE önceki takvim gününün VIX kapanışı ≥ 18,4; yerel Pzt–Per.
  * Tetik: bugün pencere içindeki ilk KAPANMIŞ 1 saatlik bar, kapanışı < önceki işlem gününün seans dibi.
    NDX: NY 03:00 ≤ bar başı, bar bitişi ≤ 15:00; seans (dip) 09:00–16:00 NY, kapanış = 16:00 barı.
    DAX: Berlin 08:00 ≤ bar başı, bar bitişi ≤ 16:30; seans 09:00–18:00 Berlin, kapanış = 18:00 barı.
  * Giriş: tetik barı kapandıktan hemen sonra market BUY (≤ MAX_LATE_S gecikme; geç kalınırsa atlanır).
  * Stop: giriş × (1 − günlük vol), günlük vol = son 20 seans kapanış getirisinin std'si. TP YOK.
  * Çıkış: aynı yerel gün seans kapanışında (NDX 16:00 NY, DAX 18:00 Berlin) market kapanış.
  * Portföy: aynı anda TEK CAPREV pozisyonu (kartın 6. ölçütü); piyasa başına günde bir tetik.
Botun open_trade yolu KULLANILMAZ (fakeout/squeeze/probasyon kartta yok). trade_manager bu magic'e dokunmaz.
"""
from __future__ import annotations

import json
import math
import time
from datetime import date, datetime, timezone
from pathlib import Path

import caprev_shadow as cs          # saat dilimi yardımcıları + VIX geçmişi (gölge zaten tutuyor)

HERE = Path(__file__).resolve().parent
LOG_JSONL = HERE / "caprev_live.jsonl"
STATE_FILE = HERE / "caprev_live_state.json"

MAGIC_OFFSET = 7
STRESS_R1, STRESS_R5, VIX_MIN = -0.015, -0.04, 18.4
VOL_LOOKBACK = 20
BAR_MIN = 60
FULL_DAY_FRAC = 0.8
MAX_LATE_S = 600
FETCH_H1 = 1500                  # ≈ 60+ gün; ≥ 21 tam seans
POLL_EVERY_S = 30
MAX_HOLD_S = 30 * 3600           # emniyet: seans kapanışı kaçarsa
TRADE_WEEKDAYS = (0, 1, 2, 3)

PROFILES: dict[str, dict] = {
    "NDX.INDX": {"tz": "US", "rth": (540, 960), "close": 960, "win": (180, 900), "need_from": 570},
    "GDAXI.INDX": {"tz": "EU", "rth": (540, 1080), "close": 1080, "win": (480, 990), "need_from": 540},
}


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def rth_days(bars: list[dict], prof: dict) -> dict[date, dict]:
    """1h barlarından tam seans günleri: {tarih: {low, close, n}}. close = bitişi seans kapanışı olan bar."""
    lo_m, hi_m = prof["rth"]
    need = (hi_m - max(lo_m, prof["need_from"])) // BAR_MIN * FULL_DAY_FRAC
    acc: dict[date, dict] = {}
    for b in bars:
        d, m, _ = cs.to_local(b["t"], prof["tz"])
        if not (m >= lo_m and m + BAR_MIN <= hi_m):
            continue
        a = acc.setdefault(d, {"low": b["low"], "close": None, "n": 0})
        a["low"] = min(a["low"], b["low"])
        a["n"] += 1
        if m + BAR_MIN == prof["close"]:
            a["close"] = b["close"]
    return {d: a for d, a in sorted(acc.items()) if a["n"] >= need}


def daily_context(days: dict[date, dict], today: date) -> dict | None:
    """Bugünden ÖNCEKİ günlerden r1, r5, dvol (kapanış getirileri) ve önceki günün seans dibi (≤4 gün önce)."""
    prev = [d for d in days if d < today]
    closes = [(d, days[d]["close"]) for d in prev if days[d]["close"] is not None]
    if len(closes) < VOL_LOOKBACK + 1 or not prev:
        return None
    cl = [c for _, c in closes]
    rets = [cl[i] / cl[i - 1] - 1 for i in range(1, len(cl))]
    w = rets[-VOL_LOOKBACK:]
    mu = sum(w) / len(w)
    dvol = math.sqrt(sum((x - mu) ** 2 for x in w) / (len(w) - 1))
    r1, r5 = rets[-1], cl[-1] / cl[-6] - 1
    pd_day = prev[-1]
    pdl = days[pd_day]["low"] if (today - pd_day).days <= 4 else None
    return {"prev_day": str(pd_day), "r1": r1, "r5": r5, "dvol": dvol, "pdl": pdl,
            "stress": bool(r1 <= STRESS_R1 or r5 <= STRESS_R5)}


def prev_day_vix(hist: dict, today: date) -> float | None:
    """Bugünden önceki en son günün VIX değeri (gölgenin günlük-son-değer geçmişi; kartta 'dünkü kapanış')."""
    keys = [k for k in sorted(hist) if k < str(today)]
    return float(hist[keys[-1]]) if keys else None


def trigger(bars: list[dict], prof: dict, today: date, pdl: float) -> dict | None:
    """Bugün pencere içindeki ilk kapanmış 1h bar: kapanış < pdl (bar başı ≥ pencere başı, bitişi ≤ sonu)."""
    lo, hi = prof["win"]
    for b in bars:
        d, m, _ = cs.to_local(b["t"], prof["tz"])
        if d == today and m >= lo and m + BAR_MIN <= hi and b["close"] < pdl:
            return b
    return None


def session_close_utc(day: date, prof: dict) -> float:
    return cs.local_to_utc(day, prof["close"], prof["tz"])


# ═════════════════════════ durum / kayıt ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"fired": {}}


def _save_state(st: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _append(rec: dict) -> None:
    with open(LOG_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")


# ═════════════════════════ MT5 icra ═════════════════════════

_last_poll = 0.0


def magic(config) -> int:
    return int(getattr(config, "MAGIC_NUMBER", 52890969)) + MAGIC_OFFSET


def _h1(rates, off_s: int) -> list[dict]:
    return [{"t": int(r["time"]) - off_s, "open": float(r["open"]), "high": float(r["high"]),
             "low": float(r["low"]), "close": float(r["close"])} for r in rates]


def _open_positions(mt5, config) -> list:
    mg = magic(config)
    return [p for p in (mt5.positions_get() or []) if p.magic == mg]


def _close_position(mt5, config, pos, log, why: str) -> None:
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "position": pos.ticket,
           "volume": float(pos.volume), "type": mt5.ORDER_TYPE_SELL, "price": tick.bid,
           "deviation": config.DEVIATION_POINTS, "magic": magic(config), "comment": "fxs CAPREV exit",
           "type_filling": mt5.ORDER_FILLING_IOC}
    res = mt5.order_send(req)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    _append({"kind": "exit", "ticket": pos.ticket, "symbol": pos.symbol, "why": why, "bid": tick.bid,
             "ok": ok, "retcode": getattr(res, "retcode", None)})
    (log.info if ok else log.error)("CAPREV %s kapanış ticket=%s @%.2f (%s) retcode=%s",
                                    "✅" if ok else "❌", pos.ticket, tick.bid, why, getattr(res, "retcode", None))


def _manage_exits(mt5, config, log, now: float, st: dict) -> None:
    open_pos = _open_positions(mt5, config)
    live_tickets = {str(p.ticket) for p in open_pos}
    st["pos"] = {k: v for k, v in st.get("pos", {}).items() if k in live_tickets}   # SL ile kapananlar düşer
    for pos in open_pos:
        meta = st.get("pos", {}).get(str(pos.ticket))
        if meta:
            due = meta["exit_t"]
        else:                                           # bot yeniden başladıysa: açılış gününün kapanışı
            prof = PROFILES["GDAXI.INDX" if "GER" in pos.symbol.upper() else "NDX.INDX"]
            due = session_close_utc(cs.to_local(pos.time - meta_off(st), prof["tz"])[0], prof)
        if now >= due:
            _close_position(mt5, config, pos, log, "seans kapanışı")
        elif now - (meta or {}).get("entry_t", now) > MAX_HOLD_S:
            _close_position(mt5, config, pos, log, "emniyet süresi")


def manage_exits(mt5, config, log, now: float | None = None) -> None:
    """Açık CAPREV pozisyonlarını seans kapanışında kapat (ana döngünün başında, frenlerden önce)."""
    now = time.time() if now is None else now
    st = _load_state()
    _manage_exits(mt5, config, log, now, st)
    _save_state(st)


def meta_off(st: dict) -> int:
    return int(st.get("last_off", 0))


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok,
         log_trade, now: float | None = None) -> None:
    """Bot ana döngüsünden her tarama çağrılır. Hata → çağıran yakalar (fail-open)."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    st = _load_state()
    live = bool(getattr(config, "CAPREV_LIVE", True)) and bool(config.LIVE_TRADING)
    vix_hist = cs._load_state().get("vix_hist", {})
    for market, prof in PROFILES.items():
        sym = resolve_symbol(market)
        if not sym:
            continue
        today, mloc, wd = cs.to_local(now, prof["tz"])
        key = f"{market}|{today}"
        if wd not in TRADE_WEEKDAYS or key in st["fired"]:
            continue
        off = offset_fn(sym)
        st["last_off"] = off
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, FETCH_H1)     # 1 → koşan bar hariç
        if rates is None or len(rates) < 300:
            continue
        bars = _h1(rates, off)
        ctx = daily_context(rth_days(bars, prof), today)
        vix = prev_day_vix(vix_hist, today)
        vix_src = "dün"
        if vix is None:
            vix, vix_src = get_vix(), "anlık"
        if ctx is None or ctx["pdl"] is None or not ctx["stress"] or vix is None or vix < VIX_MIN:
            continue
        trig = trigger(bars, prof, today, ctx["pdl"])
        if trig is None:
            continue
        st["fired"][key] = True
        late = now - (trig["t"] + BAR_MIN * 60)
        base = {"market": market, "date": str(today), "trigger_t": trig["t"], "trigger_close": trig["close"],
                "pdl": ctx["pdl"], "r1": round(ctx["r1"], 5), "r5": round(ctx["r5"], 5), "dvol": round(ctx["dvol"], 6),
                "vix": vix, "vix_src": vix_src, "latency_s": round(late, 1)}
        if late > MAX_LATE_S:
            _append({"kind": "skip", "reason": "geç tespit", **base})
            continue
        if _open_positions(mt5, config):
            _append({"kind": "skip", "reason": "portföyde açık CAPREV var (tek pozisyon)", **base})
            log.info("CAPREV %s tetik ama açık CAPREV pozisyonu var → atlandı", market)
            continue
        _enter(mt5, config, log, market, sym, prof, today, ctx, base, now, st, live,
               send_order, mk_comment, autotrading_ok, log_trade)
    st["fired"] = {k: v for k, v in st["fired"].items() if k.split("|")[1] >= str(date.fromtimestamp(now - 15 * 86400))}
    _save_state(st)


def _enter(mt5, config, log, market, sym, prof, today, ctx, base, now, st, live,
           send_order, mk_comment, autotrading_ok, log_trade) -> None:
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    sl = round(ask * (1 - ctx["dvol"]), info.digits)
    lot = float(getattr(config, "CAPREV_LIVE_LOT", 1.0))
    exit_t = session_close_utc(today, prof)
    line = f"CAPREV {market} BUY {lot} lot @ {ask} SL={sl} (dvol %{100 * ctx['dvol']:.2f}, VIX {base['vix']:.1f}), çıkış seans kapanışı"
    if not live:
        log.info("[GÖZLEM] %s", line)
        _append({"kind": "observe", "ask": ask, "sl": sl, **base})
        return
    if not autotrading_ok():
        log.error("CAPREV AutoTrading KAPALI — emir gönderilmedi: %s", line)
        _append({"kind": "skip", "reason": "autotrading kapalı", **base})
        return
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot, "type": mt5.ORDER_TYPE_BUY,
           "price": ask, "sl": sl, "tp": 0.0, "deviation": config.DEVIATION_POINTS, "magic": magic(config),
           "comment": mk_comment("fxs ", f"CAPREV {market[:3]}"), "type_time": mt5.ORDER_TIME_GTC}
    res = send_order(req, sym)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    rec = {"kind": "entry", "ok": ok, "retcode": getattr(res, "retcode", None), "ask": ask, "sl": sl,
           "lot": lot, "exit_t": exit_t, **base}
    if ok:
        ticket = int(getattr(res, "order", 0))
        rec["ticket"] = ticket
        st.setdefault("pos", {})[str(ticket)] = {"entry_t": now, "exit_t": exit_t, "market": market}
        log.info("[CANLI] ✅ %s ticket=%s", line, ticket)
        log_trade("LIVE", f"{market}:BUY:CAPREV", sym, "BUY", ask, 0.0, sl, ["caprev"], f"ticket={ticket}")
    else:
        log.error("[CANLI] ❌ CAPREV emir reddedildi retcode=%s → %s", rec["retcode"], line)
    _append(rec)
