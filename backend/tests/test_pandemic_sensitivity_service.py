"""Unit tests for services/pandemic_sensitivity_service.py.

We test the pure scoring & classification functions directly so the suite
runs in <1s without hitting Yahoo Finance. The refresh loop / yfinance fetch
path is exercised by a separate integration smoke test (not run in CI).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from services import pandemic_sensitivity_service as psi


def _synthetic_df(closes: list[float], volumes: list[int] | None = None) -> pd.DataFrame:
    """Build a daily OHLCV frame the service will accept (close + volume only)."""
    idx = pd.date_range(end="2026-05-12", periods=len(closes), freq="B", tz="UTC")
    df = pd.DataFrame({
        "close": closes,
        "volume": volumes if volumes is not None else [1_000_000] * len(closes),
    }, index=idx)
    return df


class TestClassifyRisk:
    @pytest.mark.parametrize("psi_score,expected_level", [
        (0,    "NORMAL"),
        (15.0, "NORMAL"),
        (25.0, "ELEVATED"),
        (45.0, "WARNING"),
        (65.0, "HIGH_RISK"),
        (85.0, "CRITICAL"),
        (100,  "CRITICAL"),
    ])
    def test_thresholds(self, psi_score, expected_level):
        level, color, summary = psi._classify_risk(psi_score)
        assert level == expected_level
        assert color.startswith("#")
        assert isinstance(summary, str) and len(summary) > 10


class TestScoreTicker:
    def test_normal_market_low_score(self):
        # Flat-ish series, no breakout, no relative outperformance
        closes = [100.0 + (i * 0.05) for i in range(120)]
        df = _synthetic_df(closes)
        bench = _synthetic_df([100.0 + (i * 0.05) for i in range(120)])
        c = psi._score_ticker("X", "Test", df, bench, direction_sign=1)
        assert c is not None
        assert 0 <= c.score < 25, f"flat market should score low, got {c.score}"

    def test_pandemic_style_outperformance_fires(self):
        # Ticker rallies 25% vs flat benchmark over last 20 days
        closes = [100.0] * 100 + [100.0 + (i + 1) * 1.2 for i in range(20)]
        bench_closes = [100.0] * 120
        df = _synthetic_df(closes)
        bench = _synthetic_df(bench_closes)
        c = psi._score_ticker("MRNA", "Moderna", df, bench, direction_sign=1)
        assert c is not None
        assert c.rel_return_20d > 15.0
        assert c.score >= 50, f"strong outperformance should score high, got {c.score}"

    def test_inverse_basket_falls_fires_on_drop(self):
        # Inverse ticker (e.g. JETS) drops 25% — should produce HIGH score
        closes = [100.0] * 100 + [100.0 - (i + 1) * 1.2 for i in range(20)]
        bench_closes = [100.0] * 120
        df = _synthetic_df(closes)
        bench = _synthetic_df(bench_closes)
        c = psi._score_ticker("JETS", "Airlines", df, bench, direction_sign=-1)
        assert c is not None
        assert c.rel_return_20d < -15.0
        assert c.score >= 50, f"inverse basket on big drop should fire, got {c.score}"

    def test_insufficient_history_returns_none(self):
        df = _synthetic_df([100.0] * 30)   # <60 days
        bench = _synthetic_df([100.0] * 120)
        assert psi._score_ticker("X", "Test", df, bench, direction_sign=1) is None

    def test_volume_surge_adds_score(self):
        # Same flat price, but recent volume spike vs baseline
        closes = [100.0] * 120
        volumes = [1_000_000] * 115 + [10_000_000] * 5
        df = _synthetic_df(closes, volumes)
        bench = _synthetic_df([100.0] * 120)
        c = psi._score_ticker("X", "Test", df, bench, direction_sign=1)
        assert c is not None
        assert c.volume_z > 3.0, f"vol z should fire on 10x volume, got {c.volume_z}"

    def test_macro_vix_high_adds_bonus(self):
        # VIX printing 35 (elevated regime). No volume column needed.
        idx = pd.date_range(end="2026-05-12", periods=120, freq="B", tz="UTC")
        df = pd.DataFrame({"close": [15.0] * 100 + [35.0] * 20}, index=idx)
        bench = _synthetic_df([100.0] * 120)
        c = psi._score_ticker("^VIX", "VIX", df, bench, direction_sign=1, is_macro=True)
        assert c is not None
        # VIX > 20 contributes bonus regardless of relative return
        assert c.score > 0


class TestScoreBasket:
    def test_basket_aggregation_averages_contributors(self):
        # Stuff two tickers into the vaccine basket, both with strong returns
        idx = pd.date_range(end="2026-05-12", periods=120, freq="B", tz="UTC")
        bench_df = pd.DataFrame({
            "close": [100.0] * 120,
            "volume": [1_000_000] * 120,
        }, index=idx)
        strong_df = pd.DataFrame({
            "close": [100.0] * 100 + [100.0 + (i + 1) * 1.5 for i in range(20)],
            "volume": [1_000_000] * 120,
        }, index=idx)
        psi._basket_history.clear()
        psi._basket_history["MRNA"] = strong_df
        psi._basket_history["PFE"] = strong_df.copy()
        psi._benchmark_history = bench_df

        cfg = {
            "label": "Vaccines",
            "weight": 0.22,
            "tickers": {"MRNA": "Moderna", "PFE": "Pfizer"},
            "direction": 1,
            "rationale": "test",
        }
        b = psi._score_basket("vaccine_therapeutics", cfg)
        assert b is not None
        assert len(b.contributors) == 2
        assert b.score >= 50
        assert b.avg_rel_return_20d > 15.0

    def test_basket_returns_none_when_no_contributors(self):
        psi._basket_history.clear()
        cfg = {
            "label": "Empty",
            "weight": 0.10,
            "tickers": {"GHOST": "missing"},
            "direction": 1,
            "rationale": "test",
        }
        assert psi._score_basket("ghost", cfg) is None


class TestComposite:
    def test_no_data_returns_neutral_snapshot(self):
        psi._basket_history.clear()
        psi._benchmark_history = None
        psi._last_snapshot = None
        snap = psi.get_snapshot()
        assert snap["psi_score"] == 0.0
        assert snap["risk_level"] == "NORMAL"
        assert snap["baskets"] == []

    def test_psi_band_magnitude_smoothness(self):
        # Curve must be monotonic non-decreasing through the bands
        prev = -1.0
        for s in [0, 10, 20, 25, 35, 40, 50, 55, 60, 70, 79, 80, 90, 99, 100]:
            m = psi._psi_band_magnitude(s)
            assert m >= prev - 1e-6, f"non-monotonic at PSI={s}: {prev} -> {m}"
            prev = m
        # Boundary spot-checks
        assert psi._psi_band_magnitude(0) == 0.0
        assert psi._psi_band_magnitude(19.9) == 0.0
        assert abs(psi._psi_band_magnitude(40) - 2.0) < 0.01
        assert abs(psi._psi_band_magnitude(60) - 5.0) < 0.01
        assert abs(psi._psi_band_magnitude(80) - 9.0) < 0.01
        assert abs(psi._psi_band_magnitude(100) - 13.0) < 0.01

    def test_meta_adjustment_normal_psi_zero_impact(self):
        psi._last_snapshot = {"psi_score": 12.0, "risk_level": "NORMAL", "baskets": []}
        for sym in ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"):
            for direction in ("BUY", "SELL"):
                adj = psi.compute_meta_adjustment(sym, direction)
                assert adj["adjustment"] == 0.0
                assert adj["applied"] is False

    def test_meta_adjustment_critical_penalises_equity_longs(self):
        # PSI=85 (CRITICAL) — magnitude ≈ 9 + (5/20)*4 ≈ 10.0
        psi._last_snapshot = {"psi_score": 85.0, "risk_level": "CRITICAL", "baskets": []}
        adj = psi.compute_meta_adjustment("NDX.INDX", "BUY")
        # bias = -1.0, magnitude ≈ 10  => delta ≈ -10
        assert adj["adjustment"] < -8.0
        assert adj["adjustment"] > -15.0   # hard cap respected
        assert adj["applied"] is True
        assert "CRITICAL" in adj["rationale"]

    def test_meta_adjustment_critical_boosts_gold_longs(self):
        psi._last_snapshot = {"psi_score": 85.0, "risk_level": "CRITICAL", "baskets": []}
        adj = psi.compute_meta_adjustment("XAUUSD", "BUY")
        # bias = +0.9, magnitude ≈ 10  => delta ≈ +9
        assert adj["adjustment"] > 7.0
        assert adj["adjustment"] < 15.0
        assert adj["applied"] is True

    def test_meta_adjustment_high_risk_penalises_oil_longs(self):
        psi._last_snapshot = {"psi_score": 70.0, "risk_level": "HIGH_RISK", "baskets": []}
        adj = psi.compute_meta_adjustment("USOIL.FOREX", "BUY")
        # bias = -0.8, magnitude = 5 + (10/20)*4 = 7  => delta ≈ -5.6
        assert adj["adjustment"] < -3.0
        assert adj["adjustment"] > -8.0

    def test_meta_adjustment_warning_band_modest_impact(self):
        # WARNING (50) magnitude = 2 + (10/20)*3 = 3.5 — should be modest
        psi._last_snapshot = {"psi_score": 50.0, "risk_level": "WARNING", "baskets": []}
        adj = psi.compute_meta_adjustment("NDX.INDX", "BUY")
        assert -5.0 < adj["adjustment"] < -2.0

    def test_meta_adjustment_unknown_symbol_zero(self):
        psi._last_snapshot = {"psi_score": 80.0, "risk_level": "CRITICAL", "baskets": []}
        adj = psi.compute_meta_adjustment("EURUSD", "BUY")
        assert adj["adjustment"] == 0.0
        assert adj["applied"] is False

    def test_meta_adjustment_hold_direction_zero(self):
        psi._last_snapshot = {"psi_score": 95.0, "risk_level": "CRITICAL", "baskets": []}
        adj = psi.compute_meta_adjustment("NDX.INDX", "HOLD")
        assert adj["adjustment"] == 0.0

    def test_meta_adjustment_asymmetry_buy_vs_sell(self):
        # Equity longs penalized more than shorts boosted (precaution principle)
        psi._last_snapshot = {"psi_score": 85.0, "risk_level": "CRITICAL", "baskets": []}
        buy_adj = psi.compute_meta_adjustment("NDX.INDX", "BUY")
        sell_adj = psi.compute_meta_adjustment("NDX.INDX", "SELL")
        assert abs(buy_adj["adjustment"]) > abs(sell_adj["adjustment"])
        assert buy_adj["adjustment"] < 0   # penalty
        assert sell_adj["adjustment"] > 0  # cushion (smaller)

    def test_meta_adjustment_handles_service_failure_gracefully(self):
        # Simulate a broken snapshot — should NEVER raise
        psi._last_snapshot = None
        psi._basket_history.clear()
        psi._benchmark_history = None
        adj = psi.compute_meta_adjustment("NDX.INDX", "BUY")
        assert adj["adjustment"] == 0.0
        assert adj["applied"] is False

    def test_get_ml_features_includes_basket_scores(self):
        psi._last_snapshot = {
            "psi_score": 42.5,
            "risk_level": "WARNING",
            "baskets": [
                {"key": "vaccine_therapeutics", "score": 55.0},
                {"key": "macro_risk", "score": 30.0},
            ],
        }
        feats = psi.get_ml_features()
        assert feats["psi_score"] == 42.5
        assert feats["psi_risk_level_num"] == 2   # WARNING
        assert feats["psi_basket_vaccine_therapeutics"] == 55.0
        assert feats["psi_basket_macro_risk"] == 30.0
