"""c3b_live.py — NDX RSI2 geri dönüşü (C3b) CANLI icra (demo hesap).

KART: backend/data/evolution/go_live_cards/ndx_c3b_rsi2_upexit.json — 6/6, n=155, isabet %78,1, ort +65 bp, 11/11 yıl artı.
KULLANICI KARARI 2026-11-08: "pozitif olanların hepsini kendilerine özel lotla canlıya bağla". Lot: kural_katalogu (2.0).
Kapatma: config.C3B_LIVE = False.

KURAL (c3b_shadow ile BİREBİR; sinyal ve seri fonksiyonları oradan alınır):
  S = 15:30 ET M30 barından önceki barın kapanışı, E = 15:30 barının açılışı. RSI2(S serisi) < 10 → E'de uzun.
  Çıkış: ilk S_t > S_{t−1} günü 15:30 açılışında; en geç 5 işlem günü sonra. Tek pozisyon; çıkış günü yeni sinyal
  varsa aynı açılışta yeniden girilir. TP yok.
  DOZ (2026-11-16, research/ndx_10y_1m_20261116 H5 + EK1-c): opsiyon vade haftasında (ayın 3. Cuması ve önceki 4 gün) giriş
  lotu yarıya iner. Dukascopy 1m: vade haftası ESKİ −19 bp (n 8) / YENİ −17 bp (n 18) vs diğer +74 / +99; kitap aylık Sharpe
  1,82 → 1,95 (P 0,94, iki dönemde de artı). Sınıf B− (TS-01 O4'ün yeniden ölçümü). Kapatma: config.C3B_OPEX_HALF = False.
  TEK FARK: kartta stop yok; broker tarafında ACİL DURUM SL'i (varsayılan %10, `C3B_LIVE_EMERGENCY_SL`) konur — geçmişteki en
  kötü işlem −%6,8 olduğundan örneklemde hiçbir işlemi değiştirmez; yalnız bot ölürse sınırsız zarara karşı sigortadır.
  KULLANICI KARARI 2026-11-24 (research/c3b_derin_20261124/RAPOR.md, kart go_live_cards/ndx_c3b_e16_k1.json):
  E16 — karar yine 15:30 fiyatıyla verilir, GİRİŞ 16:00 ET'de (M30 16:00 barı açılışı). Çıkış 15:30'da kalır; çıkış günü
        yeni sinyal varsa 16:00'da yeniden girilir. Duka 2018-26 Calmar ×1,30, Sharpe 1,50 → 1,61 (P 0,96), MT5 NAS100 ×1,56.
        Kapatma: config.C3B_ENTRY_1600 = False (eski 15:30 girişi).
  K1 — lot dozu: stres (dünkü VIX ≥ 18,4) ∧ derin (z5 ≤ −1,072) işlemi C3B_K1_VD_LOT (3.0), diğerleri C3B_K1_OTHER_LOT (1.0).
        Oran 1 : ⅓, ölçek taban maks. düşüşüne eşitlendi (×1,54 → 3,09 / 1,03, aşağı yuvarlandı). Duka eşit riskte net +%30,
        zararlıların toplamı −%50, kâr +%11; işlem sayısı aynı (132). ⚠️ Kanıt yalnız 2018-26 NDX'te; taze 38 araçta tutmadı (X).
        VIX geçmişi yoksa işlem "stres değil" sayılır (küçük lot). Vade haftası yarım lotu bunun üstüne uygulanır.
        Yoğunlaşma tavanı dolarsa lot kalan kapasiteye indirilir (≥ C3B_MIN_FIT_LOT), altındaysa atlanır.
        K2 (0,25 + 0,375·stres + 0,375·derin) yalnız GÖLGE: giriş olayına `k2_lot_golge` yazılır, emir değişmez.
        Kapatma: config.C3B_DOSE_K1 = False (sabit C3B_LIVE_LOT).
"""
from __future__ import annotations

import json
import math
import time
from datetime import date
from pathlib import Path

import c3b_shadow as sh
import caprev_shadow as cs
import kural_katalogu as kk

RULE = "C3B"
HERE = Path(__file__).resolve().parent
STATE_FILE = HERE / "c3b_live_state.json"
POLL_EVERY_S = 30
EMERGENCY_SL = 0.10
OPEX_LOT_MULT = 0.5
ENTRY_1600_MIN = 960            # 16:00 ET
BAR_S = 1800
STRESS_VIX = 18.4
Z5_TH = -1.072
Z5_VOL_N = 20
K1_VD_LOT = 3.0
K1_OTHER_LOT = 1.0
K2_SCALE_LOT = 3.09             # taban 2,0 × eşit risk ölçeği 1,543 (yalnız gölge)
MIN_FIT_LOT = 0.5


def z5(values: list[float], i: int) -> float | None:
    """z5 = (S_i/S_{i−5} − 1) / (dvol·√5); dvol = i−1'e kadarki son 20 günlük getirinin std'si (araştırma motoru.z5_of)."""
    if i < Z5_VOL_N + 1 or i < 5:
        return None
    rets = [values[k] / values[k - 1] - 1 for k in range(i - Z5_VOL_N, i)]
    m = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / (len(rets) - 1))
    if sd <= 0:
        return None
    return (values[i] / values[i - 5] - 1) / (sd * math.sqrt(5))


def dose(vix_prev: float | None, z: float | None, vd_lot: float = K1_VD_LOT, other_lot: float = K1_OTHER_LOT) -> dict:
    """K1 dozu + K2 gölge lotu. VIX/z5 yoksa koşul yanlış sayılır (küçük lot)."""
    stress = vix_prev is not None and vix_prev >= STRESS_VIX
    deep = z is not None and z <= Z5_TH
    return {"stress": stress, "deep": deep, "vd": stress and deep, "lot": vd_lot if (stress and deep) else other_lot,
            "k2_lot_golge": round(K2_SCALE_LOT * (0.25 + 0.375 * stress + 0.375 * deep), 2)}


def opex_week(d: date) -> bool:
    """Ayın 3. Cuması ve ondan önceki 4 gün (Pzt–Cum vade haftası)."""
    first = date(d.year, d.month, 1)
    fri3 = first.toordinal() + (4 - first.weekday()) % 7 + 14
    return fri3 - 4 <= d.toordinal() <= fri3


def entry_lot(base: float, day: date, enabled: bool = True, step: float = 0.01) -> float:
    """Doz: vade haftasında base × OPEX_LOT_MULT (lot adımına yuvarlı)."""
    if enabled and opex_week(day):
        return round(round(base * OPEX_LOT_MULT / step) * step, 8)
    return base


def fit_lot(lot: float, open_lot: float, cap: float, min_lot: float, step: float = 0.01) -> float | None:
    """Tavan dolarsa lotu kalan kapasiteye indir; kalan < min_lot ise None (atla)."""
    room = cap - open_lot
    if lot <= room + 1e-9:
        return lot
    fit = math.floor(room / step + 1e-9) * step
    return round(fit, 8) if fit >= min_lot - 1e-9 else None


def _vix_prev(day: date) -> float | None:
    """Gölge modülünün VIX geçmişi (salt okunur; aynı taramada c3b_shadow günceller)."""
    try:
        return cs.vix_features(sh._load_state().get("vix_hist", {}), day, None)["vix_prev"]
    except Exception:
        return None

_last_poll = 0.0


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_d": None, "pos": {}}


def _save_state(st: dict) -> None:
    kk.save_json(STATE_FILE, st)


def should_exit(series: list[dict], entry_idx: int, i: int) -> str | None:
    """Pozisyon çıkış nedeni: 'yukselis' (girişten sonra herhangi bir gün S_t > S_{t−1}), 'sure' (≥ MAX_HOLD) ya da None.
    Bot kapalıyken kaçan yükseliş günü de sayılır (geç çıkış, kayıtta gecikme görünür)."""
    for k in range(entry_idx + 1, i + 1):
        if series[k]["S"] > series[k - 1]["S"]:
            return "yukselis"
    return "sure" if i - entry_idx >= sh.MAX_HOLD else None


def _entry_index(series: list[dict], d_iso: str) -> int | None:
    for k, s in enumerate(series):
        if str(s["d"]) == d_iso:
            return k
    return None


def manage_and_enter(mt5, config, log, series: list[dict], today: date, st: dict, now: float, sym: str, off: int,
                     send_order, mk_comment, autotrading_ok, log_trade) -> None:
    """Bugünün 15:30 barı göründüğünde: önce çıkış, sonra giriş (tek pozisyon)."""
    i = len(series) - 1
    day = series[i]
    rsi = sh.rsi2([s["S"] for s in series])
    for pos in kk.open_positions(mt5, config, RULE, sym):
        meta = st["pos"].get(str(pos.ticket))
        if meta is None:       # bot yeniden başladı: giriş gününü pozisyon zamanından türet
            meta = {"d": str(cs.to_local(pos.time - off, sh.TZ)[0])}
        k0 = _entry_index(series, meta["d"])
        why = "giriş günü seride yok" if k0 is None else should_exit(series, k0, i)
        if why and kk.close(mt5, config, log, send_order, RULE, pos, why):
            st["pos"].pop(str(pos.ticket), None)
    if rsi[i] >= sh.RSI_TH:
        return
    late = now - day["t"]
    z = z5([s["S"] for s in series], i)
    rec = {"day": str(day["d"]), "rsi2": round(rsi[i], 2), "S": day["S"], "E": day["E"], "latency_s": round(late, 1),
           "z5": None if z is None else round(z, 3), "vix_prev": _vix_prev(day["d"]), "t_1530": day["t"]}
    if kk.open_positions(mt5, config, RULE, sym):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "açık C3b pozisyonu var (tek pozisyon)", **rec})
        return
    e16 = bool(getattr(config, "C3B_ENTRY_1600", True))
    if late > (BAR_S + sh.MAX_LATE_S if e16 else sh.MAX_LATE_S):     # E16'da yalnız 16:00 girişine yetişmek gerekir
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "geç tespit", **rec})
        return
    if e16:
        st["pending"] = rec                                     # E16: giriş 16:00 barında (poll → _try_pending)
        kk.append_event({"kind": "pending", "rule": RULE, "reason": "16:00 girişi bekleniyor", **rec})
        log.info("C3b sinyal %s RSI2=%.1f z5=%s VIX(dün)=%s → giriş 16:00 ET", rec["day"], rec["rsi2"], rec["z5"], rec["vix_prev"])
        return
    _enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade)


def _try_pending(mt5, config, log, st: dict, today: date, now: float, sym: str, send_order, mk_comment, autotrading_ok,
                 log_trade) -> bool:
    """16:00 ET girişi. True → durum değişti (kaydet)."""
    rec = st.get("pending")
    if not rec:
        return False
    if rec["day"] != str(today):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "16:00 girişi kaçtı (gün değişti)", **rec})
        st["pending"] = None
        return True
    t16 = rec["t_1530"] + BAR_S
    if now < t16:
        return False
    rec = {**rec, "latency_s": round(now - t16, 1), "entry": "1600"}
    st["pending"] = None
    if now - t16 > sh.MAX_LATE_S:
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "16:00 girişinde geç tespit", **rec})
        return True
    if kk.open_positions(mt5, config, RULE, sym):
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "açık C3b pozisyonu var (tek pozisyon)", **rec})
        return True
    _enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade)
    return True


def _enter(mt5, config, log, sym, rec, st, now, send_order, mk_comment, autotrading_ok, log_trade) -> None:
    tick, info = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if tick is None or info is None:
        return
    ask = round(tick.ask, info.digits)
    step = float(getattr(info, "volume_step", 0.01) or 0.01)
    base = kk.lot_of(config, RULE)
    dz = dose(rec.get("vix_prev"), rec.get("z5"), float(getattr(config, "C3B_K1_VD_LOT", K1_VD_LOT)),
              float(getattr(config, "C3B_K1_OTHER_LOT", K1_OTHER_LOT)))
    if bool(getattr(config, "C3B_DOSE_K1", True)):
        base = dz["lot"]
    rec.update({"stres": dz["stress"], "derin": dz["deep"], "vd": dz["vd"], "k2_lot_golge": dz["k2_lot_golge"],
                "doz": "K1" if bool(getattr(config, "C3B_DOSE_K1", True)) else "sabit"})
    lot = entry_lot(base, date.fromisoformat(rec["day"]), bool(getattr(config, "C3B_OPEX_HALF", True)), step)
    rec["opex_week"] = opex_week(date.fromisoformat(rec["day"]))
    sl = round(ask * (1 - float(getattr(config, "C3B_LIVE_EMERGENCY_SL", EMERGENCY_SL))), info.digits)
    ok_c, open_lot, cap = kk.concentration_ok(mt5, config, sym, lot)
    if not ok_c:
        fit = fit_lot(lot, open_lot, cap, float(getattr(config, "C3B_MIN_FIT_LOT", MIN_FIT_LOT)), step)
        if fit is None:
            kk.append_event({"kind": "skip", "rule": RULE, "reason": f"yoğunlaşma tavanı {open_lot}+{lot}>{cap}", **rec})
            log.warning("C3b atlandı: %s üzerinde açık kural lotu %.2f + %.2f > tavan %.2f", sym, open_lot, lot, cap)
            return
        log.warning("C3b lotu tavan için %.2f → %.2f indirildi (açık %.2f, tavan %.2f)", lot, fit, open_lot, cap)
        rec["lot_istenen"] = lot
        lot = fit
    if not autotrading_ok():
        log.error("C3b AutoTrading KAPALI — emir gönderilmedi")
        kk.append_event({"kind": "skip", "rule": RULE, "reason": "autotrading kapalı", **rec})
        return
    ok, ticket, rc = kk.buy(mt5, config, log, send_order, mk_comment, RULE, sym, lot, ask, sl, 0.0, "C3b NDX RSI2")
    kk.append_event({"kind": "entry", "rule": RULE, "ok": ok, "retcode": rc, "ticket": ticket, "ask": ask, "sl": sl,
                     "lot": lot, **rec})
    if not ok:
        log.error("[CANLI] ❌ C3b emir reddedildi retcode=%s", rc)
        return
    st["pos"][str(ticket)] = {"d": rec["day"], "entry_t": now}
    kk.announce_open(log, RULE, f"{sym} BUY {lot} lot @ {ask} · acil SL {sl} · RSI2={rec['rsi2']} · ticket {ticket}",
                     {"gecikme_s": rec["latency_s"], "doz": rec["doz"], "stres∧derin": rec["vd"], "z5": rec.get("z5"),
                      "vix_dun": rec.get("vix_prev"), "k2_golge_lot": rec["k2_lot_golge"]})
    log_trade("LIVE", "NDX.INDX:BUY:C3B", sym, "BUY", ask, 0.0, sl, ["c3b"], f"ticket={ticket}")


def poll(mt5, config, log, resolve_symbol, get_vix, offset_fn, send_order, mk_comment, autotrading_ok, log_trade,
         now: float | None = None) -> None:
    """Bot ana döngüsünden her tarama çağrılır (shadow'dan SONRA: VIX geçmişini o günceller). Hata → çağıran yakalar."""
    global _last_poll
    now = time.time() if now is None else now
    if now - _last_poll < POLL_EVERY_S or not kk.is_enabled(config, RULE):
        return
    _last_poll = now
    today, mloc, wd = cs.to_local(now, sh.TZ)
    if wd >= 5 or mloc < sh.ENTRY_MIN:
        return
    st = _load_state()
    if st.get("pending"):
        sym = resolve_symbol(sh.MARKET)
        if sym and _try_pending(mt5, config, log, st, today, now, sym, send_order, mk_comment, autotrading_ok, log_trade):
            _save_state(st)
    if st.get("last_d") == str(today):
        return
    sym = resolve_symbol(sh.MARKET)
    if not sym:
        return
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M30, 0, sh.FETCH_M30)    # 0 → 15:30 barı açılışı görünür
    if rates is None or len(rates) < 100:
        return
    off = offset_fn(sym)
    series = sh.daily_series(cs._m15_utc(rates, off))
    if not series or series[-1]["d"] != today:
        return                                                                  # bugünün 15:30 barı henüz yok
    manage_and_enter(mt5, config, log, series, today, st, now, sym, off, send_order, mk_comment, autotrading_ok, log_trade)
    st["last_d"] = str(today)
    _save_state(st)
