"""xau_r0b_live.py — XAUUSD 1h "yeni 20 mum tepesinde AL" + S2 (R0B_G1 + "dün > +%1 ise atla") CANLI icra (demo hesap).

KULLANICI KARARI 2026-11-12: "1h kuralını canlıya al". Gölge (xau_shadow.py) yan yana çalışmaya devam eder — araştırma
bacağı ile canlı dolum farkını ölçmek için.

KANIT: MK-04 → MK-06 R0B_G1 (research/decider_xau_tpsl_20261015/mekanik; Dukascopy H1 2008-01→2026-06; kart 10/10) +
MK-13 S2 (research/xau_best_days_20261015/dogrulama; A, kural içi filtre). Tek pozisyon S2 %1: n 3.259 (19 yıl, ≈3,4/hafta,
≈14–15/ay), ort +0,109R, isabet %36,3, 16/19 yıl artı, maks. düşüş −48,6R.
UYARILAR (karar öncesi kullanıcıya söylendi): seçim düzeltmesinde (max-z) sürüklenme-üstü fark anlamlı değil (p_sel 0,47) —
kazancın bir kısmı altının 2008-26 yükselişi; gölge ileri karnesi n 6 (−0,6R), karar için yetersiz. Durdurma ölçütü
(önceden yazılı): canlı n=60 işlemde ort. R < 0 → config.XAU_R0B_LIVE = False.

KURAL (xau_shadow.py saf fonksiyonları AYNEN kullanılır — araştırma paritesi orada sınandı):
  Sinyal: kapanmış 1h bar i'nin yükseği ≥ önceki 20 barın en yükseği (xs.is_signal).
  S2: önceki UTC gününün getirisi > +%1 ise ATLA (xs.prevday_ret; geçmiş yetmezse atlanmaz — gölgeyle aynı).
  Giriş: bar kapanır kapanmaz market BUY (≤ 10 dk gecikme; araştırma = sonraki bar açılışı + 0,12).
  SL = giriş − 1,5×ATR14(H1, sinyal barı dahil; xs.atr_at), broker tarafında. TP YOK.
  Çıkış: giriş barı dahil 20. 1h barın kapanışı; Cuma 16:50 NY (hafta sonu boşluğu = araştırmada segment sonu);
  pozisyon tutulurken > 3 saatlik bar boşluğu görülürse (tatil) ilk fırsatta kapat.
  Tek pozisyon. Çıkış barında gelen yeni sinyal açılır (ana döngüde çıkışlar girişlerden önce çalışır — araştırmadaki gibi).
  Yalnız BUY (SELL kanıtı yok; config BLOCKED_SYMBOL_DIRECTIONS zaten XAUUSD SELL'i yasaklıyor).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import caprev_shadow as cs
import kural_katalogu as kk
import xau_shadow as xs

RULE = "XAU_R0B"
MARKET = "XAUUSD"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "xau_r0b_live_state.json"
POLL_EVERY_S = 20
MAX_LATE_S = xs.MAX_LATE_S            # 600 sn — gölgeyle aynı
MAX_TICK_AGE_S = 180
BAR_S = xs.BAR_S
HOLD_BARS = xs.HOLD                   # 20
STOP_K = xs.STOP_K                    # 1,5
GAP_S = xs.GAP_S                      # 3 saat
S2_THR_DEFAULT = xs.S2_THR            # 0,010
FRIDAY_CLOSE_NY_MIN = 16 * 60 + 50    # altın CFD Cuma 17:00 NY kapanır
FETCH_H1 = 200
EXIT_FETCH_H1 = 40
FIRED_KEEP_S = 7 * 86400

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def s2_thr(config) -> float:
    return float(getattr(config, "XAU_R0B_S2_THR", S2_THR_DEFAULT))


def evaluate(bars: list[dict], thr: float = S2_THR_DEFAULT) -> tuple[dict | None, str | None]:
    """Son KAPANMIŞ bar (bars[-1]) için karar. Dönüş (sinyal, None) | (None, atlama nedeni) | (None, None) = sinyal yok."""
    i = len(bars) - 1
    if i < xs.LOOK or not xs.is_signal(bars, i):
        return None, None
    atr = xs.atr_at(bars, i)
    if atr is None or atr <= 0:
        return None, "ATR yok"
    pr = xs.prevday_ret(bars, i)
    if pr is not None and pr > thr:
        return None, f"S2: önceki gün {pr * 100:+.2f}% > +{thr * 100:.2f}% (kovalama)"
    b = bars[i]
    return {"sig_t": b["t"], "sig_high": b["high"], "sig_close": b["close"], "atr": atr, "stop_dist": STOP_K * atr,
            "prevday_ret": pr}, None


def held_bars(bars: list[dict], entry_bar_t: float) -> list[dict]:
    """Giriş barından (dahil) itibaren kapanmış barlar."""
    return [b for b in bars if b["t"] >= entry_bar_t]


def exit_reason(bars: list[dict], entry_bar_t: float, now: float) -> str | None:
    """Çıkış nedeni ya da None. bars: kapanmış H1 (UTC)."""
    h = held_bars(bars, entry_bar_t)
    if len(h) >= HOLD_BARS:
        return f"{HOLD_BARS} bar zaman çıkışı"
    if any(h[j]["t"] - h[j - 1]["t"] > GAP_S for j in range(1, len(h))) or (h and h[0]["t"] - entry_bar_t > GAP_S):
        return "segment sonu (> 3 saat boşluk)"
    if friday_close_due(now):
        return "Cuma kapanışı (hafta sonu boşluğu)"
    return None


def friday_close_due(now: float) -> bool:
    _, m, wd = cs.to_local(now, "US")
    return wd == 4 and m >= FRIDAY_CLOSE_NY_MIN


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"fired": {}, "pos": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


def _closed_bars(mt5, sym: str, off: int, n: int) -> list[dict]:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, n)          # 1 → koşan bar hariç
    return xs._bars(rates, off) if rates is not None else []


# ═════════════════════════ MT5 ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    """20 bar / Cuma / boşluk çıkışı (ana döngüde frenden ÖNCE). SL broker tarafında."""
    if not kk.is_enabled(config, RULE):
        return
    now = time.time() if now is None else now
    positions = kk.open_positions(mt5, config, RULE)
    if not positions:
        return
    st = _load_state()
    for pos in positions:
        off = offset_fn(pos.symbol)
        meta = st.get("pos", {}).get(str(pos.ticket))
        if meta:
            entry_bar_t = float(meta["entry_bar_t"])
        else:                                                               # durum dosyası yoksa: açılış anının saat başı
            entry_bar_t = (int(float(pos.time) - off) // BAR_S) * BAR_S
        bars = _closed_bars(mt5, pos.symbol, off, EXIT_FETCH_H1)
        why = exit_reason(bars, entry_bar_t, now) if bars else (
            "zaman çıkışı (bar okunamadı)" if now - entry_bar_t >= (HOLD_BARS + 2) * BAR_S else None)
        if why and kk.close(mt5, config, log, send_order, RULE, pos, why):
            st.get("pos", {}).pop(str(pos.ticket), None)
            _save_state(st)


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    sym = resolve_symbol(MARKET)
    if not sym:
        return
    off = offset_fn(sym)
    bars = _closed_bars(mt5, sym, off, FETCH_H1)
    if len(bars) < xs.LOOK + xs.ATR_N + 5:
        return
    last = bars[-1]
    late = now - (last["t"] + BAR_S)
    key = str(int(last["t"]))
    st = _load_state()
    if key in st["fired"] or late < 0 or late > MAX_LATE_S:
        return
    sig, why = evaluate(bars, s2_thr(config))
    if sig is None and why is None:
        return                                                              # sinyal yok (kayıt gerekmez)
    st["fired"][key] = True
    st["fired"] = {k: v for k, v in st["fired"].items() if int(k) >= now - FIRED_KEEP_S}
    _save_state(st)
    rec = {"market": MARKET, "sig_t": last["t"], "sig_high": last["high"], "latency_s": round(late, 1)}
    if sig is None:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": why, **rec})
        log.info("XAU 1h yeni tepe atlandı: %s", why)
        return
    _try_enter(mt5, config, log, sym, sig, rec, st, now, off, send_order, mk_comment, autotrading_ok, log_trade)


def _try_enter(mt5, config, log, sym, sig, rec, st, now, off, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    rec = {**rec, "atr": round(sig["atr"], 3), "stop_dist": round(sig["stop_dist"], 3),
           "prevday_ret": None if sig["prevday_ret"] is None else round(sig["prevday_ret"], 5)}
    skip = lambda r: kk.append_event({"kind": "skip", "rule": RULE, "reason": r, **rec})
    if kk.open_positions(mt5, config, RULE, sym):
        return skip("açık XAU 1h pozisyonu var (tek pozisyon)")
    if friday_close_due(now):
        return skip("Cuma kapanış penceresi")
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return skip("tick/sembol bilgisi yok")
    if abs(now - (float(tick.time) - off)) > MAX_TICK_AGE_S:
        return skip("bayat tick (piyasa kapalı?)")
    ask = round(float(tick.ask), info.digits)
    lot = kk.lot_of(config, RULE)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        return skip(f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}")
    if not autotrading_ok():
        log.error("XAU 1h AutoTrading KAPALI — emir gönderilmedi")
        return skip("autotrading kapalı")
    sl = round(ask - sig["stop_dist"], info.digits)
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, 0.0, "XAU R0B")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ XAU 1h emir reddedildi retcode=%s", rc)
        return
    st["pos"][str(ticket)] = {"entry_bar_t": sig["sig_t"] + BAR_S, "entry_t": now, "ask": ask, "sl": sl}
    _save_state(st)
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · SL {sl} (1,5×ATR) · TP yok · 20 bar · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"], "atr": rec["atr"], "dun": rec["prevday_ret"]})
    log_trade("LIVE", f"{MARKET}:BUY:XAU_R0B", sym, "BUY", ask, 0.0, sl, ["xau_r0b_s2"], f"ticket={ticket}")
