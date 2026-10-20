"""IO-23 gölge kaydı saf çekirdeği (MT5 gerekmez): ema50_dist_atr islem_otopsi tanımıyla aynı mı +
would_block mantığı. Çalıştır: cd 'yeni deneme' && python3 -m pytest -q test_sqz_ema50_shadow.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import phase_rules as pr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.islem_otopsi.indicators import atr, ema  # noqa: E402


def _bars(n=200, seed=3):
    rng = np.random.default_rng(seed)
    c = 25000 + np.cumsum(rng.normal(0, 30, n))
    h, l = c + rng.uniform(5, 40, n), c - rng.uniform(5, 40, n)
    return [{"high": float(a), "low": float(b), "close": float(x)} for a, b, x in zip(h, l, c)]


def test_matches_islem_otopsi_definition():
    b = _bars()
    df = pd.DataFrame(b)
    px = b[-1]["close"] + 12.0
    ref = (px - ema(df.close, 50).iloc[-1]) / atr(df).iloc[-1]
    got = pr.ema50_dist_atr(b, px)[0]
    assert abs(got - ref) < 0.02


def test_insufficient_bars_is_none():
    assert pr.ema50_dist_atr(_bars(50), 25000.0) is None


def test_would_block_logic():
    assert pr.sqz_ema50_would_block(0.8, 1.0, "BUY") is True
    assert pr.sqz_ema50_would_block(0.8, 2.0, "BUY") is False
    assert pr.sqz_ema50_would_block(1.2, 0.5, "BUY") is False
    assert pr.sqz_ema50_would_block(0.8, -1.0, "SELL") is True      # SELL: EMA50'nin 1 ATR altı = lehte yakın
    assert pr.sqz_ema50_would_block(None, 1.0, "BUY") is None
