"""range_band_bridge.py — Zaman Makinesi fiyat bandını botun TP/SL'siyle eşler (kaynak yöntem: day-trader-skill /
trader-timemachine, MIT; backend/services/time_machine_service.py).

KANIT: DTS-03 (research/dts_uyarlama_20261104) ufuk-sonu %90 bant 5m/15m/1h × 4 sembolde %88,2–91,7 kapsama (A).
DTS-06: bandın botun işlemlerine uygulanması (TP %90 dışında / SL %50 içinde / dokunma payı) sonucu AYIRT ETMEDİ
→ bot tarafında YALNIZ KAYIT (RANGE_BAND_ENABLED). RANGE_GATE_BLOCK=True yalnız ileride ayrı kanıtla açılır.
Bant YÖN söylemez. Hata → None (fail-open): emir akışı asla bloklanmaz.
"""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
HORIZON_MIN = 60


def check(mt5, mt5_symbol: str, entry: float, tp: float | None, sl: float | None, direction: str,
          horizon_min: int = HORIZON_MIN) -> dict | None:
    """{band_p5, band_p95, band_p25, band_p75, tp_outside_p90, sl_inside_p50, tp_vs_p95, width_pct, horizon_min} | None."""
    try:
        if str(_BACKEND) not in sys.path:
            sys.path.append(str(_BACKEND))          # append: bot modüllerini gölgeleme
        from services import time_machine_service as tm
        band = tm.range_band_mt5(mt5, mt5_symbol, horizon_min)
        if not band:
            return None
        lc = tm.level_check(band, float(entry), float(tp) if tp else None, float(sl) if sl else None,
                            "buy" if str(direction).upper().startswith("BUY") else "sell")
        out = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in lc.items()}
        out.update({"width_pct": round(band["width_pct"], 4), "horizon_min": band["horizon_min"],
                    "pool_sessions": band["pool_sessions"]})
        return out
    except Exception:
        return None
