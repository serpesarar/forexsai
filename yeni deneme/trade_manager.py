"""Kanıta dayalı işlem-SONRASI yönetim + SELL sabır kapısı.

Kanıt: research/trade_mgmt_ndx/REPORT.md + results_multi_symbol.json
(223 NDX + 122 DAX gerçek MT5 işlemi, 1m sızıntısız replay, haftalık
dilim doğrulamalı):

  * NDX BUY  → BE@30dk + kazananı-koştur (TP kaldır, 0.6R iz süren SL)
               Δ+29.5R [16.4,43.5] P=%100; 4 haftanın hiçbirinde negatif değil.
  * GDAXI BUY→ yalnız kazananı-koştur (BE DAX'ta nötr — Δ+12.1R P=%98.3).
  * NDX SELL (vixreg) → 10dk sabır kapısı: sinyalden 10dk sonra işlem hâlâ
               "yaşıyorsa" (±TP/SL menzili görülmemiş) ve aleyhte hareket
               <0.3R ise gir. Kanıt: Δ+39.3R (132 SELL'in 63'ü ilk 10dk'da
               kendini SL'e taşıyordu). BUY'A UYGULANMAZ (orada −41R).
  * SELL pozisyonlarına BE/trail UYGULANMAZ (kanıt: NDX SELL BE Δ−7.5R).
  * USOIL/XAU: kanıt eşiği geçilemedi — dokunulmaz.
  * 2026-08-01: CHREV BUY pozisyonları da aynı sembol-kurallarıyla yönetilir
    (MGMT_INCLUDE_CHREV=False ile eski davranış).

Durum `mgmt_state.json`'da (ticket bazlı orijinal geometri; restart-dayanıklı).
Yaş ölçümü first_seen bazlı (broker saat-dilimi kaymasından bağımsız;
restart'ta BE gecikir — konservatif, kanıt BE45'te de pozitif).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import config
import phase_rules as pr

STATE_FILE = Path(__file__).resolve().parent / "mgmt_state.json"

BE_MINUTES = getattr(config, "MGMT_BE_MINUTES", 30)
TRAIL_R = getattr(config, "MGMT_TRAIL_R", 0.6)
# Kazananı-koştur yalnız kanıt-benzeri geometride (araştırma tp/sl≈0.73;
# S/R girişleri bazen TP'yi çok yakına koyar — ör. tp16/sl91=0.18 — orada
# 0.6R trail 16 puanlık kârı korumak için ~55 puan geri-verme payı bırakır,
# kanıt bu geometriyi KAPSAMIYOR → TP'ye dokunma, normal TP'de çık).
RUNNER_MIN_TP_SL_RATIO = getattr(config, "MGMT_RUNNER_MIN_TP_SL_RATIO", 0.4)
PATIENCE_MIN = getattr(config, "VIXREG_SELL_PATIENCE_MIN", 10)
PATIENCE_FLOOR_R = 0.3          # aleyhte 0.3R'dan fazla gitmişse teyit yok

# hangi (forexsai_sym, magic'ler) BUY pozisyonları yönetilir + BE uygulanır mı
# 2026-08-01: CHREV magic'i de kapsama alındı (MGMT_INCLUDE_CHREV=False ile
# çıkar). Gerekçe: kanıt veri seti (trade_mgmt_ndx, 223 NDX + 122 DAX gerçek
# işlem) CHREV işlemlerini de İÇERİYORDU ve kurallar sembol+yön (NDX BUY /
# DAX BUY) seviyesinde doğrulandı; canlıda CHREV ort. kayıp 610$ vs ort.
# kazanç 390$ — kayıp kuyruğunu BE, kazanç tarafını koştur düzeltir.
# SELL tarafı bilinçli KAPSAM DIŞI (BE/trail SELL'de Δ−7.5R; sabır kapısı
# 2026-07-28 OOS kanıtıyla varsayılan kapalı — genellenmedi).


def _managed_magics() -> set:
    m = {config.MAGIC_NUMBER, getattr(config, "VIX_REGIME_MAGIC", -1)}
    if getattr(config, "MGMT_INCLUDE_CHREV", True):
        m.add(getattr(config, "CHANNEL_REVERSION_MAGIC", -1))
    return m


def _usoil_breakout_magics() -> set:
    if not getattr(config, "MGMT_INCLUDE_USOIL_BREAKOUT", True):
        return set()
    return {getattr(config, "USOIL_BREAKOUT_MAGIC", -1)}


_RULES = {
    "NDX.INDX":    {"be": True,  "magics": _managed_magics},
    "GDAXI.INDX":  {"be": False, "magics": _managed_magics},
    # 2026-08-06: USOIL BREAKOUT scope — kazananı-koştur (BE YOK, NDX'e özel
    # 30dk kuralı burada anlamsız). Kanıt: research/usoil_breakout_2026-08-06/
    # RAPOR.md — sabit TP=1xATR kronolojik TEST'te -0.026R/işlem (breakeven
    # altı), AYNI giriş kuralıyla BE(1R-kâr)+trail(1.0xATR) TEST'te +0.084R/
    # işlem (n=188). Bu scope'un geometrisi (TP=SL=1.0xATR, oran 1.0) zaten
    # RUNNER_MIN_TP_SL_RATIO eşiğinin (0.4) üstünde — orig_tp'ye ulaşınca
    # mevcut "kazananı koştur" mekanizması otomatik devreye girer.
    "USOIL.FOREX": {"be": False, "magics": _usoil_breakout_magics,
                    "trail_r": getattr(config, "MGMT_USOIL_TRAIL_R", 1.0)},
}

_state: dict | None = None
_pending_sells: list[dict] = []          # sabır kapısı kuyruğu (in-memory)


def _load_state() -> dict:
    global _state
    if _state is None:
        try:
            _state = json.loads(STATE_FILE.read_text())
        except Exception:
            _state = {}
    return _state


def _save_state() -> None:
    try:
        STATE_FILE.write_text(json.dumps(_state or {}, indent=1))
    except Exception:
        pass


def _modify(mt5, log, pos, new_sl: float, new_tp: float, why: str) -> bool:
    info = mt5.symbol_info(pos.symbol)
    digits = info.digits if info else 2
    req = {"action": mt5.TRADE_ACTION_SLTP, "position": pos.ticket,
           "symbol": pos.symbol, "sl": round(new_sl, digits),
           "tp": round(new_tp, digits) if new_tp else 0.0}
    res = mt5.order_send(req)
    ok = bool(res and res.retcode == mt5.TRADE_RETCODE_DONE)
    if ok:
        log.info("[MGMT] ✅ %s ticket=%s SL→%.2f TP→%s (%s)",
                 pos.symbol, pos.ticket, req["sl"], req["tp"] or "KALDIRILDI", why)
    else:
        log.warning("[MGMT] ❌ modify reddedildi ticket=%s rc=%s (%s)",
                    pos.ticket, getattr(res, "retcode", "?"), why)
    return ok


def manage_positions(mt5, log, resolve_symbol) -> None:
    """Her taramada çağrılır: BE@30dk (NDX) + kazananı-koştur (NDX+DAX, BUY)."""
    if not getattr(config, "TRADE_MGMT_ENABLED", True) or not config.LIVE_TRADING:
        return
    st = _load_state()
    now = time.time()
    live_tickets = set()

    for fxs_sym, rule in _RULES.items():
        mt5_symbol = resolve_symbol(fxs_sym)
        if not mt5_symbol:
            continue
        magics = rule["magics"]()
        for pos in (mt5.positions_get(symbol=mt5_symbol) or []):
            if pos.magic not in magics or pos.type != mt5.ORDER_TYPE_BUY:
                continue                 # kanıt yalnız BUY yönetimi için
            key = str(pos.ticket)
            live_tickets.add(key)
            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick is None:
                continue
            bid = tick.bid

            if key not in st:            # ilk görüş: orijinal geometriyi kaydet
                if not pos.sl or not pos.tp:
                    continue             # geometri yoksa yönetme
                st[key] = {"first_seen": now, "entry": pos.price_open,
                           "orig_sl": pos.sl, "orig_tp": pos.tp,
                           "sl_dist": abs(pos.price_open - pos.sl),
                           "phase": "normal", "symbol": fxs_sym}
                _save_state()
            s = st[key]
            sl_dist = s["sl_dist"]
            if sl_dist <= 0:
                continue
            trail_r = rule.get("trail_r", TRAIL_R)

            # ── KAZANANI KOŞTUR: fiyat orijinal TP'ye vardı → TP kaldır, trail
            #    (yalnız kanıt-benzeri geometri: tp_dist/sl_dist ≥ eşik)
            tp_sl_ratio = abs(s["orig_tp"] - s["entry"]) / sl_dist
            if (s["phase"] == "normal" and bid >= s["orig_tp"]
                    and tp_sl_ratio >= RUNNER_MIN_TP_SL_RATIO):
                trail_sl = max(pos.sl or 0, s["orig_tp"] - trail_r * sl_dist)
                if _modify(mt5, log, pos, trail_sl, 0.0, "runner: TP kaldırıldı, trail başladı"):
                    s["phase"] = "run"
                    _save_state()
                continue
            if s["phase"] == "run":
                new_sl = bid - trail_r * sl_dist
                info = mt5.symbol_info(mt5_symbol)
                step = (info.point * 10) if info else 0.5
                if new_sl > (pos.sl or 0) + step:      # yalnız lehte, spam'siz
                    _modify(mt5, log, pos, new_sl, 0.0, "runner trail")
                continue

            # ── BAŞABAŞ STOP ──────────────────────────────────────────────
            # FAZ 0.1 (2026-08-14): koşulsuz BE@30dk KALDIRILDI.
            # Kanıt (aynı 133 işlemin bar-bar karşı-olgusalı): BE'siz WR %72.7
            # / +3.078$ · koşulsuz BE ile %39.4 / +1.282$ — stop, pozisyon daha
            # lehe gitmeden başabaşa çekiliyor ve normal salınım onu vuruyordu.
            # Yeni kural: BE yalnız MFE ≥ 0.5×SL mesafesi görüldükten SONRA.
            # Eski davranış: config.MGMT_BE_MODE = "time30".
            if rule["be"]:
                mfe = max(float(s.get("mfe") or 0.0), bid - s["entry"])
                if mfe != s.get("mfe"):
                    s["mfe"] = mfe
                    _save_state()
                mode = str(pr.flag(config, "MGMT_BE_MODE"))
                if pr.be_should_arm(mode, mfe, sl_dist, now - s["first_seen"],
                                    BE_MINUTES,
                                    float(pr.flag(config, "MGMT_BE_MFE_R"))):
                    if bid > s["entry"] and (pos.sl or 0) < s["entry"]:
                        why = ("BE (MFE≥%.1fR)" % float(pr.flag(config, "MGMT_BE_MFE_R"))
                               if mode == "conditional_mfe" else "BE@30dk")
                        if _modify(mt5, log, pos, s["entry"], pos.tp, why):
                            s["phase"] = "be"
                            _save_state()

    # ── FAZ 0.2: ZAMAN STOPU — 120 dk'da ne TP ne SL vurulmadıysa kapat ────
    try:
        _time_stop_pass(mt5, log, resolve_symbol, st, now, live_tickets)
    except Exception as exc:                                    # fail-open
        log.warning("[MGMT] zaman stopu hatası: %s", exc)

    # kapanan pozisyonların durumunu temizle
    stale = [k for k, v in st.items() if k not in live_tickets
             and now - v.get("first_seen", 0) > 86400]
    if stale:
        for k in stale:
            st.pop(k, None)
        _save_state()


# ─── FAZ 0.2 — zaman stopu (2026-08-14) ─────────────────────────────────────
# Kanıt: 133 işlemin medyan süresi 47 dk; 10+ saat açık kalan 2 "zombi" işlem
# 550$'er kaybetti. 120 dk'da karara varmamış pozisyon piyasadan kapatılır.
# Kapsam: MGMT_TIME_STOP_SYMBOLS (varsayılan NDX) · her iki yön · bot magic'leri.
# Yaş ölçümü first_seen bazlı → restart'ta gecikir (konservatif, kasten).

def _all_bot_magics() -> set:
    m = _managed_magics() | _usoil_breakout_magics()
    for name in ("MAGIC_NUMBER", "CHANNEL_REVERSION_MAGIC", "VIX_REGIME_MAGIC"):
        v = getattr(config, name, None)
        if v:
            m.add(v)
    m.add(getattr(config, "MAGIC_NUMBER", 0) + 4)      # DAYCOMBO
    return {x for x in m if x and x > 0}


def _close_at_market(mt5, log, pos, why: str) -> bool:
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return False
    is_buy = pos.type == mt5.ORDER_TYPE_BUY
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol,
           "volume": float(pos.volume), "position": pos.ticket,
           "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
           "price": tick.bid if is_buy else tick.ask,
           "deviation": getattr(config, "DEVIATION_POINTS", 30),
           "magic": pos.magic, "comment": "fxs timestop",
           "type_time": mt5.ORDER_TIME_GTC,
           "type_filling": mt5.ORDER_FILLING_IOC}
    res = mt5.order_send(req)
    ok = bool(res and res.retcode == mt5.TRADE_RETCODE_DONE)
    if ok:
        log.info("[MGMT] ⏱ %s ticket=%s kapatıldı (%s, kâr=%.2f)",
                 pos.symbol, pos.ticket, why, float(pos.profit))
    else:
        log.warning("[MGMT] ❌ zaman stopu kapatma reddedildi ticket=%s rc=%s",
                    pos.ticket, getattr(res, "retcode", "?"))
    return ok


def _time_stop_pass(mt5, log, resolve_symbol, st: dict, now: float,
                    live_tickets: set) -> None:
    minutes = float(pr.flag(config, "MGMT_TIME_STOP_MIN") or 0)
    if minutes <= 0:
        return
    magics = _all_bot_magics()
    for fxs_sym in pr.flag(config, "MGMT_TIME_STOP_SYMBOLS"):
        mt5_symbol = resolve_symbol(fxs_sym)
        if not mt5_symbol:
            continue
        for pos in (mt5.positions_get(symbol=mt5_symbol) or []):
            if pos.magic not in magics:
                continue
            key = str(pos.ticket)
            live_tickets.add(key)
            if key not in st:
                st[key] = {"first_seen": now, "entry": pos.price_open,
                           "orig_sl": pos.sl, "orig_tp": pos.tp,
                           "sl_dist": abs(pos.price_open - (pos.sl or pos.price_open)),
                           "phase": "normal", "symbol": fxs_sym}
                _save_state()
                continue                     # yaşı bu taramadan itibaren say
            s = st[key]
            if s.get("phase") == "run":
                continue                     # koşan kazanan — zaman stopu vurmaz
            age = now - float(s.get("first_seen") or now)
            if pr.time_stop_due(age, minutes):
                if _close_at_market(mt5, log, pos,
                                    f"zaman stopu {minutes:.0f}dk"):
                    s["phase"] = "time_stopped"
                    _save_state()


# ─── SELL sabır kapısı (vixreg NDX) ──────────────────────────────────────────

def _skip_log(scope_key, px, tp_d, sl_d, reason, extra=None):
    """Kapının elediği SELL niyetini kaydet (gevşetme kararı için kanıt)."""
    try:
        import forexsai_demo_bot as bot
        sym = scope_key.split(":")[0]
        bot.log_gate_skip(scope_key, "", sym, "SELL", px, reason,
                          tp_dist=tp_d, sl_dist=sl_d, extra=extra)
    except Exception:
        pass


def queue_sell(log, scope_key: str, signal_px: float, tp_dist: float,
               sl_dist: float, opener) -> None:
    """SELL sinyalini hemen açma — 10dk sabır kuyruğuna al."""
    if any(p["scope_key"] == scope_key for p in _pending_sells):
        return
    _pending_sells.append({"scope_key": scope_key, "signal_px": signal_px,
                           "signal_time": time.time(), "tp_dist": tp_dist,
                           "sl_dist": sl_dist, "opener": opener})
    log.info("[SABIR] %s SELL kuyruğa alındı @%.2f — %ddk sonra teyitli karar",
             scope_key, signal_px, PATIENCE_MIN)


def process_pending(mt5, log, mt5_symbol: str) -> None:
    """Kuyruktaki SELL niyetlerini değerlendir (her taramada çağrılır)."""
    if not _pending_sells:
        return
    now = time.time()
    done = []
    for p in _pending_sells:
        age = now - p["signal_time"]
        if age < PATIENCE_MIN * 60:
            continue
        done.append(p)
        if age > 30 * 60:                 # bayat niyet — açma
            log.info("[SABIR] %s bayat (%.0fdk) — iptal", p["scope_key"], age / 60)
            _skip_log(p["scope_key"], p["signal_px"], p["tp_dist"], p["sl_dist"],
                      "patience_stale", {"age_min": round(age / 60, 1)})
            continue
        # sinyalden bu yana 1m yüksek/alçak — "işlem bizsiz bitti mi?"
        n = max(2, int(age // 60) + 2)
        rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M1, 0, n)
        tick = mt5.symbol_info_tick(mt5_symbol)
        if rates is None or tick is None:
            log.warning("[SABIR] %s veri yok — fail-open GİRİLMEDİ", p["scope_key"])
            continue
        hi = max(float(r["high"]) for r in rates)
        lo = min(float(r["low"]) for r in rates)
        spx, sld, tpd = p["signal_px"], p["sl_dist"], p["tp_dist"]
        # Donuk piyasa koruması (2026-07-23): 10+ dk sonra bid hâlâ sinyal
        # fiyatının BİREBİR aynısıysa piyasa kapalı/donuk demektir (NDX 21-22
        # UTC molasında bid 29000.10'da sabitti → her açma denemesi 10018
        # 'market closed' reddi yedi). Açma, iptal et.
        if abs(tick.bid - spx) < 1e-9 and hi == lo:
            log.info("[SABIR] %s fiyat %ddk'dır DONUK (%.2f) — piyasa kapalı "
                     "görünümü, İPTAL", p["scope_key"], PATIENCE_MIN, spx)
            continue          # donuk piyasa = sinyal değil, kanıt kaydına girmez
        if hi >= spx + sld or lo <= spx - tpd:
            log.info("[SABIR] %s ilk %ddk'da ±menzil görüldü (işlem bizsiz "
                     "biterdi) — İPTAL", p["scope_key"], PATIENCE_MIN)
            _skip_log(p["scope_key"], spx, tpd, sld, "patience_range_hit",
                      {"hi": round(hi, 2), "lo": round(lo, 2)})
            continue
        if tick.bid >= spx + PATIENCE_FLOOR_R * sld:
            log.info("[SABIR] %s teyit yok (aleyhte ≥%.1fR) — İPTAL",
                     p["scope_key"], PATIENCE_FLOOR_R)
            _skip_log(p["scope_key"], spx, tpd, sld, "patience_no_confirm",
                      {"bid": round(tick.bid, 2)})
            continue
        log.info("[SABIR] %s teyit TAMAM (%.0fdk yaşadı) → giriş", p["scope_key"], age / 60)
        try:
            p["opener"]()
        except Exception as exc:
            log.exception("[SABIR] opener hata: %s", exc)
    for p in done:
        _pending_sells.remove(p)
