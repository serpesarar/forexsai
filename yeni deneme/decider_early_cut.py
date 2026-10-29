"""decider_early_cut.py — claude_decider XAUUSD BUY pozisyonlarında ERKEN KESME (2026-10-21, kullanıcı kararı).

KURAL: pozisyon açıldıktan sonra ilk kez ≥ EARLY_CUT_MIN dakika geçtiğinde, son KAPANMIŞ 1m barın
kapanışıyla R = (kapanış − giriş) / (giriş − ilk SL) hesaplanır; R ≤ EARLY_CUT_R ise piyasadan kapatılır.
Her pozisyon için karar YALNIZ BİR KEZ verilir. EARLY_CUT_MAX_LATE_MIN'den geç görülen pozisyona dokunulmaz
(bot kapalıyken açılmış/kaçırılmış — kural o anı ölçmedi).

KANIT (defter DX-04, research/decider_xau_ileri_20261021/SONUC.md): decider XAU BUY kararlarında
gölge 566 +0,013R/işlem P %97,9 (iki yarı +), ileri ≥10-15 +0,037 P %99,7, sonraki-bar çıkışı +0,013,
spread ×1,5 P %92, plato 5–10 dk / −0,3…−0,7 R'nin 24/25 hücresi ≥0, rastgele-gün plasebosunu %93 aşıyor.
SELL'e TAŞINMIYOR (n=82 tutarsız) → yalnız BUY. Etki küçük: kural decider XAU'yu başabaşa getirir, kârlı yapmaz.

Neden botta: decider döngüsü 20 dk'da bir döner, 5. dakikayı yakalayamaz; botun ana döngüsü ~1 dk.
Bot trade_manager'ı decider magic'ine DOKUNMAZ (ayrı magic tasarımı) — bu modül yalnız bu kuralı uygular.

2026-10-29 GÖLGE (DX-06, research/decider_xau_sl_20261029/SONUC.md): ileri dönemin gerçek icrasında
kural −3,6R; DECIDER_EARLY_CUT_LIVE=False iken "kes" yalnız [GÖLGE] satırı olarak loglanır.
"""
from __future__ import annotations

from typing import Callable, Optional

import config
import phase_rules as pr

_karar_verildi: set[int] = set()        # bu oturumda değerlendirilmiş ticket'lar (tek karar)


def early_cut_decision(direction: str, entry: float, sl0: float, close_px: float, age_min: float,
                       cut_r: float = -0.5, min_age: float = 5.0,
                       max_late: float = 10.0) -> tuple[str, Optional[float]]:
    """Saf çekirdek → ('bekle' | 'kes' | 'tut' | 'gec' | 'gecersiz', R).

    bekle: henüz min_age dolmadı · gec: ilk görüş max_late'ten sonra (dokunma) ·
    kes: R ≤ cut_r · tut: R > cut_r · gecersiz: SL/giriş/yön kullanılamaz."""
    if direction != "BUY" or not entry or not sl0 or entry <= sl0:
        return "gecersiz", None
    if age_min < min_age:
        return "bekle", None
    if age_min > max_late:
        return "gec", None
    r = (float(close_px) - float(entry)) / (float(entry) - float(sl0))
    return ("kes" if r <= cut_r else "tut"), r


def _close(mt5, pos, log, why: str) -> bool:
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        return False
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": float(pos.volume),
           "position": pos.ticket, "type": mt5.ORDER_TYPE_SELL, "price": tick.bid,
           "deviation": getattr(config, "DEVIATION_POINTS", 30), "magic": pos.magic,
           "comment": "CDEC erken kes", "type_time": mt5.ORDER_TIME_GTC}
    res = None
    for mode in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN):
        req["type_filling"] = mode
        res = mt5.order_send(req)
        if res is not None and res.retcode == mt5.TRADE_RETCODE_DONE:
            log.info("[ERKEN-KES] ✂ %s ticket=%s kapatıldı (%s, kâr=%.2f)", pos.symbol, pos.ticket,
                     why, float(pos.profit))
            return True
        if res is None or res.retcode != 10030:          # 10030 = filling desteklenmiyor → sıradaki mod
            break
    log.warning("[ERKEN-KES] ❌ ticket=%s kapatılamadı rc=%s", pos.ticket, getattr(res, "retcode", "?"))
    return False


def manage(mt5, log, resolve_symbol: Callable[[str], Optional[str]]) -> None:
    """Botun ana döngüsünden her taramada çağrılır. Her hata yutulur (fail-open: dokunmaz)."""
    if not pr.flag(config, "DECIDER_EARLY_CUT_ENABLED"):
        return
    magic = int(pr.flag(config, "DECIDER_EARLY_CUT_MAGIC"))
    syms = {resolve_symbol(s) for s in pr.flag(config, "DECIDER_EARLY_CUT_SYMBOLS")} - {None}
    if not syms:
        return
    cut_r = float(pr.flag(config, "DECIDER_EARLY_CUT_R"))
    min_age = float(pr.flag(config, "DECIDER_EARLY_CUT_MIN"))
    max_late = float(pr.flag(config, "DECIDER_EARLY_CUT_MAX_LATE_MIN"))
    live = bool(pr.flag(config, "DECIDER_EARLY_CUT_LIVE"))
    for pos in (mt5.positions_get() or []):
        try:
            if pos.magic != magic or pos.symbol not in syms or pos.ticket in _karar_verildi:
                continue
            tick = mt5.symbol_info_tick(pos.symbol)
            if tick is None:
                continue
            age_min = (float(tick.time) - float(pos.time)) / 60.0      # ikisi de broker saati
            rates = mt5.copy_rates_from_pos(pos.symbol, mt5.TIMEFRAME_M1, 1, 1)   # son KAPANMIŞ bar
            if rates is None or len(rates) == 0:
                continue
            direction = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
            verdict, r = early_cut_decision(direction, float(pos.price_open), float(pos.sl),
                                            float(rates[-1]["close"]), age_min, cut_r, min_age, max_late)
            if verdict == "bekle":
                continue
            _karar_verildi.add(pos.ticket)
            if verdict == "kes" and live:
                _close(mt5, pos, log, f"{age_min:.1f} dk'da R={r:+.2f} ≤ {cut_r:+.2f}")
            elif verdict == "kes":
                log.info("[ERKEN-KES] [GÖLGE] %s ticket=%s %.1f dk'da R=%+.2f ≤ %+.2f → kesilirdi, "
                         "dokunulmadı", pos.symbol, pos.ticket, age_min, r, cut_r)
            elif verdict == "tut":
                log.info("[ERKEN-KES] %s ticket=%s %.1f dk'da R=%+.2f > %+.2f → tutuluyor", pos.symbol,
                         pos.ticket, age_min, r, cut_r)
        except Exception as exc:
            log.debug("erken kesme atlandı ticket=%s: %s", getattr(pos, "ticket", "?"), exc)
