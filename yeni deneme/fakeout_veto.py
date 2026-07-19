"""fakeout_veto.py — işlem açmadan önce sahte-kırılım dedektörüne danış.

4 sembolde OOS %70/%70+ doğrulanmış dedektör (backend/services/fakeout_service):
taze bir seviye kırılımı işlem YÖNÜNDEyse ve dedektör SAHTE diyorsa emri veto et
("kırdı, kesin gidecek" tuzağı). Saf çekirdek lokalde çağrılır (backend HTTP'sine
bağımlılık yok — bot Windows'ta backend erişimi olmadan da çalışır).

Env: FAKEOUT_VETO=0 ile kapatılır (default açık). Tüm hata yolları fail-open:
dedektör çalışamazsa emir NORMAL akışına devam eder, asla işlem engellenmez.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("fakeout_veto")

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
_MIN_BARS = 130


def fakeout_check(mt5, mt5_symbol: str, forexsai_sym: str,
                  direction: str) -> tuple[bool, str]:
    """(allow, reason) — allow=False ise emir gönderilmemeli.

    Veto şartı (en yüksek kanıt): taze kırılım işlem yönünde + dedektör
    çağrısı 'fake' (NDX %70 / DAX %75 / XAU %72 / USOIL %86 OOS isabet).
    'pending_next_bar' bilgi olarak loglanır ama VETO ETMEZ (fail-open ruhu).
    """
    if os.getenv("FAKEOUT_VETO", "1") == "0":
        return True, ""
    try:
        rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_M5, 0, 400)
        if rates is None or len(rates) < _MIN_BARS:
            return True, ""
        bars = [{"open": float(r["open"]), "high": float(r["high"]),
                 "low": float(r["low"]), "close": float(r["close"]),
                 "volume": float(r["tick_volume"]), "time": int(r["time"])}
                for r in rates]
        if str(_BACKEND) not in sys.path:
            sys.path.append(str(_BACKEND))     # append: bot modüllerini gölgeleme
        from services.fakeout_service import assess_bars
        fk = assess_bars(bars, symbol=forexsai_sym)
        if fk.get("status") != "assessed":
            return True, ""
        bo = fk.get("breakout") or {}
        aligned = ((direction == "BUY" and bo.get("direction") == "up")
                   or (direction == "SELL" and bo.get("direction") == "down"))
        if not aligned:
            return True, ""
        det = fk.get("detector") or {}
        call = det.get("call")
        if call == "fake":
            reason = (f"FAKEOUT VETO: {bo.get('level_kind')} {bo.get('level_price')} "
                      f"kırılımı işlem yönünde ama dedektör SAHTE dedi "
                      f"(p={det.get('p_fake')}, aşama={det.get('stage')})")
            log.warning("%s %s %s", forexsai_sym, direction, reason)
            return False, reason
        if call == "pending_next_bar":
            log.info("%s %s: taze kırılım, dedektör teyit barı bekliyor (~5dk) — "
                     "emir engellenmedi ama dikkat", forexsai_sym, direction)
        return True, ""
    except Exception as exc:   # fail-open
        log.debug("fakeout_check fail-open (%s): %s", forexsai_sym, exc)
        return True, ""
