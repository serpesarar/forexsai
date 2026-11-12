"""aysonu_live.py — AY SONU DENGELEME AKIŞI, CANLI icra (demo hesap). NAS100 + US500.

KULLANICI KARARI 2026-11-12: "önerdiklerinin hepsini bota direkt bağla, canlı". Kanıt: research/qs03_akis_takvim_20261111/
(QS-03…07; defter §2.43). Mekanizma: sabit hisse/tahvil oranlı fonlar (emeklilik, 60/40, hedef-tarih) ay sonunda oranı geri kurar.
Ay içinde hisse tahvili çok geçtiyse fonlar ayın SON SEANSINDA hisse satar, tahvil hisseyi geçtiyse alır; akış yeni ayda geri döner.

İKİ BACAK (ikisi de zaman çıkışlı; TP yok; SL yalnız acil durum sigortası):
  AYSONU_SON  "son seans"  — kart go_live_cards/qs06_son_seans.json 6/6 (2014-26 +31 bp P 1,00; broker NAS100 +38, US500 +44 bp).
      D = ayın son NYSE işlem günü. Δ = SPY ay içi − TLT ay içi getirisi, D−3 kapanışında (önceki ay son kapanışı → D−3 kapanışı).
      Δ ≥ +%2 → SAT, Δ ≤ −%2 → AL (arada işlem yok). Giriş D 09:30 ET (≤10 dk gecikme), çıkış D 16:00 ET.
      Acil SL %4 (geçmişte en kötü seyir NAS100 −%2,3, US500 −%1,5 → hiçbir işlemi kesmez).
  AYSONU_E2   "ay başı uzun" — kart qs04_e2_ay_basi_uzun.json + döngü qs04_ay_sonu_dongusu.json 6/6 (broker NAS100 +56 bp).
      Δ_D = SPY ay içi − TLT ay içi, D KAPANIŞINDA. Δ_D ≥ +%2 → AL (yalnız uzun; kısa bacak her dönemde eksiydi).
      Giriş D 16:20–17:00 ET (araştırma 16:30), çıkış D'den sonraki 3. işlem günü 16:30 ET. Acil SL %8 (en kötü seyir −%6,5).
BAĞLANMAYANLAR (bilinçli): R1 D−3→D (son seansı içerir, aynı bahsi ikiler), F1 son yarım saat (son seansın içinde), GER40 Avrupa son
seansı (2015 sonrası sönük), tatil öncesi (C+), QS-01 Instagram kuralı (C).
US500 lotu: NAS100 lotuyla AYNI NOMİNAL (fiyat × kontrat büyüklüğü oranı) — iki endeks korelasyonu ~0,94; bilinçli ikili bahis.
Veri: SPY/TLT günlük kapanış yfinance (kutuda 1.5.2). Takvim: NYSE tatilleri 2025-2028 aşağıda; veri tarihleriyle çapraz denetlenir —
uyuşmazsa işlem YOK. Kapatma: config.AYSONU_SON_LIVE / AYSONU_E2_LIVE = False. Durdurma ölçütü (önceden yazılı): son seans n=24'te ort<0.
"""
from __future__ import annotations

import calendar
import json
import time
from datetime import date, timedelta
from pathlib import Path

import c3b_shadow as sh          # TZ="US"
import caprev_shadow as cs       # to_local
import kural_katalogu as kk

HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "aysonu_live_state.json"
R_SON, R_E2 = "AYSONU_SON", "AYSONU_E2"
SYMBOLS = ("NDX.INDX", "US500")            # resolve_symbol anahtarları (NDX.INDX → NAS100)
REF = "NDX.INDX"                           # lot referansı
TH = 0.02
POLL_EVERY_S = 20
DATA_REFRESH_S = 600
SON_ENTRY_MIN, SON_LATE_MIN, SON_EXIT_MIN = 570, 580, 960      # 09:30, 09:40, 16:00 ET
E2_ENTRY_MIN, E2_ENTRY_END, E2_EXIT_MIN = 980, 1020, 990       # 16:20, 17:00, 16:30 ET
SL_SON, SL_E2 = 0.04, 0.08

NYSE_HOLIDAYS = {date(*d) for d in (
    (2025, 1, 1), (2025, 1, 9), (2025, 1, 20), (2025, 2, 17), (2025, 4, 18), (2025, 5, 26), (2025, 6, 19), (2025, 7, 4),
    (2025, 9, 1), (2025, 11, 27), (2025, 12, 25),
    (2026, 1, 1), (2026, 1, 19), (2026, 2, 16), (2026, 4, 3), (2026, 5, 25), (2026, 6, 19), (2026, 7, 3), (2026, 9, 7),
    (2026, 11, 26), (2026, 12, 25),
    (2027, 1, 1), (2027, 1, 18), (2027, 2, 15), (2027, 3, 26), (2027, 5, 31), (2027, 6, 18), (2027, 7, 5), (2027, 9, 6),
    (2027, 11, 25), (2027, 12, 24),
    (2028, 1, 17), (2028, 2, 21), (2028, 4, 14), (2028, 5, 29), (2028, 6, 19), (2028, 7, 4), (2028, 9, 4), (2028, 11, 23),
    (2028, 12, 25),
)}
CAL_LAST_YEAR = 2028

_last_poll = 0.0
_last_exit_poll = 0.0
_data = {"t": 0.0, "eq": None, "bd": None}


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def trading_days(year: int, month: int) -> list[date]:
    """NYSE işlem günleri (hafta içi − tam gün tatiller). Takvim kapsamı dışında → boş liste."""
    if year > CAL_LAST_YEAR:
        return []
    n = calendar.monthrange(year, month)[1]
    return [d for d in (date(year, month, k) for k in range(1, n + 1)) if d.weekday() < 5 and d not in NYSE_HOLIDAYS]


def _next_month(y: int, m: int) -> tuple[int, int]:
    return (y + 1, 1) if m == 12 else (y, m + 1)


def _prev_month(y: int, m: int) -> tuple[int, int]:
    return (y - 1, 12) if m == 1 else (y, m - 1)


def month_info(d: date) -> dict | None:
    """d'nin ayı için {D, Dm3, p0, Dp3}: son işlem günü, 3 işlem günü öncesi, önceki ayın son işlem günü, D'den sonraki 3. işlem günü."""
    days = trading_days(d.year, d.month)
    prev = trading_days(*_prev_month(d.year, d.month))
    nxt = trading_days(*_next_month(d.year, d.month))
    if len(days) < 5 or not prev or len(nxt) < 3:
        return None
    return {"D": days[-1], "Dm3": days[-4], "p0": prev[-1], "Dp3": nxt[2]}


def e2_exit_day(entry_day: date) -> date | None:
    mi = month_info(entry_day)
    return mi["Dp3"] if mi and mi["D"] == entry_day else None


def delta(eq: dict, bd: dict, d0: date, d1: date) -> float | None:
    """Hisse − tahvil getirisi d0 kapanışı → d1 kapanışı. Eksik tarih → None (takvim/veri uyuşmazlığı)."""
    try:
        return (eq[d1] / eq[d0] - 1.0) - (bd[d1] / bd[d0] - 1.0)
    except (KeyError, ZeroDivisionError, TypeError):
        return None


def flow_side(dl: float | None, th: float = TH) -> int:
    """Δ ≥ +th → −1 (fonlar hisse satar → SAT), Δ ≤ −th → +1 (AL), arada / None → 0."""
    if dl is None:
        return 0
    return -1 if dl >= th else (1 if dl <= -th else 0)


def parity_lot(ref_lot: float, ref_px: float, ref_cs: float, px: float, cs_: float,
               step: float, vmin: float, vmax: float) -> float:
    """Referans lotla aynı nominal: lot = ref_lot × (ref_px·ref_cs)/(px·cs); adım/sınırlara yuvarla."""
    if px <= 0 or cs_ <= 0 or step <= 0:
        return 0.0
    raw = ref_lot * (ref_px * ref_cs) / (px * cs_)
    lot = round(round(raw / step) * step, 8)
    return max(vmin, min(vmax, lot))


def son_exit_due(entry_day: date, now_day: date, now_min: int) -> bool:
    return now_day > entry_day or (now_day == entry_day and now_min >= SON_EXIT_MIN)


def e2_exit_due(entry_day: date, now_day: date, now_min: int) -> bool:
    ex = e2_exit_day(entry_day)
    if ex is None:                                    # takvim dışı → güvenli taraf: 3 takvim günü + 16:30
        ex = entry_day + timedelta(days=3)
    return now_day > ex or (now_day == ex and now_min >= E2_EXIT_MIN)


# ═════════════════════════ veri ═════════════════════════

def _fetch_closes(now: float, log) -> tuple[dict | None, dict | None]:
    """SPY ve TLT günlük düzeltilmiş kapanışlar {date: close}; 10 dk önbellek."""
    if _data["eq"] is not None and now - _data["t"] < DATA_REFRESH_S:
        return _data["eq"], _data["bd"]
    try:
        import yfinance as yf
        out = []
        for tk in ("SPY", "TLT"):
            h = yf.Ticker(tk).history(period="4mo", auto_adjust=True)
            if h is None or len(h) < 30:
                raise ValueError(f"{tk} verisi boş")
            out.append({ts.date(): float(v) for ts, v in h["Close"].items()})
        _data.update(t=now, eq=out[0], bd=out[1])
    except Exception as e:                              # veri yoksa işlem yok
        log.warning("AYSONU: SPY/TLT verisi alınamadı: %s", e)
    return _data["eq"], _data["bd"]


# ═════════════════════════ durum ═════════════════════════

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


# ═════════════════════════ çıkış (ana döngüde frenden ÖNCE) ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    global _last_exit_poll
    now = time.time() if now is None else now
    if now - _last_exit_poll < POLL_EVERY_S:
        return
    _last_exit_poll = now
    now_day, now_min, _ = cs.to_local(now, sh.TZ)
    for key in SYMBOLS:
        sym = resolve_symbol(key)
        if not sym:
            continue
        for rule, due in ((R_SON, son_exit_due), (R_E2, e2_exit_due)):
            for pos in kk.open_positions(mt5, config, rule, sym):
                entry_day = cs.to_local(pos.time - offset_fn(sym), sh.TZ)[0]
                if due(entry_day, now_day, now_min):
                    kk.close(mt5, config, log, send_order, rule, pos,
                             "son seans 16:00 ET çıkışı" if rule == R_SON else "ay başı 3. gün 16:30 ET çıkışı")


# ═════════════════════════ giriş ═════════════════════════

def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    """Bot ana döngüsünden her tarama çağrılır (imza diğer canlı modüllerle aynı). Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S:
        return
    _last_poll = now
    son_on, e2_on = kk.is_enabled(config, R_SON), kk.is_enabled(config, R_E2)
    if not (son_on or e2_on):
        return
    today, mloc, wd = cs.to_local(now, sh.TZ)
    if wd >= 5:
        return
    mi = month_info(today)
    if mi is None:
        if today.year > CAL_LAST_YEAR:
            log.error("AYSONU: NYSE takvimi %d sonrası tanımlı değil — NYSE_HOLIDAYS'i güncelle", CAL_LAST_YEAR)
        return
    if today != mi["D"]:
        return
    st = _load_state()
    th = float(getattr(config, "AYSONU_THRESHOLD", TH))
    if son_on and SON_ENTRY_MIN <= mloc <= SON_LATE_MIN and st.get("son_d") != str(today):
        eq, bd = _fetch_closes(now, log)
        if eq is None:
            return
        st["son_d"] = str(today); _save_state(st)                       # günde ≤ 1 karar
        dl = delta(eq, bd, mi["p0"], mi["Dm3"])
        s = flow_side(dl, th)
        rec = {"rule": R_SON, "day": str(today), "p0": str(mi["p0"]), "Dm3": str(mi["Dm3"]),
               "delta_pct": None if dl is None else round(dl * 100, 3), "side": s}
        if dl is None:
            kk.append_event({"kind": "skip", "reason": "SPY/TLT verisinde p0 veya D−3 yok (takvim uyuşmazlığı)", **rec})
            log.error("AYSONU son seans: veri/takvim uyuşmazlığı — işlem yok (%s)", rec)
            return
        if s == 0:
            kk.append_event({"kind": "nosignal", **rec})
            log.info("AYSONU son seans: Δ=%.2f%% eşik içinde — bu ay işlem yok", dl * 100)
        else:
            _enter_all(mt5, config, log, resolve_symbol, R_SON, s, SL_SON, rec, send_order, mk_comment, autotrading_ok, log_trade)
    if e2_on and E2_ENTRY_MIN <= mloc <= E2_ENTRY_END and st.get("e2_d") != str(today):
        eq, bd = _fetch_closes(now, log)
        if eq is None or today not in eq or today not in bd:            # bugünün kapanışı henüz yoksa sonraki taramada dene
            return
        st["e2_d"] = str(today); _save_state(st)
        dl = delta(eq, bd, mi["p0"], today)
        rec = {"rule": R_E2, "day": str(today), "p0": str(mi["p0"]), "delta_D_pct": None if dl is None else round(dl * 100, 3),
               "exit_day": str(mi["Dp3"])}
        if dl is not None and dl >= th:
            _enter_all(mt5, config, log, resolve_symbol, R_E2, 1, SL_E2, rec, send_order, mk_comment, autotrading_ok, log_trade)
        else:
            kk.append_event({"kind": "nosignal", **rec})
            log.info("AYSONU ay başı: Δ_D=%s — uzun koşulu (≥ +%%2) yok", rec["delta_D_pct"])


def _lot_for(mt5, config, rule: str, key: str, sym: str, ref_sym: str | None) -> float:
    base = kk.lot_of(config, rule)
    if key == REF or not getattr(config, "AYSONU_US500_PARITY", True) or not ref_sym:
        return base if key == REF else float(getattr(config, f"{rule}_US500_LOT", base))
    ri, ti = mt5.symbol_info(ref_sym), mt5.symbol_info(sym)
    rt, tt = mt5.symbol_info_tick(ref_sym), mt5.symbol_info_tick(sym)
    if None in (ri, ti, rt, tt):
        return 0.0
    return parity_lot(base, rt.bid, float(ri.trade_contract_size), tt.bid, float(ti.trade_contract_size),
                      float(ti.volume_step), float(ti.volume_min), float(ti.volume_max))


def _enter_all(mt5, config, log, resolve_symbol, rule, side, sl_frac, rec, send_order, mk_comment, autotrading_ok, log_trade):
    ref_sym = resolve_symbol(REF)
    for key in SYMBOLS:
        sym = resolve_symbol(key)
        if not sym:
            kk.append_event({"kind": "skip", "reason": f"{key} sembolü çözülemedi", **rec})
            continue
        if kk.open_positions(mt5, config, rule, sym):
            kk.append_event({"kind": "skip", "reason": f"açık {rule} pozisyonu var ({sym})", **rec})
            continue
        lot = _lot_for(mt5, config, rule, key, sym, ref_sym)
        if lot <= 0:
            kk.append_event({"kind": "skip", "reason": f"lot hesaplanamadı ({sym})", **rec})
            continue
        _enter(mt5, config, log, sym, key, rule, side, lot, sl_frac, rec, send_order, mk_comment, autotrading_ok, log_trade)


def _enter(mt5, config, log, sym, key, rule, side, lot, sl_frac, rec, send_order, mk_comment, autotrading_ok, log_trade):
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        kk.append_event({"kind": "skip", "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap} ({sym})", **rec})
        log.warning("%s atlandı: %s açık kural lotu %.2f + %.2f > tavan %.2f", rule, sym, open_lot, lot, cap)
        return
    if not autotrading_ok():
        log.error("%s AutoTrading KAPALI — emir gönderilmedi", rule)
        kk.append_event({"kind": "skip", "reason": "autotrading kapalı", "symbol": sym, **rec})
        return
    d = "BUY" if side > 0 else "SELL"
    px = round(tick.ask if side > 0 else tick.bid, info.digits)
    sl = round(px * (1 - sl_frac) if side > 0 else px * (1 + sl_frac), info.digits)
    tag = ("AYS son " if rule == R_SON else "AYS e2 ") + d
    fn = kk.buy if side > 0 else kk.sell
    ok, ticket, rc = fn(mt5, config, log, send_order, mk_comment, rule, sym, lot, px, sl, 0.0, tag)
    kk.append_event({"kind": "entry", "ok": ok, "retcode": rc, "ticket": ticket, "symbol": sym, "dir": d, "price": px,
                     "sl": sl, "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ %s %s emir reddedildi retcode=%s", rule, sym, rc)
        return
    kk.announce_open(log, rule, f"{sym} {d} {lot} lot @ {px} · acil SL {sl} · ticket {ticket}",
                     {k: v for k, v in rec.items() if k in ("delta_pct", "delta_D_pct", "Dm3", "exit_day")})
    log_trade("LIVE", f"{key}:{d}:{rule}", sym, d, px, 0.0, sl, ["aysonu"], f"ticket={ticket}")
