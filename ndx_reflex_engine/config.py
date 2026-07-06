"""NDX Reflex Engine — central configuration.

All constants live here. No magic numbers in pipeline/trigger/model code.
Paths are Mac-side research paths; live/ modules get their own config on the MT5 box.
"""
from __future__ import annotations

import os
from datetime import date

# ── Paths ────────────────────────────────────────────────────────────────────
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ENGINE_DIR, "data")
TICKS_RAW_DIR = os.path.expanduser("~/dukascopy_us100/data")
TICKS_PARQUET_DIR = os.path.join(DATA_DIR, "ticks")
BARS_DIR = os.path.join(DATA_DIR, "bars_1m")
GAPS_PATH = os.path.join(DATA_DIR, "gap_registry.parquet")
EVENTS_DIR = os.path.join(DATA_DIR, "events")
MODELS_DIR = os.path.join(DATA_DIR, "models")

# ── Instrument / session (all times UTC) ─────────────────────────────────────
SYMBOL_PROXY = "usatechidxusd"          # Dukascopy US Tech 100 CFD (research proxy)
SYMBOL_BROKER = "USTEC"                 # IC Markets live instrument
SYMBOL_CANON = "NDX.INDX"              # panel-canonical name

# NY cash session in UTC. 2025 US DST: Mar 9 – Nov 2 ⇒ cash open 13:30 UTC (else 14:30).
US_CORE_HOURS_UTC = (13, 21)            # audit window used for completeness checks
DST_2025 = (date(2025, 3, 9), date(2025, 11, 2))

# Scalper trading window (events allowed) and hard flat time.
EVENT_WINDOW_UTC = (13, 20)             # generate/trade events 13:00–20:00 UTC
FLAT_BY_UTC = "20:45"                   # all labels must resolve before this

# NYSE 2025 full holidays + special closures (proxy follows US index hours).
HOLIDAYS_2025 = {
    date(2025, 1, 1), date(2025, 1, 9), date(2025, 1, 20), date(2025, 2, 17),
    date(2025, 4, 18), date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 4),
    date(2025, 9, 1), date(2025, 11, 27), date(2025, 12, 25),
}
EARLY_CLOSE_2025 = {date(2025, 7, 3), date(2025, 11, 28), date(2025, 12, 24)}

# ── Tick → bar aggregation ───────────────────────────────────────────────────
BAR_MINUTES = 1
GAP_MAX_SILENT_MIN = 5                  # >5 silent minutes inside session ⇒ gap
MICRO_WINDOWS_S = (30, 60, 300)         # event-time trailing tick windows (Tier B)

# ── Labeling (triple barrier) ────────────────────────────────────────────────
TB_TP_ATR_GRID = (0.5, 0.75, 1.0, 1.5)
TB_SL_ATR_GRID = (0.75, 1.0, 1.5)
TB_TIME_STOP_MIN_GRID = (30, 60, 120)
ATR_PERIOD = 14                         # on 1m mid bars
AMBIGUOUS_BAR_IS_LOSS = True            # TP+SL same bar ⇒ LOSS (conservative)

# ── Trigger parameters (kept aligned with validated live logic) ─────────────
CHAN_WINDOW = 50                        # linreg channel window (claude_decider WIN_N)
CHAN_Z_TRIGGER = 2.0
VWAP_Z_TRIGGER = 1.5
SR_ZONE_MIN_TOUCHES = 4                 # bot sr_zones params
SR_ZONE_WIDTH_PTS = 10.0
SR_ZONE_LOOKBACK = 100                  # 1m bars
SWEEP_MAX_PIERCE_ATR = 0.6
SWEEP_RECLAIM_BARS = 3
ORB_MINUTES = 15
MOM_STRETCH_ATR = 2.0                   # bot MOMENTUM_EXCESS_ATR
FAMILY_REFRACTORY_MIN = 30              # per-family cool-off after an event
DEDUP_MIN = 60                          # dedup window for all reported statistics

# ── Model / decision ─────────────────────────────────────────────────────────
MIN_TRAIN_EVENTS_PER_FAMILY = 400
FRICTION_SPREAD_MULT = 1.5              # proxy-spread safety multiplier
SLIPPAGE_PTS = 1.0
EV_MARGIN_R = 0.05                      # required EV margin in R units
WF_FOLDS = 6
WF_EMBARGO_DAYS = 1
BOOTSTRAP_P_EV_POS = 0.975
PLACEBO_SHIFTS = 200
PLACEBO_SHIFT_MIN = (30, 180)           # random |shift| range, minutes

LGBM_PARAMS = {
    "objective": "binary",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": 5,
    "min_child_samples": 50,
    "feature_fraction": 0.7,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "verbosity": -1,
    "seed": 20260704,
}
