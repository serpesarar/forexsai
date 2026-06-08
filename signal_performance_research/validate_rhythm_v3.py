"""Validation harness for rhythm_detector_v3.

Proves the statistical claims behind the rewrite by Monte-Carlo, so we never
deploy an engine that hallucinates cycles. Three batteries:

  A. CALIBRATION ON NOISE
     Pure Gaussian random walks (I(1), no cycle). A trustworthy detector should
     flag a "tradeable cycle" at roughly the significance level (~5%), NOT on
     every series. The OLD v2 engine fires almost always — this is the headline
     improvement.

  B. RED-NOISE ROBUSTNESS
     AR(1) price series (persistent returns, still no real cycle). The red-noise
     null is exactly what should stop these from being mistaken for rhythm.
     False-positive rate should again sit near alpha, not balloon.

  C. POWER ON REAL CYCLES
     Price = trend + known sinusoid + noise at several SNRs. The detector should
     (i) detect, (ii) recover the right period, and (iii) show positive OOS skill.
     This guards against throwing the baby out with the bathwater.

Run:  python signal_performance_research/validate_rhythm_v3.py
No network, no Supabase, no prod side effects.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from rhythm_detector_v3 import RhythmDetector, RhythmConfig  # noqa: E402

SPS = 300.0          # 5m bars
N = 600              # window
RUNS = 400
SEED = 12345


def _make_detector() -> RhythmDetector:
    return RhythmDetector(RhythmConfig(
        window_samples=N,
        seconds_per_sample=SPS,
        min_period_samples=4,
        max_period_samples=120,
        significance_alpha=0.05,
        oos_fraction=0.30,
        min_oos_skill=0.05,
        min_amplitude_pct=0.0005,
        confidence_threshold=0.55,
    ))


def _run_series(prices: np.ndarray):
    det = _make_detector()
    for i, p in enumerate(prices):
        det.add_tick(float(p), timestamp=float(i))
    state = det.detect_wave_pattern()
    decision = det.should_trade()
    return state, decision


def random_walk(rng, n=N, start=100.0, vol=0.001):
    r = rng.normal(0.0, vol, n)
    return start * np.exp(np.cumsum(r))


def ar1_returns(rng, n=N, start=100.0, vol=0.001, phi=0.4):
    r = np.zeros(n)
    e = rng.normal(0.0, vol, n)
    for i in range(1, n):
        r[i] = phi * r[i - 1] + e[i]
    return start * np.exp(np.cumsum(r))


def cyclic(rng, n=N, start=100.0, period=40, amp_pct=0.004, noise_pct=0.002):
    """Cycle buried in RANDOM-WALK noise — the realistic, usually-untradeable case."""
    t = np.arange(n)
    cycle = amp_pct * np.sin(2 * np.pi * t / period)
    noise = np.cumsum(rng.normal(0.0, noise_pct, n))
    log_p = np.log(start) + cycle + noise
    return np.exp(log_p)


def cyclic_stationary(rng, n=N, start=100.0, period=40, amp_pct=0.006, noise_pct=0.0015):
    """Cycle dominant at the LEVEL scale (iid noise) — genuinely tradeable case.

    Here the sinusoid is the leading structure in price, so the cycle model must
    beat a flat persistence forecast out-of-sample (positive OOS skill)."""
    t = np.arange(n)
    cycle = amp_pct * np.sin(2 * np.pi * t / period)
    noise = rng.normal(0.0, noise_pct, n)  # stationary, does NOT accumulate
    log_p = np.log(start) + cycle + noise
    return np.exp(log_p)


def battery(name, gen, rng, expect_detect, **kw):
    detect = 0
    tradeable = 0
    periods = []
    skills = []
    for _ in range(RUNS):
        prices = gen(rng, **kw)
        state, decision = _run_series(prices)
        is_cycle = state["pattern_type"] in ("cycle", "weak_cycle") and state["significance"] >= 1.0
        if is_cycle:
            detect += 1
            periods.append(state["dominant_period_s"] / SPS)  # back to bars
            skills.append(state["oos_skill"])
        if decision["should_trade"]:
            tradeable += 1
    det_rate = detect / RUNS
    trade_rate = tradeable / RUNS
    print(f"\n[{name}]")
    print(f"  significant-peak rate : {det_rate:6.1%}   (expect {expect_detect})")
    print(f"  TRADEABLE rate        : {trade_rate:6.1%}   <- false-positive proxy")
    if periods:
        print(f"  detected period (bars): median={np.median(periods):.1f} "
              f"p10={np.percentile(periods,10):.1f} p90={np.percentile(periods,90):.1f}")
    med_skill = float(np.median(skills)) if skills else float("nan")
    if skills:
        print(f"  OOS skill on flagged  : median={med_skill:+.3f} "
              f"frac>0={np.mean(np.array(skills)>0):.0%}")
    return det_rate, trade_rate, med_skill


def main():
    rng = np.random.default_rng(SEED)
    print("=" * 70)
    print("RHYTHM DETECTOR v3 — VALIDATION  (runs=%d, N=%d, sps=%.0fs)" % (RUNS, N, SPS))
    print("=" * 70)

    # A. pure random walk — must be near alpha, NOT ~100%
    _, a_trade, _ = battery("A. RANDOM WALK (no cycle)", random_walk, rng,
                            expect_detect="~5% (alpha)")

    # B. AR(1) red noise — red-noise null should keep this near alpha too
    _, b_trade, _ = battery("B. AR(1) RED NOISE phi=0.4 (no cycle)", ar1_returns, rng,
                            expect_detect="~5% (alpha)", phi=0.4)

    # C. genuine cycles at decreasing SNR — should detect with right period
    print("\n--- C. GENUINE CYCLE (period=40 bars) at varying noise ---")
    c_stat = battery("C0. STATIONARY-noise cycle (tradeable)", cyclic_stationary, rng,
                     expect_detect="high + positive OOS skill", period=40)
    c_strong = battery("C1. cycle in random-walk noise (amp 0.5% / noise 0.1%)", cyclic, rng,
                       expect_detect="high detect, skill humble", period=40, amp_pct=0.005, noise_pct=0.001)
    c_mid = battery("C2. cycle in random-walk noise (amp 0.4% / noise 0.2%)", cyclic, rng,
                    expect_detect="moderate", period=40, amp_pct=0.004, noise_pct=0.002)

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    ok_noise = a_trade <= 0.15 and b_trade <= 0.20
    ok_power = c_strong[0] >= 0.60
    ok_skill = (not np.isnan(c_stat[2])) and c_stat[2] > 0.0
    print(f"  noise false-positive controlled : {'PASS' if ok_noise else 'FAIL'} "
          f"(RW tradeable={a_trade:.0%}, AR1 tradeable={b_trade:.0%}; want low)")
    print(f"  retains power on real cycles     : {'PASS' if ok_power else 'FAIL'} "
          f"(rw-noise cycle detect={c_strong[0]:.0%}; want high)")
    print(f"  positive OOS skill when tradeable: {'PASS' if ok_skill else 'FAIL'} "
          f"(stationary-cycle median skill={c_stat[2]:+.3f}; want >0)")
    allp = ok_noise and ok_power and ok_skill
    print(f"\n  OVERALL: {'PASS — safe to wire into service' if allp else 'FAIL — do not deploy'}")


if __name__ == "__main__":
    main()
