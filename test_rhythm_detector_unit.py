import numpy as np

from rhythm_detector_v2 import RhythmDetector, RhythmConfig


def test_detects_sine_pattern():
    config = RhythmConfig(window_seconds=120, tick_rate_hz=1.0)
    detector = RhythmDetector(config)
    t = np.arange(200)
    prices = 100 + np.sin(2 * np.pi * (1 / 30) * t)
    for idx, price in enumerate(prices):
        detector.add_tick(float(price), timestamp=float(idx))
    state = detector.detect_wave_pattern()
    assert state["pattern_type"] in {"sine", "triangle", "sawtooth"}
    assert state["dominant_period_s"] > 0


def test_noise_returns_low_regularity():
    config = RhythmConfig(window_seconds=120, tick_rate_hz=1.0)
    detector = RhythmDetector(config)
    noise = np.random.normal(scale=1.0, size=200)
    for idx, price in enumerate(noise):
        detector.add_tick(float(price), timestamp=float(idx))
    state = detector.detect_wave_pattern()
    assert state["regularity"] < 0.5


def test_outlier_filtering_stability():
    config = RhythmConfig(window_seconds=120, tick_rate_hz=1.0)
    detector = RhythmDetector(config)
    t = np.arange(200)
    prices = 100 + np.sin(2 * np.pi * (1 / 40) * t)
    prices[100] = 1000
    for idx, price in enumerate(prices):
        detector.add_tick(float(price), timestamp=float(idx))
    state = detector.detect_wave_pattern()
    assert state["pattern_type"] != "insufficient_data"
