"""Rhythm detector v3 — statistically honest cycle detection.

Rewrite goals (forex-statistics-first):

  P0  Time base is truthful. The engine works in *samples* (bars). The caller
      supplies ``seconds_per_sample`` (e.g. 300 for 5m bars) so every period and
      forecast horizon is reported in real wall-clock time instead of pretending
      one bar is one second.

  P1  Cycles are found on **returns**, not price levels. Price levels are I(1)
      (random-walk-like); their autocorrelation is spuriously ~1 at every lag and
      will "find" a cycle in pure noise. Returns are (near) stationary, so a
      genuine oscillation shows up as a real spectral peak.

  P1  Significance is tested against an **AR(1) red-noise null**, not white noise,
      with a Bonferroni correction for the number of frequencies searched. This is
      what kills the data-snooping bias: searching many periods and keeping the
      best one inflates false positives unless the threshold accounts for it.

  P2  Confidence is **out-of-sample**. The fitted cycle must beat a random-walk /
      persistence baseline on a held-out tail of the window. An in-sample template
      correlation (the old approach) always looks good and proves nothing.

  P2  Phase is estimated by least-squares projection onto sin/cos at the dominant
      frequency over the whole window (closed-form, edge-artifact-free) instead of
      reading the Hilbert phase at the contaminated last sample.

  P2  Outliers are winsorized on the **return** series (MAD), not replaced on the
      level series (which manufactures artificial flats). Amplitude is reported as a
      fraction of price so thresholds are comparable across symbols.

Public API mirrors v2 so it is a drop-in: ``RhythmConfig``, ``RhythmState``,
``RhythmDetector`` with ``add_tick`` / ``detect_wave_pattern`` / ``should_trade``.
"""
from __future__ import annotations

import math
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import windows


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class RhythmConfig:
    """Configuration for v3 rhythm detection.

    All period/window quantities are expressed in **samples** (bars). The single
    bridge to wall-clock time is ``seconds_per_sample``.
    """

    window_samples: int = 600
    seconds_per_sample: float = 300.0          # 5m bars by default
    min_period_samples: int = 4                # Nyquist-respecting lower bound
    max_period_samples: int = 120              # at most window/5 is enforced too
    significance_alpha: float = 0.05           # red-noise test level (pre-Bonferroni)
    oos_fraction: float = 0.30                 # tail fraction held out for OOS skill
    min_oos_skill: float = 0.05                # cycle must beat persistence by this
    min_amplitude_pct: float = 0.0005          # 0.05% of price, cross-symbol comparable
    winsor_z: float = 4.0                      # MAD z-cap for return outliers
    confidence_threshold: float = 0.55
    regularity_threshold: float = 0.0          # kept for API parity; gating is OOS-based
    horizon_samples: Tuple[int, ...] = (1, 2, 4)
    max_gap_samples: float = 4.0               # reset buffer if a gap exceeds this
    # legacy aliases accepted by __init__ kwargs but mapped below
    tick_rate_hz: float = 1.0


@dataclass
class RhythmState:
    pattern_type: str
    dominant_period_s: float
    dominant_frequency_hz: float
    regularity: float
    phase: float
    confidence: float
    amplitude: float
    trend_slope: float
    p_value: float
    harmonics: List[Tuple[float, float]] = field(default_factory=list)
    predictions: Dict[str, float] = field(default_factory=dict)
    support: Optional[float] = None
    resistance: Optional[float] = None
    significance: float = 0.0      # observed power / red-noise threshold
    oos_skill: float = 0.0         # 1 - MSE_cycle / MSE_persistence on holdout
    snr: float = 0.0               # spectral peak / median band power

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
            "significance": self.significance,
            "oos_skill": self.oos_skill,
            "snr": self.snr,
        }


_INSUFFICIENT = {
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
    "significance": 0.0,
    "oos_skill": 0.0,
    "snr": 0.0,
}


def _label_for_seconds(seconds: float) -> str:
    if seconds < 90:
        return f"{int(round(seconds))}s"
    if seconds < 3600:
        return f"{int(round(seconds / 60))}m"
    return f"{seconds / 3600:.1f}h"


class RhythmDetector:
    """Statistically honest real-time rhythm detector (v3).

    Drop-in replacement for v2. Feed it bars via ``add_tick(price, timestamp)``
    where ``timestamp`` is the sample index (0,1,2,...) — the wall-clock meaning
    of one sample is carried by ``config.seconds_per_sample``.
    """

    def __init__(self, config: Optional[RhythmConfig] = None) -> None:
        self.config = config or RhythmConfig()
        self.maxlen = int(self.config.window_samples)
        self._prices: Deque[float] = deque(maxlen=self.maxlen)
        self._index: Deque[float] = deque(maxlen=self.maxlen)
        self._lock = threading.Lock()
        self._last_state: Optional[RhythmState] = None

    # -- ingestion ---------------------------------------------------------
    def add_tick(self, price: float, timestamp: Optional[float] = None) -> None:
        with self._lock:
            if timestamp is None:
                timestamp = (self._index[-1] + 1.0) if self._index else 0.0
            if self._index:
                gap = timestamp - self._index[-1]
                if gap > self.config.max_gap_samples:
                    self._prices.clear()
                    self._index.clear()
            self._index.append(float(timestamp))
            self._prices.append(float(price))

    # -- main analysis -----------------------------------------------------
    def detect_wave_pattern(self) -> Dict[str, object]:
        with self._lock:
            n = len(self._prices)
            min_n = max(64, self.config.min_period_samples * 5)
            if n < min_n:
                return dict(_INSUFFICIENT)
            prices = np.asarray(self._prices, dtype=np.float64)

        if np.any(prices <= 0) or not np.all(np.isfinite(prices)):
            return dict(_INSUFFICIENT)

        sps = float(self.config.seconds_per_sample)
        log_p = np.log(prices)

        # Linear trend on log prices (carried into the forecast).
        t = np.arange(n, dtype=np.float64)
        slope, intercept = np.polyfit(t, log_p, 1)
        log_trend = slope * t + intercept
        detr = log_p - log_trend  # stationary-ish cyclical component on log scale

        # Returns for the spectral / red-noise test.
        returns = np.diff(log_p)
        returns = self._winsorize(returns)

        # --- AR(1) red-noise null + Bonferroni-corrected significance -----
        spec = self._significant_peak(returns)
        if spec is None:
            state = RhythmState(
                pattern_type="random_walk",
                dominant_period_s=0.0,
                dominant_frequency_hz=0.0,
                regularity=0.0,
                phase=0.0,
                confidence=0.0,
                amplitude=float(np.std(detr)),
                trend_slope=float(slope),
                p_value=1.0,
            )
            self._last_state = state
            return state.as_dict()

        freq_cyc_per_sample, significance, snr, p_value = spec
        period_samples = 1.0 / freq_cyc_per_sample
        period_seconds = period_samples * sps
        freq_hz = freq_cyc_per_sample / sps if sps > 0 else 0.0

        # --- closed-form phase / amplitude via LS projection on detrended log
        amp_log, phase_rad = self._ls_sinusoid(detr, freq_cyc_per_sample, n)
        amplitude_pct = float(amp_log)  # log-amplitude ≈ fractional amplitude
        phase_norm = float(((phase_rad + math.pi) % (2 * math.pi)) / (2 * math.pi))

        # --- out-of-sample skill vs persistence ---------------------------
        oos_skill = self._oos_skill(log_p, t, freq_cyc_per_sample)

        # --- confidence: must clear amplitude floor AND have positive OOS skill
        amp_ok = amplitude_pct >= self.config.min_amplitude_pct
        sig_term = max(0.0, min(1.0, math.log10(max(significance, 1.0)) ))
        skill_term = max(0.0, min(1.0, oos_skill / 0.5))
        confidence = 0.0
        if amp_ok and oos_skill >= self.config.min_oos_skill:
            confidence = float(min(1.0, 0.5 * sig_term + 0.5 * skill_term))

        regularity = float(max(0.0, min(1.0, oos_skill)))  # API parity

        predictions = self._predict(
            prices, t, slope, intercept, freq_cyc_per_sample, amp_log, phase_rad, sps
        )
        support, resistance = self._support_resistance(prices)
        harmonics = self._harmonics(returns, freq_cyc_per_sample, sps)

        state = RhythmState(
            pattern_type="cycle" if confidence > 0 else "weak_cycle",
            dominant_period_s=float(period_seconds),
            dominant_frequency_hz=float(freq_hz),
            regularity=regularity,
            phase=phase_norm,
            confidence=confidence,
            amplitude=amplitude_pct,
            trend_slope=float(slope),
            p_value=float(p_value),
            harmonics=harmonics,
            predictions=predictions,
            support=support,
            resistance=resistance,
            significance=float(significance),
            oos_skill=float(oos_skill),
            snr=float(snr),
        )
        self._last_state = state
        return state.as_dict()

    # -- trade decision ----------------------------------------------------
    def should_trade(self) -> Dict[str, object]:
        state = self._last_state
        if state is None:
            return {
                "should_trade": False,
                "direction": "HOLD",
                "confidence": 0.0,
                "regularity": 0.0,
                "pattern_type": "unknown",
                "dominant_period_s": 0.0,
                "oos_skill": 0.0,
                "significance": 0.0,
            }

        should = (
            state.confidence >= self.config.confidence_threshold
            and state.oos_skill >= self.config.min_oos_skill
            and state.amplitude >= self.config.min_amplitude_pct
        )

        direction = "HOLD"
        if should and state.predictions:
            current = self._prices[-1] if self._prices else 0.0
            # nearest-horizon forecast
            forward = None
            for key in sorted(state.predictions, key=lambda k: state.predictions and 0):
                if not key.endswith("_ci"):
                    forward = state.predictions[key]
                    break
            if forward is not None and current:
                direction = "BUY" if forward > current else "SELL"

        return {
            "should_trade": bool(should),
            "direction": direction,
            "confidence": state.confidence,
            "regularity": state.regularity,
            "pattern_type": state.pattern_type,
            "dominant_period_s": state.dominant_period_s,
            "oos_skill": state.oos_skill,
            "significance": state.significance,
        }

    # -- internals ---------------------------------------------------------
    def _winsorize(self, x: np.ndarray) -> np.ndarray:
        if x.size == 0:
            return x
        med = np.median(x)
        mad = np.median(np.abs(x - med)) + 1e-12
        z = 0.6745 * (x - med) / mad
        cap = self.config.winsor_z
        scale = mad / 0.6745
        out = x.copy()
        hi = z > cap
        lo = z < -cap
        out[hi] = med + cap * scale
        out[lo] = med - cap * scale
        return out

    def _ar1_red_noise_spectrum(self, n_freq: int, phi: float) -> np.ndarray:
        """Theoretical AR(1) (red-noise) power spectrum shape, mean-normalised.

        Torrence & Compo (1998) discrete form. Returned array has mean ~1 over the
        positive-frequency band so it can scale the observed mean power directly.
        """
        k = np.arange(n_freq)
        # angular term cos(pi k / (n_freq-1)) spans 0..pi as in T&C
        denom = 1.0 - 2.0 * phi * np.cos(math.pi * k / max(n_freq - 1, 1)) + phi * phi
        shape = (1.0 - phi * phi) / np.maximum(denom, 1e-12)
        shape /= np.mean(shape) + 1e-12
        return shape

    def _significant_peak(
        self, returns: np.ndarray
    ) -> Optional[Tuple[float, float, float, float]]:
        """Return (freq_cycles_per_sample, significance_ratio, snr, p_value) of the
        most significant spectral peak that clears the AR(1) red-noise threshold,
        or None if no peak survives (i.e. indistinguishable from red noise).
        """
        n = returns.size
        if n < 16:
            return None
        x = returns - np.mean(returns)
        if np.allclose(x, 0.0):
            return None

        # AR(1) coefficient of the returns
        if n > 2:
            phi = float(np.clip(np.corrcoef(x[:-1], x[1:])[0, 1], -0.99, 0.99))
        else:
            phi = 0.0
        if not math.isfinite(phi):
            phi = 0.0

        window = windows.hann(n)
        xw = x * window
        spectrum = np.abs(np.fft.rfft(xw)) ** 2
        freqs = np.fft.rfftfreq(n, d=1.0)  # cycles per sample
        nf = spectrum.size

        # frequency band corresponding to the period search range
        f_lo = 1.0 / self.config.max_period_samples
        # do not trust periods longer than window/5 (too few cycles to verify)
        f_window_floor = 5.0 / n
        f_lo = max(f_lo, f_window_floor)
        f_hi = 1.0 / self.config.min_period_samples
        band = (freqs >= f_lo) & (freqs <= f_hi)
        if not np.any(band):
            return None

        red_shape = self._ar1_red_noise_spectrum(nf, phi)
        mean_power = np.mean(spectrum[1:]) + 1e-30  # exclude DC
        expected = red_shape * mean_power           # red-noise expectation per freq

        m_tests = int(np.count_nonzero(band))       # Bonferroni denominator
        alpha = self.config.significance_alpha / max(m_tests, 1)
        # chi-square(2)/2 upper quantile = -ln(alpha)
        sig_factor = -math.log(max(alpha, 1e-300))
        threshold = expected * sig_factor

        ratio = np.full_like(spectrum, -np.inf)
        ratio[band] = spectrum[band] / np.maximum(threshold[band], 1e-30)
        best = int(np.argmax(ratio))
        if ratio[best] < 1.0:
            return None  # nothing beats red noise → treat as random walk

        f_dom = float(freqs[best])
        if f_dom <= 0:
            return None
        significance = float(spectrum[best] / np.maximum(expected[best], 1e-30))
        band_median = float(np.median(spectrum[band]) + 1e-30)
        snr = float(spectrum[best] / band_median)

        # single-frequency tail p-value under red noise, Bonferroni-adjusted
        x_ratio = spectrum[best] / (expected[best] + 1e-30)
        p_single = math.exp(-x_ratio)  # chi2_2 tail
        p_value = float(min(1.0, p_single * m_tests))
        return f_dom, significance, snr, p_value

    def _ls_sinusoid(self, y: np.ndarray, freq: float, n: int) -> Tuple[float, float]:
        """Least-squares fit y ≈ b cos(wt) + c sin(wt). Returns (amplitude, phase_now).

        Phase is evaluated analytically at the last sample t=n-1, free of the edge
        artefacts that contaminate a Hilbert phase read at the boundary.
        """
        t = np.arange(n, dtype=np.float64)
        w = 2.0 * math.pi * freq
        c = np.cos(w * t)
        s = np.sin(w * t)
        A = np.column_stack([c, s])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        b, d = float(coef[0]), float(coef[1])
        amplitude = math.hypot(b, d)
        # instantaneous phase at t=n-1:  y ≈ amplitude * cos(w t - phi0)
        phi0 = math.atan2(d, b)
        phase_now = w * (n - 1) - phi0
        return amplitude, phase_now

    def _oos_skill(self, log_p: np.ndarray, t: np.ndarray, freq: float) -> float:
        """Walk-forward skill of the cycle model vs a persistence (random-walk)
        baseline on a held-out tail. >0 means the cycle genuinely predicts.
        """
        n = log_p.size
        split = int(n * (1.0 - self.config.oos_fraction))
        if split < 32 or n - split < 8:
            return 0.0

        tr_t = t[:split]
        tr_y = log_p[:split]
        # fit trend + sinusoid on the training segment
        slope, intercept = np.polyfit(tr_t, tr_y, 1)
        detr_tr = tr_y - (slope * tr_t + intercept)
        amp, phase_now_tr = self._ls_sinusoid(detr_tr, freq, split)
        w = 2.0 * math.pi * freq
        # recover phi0 from training fit
        # phase_now_tr = w*(split-1) - phi0  ->  phi0 = w*(split-1) - phase_now_tr
        phi0 = w * (split - 1) - phase_now_tr

        oos_t = t[split:]
        oos_y = log_p[split:]
        pred_cycle = (slope * oos_t + intercept) + amp * np.cos(w * oos_t - phi0)
        persist = np.full(oos_y.shape, tr_y[-1])  # random-walk baseline

        mse_cycle = float(np.mean((oos_y - pred_cycle) ** 2))
        mse_persist = float(np.mean((oos_y - persist) ** 2)) + 1e-30
        skill = 1.0 - mse_cycle / mse_persist
        return float(skill)

    def _predict(
        self,
        prices: np.ndarray,
        t: np.ndarray,
        slope: float,
        intercept: float,
        freq: float,
        amp_log: float,
        phase_rad: float,
        sps: float,
    ) -> Dict[str, float]:
        n = prices.size
        w = 2.0 * math.pi * freq
        phi0 = w * (n - 1) - phase_rad  # so cos(w t - phi0) matches phase_now at t=n-1
        out: Dict[str, float] = {}
        for h in self.config.horizon_samples:
            tt = (n - 1) + h
            log_pred = (slope * tt + intercept) + amp_log * math.cos(w * tt - phi0)
            label = _label_for_seconds(h * sps)
            out[label] = float(math.exp(log_pred))
        return out

    def _harmonics(self, returns: np.ndarray, f_dom: float, sps: float) -> List[Tuple[float, float]]:
        n = returns.size
        x = returns - np.mean(returns)
        spectrum = np.abs(np.fft.rfft(x * windows.hann(n))) ** 2
        freqs = np.fft.rfftfreq(n, d=1.0)
        harmonics: List[Tuple[float, float]] = []
        for mult in (2, 3):
            target = f_dom * mult
            if target <= 0 or target >= 0.5:
                continue
            idx = int(np.argmin(np.abs(freqs - target)))
            period_s = (1.0 / freqs[idx]) * sps if freqs[idx] > 0 else 0.0
            harmonics.append((float(period_s), float(spectrum[idx])))
        return harmonics

    def _support_resistance(self, prices: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
        if prices.size < 20:
            return None, None
        tail = prices[-20:]
        return float(np.min(tail)), float(np.max(tail))


__all__ = ["RhythmDetector", "RhythmConfig", "RhythmState"]
