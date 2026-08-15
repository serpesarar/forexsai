"""phase_rules birim testleri — MT5 gerekmez, Mac'te koşar.

Amaç: 2026-08-14 karşı-olgusal denetiminden gelen kuralların TANIMINA sadık
olduğunu kanıtlamak (eşikler, sınır durumları, fail-open davranışı).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "yeni deneme"))
import phase_rules as pr  # noqa: E402


class Cfg:
    """Sahte config — yalnız verilen alanlar tanımlı."""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def bars(seq):
    """[(high, low, close), ...] → bot mum formatı."""
    return [{"high": h, "low": l, "close": c} for h, l, c in seq]


# ATR-TP deneyi 2026-08-15 dış-örneklem sonrası varsayılan KAPALI; davranışını
# test etmek için açıkça açıyoruz.
ATR_ON = Cfg(TP_MODE="atr")


# ── bayrak çözümlemesi ──────────────────────────────────────────────────────

def test_flag_config_overrides_default():
    assert pr.flag(None, "TP_MODE") == "fixed"
    assert pr.flag(Cfg(TP_MODE="atr"), "TP_MODE") == "atr"


def test_defaults_after_oos_validation():
    """2026-08-15 dış-örneklem sonrası varsayılanlar.

    Dış-örneklemde ELENEN iki kural (ATR TP + zaman stopu) varsayılan KAPALI;
    hayatta kalan koşullu BE açık. Faz-1 bayrakları kutuda açıldı ama kod
    varsayılanı 'eski davranış' kalır (geri alma güvencesi)."""
    assert pr.flag(None, "MGMT_BE_MODE") == "conditional_mfe"
    assert pr.flag(None, "MGMT_TIME_STOP_MIN") == 0      # OOS: −1.900$
    assert pr.flag(None, "TP_MODE") == "fixed"           # OOS: WR ↑ ama para ↓
    assert pr.flag(None, "NDX_SESSION_BLOCK_ENABLED") is False
    assert pr.flag(None, "NDX_FRIDAY_BLOCK") is False
    assert pr.flag(None, "NDX_SR_ENTRY_ENABLED") is True
    assert pr.flag(None, "PHASE1_CONFIG_RESTORE") is False
    assert pr.flag(None, "POS_TIGHT_BLOCK") is False      # gölge
    assert pr.flag(None, "PROBATION_LIVE") is False       # gölge


# ── FAZ 0.3 — TP = 2.5 × ATR70(1m) ─────────────────────────────────────────

def test_atr_simple_constant_range():
    b = bars([(10, 8, 9)] * 80)          # TR = 2 her barda (gap yok)
    assert pr.atr_simple(b, 70) == pytest.approx(2.0)


def test_atr_needs_enough_bars():
    assert pr.atr_simple(bars([(10, 8, 9)] * 40), 70) is None


def test_tp_distance_uses_atr_for_ndx():
    b = bars([(10, 8, 9)] * 80)          # ATR70 = 2 → TP = 5.0
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", b, 80.0, ATR_ON)
    assert src == "atr70" and d == pytest.approx(5.0)


def test_daycombo_is_exempt():
    b = bars([(10, 8, 9)] * 80)
    d, src = pr.tp_distance("NDX.INDX:BUY:DAYCOMBO", "NDX.INDX", b, 80.0, ATR_ON)
    assert src == "fixed_scope_excluded" and d == 80.0


def test_other_symbols_untouched():
    b = bars([(10, 8, 9)] * 80)
    for sym, scope in (("USOIL.FOREX", "USOIL.FOREX:BUY"),
                       ("GDAXI.INDX", "GDAXI.INDX:BUY")):
        d, src = pr.tp_distance(scope, sym, b, 67.0, ATR_ON)
        assert src == "fixed_scope_out" and d == 67.0


def test_tp_floor_kicks_in_when_atr_collapses():
    """Ölü saat koruması: ATR70=2 → TP 5pt ama SL 110 → taban 0.3×110=33pt."""
    b = bars([(10, 8, 9)] * 80)
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", b, 80.0, ATR_ON, sl_dist=110.0)
    assert src == "atr70_floored" and d == pytest.approx(33.0)


def test_tp_floor_not_applied_without_sl_dist():
    b = bars([(10, 8, 9)] * 80)
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", b, 80.0, ATR_ON)
    assert src == "atr70" and d == pytest.approx(5.0)


def test_tp_floor_can_be_disabled():
    b = bars([(10, 8, 9)] * 80)
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", b, 80.0,
                            Cfg(TP_MODE="atr", TP_ATR_MIN_R=0.0), sl_dist=110.0)
    assert src == "atr70" and d == pytest.approx(5.0)


def test_tp_floor_does_not_shrink_a_large_atr_target():
    b = bars([(60, 8, 30)] * 80)          # ATR büyük → TP taban üstünde
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", b, 80.0, ATR_ON, sl_dist=110.0)
    assert src == "atr70" and d > 33.0


def test_tp_falls_back_when_no_bars():
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", None, 80.0, ATR_ON)
    assert src == "fixed_no_atr" and d == 80.0


def test_tp_mode_fixed_is_old_behaviour():
    b = bars([(10, 8, 9)] * 80)
    d, src = pr.tp_distance("NDX.INDX:BUY", "NDX.INDX", b, 80.0, Cfg(TP_MODE="fixed"))
    assert src == "fixed" and d == 80.0


def test_vixreg_scope_also_covered():
    b = bars([(10, 8, 9)] * 80)
    d, src = pr.tp_distance("NDX.INDX:SELL:VIXREG", "NDX.INDX", b, 80.0, ATR_ON)
    assert src == "atr70" and d == pytest.approx(5.0)


# ── FAZ 0.1 — koşullu başabaş ──────────────────────────────────────────────

def test_be_conditional_needs_half_r():
    assert not pr.be_should_arm("conditional_mfe", mfe=54, sl_dist=110,
                                age_sec=99999, be_minutes=30)
    assert pr.be_should_arm("conditional_mfe", mfe=55, sl_dist=110,
                            age_sec=0, be_minutes=30)


def test_be_time30_is_old_behaviour():
    assert pr.be_should_arm("time30", mfe=0, sl_dist=110,
                            age_sec=1801, be_minutes=30)
    assert not pr.be_should_arm("time30", mfe=0, sl_dist=110,
                                age_sec=1799, be_minutes=30)


def test_be_off_mode_never_arms():
    assert not pr.be_should_arm("off", mfe=999, sl_dist=110,
                                age_sec=99999, be_minutes=30)


def test_be_guards_zero_sl():
    assert not pr.be_should_arm("conditional_mfe", 10, 0, 0, 30)


# ── FAZ 0.2 — zaman stopu ──────────────────────────────────────────────────

def test_time_stop_threshold():
    assert not pr.time_stop_due(119 * 60, 120)
    assert pr.time_stop_due(120 * 60, 120)
    assert not pr.time_stop_due(10 ** 9, 0)          # 0 = kapalı


# ── FAZ 1.1/1.2 — zaman pencereleri ────────────────────────────────────────

CFG1 = Cfg(NDX_SESSION_BLOCK_ENABLED=True, NDX_FRIDAY_BLOCK=True,
           NDX_WEEKEND_HOLD_BLOCK=True)


def utc(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def test_asia_window_wraps_midnight():
    # 2026-08-11 Salı
    assert pr.entry_window_block(utc(2026, 8, 11, 23), "NDX.INDX", CFG1)[0]
    assert pr.entry_window_block(utc(2026, 8, 11, 3), "NDX.INDX", CFG1)[0]
    assert pr.entry_window_block(utc(2026, 8, 11, 6, 59), "NDX.INDX", CFG1)[0]
    assert not pr.entry_window_block(utc(2026, 8, 11, 7), "NDX.INDX", CFG1)[0]
    assert not pr.entry_window_block(utc(2026, 8, 11, 15), "NDX.INDX", CFG1)[0]


def test_friday_block():
    assert pr.entry_window_block(utc(2026, 8, 14, 15), "NDX.INDX", CFG1)[0]   # Cuma
    assert not pr.entry_window_block(utc(2026, 8, 13, 15), "NDX.INDX", CFG1)[0]  # Per


def test_weekend_hold_only_friday_late():
    cfg = Cfg(NDX_SESSION_BLOCK_ENABLED=False, NDX_FRIDAY_BLOCK=False,
              NDX_WEEKEND_HOLD_BLOCK=True)
    assert pr.entry_window_block(utc(2026, 8, 14, 20, 50), "NDX.INDX", cfg)[0]
    assert not pr.entry_window_block(utc(2026, 8, 14, 20, 30), "NDX.INDX", cfg)[0]


def test_other_symbols_not_blocked():
    for sym in ("USOIL.FOREX", "GDAXI.INDX", "XAUUSD"):
        assert not pr.entry_window_block(utc(2026, 8, 14, 3), sym, CFG1)[0]


def test_windows_off_by_default():
    assert not pr.entry_window_block(utc(2026, 8, 14, 3), "NDX.INDX", None)[0]


# ── FAZ 1.3/1.4 ────────────────────────────────────────────────────────────

def test_sr_arm_toggle():
    assert pr.sr_entry_allowed("NDX.INDX", None)                    # varsayılan açık
    assert not pr.sr_entry_allowed("NDX.INDX", Cfg(NDX_SR_ENTRY_ENABLED=False))
    assert pr.sr_entry_allowed("USOIL.FOREX", Cfg(NDX_SR_ENTRY_ENABLED=False))


def test_config_restore():
    assert pr.only_confirm_required(None) is None
    assert pr.only_confirm_required(Cfg(PHASE1_CONFIG_RESTORE=True)) is True
    assert pr.zone_min_touch(None, current=2) == 2
    assert pr.zone_min_touch(Cfg(PHASE1_CONFIG_RESTORE=True), current=2) == 4


# ── FAZ 2 — dalga konumu + RSI ─────────────────────────────────────────────

def test_wave_position_scales():
    b = bars([(110, 90, 100)] * 48)
    assert pr.wave_position(b, 90) == pytest.approx(0.0)
    assert pr.wave_position(b, 110) == pytest.approx(1.0)
    assert pr.wave_position(b, 100) == pytest.approx(0.5)


def test_position_gate_thresholds():
    assert pr.position_gate_blocks("SELL", 0.59, 0.60, 0.40)
    assert not pr.position_gate_blocks("SELL", 0.61, 0.60, 0.40)
    assert pr.position_gate_blocks("BUY", 0.41, 0.60, 0.40)
    assert not pr.position_gate_blocks("BUY", 0.39, 0.60, 0.40)
    assert not pr.position_gate_blocks("SELL", None, 0.60, 0.40)   # fail-open


def test_rsi_extremes():
    assert pr.rsi([float(i) for i in range(40)], 14) == pytest.approx(100.0)
    assert pr.rsi([float(40 - i) for i in range(40)], 14) == pytest.approx(0.0, abs=1e-6)
    assert pr.rsi([1.0, 2.0], 14) is None


# ── FAZ 3 — probasyon ──────────────────────────────────────────────────────

def test_probation_band_formula():
    assert pr.probation_band(10.0, 5, 1.28) == pytest.approx(1.28 * 10 * 5 ** 0.5)


def test_probation_cancels_when_band_exceeded():
    # ATR=10 → band ≈ 28.6
    b = bars([(100, 95, 98)] * 4 + [(100, 60, 70)])       # BUY aleyhine 40
    cancel, adverse, band = pr.probation_verdict("BUY", 100.0, 10.0, b)
    assert cancel and adverse == pytest.approx(40.0) and band == pytest.approx(28.62, abs=0.1)


def test_probation_allows_inside_band():
    b = bars([(101, 95, 99)] * 5)                          # aleyhe 5
    cancel, adverse, _ = pr.probation_verdict("BUY", 100.0, 10.0, b)
    assert not cancel and adverse == pytest.approx(5.0)


def test_probation_sell_side():
    b = bars([(140, 99, 120)] * 5)                         # SELL aleyhine 40
    cancel, adverse, _ = pr.probation_verdict("SELL", 100.0, 10.0, b)
    assert cancel and adverse == pytest.approx(40.0)


def test_probation_uses_only_first_n_bars():
    b = bars([(101, 99, 100)] * 5 + [(200, 50, 60)])       # 6. bar sayılmamalı
    cancel, adverse, _ = pr.probation_verdict("BUY", 100.0, 10.0, b, bars=5)
    assert not cancel and adverse == pytest.approx(1.0)


# ── opsiyonel soğuma ───────────────────────────────────────────────────────

def test_loss_cooldown_disabled_by_default():
    assert pr.loss_streak_cooldown_active(1000.0, 5, 1060.0, None)[0] is False


def test_loss_cooldown_when_enabled():
    cfg = Cfg(SCOPE_LOSS_COOLDOWN_ENABLED=True, SCOPE_LOSS_COOLDOWN_MIN=120,
              SCOPE_LOSS_COOLDOWN_STREAK=2)
    active, left = pr.loss_streak_cooldown_active(1000.0, 2, 1000.0 + 60 * 60, cfg)
    assert active and left == pytest.approx(60.0)
    assert not pr.loss_streak_cooldown_active(1000.0, 1, 1000.0 + 60, cfg)[0]
    assert not pr.loss_streak_cooldown_active(1000.0, 2, 1000.0 + 121 * 60, cfg)[0]
