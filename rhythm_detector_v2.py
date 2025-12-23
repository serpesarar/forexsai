from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple
import math
import threading

import numpy as np
import pandas as pd
from scipy.signal import detrend, hilbert, sawtooth, windows, find_peaks
from scipy.stats import norm


@dataclass
class RhythmConfig:
    """Configuration for rhythm detection.

    Parameters
    ----------
    window_seconds : int
        Sliding window size in seconds.
    tick_rate_hz : float
        Expected ticks per second.
    min_period_s : float
        Minimum rhythm period to consider.
    max_period_s : float
        Maximum rhythm period to consider.
    outlier_zscore : float
        Z-score threshold for outlier filtering.
    regularity_threshold : float
        Minimum regularity score required for a trade.
    confidence_threshold : float
        Minimum confidence required for a trade.
    min_amplitude : float
        Minimum amplitude to accept rhythm.
    dtw_downsample : int
        Downsample factor for DTW matching.
    max_gap_s : float
        Maximum gap before resetting the buffer.
    fill_gaps : bool
        Whether to fill small gaps using last price.
    """

    window_seconds: int = 900
    tick_rate_hz: float = 1.0
    min_period_s: float = 8.0
    max_period_s: float = 240.0
    outlier_zscore: float = 3.5
    regularity_threshold: float = 0.75
    confidence_threshold: float = 0.85
    min_amplitude: float = 0.0005
    dtw_downsample: int = 4
    max_gap_s: float = 10.0
    fill_gaps: bool = True


@dataclass
class RhythmState:
    """Computed rhythm state."""

    pattern_type: str
    dominant_period_s: float
    dominant_frequency_hz: float
    regularity: float
    phase: float
    confidence: float
    amplitude: float
    trend_slope: float
    p_value: float
    harmonics: List[Tuple[float, float]]
    predictions: Dict[str, float]
    support: Optional[float]
    resistance: Optional[float]

    def as_dict(self) -> Dict[str, object]:
        return {
            "pattern_type": self.pattern_type,
            "dominant_period_s": self.dominant_period_s,
            "dominant_frequency_hz": self.dominant_frequency_hz,
            "regularity": self.regularity,
            "phase": self.phase,
            "confidence": self.confidence,
            "amplitude": self.amplitude,
            "trend_slope": self.trend_slope,
            "p_value": self.p_value,
            "harmonics": self.harmonics,
            "predictions": self.predictions,
            "support": self.support,
            "resistance": self.resistance,
        }


class RhythmDetector:
    """Real-time rhythm detection for price ticks.

    This detector ingests 1-second tick data, performs FFT + autocorrelation
    rhythm analysis, classifies waveforms, and provides predictive signals.

    Core API:
    - add_tick(price, timestamp=None)
    - detect_wave_pattern()
    - should_trade()
    """

    def __init__(self, config: RhythmConfig | None = None) -> None:
        self.config = config or RhythmConfig()
        self.maxlen = int(self.config.window_seconds * self.config.tick_rate_hz)
        self._prices: Deque[float] = deque(maxlen=self.maxlen)
        self._timestamps: Deque[float] = deque(maxlen=self.maxlen)
        self._lock = threading.Lock()
        self._last_state: Optional[RhythmState] = None

    def add_tick(self, price: float, timestamp: Optional[float] = None) -> None:
        """Add a new price tick to the buffer.

        Parameters
        ----------
        price : float
            Latest price tick.
        timestamp : float, optional
            Unix timestamp in seconds.
        """

        with self._lock:
            if timestamp is None:
                timestamp = self._timestamps[-1] + 1.0 / self.config.tick_rate_hz if self._timestamps else 0.0

            if self._timestamps:
                gap = timestamp - self._timestamps[-1]
                if gap > self.config.max_gap_s:
                    self._prices.clear()
                    self._timestamps.clear()
                elif self.config.fill_gaps and gap > (1.0 / self.config.tick_rate_hz):
                    missing = int(gap * self.config.tick_rate_hz) - 1
                    for idx in range(missing):
                        self._timestamps.append(self._timestamps[-1] + 1.0 / self.config.tick_rate_hz)
                        self._prices.append(self._prices[-1])

            self._timestamps.append(timestamp)
            self._prices.append(float(price))

    def detect_wave_pattern(self) -> Dict[str, object]:
        """Detect rhythm pattern and return computed state.

        Returns
        -------
        dict
            Rhythm state dictionary.
        """

        with self._lock:
            if len(self._prices) < max(32, int(self.config.min_period_s * self.config.tick_rate_hz)):
                return {
                    "pattern_type": "insufficient_data",
                    "dominant_period_s": 0.0,
                    "dominant_frequency_hz": 0.0,
                    "regularity": 0.0,
                    "phase": 0.0,
                    "confidence": 0.0,
                    "amplitude": 0.0,
                    "trend_slope": 0.0,
                    "p_value": 1.0,
                    "harmonics": [],
                    "predictions": {},
                    "support": None,
                    "resistance": None,
                }

            prices = np.asarray(self._prices, dtype=np.float64)

        filtered = self._filter_outliers(prices)
        detrended = detrend(filtered)
        amplitude = float(np.ptp(detrended) / 2.0)

        freqs, magnitudes = self._fft_spectrum(detrended)
        dominant_freq, harmonics = self._dominant_frequency(freqs, magnitudes)
        dominant_period = 1.0 / dominant_freq if dominant_freq > 0 else 0.0

        regularity, p_value = self._autocorr_regularity(detrended, dominant_freq)
        phase = self._phase(detrended)
        trend_slope = self._trend_slope(prices)

        pattern_type, confidence = self._classify_pattern(detrended, dominant_freq)
        predictions = self._predict(prices, dominant_freq, phase, amplitude)
        support, resistance = self._support_resistance(prices)

        confidence = float(min(1.0, confidence * (regularity + 1e-6)))
        state = RhythmState(
            pattern_type=pattern_type,
            dominant_period_s=dominant_period,
            dominant_frequency_hz=dominant_freq,
            regularity=regularity,
            phase=phase,
            confidence=confidence,
            amplitude=amplitude,
            trend_slope=trend_slope,
            p_value=p_value,
            harmonics=harmonics,
            predictions=predictions,
            support=support,
            resistance=resistance,
        )
        self._last_state = state
        return state.as_dict()

    def should_trade(self) -> Dict[str, object]:
        """Return trade decision based on the latest rhythm state."""

        state = self._last_state or RhythmState(
            pattern_type="unknown",
            dominant_period_s=0.0,
            dominant_frequency_hz=0.0,
            regularity=0.0,
            phase=0.0,
            confidence=0.0,
            amplitude=0.0,
            trend_slope=0.0,
            p_value=1.0,
            harmonics=[],
            predictions={},
            support=None,
            resistance=None,
        )

        should = (
            state.confidence >= self.config.confidence_threshold
            and state.regularity >= self.config.regularity_threshold
            and state.amplitude >= self.config.min_amplitude
        )

        direction = "HOLD"
        if should and state.predictions:
            current = self._prices[-1] if self._prices else 0.0
            forward = state.predictions.get("60s") or state.predictions.get("30s")
            if forward is not None:
                direction = "BUY" if forward > current else "SELL"

        return {
            "should_trade": should,
            "direction": direction,
            "confidence": state.confidence,
            "regularity": state.regularity,
            "pattern_type": state.pattern_type,
            "dominant_period_s": state.dominant_period_s,
        }

    def _filter_outliers(self, prices: np.ndarray) -> np.ndarray:
        median = np.median(prices)
        mad = np.median(np.abs(prices - median)) + 1e-9
        z_scores = 0.6745 * (prices - median) / mad
        filtered = prices.copy()
        filtered[np.abs(z_scores) > self.config.outlier_zscore] = median
        return filtered

    def _fft_spectrum(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n = len(data)
        window = windows.hann(n)
        padded = int(2 ** math.ceil(math.log2(n)))
        spectrum = np.fft.rfft(data * window, n=padded)
        magnitudes = np.abs(spectrum)
        freqs = np.fft.rfftfreq(padded, d=1.0 / self.config.tick_rate_hz)
        return freqs, magnitudes

    def _dominant_frequency(self, freqs: np.ndarray, magnitudes: np.ndarray) -> Tuple[float, List[Tuple[float, float]]]:
        mask = (freqs > 0) & (freqs <= 1.0 / self.config.min_period_s)
        mask &= freqs >= 1.0 / self.config.max_period_s
        if not np.any(mask):
            return 0.0, []

        peaks, _ = find_peaks(magnitudes[mask])
        if peaks.size == 0:
            peak_index = np.argmax(magnitudes[mask])
        else:
            peak_index = peaks[np.argmax(magnitudes[mask][peaks])]

        masked_freqs = freqs[mask]
        dominant_freq = float(masked_freqs[peak_index])

        harmonics = []
        for multiple in (2, 3, 4):
            target = dominant_freq * multiple
            idx = np.argmin(np.abs(freqs - target))
            harmonics.append((float(freqs[idx]), float(magnitudes[idx])))
        return dominant_freq, harmonics

    def _autocorr_regularity(self, data: np.ndarray, dominant_freq: float) -> Tuple[float, float]:
        if dominant_freq <= 0:
            return 0.0, 1.0

        max_lag = int(self.config.max_period_s * self.config.tick_rate_hz)
        min_lag = max(1, int(self.config.min_period_s * self.config.tick_rate_hz))

        normed = data - np.mean(data)
        autocorr = np.correlate(normed, normed, mode="full")
        autocorr = autocorr[autocorr.size // 2 :]
        autocorr /= autocorr[0] + 1e-9

        lag_slice = autocorr[min_lag:max_lag]
        if lag_slice.size == 0:
            return 0.0, 1.0
        peak = float(np.max(lag_slice))

        n = len(data)
        z = peak * math.sqrt(n)
        p_value = float(2.0 * (1.0 - norm.cdf(abs(z))))
        return peak, p_value

    def _phase(self, data: np.ndarray) -> float:
        analytic = hilbert(data)
        phase = np.angle(analytic)
        return float((phase[-1] + np.pi) / (2 * np.pi))

    def _trend_slope(self, prices: np.ndarray) -> float:
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        return float(slope)

    def _classify_pattern(self, data: np.ndarray, dominant_freq: float) -> Tuple[str, float]:
        if dominant_freq <= 0:
            return "irregular", 0.0

        t = np.arange(len(data)) / self.config.tick_rate_hz
        wave_sine = np.sin(2 * np.pi * dominant_freq * t)
        wave_saw = sawtooth(2 * np.pi * dominant_freq * t)
        wave_tri = sawtooth(2 * np.pi * dominant_freq * t, 0.5)

        templates = {
            "sine": wave_sine,
            "sawtooth": wave_saw,
            "triangle": wave_tri,
        }

        scores = {}
        for name, template in templates.items():
            corr = np.corrcoef(data, template)[0, 1]
            dtw_score = self._dtw_similarity(data, template)
            scores[name] = 0.6 * corr + 0.4 * dtw_score

        best = max(scores, key=scores.get)
        confidence = max(0.0, min(1.0, scores[best]))
        return best, confidence

    def _dtw_similarity(self, series: np.ndarray, template: np.ndarray) -> float:
        down = max(1, self.config.dtw_downsample)
        a = series[::down]
        b = template[::down]
        n, m = len(a), len(b)

        dtw = np.full((n + 1, m + 1), np.inf)
        dtw[0, 0] = 0.0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(a[i - 1] - b[j - 1])
                dtw[i, j] = cost + min(dtw[i - 1, j], dtw[i, j - 1], dtw[i - 1, j - 1])
        distance = dtw[n, m]
        return float(1.0 / (1.0 + distance / (n + m)))

    def _predict(self, prices: np.ndarray, dominant_freq: float, phase: float, amplitude: float) -> Dict[str, float]:
        if dominant_freq <= 0:
            return {}

        current = prices[-1]
        horizon = {"30s": 30, "60s": 60, "120s": 120}
        predictions = {}

        sine_predictions = {}
        for label, seconds in horizon.items():
            radians = 2 * np.pi * dominant_freq * seconds
            sine_predictions[label] = current + amplitude * math.sin(radians + phase * 2 * np.pi)

        ar_predictions, ar_sigma = self._ar_forecast(prices, horizon)

        for label in horizon:
            if label in ar_predictions:
                predictions[label] = float(0.6 * sine_predictions[label] + 0.4 * ar_predictions[label])
            else:
                predictions[label] = float(sine_predictions[label])
            if ar_sigma is not None:
                predictions[f"{label}_ci"] = float(ar_sigma)

        return predictions

    def _ar_forecast(self, prices: np.ndarray, horizon: Dict[str, int]) -> Tuple[Dict[str, float], Optional[float]]:
        if len(prices) < 10:
            return {}, None

        diffs = np.diff(prices)
        order = min(3, max(1, len(diffs) // 10))
        y = diffs[order:]
        if y.size == 0:
            return {}, None

        X = np.column_stack([diffs[order - k - 1 : -k - 1] for k in range(order)])
        coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)

        residuals = y - X @ coeffs
        sigma = float(np.std(residuals)) if residuals.size else None

        forecasts = {}
        history = diffs.copy()
        for label, seconds in horizon.items():
            steps = int(seconds * self.config.tick_rate_hz)
            forecast = 0.0
            temp = history.tolist()
            for _ in range(steps):
                prev = np.array(temp[-order:][::-1])
                next_val = float(np.dot(coeffs, prev))
                temp.append(next_val)
                forecast += next_val
            forecasts[label] = float(prices[-1] + forecast)
        return forecasts, sigma

    def _support_resistance(self, prices: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
        if len(prices) < 10:
            return None, None

        series = pd.Series(prices)
        support = float(series.rolling(20, min_periods=5).min().iloc[-1])
        resistance = float(series.rolling(20, min_periods=5).max().iloc[-1])
        return support, resistance


__all__ = ["RhythmDetector", "RhythmConfig", "RhythmState"]
