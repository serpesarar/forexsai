"""vol_bracket — araştırma paritesi + davranış testleri."""
from __future__ import annotations

import math
import types

import numpy as np
import pandas as pd

import vol_bracket as vb


def _bars(n=300, seed=1):
    g = np.random.default_rng(seed)
    c = 26000 + np.cumsum(g.normal(0, 20, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + g.uniform(0, 15, n)
    l = np.minimum(o, c) - g.uniform(0, 15, n)
    return o, h, l, c


def test_atr_matches_research_wilder():
    o, h, l, c = _bars()
    pc = pd.Series(c).shift(1).fillna(pd.Series(o))
    tr = np.maximum(h - l, np.maximum((h - pc).abs(), (l - pc).abs()))
    ref = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().iloc[-1]   # tepe_destek engine._wilder
    assert math.isclose(vb.wilder_atr(h, l, c), ref, rel_tol=1e-9)


def test_calm_market_keeps_old_geometry():
    assert vb.bracket(80, 110, 30.0, 2.5) == (80, 110)          # 75 ≤ 110
    assert vb.scaled_lot(30, 110, 110, 0.1, 0.1) == 30


def test_volatile_widens_and_keeps_rr():
    tp, sl = vb.bracket(80, 110, 120.0, 2.5)
    assert sl == 300 and math.isclose(tp, 300 * 80 / 110)
    lot = vb.scaled_lot(30, 110, sl, 0.1, 0.1)
    assert lot == 11.0 and lot * sl <= 30 * 110 + 1e-9          # $ risk tabanı aşmaz


def test_invalid_atr_fail_open():
    assert vb.bracket(80, 110, float("nan"), 2.5) == (80, 110)
    assert vb.wilder_atr([1.0] * 5, [0.0] * 5, [0.5] * 5) != vb.wilder_atr([1.0] * 5, [0.0] * 5, [0.5] * 5)  # nan


def _fake_mt5(atr_like=120.0):
    o, h, l, c = _bars()
    h = l + atr_like                                             # TR ≈ atr_like
    rates = [dict(open=a, high=b, low=d, close=e) for a, b, d, e in zip(o, h, l, l + atr_like / 2)]
    return types.SimpleNamespace(
        TIMEFRAME_M5=5, copy_rates_from_pos=lambda *a: rates,
        symbol_info=lambda s: types.SimpleNamespace(volume_step=0.1, volume_min=0.1))


def test_adjust_scope_and_flag():
    cfg = types.SimpleNamespace(DAYCOMBO_VOL_BRACKET=True, DAYCOMBO_VOL_K=2.5)
    m = _fake_mt5()
    tp, sl, lot, note = vb.adjust(m, "NAS100", "NDX.INDX:BUY:DAYCOMBO", 80, 110, 30, cfg)
    assert sl > 110 and lot < 30 and "vol_bracket" in note
    assert vb.adjust(m, "NAS100", "NDX.INDX:SELL:VIXREG", 80, 110, 30, cfg)[:3] == (80, 110, 30)
    off = types.SimpleNamespace(DAYCOMBO_VOL_BRACKET=False)
    assert vb.adjust(m, "NAS100", "NDX.INDX:BUY:REENTRY", 80, 110, 30, off)[:3] == (80, 110, 30)


def test_adjust_fail_open_on_error():
    cfg = types.SimpleNamespace(DAYCOMBO_VOL_BRACKET=True)
    bad = types.SimpleNamespace(TIMEFRAME_M5=5, copy_rates_from_pos=lambda *a: (_ for _ in ()).throw(RuntimeError("x")))
    assert vb.adjust(bad, "NAS100", "NDX.INDX:BUY:DAYCOMBO", 80, 110, 30, cfg)[:3] == (80, 110, 30)
