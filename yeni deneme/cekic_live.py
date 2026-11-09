"""cekic_live.py — FR-15 TEYİTLİ ÇEKİÇ (NAS100 + GER40, 1h) CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/teyitli_cekic_1h.json — yerel 10/10 set artı; MT5 H1 2018-26 kör havuz +0,085R
(n 3.969, P 0,98), swap sonrası ≈ +0,07R. Düşük isabet (≈%26–30), yüksek ödül (TP 5R). Sınıf B, komşu eşiklerde kırılgan.
KULLANICI KARARI 2026-11-08: kendi lotuyla canlıya bağla (kural_katalogu: 0.5 her endekste). Kapatma: config.CEKIC_LIVE = False.

KURAL (research/fitil_ret_20261106: engine2.bars + ek7.post_entry KAPANIS_TEYIDI + final2.sim1; E68 UTC saat başı barlar):
  Çekiç barı i (1h): alt fitil/aralık ≥ 0,70 ∧ alt fitil ≥ 0,20×ATR14 ∧ alt fitil ≥ üst fitil (ATR14 = son 14 barın TR ortalaması).
  Teyit barı i+1 (ardışık): düşüğü çekiç dibinin ÜSTÜNDE (dibi kırmadı) ∧ KAPANIŞI çekiç tepesinin üstünde
  → teyit barı kapanır kapanmaz market BUY (araştırma: sonraki açılış + spread). SL = çekiç dibi, TP = giriş + 5×(giriş − dip).
  Risk < 2×spread → işlem yok. Zaman çıkışı 24 saat; hafta sonu boşluğu için Cuma 16:45 NY'de kapat.
  Tek pozisyon (sembol başına). Kısa (SAT) yok — kanıt yok.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import caprev_shadow as cs
import kural_katalogu as kk

RULE = "CEKIC"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "cekic_live_state.json"
POLL_EVERY_S = 20
MAX_LATE_S = 300
MAX_TICK_AGE_S = 180
BAR_S = 3600
ATR_N = 14
MIN_LW_RANGE = 0.70
MIN_LW_ATR = 0.20
MIN_DOM = 1.0
TP_R = 5.0
HOLD_S = 24 * 3600
MIN_RISK_SPREADS = 2.0
FRIDAY_CLOSE_NY_MIN = 16 * 60 + 45
FETCH_H1 = 60
MARKETS = ("NDX.INDX", "GDAXI.INDX")

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def atr14(bars: list[dict], i: int) -> float | None:
    """i. bara kadar (dahil) son 14 barın TR ortalaması (araştırma: tr.rolling(14).mean()). Yetersizse None."""
    if i < ATR_N:
        return None
    tr = []
    for k in range(i - ATR_N + 1, i + 1):
        b, pc = bars[k], bars[k - 1]["close"]
        tr.append(max(b["high"] - b["low"], abs(b["high"] - pc), abs(b["low"] - pc)))
    return sum(tr) / ATR_N


def is_hammer(bars: list[dict], i: int) -> bool:
    b = bars[i]
    atr, rng = atr14(bars, i), b["high"] - b["low"]
    if atr is None or atr <= 0 or rng <= 0:
        return False
    lw = min(b["open"], b["close"]) - b["low"]
    uw = b["high"] - max(b["open"], b["close"])
    if lw <= 0:
        return False
    dom = float("inf") if uw <= 0 else lw / uw
    return lw / rng >= MIN_LW_RANGE and lw / atr >= MIN_LW_ATR and dom >= MIN_DOM


def confirmed(hammer: dict, nxt: dict) -> bool:
    """Teyit barı: ardışık, çekiç dibini kırmadı, kapanışı çekiç tepesinin üstünde."""
    return (nxt["t"] - hammer["t"] <= 2 * BAR_S and nxt["low"] > hammer["low"] and nxt["close"] > hammer["high"])


def build_order(hammer: dict, ask: float, bid: float) -> tuple[dict | None, str | None]:
    dist = ask - hammer["low"]
    if dist < MIN_RISK_SPREADS * (ask - bid):
        return None, "risk < 2×spread"
    if dist <= 0:
        return None, "giriş çekiç dibinin altında"
    return {"sl": hammer["low"], "tp": ask + TP_R * dist, "risk": dist}, None


def find_signal(bars: list[dict]) -> dict | None:
    """Son iki KAPANMIŞ barda (çekiç = bars[-2], teyit = bars[-1]) kurulum var mı?"""
    if len(bars) < ATR_N + 3:
        return None
    h, c = bars[-2], bars[-1]
    if is_hammer(bars, len(bars) - 2) and confirmed(h, c):
        return {"hammer": h, "confirm": c, "atr": atr14(bars, len(bars) - 2)}
    return None


def friday_close_due(now: float) -> bool:
    d, m, wd = cs.to_local(now, "US")
    return wd == 4 and m >= FRIDAY_CLOSE_NY_MIN


# ═════════════════════════ durum / MT5 ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"fired": {}, "pos": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


def manage_exits(mt5, config, log, send_order, offset_fn, now: float | None = None) -> None:
    """24 saat zaman çıkışı + Cuma kapanış öncesi (ana döngüde frenden ÖNCE). SL/TP broker tarafında."""
    if not kk.is_enabled(config, RULE):
        return
    now = time.time() if now is None else now
    st = _load_state()
    for pos in kk.open_positions(mt5, config, RULE):
        meta = st.get("pos", {}).get(str(pos.ticket))
        opened_utc = meta["entry_t"] if meta else float(pos.time) - offset_fn(pos.symbol)   # pos.time = sunucu saati
        age = now - opened_utc
        if age >= HOLD_S:
            kk.close(mt5, config, log, send_order, RULE, pos, "24 saat zaman çıkışı")
        elif friday_close_due(now):
            kk.close(mt5, config, log, send_order, RULE, pos, "Cuma kapanışı (hafta sonu boşluğu)")


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    if friday_close_due(now):
        return
    st = _load_state()
    changed = False
    for market in MARKETS:
        sym = resolve_symbol(market)
        if not sym:
            continue
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, FETCH_H1)       # 1 → koşan bar hariç
        if rates is None or len(rates) < ATR_N + 3:
            continue
        off = offset_fn(sym)
        bars = cs._m15_utc(rates, off)
        sig = find_signal(bars)
        if sig is None:
            continue
        key = f"{market}|{int(sig['confirm']['t'])}"
        if key in st["fired"]:
            continue
        late = now - (sig["confirm"]["t"] + BAR_S)
        if late < 0 or late > MAX_LATE_S:
            continue                                                                # teyit barı henüz kapanmadı / geç kalındı
        st["fired"][key] = True
        changed = True
        _try_enter(mt5, config, log, market, sym, sig, late, st, now, send_order, mk_comment, autotrading_ok, log_trade, off)
    if changed:
        cut = now - 7 * 86400
        st["fired"] = {k: v for k, v in st["fired"].items() if int(k.split("|")[1]) >= cut}
        _save_state(st)


def _try_enter(mt5, config, log, market, sym, sig, late, st, now, send_order, mk_comment, autotrading_ok, log_trade,
               off: int = 0) -> None:
    h = sig["hammer"]
    rec = {"market": market, "hammer_t": h["t"], "hammer_low": h["low"], "hammer_high": h["high"],
           "confirm_close": sig["confirm"]["close"], "atr14": round(sig["atr"], 3), "latency_s": round(late, 1)}
    if kk.open_positions(mt5, config, RULE, sym):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "açık çekiç pozisyonu var (tek pozisyon)", **rec})
        return
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    if abs(now - (float(tick.time) - off)) > MAX_TICK_AGE_S:      # araştırma: teyit sonrası ilk bar ≤30 dk içinde yoksa işlem yok
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "bayat tick (piyasa kapalı?)", **rec})
        return
    ask, bid = round(tick.ask, info.digits), round(tick.bid, info.digits)
    pl, why = build_order(h, ask, bid)
    if pl is None:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": why, **rec})
        return
    lot = kk.lot_of(config, RULE)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}", **rec})
        log.warning("Çekiç atlandı: %s üzerinde açık kural lotu %.2f + %.2f > tavan %.2f", sym, open_lot, lot, cap)
        return
    if not autotrading_ok():
        log.error("Çekiç AutoTrading KAPALI — emir gönderilmedi")
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "autotrading kapalı", **rec})
        return
    sl, tp = round(pl["sl"], info.digits), round(pl["tp"], info.digits)
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, tp, f"CEKIC {market[:3]}")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "tp": tp, "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ Çekiç emir reddedildi retcode=%s", rc)
        return
    st["pos"][str(ticket)] = {"entry_t": now, "market": market}
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · SL {sl} (çekiç dibi) · TP {tp} (5R) · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"], "risk_pt": round(pl["risk"], 2)})
    log_trade("LIVE", f"{market}:BUY:CEKIC", sym, "BUY", ask, tp, sl, ["cekic"], f"ticket={ticket}")
