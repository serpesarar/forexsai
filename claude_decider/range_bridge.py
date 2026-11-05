"""range_bridge.py — Zaman Makinesi 60 dk fiyat bandının decider köprüsü (kaynak yöntem: day-trader-skill /
trader-timemachine, MIT; çekirdek backend/services/time_machine_service.py — tek uygulama, bot da aynısını kullanır).

KANIT: DTS-03 (research/dts_uyarlama_20261104) — ufuk-sonu %90 bant 5m/15m/1h × 4 sembol × 3 ufukta %88,2–91,7
kapsama (A). Olasılık meyli tabanı GEÇMEDİ → bant YÖN söylemez. DTS-06: TP/SL'nin banda göre konumu botun
işlemlerinde sonucu ayırt etmedi; panel sinyallerinde 'TP1 %90 bandın dışında' zayıf olumsuz işaret (C).
Kullanıcı kararı (2026-11-04): bant decider'a TP/SL mantığıyla birlikte BİLGİ olarak eklenir.
Fail-open: her hata None — karar akışı asla bloklanmaz. Broker saati → UTC dönüşümü çekirdekte (tick'ten).
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent / "backend"
HORIZON_MIN = 60


def range_context(sym_map: dict[str, str], fx_sym: str, price: float | None, atr_by_dir: dict | None = None,
                  stop_mults: tuple[float, float] = (1.0, 1.5)) -> dict | None:
    """{ufuk_dk, p5..p95 (bu fiyata uygulanmış), genislik_%, seviyeler{yön: level_check}, kalibrasyon, okuma}."""
    try:
        import MetaTrader5 as mt5
        mt5_sym = sym_map.get(fx_sym)
        if not mt5_sym or not price:
            return None
        if str(_BACKEND) not in sys.path:
            sys.path.append(str(_BACKEND))          # append: decider modüllerini gölgeleme
        from services import time_machine_service as tm
        band = tm.range_band_mt5(mt5, mt5_sym, HORIZON_MIN)
        if not band:
            return None
        out = {"ufuk_dk": band["horizon_min"], "genislik_%": round(band["width_pct"], 3),
               **{k: round(price * band[f"rel_{k}"], 5) for k in ("p5", "p25", "p50", "p75", "p95")},
               "kalibrasyon": band["calibration"],
               "okuma": "bant YÖN söylemez; yalnız 60 dk içinde fiyatın tipik olarak nereye kadar gidebildiğini söyler"}
        tp_m, sl_m = stop_mults
        lv = {}
        for d, atr in (atr_by_dir or {}).items():
            if not atr:
                continue
            sign = 1 if d == "BUY" else -1
            tp, sl = price + sign * tp_m * atr, price - sign * sl_m * atr
            lv[d] = {k: (round(v, 5) if isinstance(v, float) else v)
                     for k, v in tm.level_check(band, price, tp, sl, "buy" if d == "BUY" else "sell").items()
                     if k in ("tp_outside_p90", "sl_inside_p50", "tp_vs_p95")}
        if lv:
            out["seviyeler"] = lv
        return out
    except Exception:
        return None
