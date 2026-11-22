"""korku_live.py — NAS100 "korku gecesi" paketi K1-T30 + OPEX vetosu + XP çıkışı CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/ndx_korku_t30_paket.json — 6/6 LIVE (Dukascopy NDX 1m 2018-26 n 324 +74,3 bp, isabet %77;
MT5 NAS100 M30 n 309 +73,9 bp 6/6). Kanıt: research/korku_evren_20261119 (EV-01, defter §2.101) + paket §2.95 kapı 03.
KULLANICI KARARI 2026-11-19: "bunu canlıya al". Lot: kural_katalogu (0.75). Kapatma: config.KORKU_LIVE = False.
Durdurma ölçütü (önceden yazılı): canlı n=40 işlemde ort. net < 0 → kapat.

KURAL (donduruldu; değiştirmek kanıtı geçersiz kılar). Tüm saatler New York (ET), M30 barları (bar açılışı):
  P16 = bugünkü 16:00 barının açılışı, O15 = 15:00 barının açılışı, TWAP = 09:30…15:30 barlarının (13 bar) kapanış ortalaması.
  P16 ≤ TWAP × (1 − 0,003)  ∧  P16 < O15   →  16:00'da AL (ask).
  OPEX vetosu: ayın 3. Cuması (tatilse önceki işlem günü) vade günü; vadeye 0, 1 ya da 2 işlem günü kala AÇMA.
  Çıkış XP: sonraki her işlem gününün P16'sına bakılır; P16 > önceki P16 (ilk gün: giriş günü P16) → kapat; değilse referans güncellenir;
  5. işlem günü her durumda kapat. TP/SL yok.
  TEK FARK: broker tarafında ACİL DURUM SL'i (%13, `KORKU_LIVE_EMERGENCY_SL`). Araştırmada giriş sonrası en derin seyir −%11,9
  (2025-04-03) → %13 hiçbir geçmiş işlemi kesmez; yalnız bot ölürse sigorta.
  Tek pozisyon: açık KORKU pozisyonu varken yeni sinyal atlanır (kart 6. ölçütü: tek pozisyon +69 bp, n 266).
  Giriş gecikmesi en çok 10 dk (kart 5. ölçütü: sonraki mum açılışı +71,4 vs +74,3 bp).
  KOŞULLU EKLEME GÖLGESİ (2026-11-22, research/korku_bolunmus_20261122 KR-03/04 B + kart 6/6; KULLANICI KARARI: GÖLGE):
  D1 16:00'da XP çıkmadıysa ve D1 P16 girişin ≥ 50 bp altındaysa "+1 birim" sanal alınır (D1 P16 + giriş spread'i), ana pozisyonla aynı XP
  çıkışında sanal kapanır. EMİR YOK; yalnız korku_ekleme_golge.jsonl. config.KORKU_ADD_SHADOW (varsayılan True).
  Kaçırılan çıkış kontrolü (bot kapalıyken 16:00 geçtiyse): bar geçmişinden aynı kural yeniden hesaplanır, çıkış günü geçmişse hemen kapatılır.
"""
from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import aysonu_live as ay          # NYSE_HOLIDAYS, CAL_LAST_YEAR
import c3b_shadow as sh          # TZ="US", MARKET="NDX.INDX"
import caprev_shadow as cs
import kural_katalogu as kk

RULE = "KORKU"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "korku_live_state.json"
POLL_EVERY_S = 20
MIN_OPEN, MIN_LAST_HOUR, MIN_ENTRY = 570, 900, 960      # 09:30, 15:00, 16:00 ET
TWAP_TH_BP = -30.0
MAX_HOLD = 5
MIN_SESSION_BARS = 12
MAX_LATE_S = 600
EMERGENCY_SL = 0.13
FETCH_M30 = 400
ADD_LOSS_BP = 50.0
ADD_SHADOW_LOG = HERE / "korku_ekleme_golge.jsonl"


# ═════════════════════════ takvim ═════════════════════════

def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in ay.NYSE_HOLIDAYS


def opex_day(y: int, m: int) -> date:
    """Ayın 3. Cuması; tatilse önceki işlem günü."""
    first = date(y, m, 1)
    d = first + timedelta(days=(4 - first.weekday()) % 7 + 14)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def days_to_opex(d: date) -> int:
    """d'den sonraki (d dahil) ilk vade gününe kadar kalan işlem günü sayısı (vade günü = 0)."""
    ex = opex_day(d.year, d.month)
    if ex < d:
        y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
        ex = opex_day(y, m)
    k, cur = 0, d
    while cur < ex:
        cur += timedelta(days=1)
        if is_trading_day(cur):
            k += 1
    return k


def opex_veto(d: date) -> bool:
    return days_to_opex(d) in (0, 1, 2)


# ═════════════════════════ saf yardımcılar (test edilebilir) ═════════════════════════

def day_table(bars: list[dict]) -> dict[date, dict]:
    """bars [{t (UTC, bar açılışı), open, close}] → gün başına {p16, o15, twap, n}."""
    out: dict[date, dict] = {}
    for b in bars:
        d, m, wd = cs.to_local(b["t"], sh.TZ)
        if wd >= 5:
            continue
        r = out.setdefault(d, {"c": [], "p16": None, "o15": None, "t16": None})
        if MIN_OPEN <= m < MIN_ENTRY:
            r["c"].append(b["close"])
        if m == MIN_LAST_HOUR:
            r["o15"] = b["open"]
        elif m == MIN_ENTRY:
            r["p16"], r["t16"] = b["open"], b["t"]
    for r in out.values():
        r["n"] = len(r["c"])
        r["twap"] = sum(r["c"]) / len(r["c"]) if r["c"] else None
    return out


def find_signal(tab: dict[date, dict], today: date) -> dict | None:
    r = tab.get(today)
    if not is_trading_day(today) or r is None or r["p16"] is None or r["o15"] is None or r["twap"] is None:
        return None
    if r["n"] < MIN_SESSION_BARS:
        return None
    twap_bp = (r["p16"] / r["twap"] - 1.0) * 1e4
    if twap_bp > TWAP_TH_BP or not r["p16"] < r["o15"]:
        return None
    return {"p16": r["p16"], "o15": r["o15"], "twap": round(r["twap"], 3), "twap_bp": round(twap_bp, 2),
            "son_saat_bp": round((r["p16"] / r["o15"] - 1.0) * 1e4, 2), "t16": r["t16"]}


def xp_exit(tab: dict[date, dict], entry_day: date, today: date, now_min: int) -> tuple[str, date] | None:
    """XP: giriş gününden sonraki işlem günlerinin P16'ları sırayla; (neden, çıkış günü) ya da None (henüz değil).
    Bugünün P16'sı yalnız 16:00 barı görünmüşse (now_min ≥ 16:00) kullanılır."""
    ref = tab.get(entry_day, {}).get("p16")
    if ref is None:
        return None
    k, d = 0, entry_day
    while d < today:
        d += timedelta(days=1)
        if not is_trading_day(d):
            continue
        p = tab.get(d, {}).get("p16")
        if p is None:
            if d < today:
                continue                              # veri boşluğu: o günü atla (araştırma da veri olmayan günü saymaz)
            return None
        if d == today and now_min < MIN_ENTRY:
            return None
        k += 1
        if p > ref:
            return "yukselis", d
        if k >= MAX_HOLD:
            return "sure", d
        ref = p
    return None


def d1_add_signal(tab: dict[date, dict], entry_day: date, entry_ask: float, today: date, now_min: int) -> dict | None:
    """KR-03: giriş sonrası ilk işlem günü (D1) 16:00'da XP çıkmadı ∧ D1 P16 girişin ≥ ADD_LOSS_BP altında → sanal ek."""
    p0 = tab.get(entry_day, {}).get("p16")
    if p0 is None:
        return None
    d = entry_day
    while d < today:
        d += timedelta(days=1)
        if not is_trading_day(d):
            continue
        p1 = tab.get(d, {}).get("p16")
        if p1 is None:
            if d < today:
                continue
            return None
        if d == today and now_min < MIN_ENTRY:
            return None
        loss = (p1 / entry_ask - 1.0) * 1e4
        if p1 > p0 or loss > -ADD_LOSS_BP:
            return {"d1": str(d), "eklendi": False, "d1_bp": round(loss, 1)}
        spread = max(0.0, entry_ask - p0)
        return {"d1": str(d), "eklendi": True, "d1_bp": round(loss, 1), "ek_ask": round(p1 + spread, 3)}
    return None


def _shadow_append(rec: dict) -> None:
    try:
        with open(ADD_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _add_shadow(config, st: dict, p, tab, entry_day, today, mloc, ex) -> None:
    """Gölge: D1'de ek kararını bir kez yaz; ana XP çıkışında sanal ek birimin sonucunu yaz. Emir göndermez, hata yutulur."""
    if not bool(getattr(config, "KORKU_ADD_SHADOW", True)):
        return
    sh_st = st.setdefault("add_shadow", {})
    key = str(p.ticket)
    rec = sh_st.get(key)
    if rec is None:
        sig = d1_add_signal(tab, entry_day, float(p.price_open), today, mloc)
        if sig is None:
            return
        rec = sh_st[key] = {"ticket": p.ticket, "giris": str(entry_day), "giris_ask": float(p.price_open), **sig}
        _shadow_append({"kind": "d1_karar", **rec})
    if ex and rec.get("eklendi") and not rec.get("kapandi"):
        px = tab.get(ex[1], {}).get("p16")
        if px is not None:
            days = (date.fromisoformat(str(ex[1])) - date.fromisoformat(rec["d1"])).days
            r = (px / rec["ek_ask"] - 1.0) * 1e4 - 1.756 * days
            rec.update({"kapandi": True, "cikis": str(ex[1]), "ek_net_bp": round(r, 1)})
            _shadow_append({"kind": "ek_kapanis", **rec})
    if ex and (not rec.get("eklendi") or rec.get("kapandi")):
        sh_st.pop(key, None)


def stop_price(ask: float, digits: int, frac: float = EMERGENCY_SL) -> float:
    return round(ask * (1.0 - frac), digits)


def _bars(mt5, sym: str, offset_fn) -> list[dict]:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, FETCH_M30)
    return cs._m15_utc(rates, offset_fn(sym)) if rates is not None and len(rates) else []


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_d": None}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


_last_poll = 0.0
_last_exit_poll = 0.0


# ═════════════════════════ çıkış (ana döngüde frenden ÖNCE) ═════════════════════════

def manage_exits(mt5, config, log, send_order, offset_fn, resolve_symbol, now: float | None = None) -> None:
    global _last_exit_poll
    now = time.time() if now is None else now
    if now - _last_exit_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_exit_poll = now
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    pos = kk.open_positions(mt5, config, RULE, sym)
    if not pos:
        return
    tab = day_table(_bars(mt5, sym, offset_fn))
    today, mloc, _ = cs.to_local(now, sh.TZ)
    st = _load_state()
    for p in pos:
        entry_day = cs.to_local(p.time - offset_fn(sym), sh.TZ)[0]
        ex = xp_exit(tab, entry_day, today, mloc)
        try:
            _add_shadow(config, st, p, tab, entry_day, today, mloc, ex)
        except Exception as e:                      # gölge asla canlı çıkışı engellemez
            log.warning("KORKU ekleme gölgesi hatası: %s", e)
        if ex:
            why = f"XP {ex[0]} ({ex[1]})" + ("" if ex[1] == today else " — geç kontrol")
            kk.close(mt5, config, log, send_order, RULE, p, why)
    _save_state(st)


# ═════════════════════════ giriş ═════════════════════════

def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    today, mloc, wd = cs.to_local(now, sh.TZ)
    if wd >= 5 or not (MIN_ENTRY <= mloc <= MIN_ENTRY + MAX_LATE_S // 60):
        return
    if today.year > ay.CAL_LAST_YEAR:
        log.error("KORKU: NYSE takvimi %d sonrası tanımlı değil — aysonu_live.NYSE_HOLIDAYS'i güncelle", ay.CAL_LAST_YEAR)
        return
    st = _load_state()
    if st.get("last_d") == str(today):
        return
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    tab = day_table(_bars(mt5, sym, offset_fn))
    if tab.get(today, {}).get("p16") is None:
        return                                                                 # 16:00 barı henüz yok
    st["last_d"] = str(today)
    _save_state(st)
    sig = find_signal(tab, today)
    if sig is None:
        return
    rec = {"day": str(today), **{k: v for k, v in sig.items() if k != "t16"}, "latency_s": round(now - sig["t16"], 1),
           "vadeye_gun": days_to_opex(today)}
    if opex_veto(today):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "OPEX vetosu (vadeye 0–2 işlem günü)", **rec})
        log.info("KORKU sinyali OPEX vetosuyla atlandı (vadeye %d işlem günü): %s", rec["vadeye_gun"], rec)
        return
    if now - sig["t16"] > MAX_LATE_S:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "geç tespit", **rec})
        return
    if kk.open_positions(mt5, config, RULE, sym):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "açık KORKU pozisyonu var (tek pozisyon)", **rec})
        return
    _enter(mt5, config, log, sym, rec, send_order, mk_comment, autotrading_ok, log_trade)


def _enter(mt5, config, log, sym, rec, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    lot = kk.lot_of(config, RULE)
    sl = stop_price(ask, info.digits, float(getattr(config, "KORKU_LIVE_EMERGENCY_SL", EMERGENCY_SL)))
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}", **rec})
        log.warning("KORKU atlandı: %s üzerinde açık kural lotu %.2f + %.2f > tavan %.2f", sym, open_lot, lot, cap)
        return
    if not autotrading_ok():
        log.error("KORKU AutoTrading KAPALI — emir gönderilmedi")
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "autotrading kapalı", **rec})
        return
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, 0.0, "KORKU T30")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl, "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ KORKU emir reddedildi retcode=%s", rc)
        return
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · acil SL {sl} · TWAP {rec['twap_bp']} bp · son saat {rec['son_saat_bp']} bp · "
                                f"ticket {ticket}", {"gecikme_s": rec["latency_s"], "vadeye_gun": rec["vadeye_gun"]})
    log_trade("LIVE", "NDX.INDX:BUY:KORKU", sym, "BUY", ask, 0.0, sl, ["korku_t30"], f"ticket={ticket}")
