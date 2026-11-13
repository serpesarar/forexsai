"""fx_vixreg_live.py — VIXREG-FX (FX-01 H12) CANLI icra, DEMO hesap, en küçük lot.

KULLANICI KARARI 2026-11-13 (oturum hedefi): "Forex'te ... onun üzerinde trade yapmanı istiyorum ... kazanç kapıları bulana kadar
devam et, bunu yapana kadar durma." Kart 6/6 (backend/data/evolution/go_live_cards/fx_vixreg_risk_doviz.json). Lot kullanıcı
belirlemediği için EN KÜÇÜK (0,01/çift); ezme config.FX_VIXREG_LIVE_LOT. Kapatma: config.FX_VIXREG_LIVE = False.

KANIT: research/fx_secim_20261113 (PROTOCOL EK-8/EK-9, RAPOR §8–9). H11'de hiç kullanılmamış 6 kör çiftte ön-kayıtlı: rejim farkı
+3,75 bp/gün, P 0,998, 6/6 çift; 16 çift kartı 157 epizod +19 bp, iki yarı +, maliyet ×1,5 +%1,33/yıl. Uyarılar: mutlak getiri
küçük (birim nominal ≈ +%1,5/yıl, Sharpe 0,29), 2009 öncesi tersi (çağ), NDX VIXREG ile günlük ρ 0,61.

KURAL (dondurulmuş): k günü getirisi (k−1 → k, 17:00 ET kapanışları) için pozisyon, (k−2) gününün VIX kapanışı ≥ 18,4 ise risk
para birimi UZUN (VIXREG_PAIRS yönleri), aksi DÜZ. İcra: k−1 günü 16:30–16:57 ET penceresinde hedef duruma uzlaştır (kapanışa
yakın, devir spread'inden önce). VIX geçmişi caprev_state.json'daki `vix_hist` (günün son görülen VIX'i) + bu modülün kendi kaydı.
Acil SL: girişten %5 (araştırmada stop yok; yalnız felaket koruması).

⚠️ AYRI magic (MAGIC_NUMBER + 15) ve kural_katalogu'na GİRMEZ: katalog magic'leri global MAX_TOTAL_POSITIONS (6) tavanına sayılır,
16 FX pozisyonu NDX işlemlerini kilitlerdi. Bu yüzden günlük zarar freni de bu pozisyonları saymaz (0,01 lotla etkisi küçük).
"""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import fx_fiks_shadow as fs

RULE = "FX_VIXREG"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "fx_vixreg_live_state.json"
EVENTS_JSONL = HERE / "fx_vixreg_live.jsonl"
CAPREV_STATE = HERE / "caprev_state.json"
MAGIC_OFFSET = 15
LOT_DEFAULT = 0.01
WIN_START_ET, WIN_END_ET = 16 * 60 + 30, 16 * 60 + 57
EMERGENCY_SL = 0.05
POLL_EVERY_S = 30
MAX_TICK_AGE_S = 180
PAIRS = fs.VIXREG_PAIRS
TH = fs.VIXREG_TH

_last_poll = 0.0


# ═════════════════════════ saf yardımcılar ═════════════════════════

def magic(config) -> int:
    return int(getattr(config, "MAGIC_NUMBER", 52890969)) + MAGIC_OFFSET


def enabled(config) -> bool:
    return bool(getattr(config, "FX_VIXREG_LIVE", True)) and bool(getattr(config, "LIVE_TRADING", False))


def lot(config) -> float:
    return float(getattr(config, "FX_VIXREG_LIVE_LOT", LOT_DEFAULT))


def in_window(now: float) -> date | None:
    d, m = fs.us_et(now)
    return d if d.weekday() < 5 and WIN_START_ET <= m <= WIN_END_ET else None


def target_on(hist: dict, today: date) -> bool | None:
    """Bugün (k−1) kapanışından sonraki gün (k) için hedef: bugünden ÖNCEKİ en son günün (k−2) VIX'i ≥ eşik. Geçmiş yoksa None."""
    prev = [k for k in sorted(hist) if k < today.isoformat()]
    if not prev:
        return None
    return float(hist[prev[-1]]) >= TH


def plan(target: bool, open_by_sym: dict[str, int]) -> tuple[list[tuple[str, int]], list[str]]:
    """(açılacak [(sembol, yön)], kapatılacak [sembol]). open_by_sym: {sembol: açık pozisyon yönü (+1/−1)}."""
    to_open, to_close = [], []
    for sym, side in PAIRS.items():
        cur = open_by_sym.get(sym)
        if target:
            if cur is None:
                to_open.append((sym, side))
            elif cur != side:
                to_close.append(sym)
                to_open.append((sym, side))
        elif cur is not None:
            to_close.append(sym)
    return to_open, to_close


def merged_hist(st: dict) -> dict:
    h = {}
    try:
        h.update(json.loads(CAPREV_STATE.read_text(encoding="utf-8")).get("vix_hist", {}))
    except (OSError, ValueError):
        pass
    h.update(st.get("vix_hist", {}))
    return h


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st.setdefault("vix_hist", {})
    st.setdefault("done", None)
    return st


def _save_state(st: dict) -> None:
    keep = sorted(st["vix_hist"])[-30:]
    st["vix_hist"] = {k: st["vix_hist"][k] for k in keep}
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _event(rec: dict) -> None:
    with EVENTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.time(), **rec}, ensure_ascii=False) + "\n")


# ═════════════════════════ MT5 ═════════════════════════

def _open_positions(mt5, config) -> dict[str, list]:
    mg = magic(config)
    out: dict[str, list] = {}
    for p in mt5.positions_get() or []:
        if p.magic == mg:
            out.setdefault(p.symbol, []).append(p)
    return out


def _side_of(mt5, p) -> int:
    return -1 if int(getattr(p, "type", 0)) == int(getattr(mt5, "POSITION_TYPE_SELL", 1)) else 1


def _close(mt5, config, log, send_order, p, why: str) -> bool:
    tick = mt5.symbol_info_tick(p.symbol)
    if tick is None:
        return False
    short = _side_of(mt5, p) < 0
    px = tick.ask if short else tick.bid
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "position": p.ticket, "volume": float(p.volume),
           "type": mt5.ORDER_TYPE_BUY if short else mt5.ORDER_TYPE_SELL, "price": px, "deviation": config.DEVIATION_POINTS,
           "magic": magic(config), "comment": "fxs FXVIX exit"}
    res = send_order(req, p.symbol)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    _event({"kind": "exit", "symbol": p.symbol, "ticket": p.ticket, "why": why, "price": px, "entry": p.price_open,
            "ok": ok, "retcode": getattr(res, "retcode", None), "profit": getattr(p, "profit", None)})
    log.info("[CANLI] FX-VIXREG kapat %s %s @ %s (%s) ok=%s", p.symbol, "SELL" if short else "BUY", px, why, ok)
    return ok


def _open(mt5, config, log, send_order, mk_comment, sym: str, side: int, now: float, off: int) -> bool:
    mt5.symbol_select(sym, True)
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None or abs(now - (float(tick.time) - off)) > MAX_TICK_AGE_S:
        _event({"kind": "skip", "symbol": sym, "why": "tick yok/bayat"})
        return False
    px = round(float(tick.ask if side > 0 else tick.bid), info.digits)
    sl = round(px * (1 - EMERGENCY_SL) if side > 0 else px * (1 + EMERGENCY_SL), info.digits)
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot(config),
           "type": mt5.ORDER_TYPE_BUY if side > 0 else mt5.ORDER_TYPE_SELL, "price": px, "sl": sl, "tp": 0.0,
           "deviation": config.DEVIATION_POINTS, "magic": magic(config), "comment": mk_comment("fxs ", "FXVIX"),
           "type_time": mt5.ORDER_TIME_GTC}
    res = send_order(req, sym)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    _event({"kind": "entry", "symbol": sym, "side": side, "price": px, "sl": sl, "lot": lot(config), "ok": ok,
            "retcode": getattr(res, "retcode", None), "ticket": int(getattr(res, "order", 0)) if ok else 0})
    log.info("[CANLI] FX-VIXREG aç %s %s %.2f lot @ %s SL %s ok=%s", sym, "BUY" if side > 0 else "SELL", lot(config), px, sl, ok)
    return ok


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    """Bot ana döngüsünden çağrılır (canlı kurallar döngüsü). Yalnız 16:30–16:57 ET penceresinde emir verir."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not enabled(config):
        return
    _last_poll = now
    st = _load_state()
    d_et, m_et = fs.us_et(now)
    if d_et.weekday() < 5 and m_et >= 16 * 60 + 20:                 # günün VIX'i (16:15 ET kapanışı) — kendi kaydımız
        v = get_vix() if get_vix else None
        if v is not None and st["vix_hist"].get(d_et.isoformat()) != float(v):
            st["vix_hist"][d_et.isoformat()] = float(v)
            _save_state(st)
    today = in_window(now)
    if today is None or st.get("done") == today.isoformat():
        return
    tgt = target_on(merged_hist(st), today)
    if tgt is None:
        log.warning("FX-VIXREG: VIX geçmişi yok — bugün işlem yok")
        return
    off = fs.server_offset(offset_fn("USDJPY"))
    if off is None:
        log.warning("FX-VIXREG: sunucu saat farkı ölçülemedi — atlandı")
        return
    if not autotrading_ok():
        log.error("FX-VIXREG AutoTrading KAPALI — emir gönderilmedi")
        return
    open_pos = _open_positions(mt5, config)
    cur = {s: _side_of(mt5, ps[0]) for s, ps in open_pos.items()}
    to_open, to_close = plan(tgt, cur)
    all_ok = True
    for s in to_close:
        for p in open_pos.get(s, []):
            all_ok &= _close(mt5, config, log, send_order, p, "rejim kapandı" if not tgt else "yön düzeltme")
    for s, side in to_open:
        all_ok &= _open(mt5, config, log, send_order, mk_comment, s, side, now, off)
    _event({"kind": "uzlasma", "gun": today.isoformat(), "hedef_acik": tgt, "acilan": len(to_open), "kapanan": len(to_close),
            "tamam": all_ok})
    if to_open or to_close:
        log.info("FX-VIXREG %s: hedef %s → %d aç / %d kapat (tamam=%s)", today, "UZUN" if tgt else "DÜZ",
                 len(to_open), len(to_close), all_ok)
    if all_ok:
        st["done"] = today.isoformat()
        _save_state(st)
