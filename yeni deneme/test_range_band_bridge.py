"""range_band_bridge — sahte MT5 ile: bant + TP/SL konumu; hata → None (fail-open)."""
from datetime import datetime, timezone

import numpy as np

import range_band_bridge as rbb


class FakeMT5:
    TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_H1 = 5, 15, 16385

    def __init__(self, rates, tick_time):
        self.rates, self.tick_time = rates, tick_time

    def symbol_info_tick(self, s):
        return type("T", (), {"time": self.tick_time})()

    def copy_rates_from_pos(self, s, tf, pos, n):
        return self.rates


def _rates(days=40, off=10800):
    rng = np.random.default_rng(1)
    start = int(datetime(2026, 3, 2, 22, 0, tzinfo=timezone.utc).timestamp())
    out, p = [], 100.0
    for d in range(days):
        for k in range(276):
            c = p * (1 + rng.normal(0, 4e-4))
            out.append({"time": start + d * 86400 + k * 300 + off, "open": p, "high": max(p, c) * 1.0003,
                        "low": min(p, c) * 0.9997, "close": c})
            p = c
    return out


def test_check_returns_levels():
    import sys
    import time as _t
    sys.path.append(str(rbb._BACKEND))
    from services import time_machine_service as tm
    rates = _rates()
    mt5 = FakeMT5(rates, _t.time() + 10800 + 2)
    tm._mt5_band_cache.clear()
    r = rbb.check(mt5, "NAS100", entry=100.0, tp=110.0, sl=99.99, direction="BUY")
    assert r and r["tp_outside_p90"] is True and r["band_p5"] < 100 < r["band_p95"] and r["horizon_min"] == 60


def test_check_fail_open():
    class Broken:
        def symbol_info_tick(self, s):
            raise RuntimeError("terminal yok")
    assert rbb.check(Broken(), "XYZ", 1.0, 1.1, 0.9, "SELL") is None
