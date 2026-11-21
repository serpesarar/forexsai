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
KÂR ÇIKIŞI (2026-11-21, KULLANICI KARARI "canlıya al direk"; araştırma §2.107 CD-04, ön kayıt hükmü X — DAX'ta
  çalışmadığı için; NDX'te isabet %57→%89, +48→+106 bp, Sharpe 0,71→1,34, kuyruk CVaR5 −250→−475 bp):
  * YALNIZ NDX (config.CAPREV_KAR_EXIT, varsayılan True; CAPREV_KAR_MARKETS). DAX eski kuralda kalır.
  * Stop = felaket stopu giriş × (1 − 3·dvol). D0 seans kapanışında bid ≥ giriş ise çık; değilse sonraki her işlem
    günü seans kapanışında bid ≥ giriş olunca çık; en çok D5 kapanışında (araştırmadaki exit_index, m=5) zorla çık.
  * Tutuş sürerken "tek CAPREV pozisyonu" kuralı geçerli: başka CAPREV tetiği atlanır (skip olarak loglanır).
TUTUŞ KORUMASI (2026-11-21, KQ-03 NDX kapsamı B + canlıya alma kartı 6/6 LIVE; research/caprev_kuyruk_20261121):
  korumasız kâr çıkışı KQ-03'te C (taze NQ beslemesinde kuyruk 2× tabanı aştı). config.CAPREV_KAR_GUARD (varsayılan True):
  * D0 kapanışı zararda ise YALNIZ z0 = (bid/giriş − 1)/dvol > −0,5 ve kapanış gün dibinde değilse (clv > 0) tut; değilse D0'da çık.
  * Tutulursa stop girişin 1,5×dvol altına çekilir (SLTP; başarısızsa yazılımsal stop).
  * D1…D4 kapanışında VIX ≥ girişteki dünkü VIX × 1,10 ise çık. Kâr ve D5 kuralları aynı.
BÖLÜNMÜŞ GİRİŞ + YARIM TUTUŞ (2026-11-21, KQ-06, KULLANICI ONAYI; ön kayıt C — kör ABD CFD'leri eksi; NDX'te +48→+76 bp,
  Sharpe 0,71→1,51, CVaR5 −253 ≈ taban; yeni 10 piyasanın 10'u artı). config.CAPREV_SPLIT_ENTRY (varsayılan True), yalnız kâr piyasaları (NDX):
  * Tetikte lotun YARISI (A), D0 seans kapanışında kalan YARISI (B) alınır; her yarının felaket stopu kendi girişinin 3×dvol altı.
  * Her yarının ilk kontrol kapanışında (A: D0, B: D1) bid ≥ giriş → o yarı kapanır; zararda ise o yarının yarısı kapanır, kalanı taşınır.
  * Sonraki kapanışlarda bid ≥ giriş → kapanır; en geç ilk kontrolden sonraki 5. kapanışta kapanır. KQ-03 koruması (z0/VIX) bu modda YOK.
  * B bekliyorken başka CAPREV tetiği atlanır (tek pozisyon).
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
KAR_MAX_DAYS = 5                 # D0 + en çok 5 işlem günü kapanışı (CD-04 X_5_3.0_kar)
KAR_STOP_DVOL = 3.0              # felaket stopu, dvol katı
KAR_MAX_HOLD_S = 9 * 86400       # emniyet: hafta sonu + tatil payı
KQ_HOLD_Z = 0.5                  # D0 kapanışı tutma şartı: zarar < 0,5×dvol (KQ-03 a)
KQ_HOLD_CLV = 0.0                # ve kapanış gün dibinin üstünde (q)
KQ_STOP2_DVOL = 1.5              # D0 sonrası stop (c1)
KQ_VIX_UP = 0.10                 # s ≥ 1 koruması: VIX tırmanışı (G2)
SPLIT_HOLD = 0.5                 # KQ-06 h: ilk kontrol kapanışı zarardaysa tutulan pay

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


def next_weekday(day: date) -> date:
    from datetime import timedelta
    d = day + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def kar_enabled(config, market: str) -> bool:
    mk = tuple(getattr(config, "CAPREV_KAR_MARKETS", ("NDX.INDX",)))
    return bool(getattr(config, "CAPREV_KAR_EXIT", True)) and market in mk


def split_enabled(config, market: str) -> bool:
    return kar_enabled(config, market) and bool(getattr(config, "CAPREV_SPLIT_ENTRY", True))


def split_decision(bid: float, entry: float, step: int, partial_done: bool) -> str | None:
    """KQ-06 yarı kontrolü: 'kar' (tam kapat) | 'sure' (tam kapat) | 'yarim' (payın yarısını kapat) | None (tut)."""
    if bid >= entry:
        return "kar"
    if step >= KAR_MAX_DAYS:
        return "sure"
    if step == 0 and not partial_done:
        return "yarim"
    return None


def round_volume(v: float, info) -> float:
    """Hacmi sembolün adımına aşağı yuvarla; minimumun altındaysa 0."""
    step = float(getattr(info, "volume_step", 0.01) or 0.01)
    vmin = float(getattr(info, "volume_min", step) or step)
    r = math.floor(v / step + 1e-9) * step
    return round(r, 8) if r + 1e-12 >= vmin else 0.0


def kar_decision(bid: float, entry: float, step: int, guard: dict | None = None) -> str | None:
    """Kâr çıkışı kontrol noktası (seans kapanışı, step 0 = D0). 'kar' | 'sure' | 'tutma_yok' | 'vix' | None (tut).

    guard: {"dvol", "clv", "vixchg"} — KQ-03 tutuş koruması (None → korumasız CD-04)."""
    if bid >= entry:
        return "kar"
    if step >= KAR_MAX_DAYS:
        return "sure"
    if guard is None:
        return None
    if step == 0:
        z = (bid / entry - 1) / guard["dvol"] if guard.get("dvol") else 0.0
        clv = guard.get("clv")
        if z <= -KQ_HOLD_Z or (clv is not None and clv <= KQ_HOLD_CLV):
            return "tutma_yok"
    elif guard.get("vixchg") is not None and guard["vixchg"] >= KQ_VIX_UP:
        return "vix"
    return None


def day_clv(bars: list[dict], prof: dict, day: date, bid: float) -> float | None:
    """D0 seans (rth) 1h barlarından gün aralığında kapanış konumu; bar yoksa None."""
    lo_m, hi_m = prof["rth"]
    sel = [b for b in bars if cs.to_local(b["t"], prof["tz"])[0] == day and lo_m <= cs.to_local(b["t"], prof["tz"])[1] < hi_m]
    if not sel:
        return None
    hi, lo = max(b["high"] for b in sel), min(b["low"] for b in sel)
    return (bid - lo) / (hi - lo) if hi > lo else None


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


def _close_position(mt5, config, pos, log, why: str, volume: float | None = None) -> bool:
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return False
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "position": pos.ticket,
           "volume": float(volume if volume is not None else pos.volume), "type": mt5.ORDER_TYPE_SELL, "price": tick.bid,
           "deviation": config.DEVIATION_POINTS, "magic": magic(config), "comment": "fxs CAPREV exit",
           "type_filling": mt5.ORDER_FILLING_IOC}
    res = mt5.order_send(req)
    ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    _append({"kind": "exit", "ticket": pos.ticket, "symbol": pos.symbol, "why": why, "bid": tick.bid,
             "volume": req["volume"], "ok": ok, "retcode": getattr(res, "retcode", None)})
    (log.info if ok else log.error)("CAPREV %s kapanış ticket=%s %.2f lot @%.2f (%s) retcode=%s",
                                    "✅" if ok else "❌", pos.ticket, req["volume"], tick.bid, why, getattr(res, "retcode", None))
    return ok


def _manage_exits(mt5, config, log, now: float, st: dict, get_vix=None) -> None:
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
        if meta and meta.get("mode") == "split":
            _split_check(mt5, config, log, now, pos, meta, meta_off(st))
            continue
        if meta and meta.get("mode") == "kar":
            _kar_check(mt5, config, log, now, pos, meta, meta_off(st), get_vix)
            continue
        if now >= due:
            _close_position(mt5, config, pos, log, "seans kapanışı")
        elif now - (meta or {}).get("entry_t", now) > MAX_HOLD_S:
            _close_position(mt5, config, pos, log, "emniyet süresi")


def _guard_ctx(mt5, config, pos, meta: dict, step: int, bid: float, off: int, get_vix) -> dict | None:
    if not bool(getattr(config, "CAPREV_KAR_GUARD", True)) or not meta.get("dvol"):
        return None
    prof = PROFILES[meta["market"]]
    g = {"dvol": float(meta["dvol"]), "clv": None, "vixchg": None}
    if step == 0:
        try:
            rates = mt5.copy_rates_from_pos(pos.symbol, mt5.TIMEFRAME_H1, 0, 24)
            g["clv"] = day_clv(_h1(rates, off), prof, cs.to_local(meta["exit_t"], prof["tz"])[0], bid) if rates is not None else None
        except Exception:
            g["clv"] = None
    else:
        try:
            v = get_vix() if get_vix else None
        except Exception:
            v = None
        if v and meta.get("vix0"):
            g["vixchg"] = float(v) / float(meta["vix0"]) - 1
    return g


def _move_stop(mt5, log, pos, meta: dict) -> None:
    """Tutulan pozisyonun stopunu girişin KQ_STOP2_DVOL×dvol altına çek; başarısızsa yazılımsal stop kalır."""
    info = mt5.symbol_info(pos.symbol)
    sl = float(meta["entry"]) * (1 - KQ_STOP2_DVOL * float(meta["dvol"]))
    sl = round(sl, info.digits) if info is not None else sl
    meta["soft_sl"] = sl
    try:
        res = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": pos.symbol, "position": pos.ticket, "sl": sl, "tp": 0.0})
        ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
    except Exception:
        ok, res = False, None
    _append({"kind": "stop_move", "ticket": pos.ticket, "sl": sl, "ok": ok, "retcode": getattr(res, "retcode", None)})
    (log.info if ok else log.error)("CAPREV tutuş: stop %.2f'ye çekildi (%s)", sl, "ok" if ok else "BAŞARISIZ → yazılımsal stop")


def _kar_check(mt5, config, log, now: float, pos, meta: dict, off: int = 0, get_vix=None) -> None:
    """Kâr çıkışı: her seans kapanışı anında (≤ 30 dk içinde) bid ≥ giriş mi? Tatil/kapalı günde tick bayatsa ertele."""
    prof = PROFILES[meta["market"]]
    if now - meta["entry_t"] > KAR_MAX_HOLD_S:
        _close_position(mt5, config, pos, log, "kâr çıkışı emniyet süresi")
        return
    if meta.get("soft_sl"):                             # SLTP başarısız olduysa / emniyet: yazılımsal stop
        t = mt5.symbol_info_tick(pos.symbol)
        if t is not None and 0 < t.bid <= float(meta["soft_sl"]) and float(getattr(pos, "sl", 0.0) or 0.0) < float(meta["soft_sl"]) * 0.999:
            _close_position(mt5, config, pos, log, "yazılımsal tutuş stopu")
            return
    if now < meta["exit_t"]:
        return
    tick = mt5.symbol_info_tick(pos.symbol)
    fresh = tick is not None and abs(now - (float(getattr(tick, "time", now + off)) - off)) < 1800 and tick.bid > 0
    step = int(meta.get("step", 0))
    if fresh:
        g = _guard_ctx(mt5, config, pos, meta, step, float(tick.bid), off, get_vix)
        why = kar_decision(float(tick.bid), float(meta["entry"]), step, g)
        _append({"kind": "kar_check", "ticket": pos.ticket, "step": step, "bid": tick.bid,
                 "entry": meta["entry"], "decision": why or "tut", "guard": g})
        if why:
            _close_position(mt5, config, pos, log, f"kâr çıkışı ({why}, D{step})")
            return
        if step == 0 and g is not None:
            _move_stop(mt5, log, pos, meta)
        meta["step"] = step + 1
        log.info("CAPREV kâr çıkışı: D%d kapanışı zararda (bid %.2f < giriş %.2f) → tut", step, tick.bid, meta["entry"])
    else:
        _append({"kind": "kar_check", "ticket": pos.ticket, "step": step, "decision": "bayat tick, gün sayılmadı"})
    meta["exit_t"] = session_close_utc(next_weekday(cs.to_local(meta["exit_t"], prof["tz"])[0]), prof)


def _split_check(mt5, config, log, now: float, pos, meta: dict, off: int = 0) -> None:
    """KQ-06 yarı: kontrol kapanışında kâr → kapat; ilk kontrolde zarar → payın yarısını kapat; D(ilk+5) → kapat."""
    prof = PROFILES[meta["market"]]
    if now - meta["entry_t"] > KAR_MAX_HOLD_S:
        _close_position(mt5, config, pos, log, "bölünmüş giriş emniyet süresi")
        return
    if now < meta["exit_t"]:
        return
    tick = mt5.symbol_info_tick(pos.symbol)
    fresh = tick is not None and abs(now - (float(getattr(tick, "time", now + off)) - off)) < 1800 and tick.bid > 0
    step = int(meta.get("step", 0))
    if fresh:
        why = split_decision(float(tick.bid), float(meta["entry"]), step, bool(meta.get("partial_done")))
        _append({"kind": "split_check", "ticket": pos.ticket, "part": meta.get("part"), "step": step, "bid": tick.bid,
                 "entry": meta["entry"], "decision": why or "tut"})
        if why in ("kar", "sure"):
            _close_position(mt5, config, pos, log, f"bölünmüş giriş {meta.get('part')} ({why}, kontrol {step})")
            return
        if why == "yarim":
            vol = round_volume(float(pos.volume) * (1 - SPLIT_HOLD), mt5.symbol_info(pos.symbol))
            if 0 < vol < float(pos.volume):
                _close_position(mt5, config, pos, log, f"bölünmüş giriş {meta.get('part')} yarım kapanış", volume=vol)
            else:
                _append({"kind": "split_partial_skip", "ticket": pos.ticket, "volume": float(pos.volume)})
            meta["partial_done"] = True
        meta["step"] = step + 1
    else:
        _append({"kind": "split_check", "ticket": pos.ticket, "step": step, "decision": "bayat tick, gün sayılmadı"})
    meta["exit_t"] = session_close_utc(next_weekday(cs.to_local(meta["exit_t"], prof["tz"])[0]), prof)


def _open_split_b(mt5, config, log, now: float, st: dict) -> None:
    """D0 seans kapanışında bekleyen ikinci yarıyı (B) al."""
    for key, pb in list(st.get("pending_b", {}).items()):
        if now < pb["due"]:
            continue
        st["pending_b"].pop(key, None)
        late = now - pb["due"]
        rec = {"kind": "entry_b", "market": pb["market"], "latency_s": round(late, 1), "lot": pb["lot"]}
        if late > MAX_LATE_S:
            _append({**rec, "skip": "geç (seans kapanışı kaçtı)"})
            log.warning("CAPREV bölünmüş giriş B atlandı: kapanıştan %.0f sn geç", late)
            continue
        try:
            ti = mt5.terminal_info()
            if ti is not None and not bool(getattr(ti, "trade_allowed", True)):
                _append({**rec, "skip": "autotrading kapalı"})
                continue
        except Exception:
            pass
        tick, info = mt5.symbol_info_tick(pb["sym"]), mt5.symbol_info(pb["sym"])
        if tick is None or info is None:
            _append({**rec, "skip": "tick yok"})
            continue
        ask = round(tick.ask, info.digits)
        sl = round(ask * (1 - KAR_STOP_DVOL * pb["dvol"]), info.digits)
        req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": pb["sym"], "volume": float(pb["lot"]), "type": mt5.ORDER_TYPE_BUY,
               "price": ask, "sl": sl, "tp": 0.0, "deviation": config.DEVIATION_POINTS, "magic": magic(config),
               "comment": "fxs CAPREV B", "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
        res = mt5.order_send(req)
        ok = res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
        rec.update({"ok": ok, "retcode": getattr(res, "retcode", None), "ask": ask, "sl": sl})
        if ok:
            ticket = int(getattr(res, "order", 0))
            prof = PROFILES[pb["market"]]
            d0 = cs.to_local(pb["due"], prof["tz"])[0]
            st.setdefault("pos", {})[str(ticket)] = {"entry_t": now, "market": pb["market"], "mode": "split", "part": "B",
                                                      "entry": ask, "step": 0, "dvol": pb["dvol"], "vix0": pb.get("vix0"),
                                                      "exit_t": session_close_utc(next_weekday(d0), prof)}
            rec["ticket"] = ticket
            log.info("[CANLI] ✅ CAPREV %s bölünmüş giriş B %.2f lot @ %s SL=%s ticket=%s", pb["market"], pb["lot"], ask, sl, ticket)
        else:
            log.error("[CANLI] ❌ CAPREV bölünmüş giriş B reddedildi retcode=%s", rec["retcode"])
        _append(rec)


def manage_exits(mt5, config, log, now: float | None = None, get_vix=None) -> None:
    """Açık CAPREV pozisyonlarını seans kapanışında kapat (ana döngünün başında, frenlerden önce)."""
    now = time.time() if now is None else now
    st = _load_state()
    _manage_exits(mt5, config, log, now, st, get_vix)
    _open_split_b(mt5, config, log, now, st)
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
        if st.get("pending_b"):
            _append({"kind": "skip", "reason": "bölünmüş girişin ikinci yarısı bekliyor (tek pozisyon)", **base})
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
    kar = kar_enabled(config, market)
    sl = round(ask * (1 - (KAR_STOP_DVOL if kar else 1.0) * ctx["dvol"]), info.digits)
    lot = float(getattr(config, "CAPREV_LIVE_LOT", 1.0))
    exit_t = session_close_utc(today, prof)
    split = kar and split_enabled(config, market)
    lot_b = 0.0
    if split:
        lot_a = round_volume(lot / 2, info)
        lot_b = round_volume(lot - lot_a, info)
        if lot_a <= 0 or lot_b <= 0:
            split = False
        else:
            lot = lot_a
    line = f"CAPREV {market} BUY {lot} lot @ {ask} SL={sl} (dvol %{100 * ctx['dvol']:.2f}, VIX {base['vix']:.1f}), " + (
        (f"bölünmüş giriş A (B {lot_b} lot D0 kapanışında), yarım tutuş" if split else
         f"çıkış kâr kuralı (≤D{KAR_MAX_DAYS})" if kar else "çıkış seans kapanışı"))
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
           "lot": lot, "exit_t": exit_t, "mode": "split" if split else ("kar" if kar else "d0"), **base}
    try:                                            # ZM 60 dk bandı × SL (yalnız kayıt, DTS-06; fail-open)
        import range_band_bridge
        rec["range_band"] = range_band_bridge.check(mt5, sym, ask, None, sl, "BUY")
    except Exception:
        pass
    if ok:
        ticket = int(getattr(res, "order", 0))
        rec["ticket"] = ticket
        st.setdefault("pos", {})[str(ticket)] = {"entry_t": now, "exit_t": exit_t, "market": market,
                                                  "mode": "split" if split else ("kar" if kar else "d0"), "entry": ask,
                                                  "step": 0, "dvol": ctx["dvol"], "vix0": base["vix"],
                                                  **({"part": "A"} if split else {})}
        log.info("[CANLI] ✅ %s ticket=%s", line, ticket)
        try:                                    # kural adı + geçmiş başarı ekrana (kural_katalogu); hata emri etkilemez
            import kural_katalogu
            kural_katalogu.announce_open(log, "CAPREV", f"{sym} BUY {lot} lot @ {ask} · SL {sl} · ticket {ticket}",
                                         {"VIX": base["vix"], "gecikme_s": base["latency_s"]})
        except Exception:
            pass
        log_trade("LIVE", f"{market}:BUY:CAPREV", sym, "BUY", ask, 0.0, sl, ["caprev"], f"ticket={ticket}")
    else:
        log.error("[CANLI] ❌ CAPREV emir reddedildi retcode=%s → %s", rec["retcode"], line)
    if split:                                       # B yarısı A'dan bağımsız (KQ-06 E2): A dolmasa da kapanışta alınır
        st.setdefault("pending_b", {})[f"{market}|{today}"] = {"market": market, "sym": sym, "due": exit_t, "lot": lot_b,
                                                               "dvol": ctx["dvol"], "vix0": base["vix"]}
        rec["pending_b_lot"] = lot_b
    _append(rec)
