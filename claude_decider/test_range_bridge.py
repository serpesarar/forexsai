"""range_bridge — sahte MetaTrader5 ile: bant fiyata uygulanır, decider'ın kendi TP/SL konumları; hata → None."""
import sys
import time
import types
from datetime import datetime, timezone

import numpy as np

import range_bridge


def _fake_mt5(off=10800, days=40):
    rng = np.random.default_rng(2)
    start = int(datetime(2026, 3, 2, 22, 0, tzinfo=timezone.utc).timestamp())
    rates, p = [], 100.0
    for d in range(days):
        for k in range(276):
            c = p * (1 + rng.normal(0, 4e-4))
            rates.append({"time": start + d * 86400 + k * 300 + off, "open": p, "high": max(p, c) * 1.0003,
                          "low": min(p, c) * 0.9997, "close": c})
            p = c
    m = types.ModuleType("MetaTrader5")
    m.TIMEFRAME_M5, m.TIMEFRAME_M15, m.TIMEFRAME_H1 = 5, 15, 16385
    m.symbol_info_tick = lambda s: types.SimpleNamespace(time=time.time() + off + 1)
    m.copy_rates_from_pos = lambda s, tf, pos, n: rates
    return m


def test_range_context_levels(monkeypatch):
    monkeypatch.setitem(sys.modules, "MetaTrader5", _fake_mt5())
    sys.path.append(str(range_bridge._BACKEND))
    from services import time_machine_service as tm
    tm._mt5_band_cache.clear()
    rf = range_bridge.range_context({"NDX.INDX": "NAS100"}, "NDX.INDX", 200.0, {"BUY": 5.0, "SELL": 5.0}, (1.0, 1.5))
    assert rf and rf["p5"] < 200.0 < rf["p95"] and rf["ufuk_dk"] == 60
    assert rf["seviyeler"]["BUY"]["tp_outside_p90"] is True          # TP +5 (%2,5) 60 dk bandının çok dışında
    assert "YÖN" in rf["okuma"]


def test_range_context_fail_open(monkeypatch):
    monkeypatch.setitem(sys.modules, "MetaTrader5", types.ModuleType("MetaTrader5"))   # fonksiyonsuz modül
    sys.path.append(str(range_bridge._BACKEND))
    from services import time_machine_service as tm
    tm._mt5_band_cache.clear()                       # önbellek yoksa terminal hatası → None (fail-open)
    assert range_bridge.range_context({"NDX.INDX": "NAS100"}, "NDX.INDX", 200.0) is None
    assert range_bridge.range_context({}, "NDX.INDX", 200.0) is None
