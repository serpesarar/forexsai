"""BTC optimizasyon harness'ı — ortak sabitler, yollar, bölmeler, holdout kilidi.

Bütün zamanlar UTC **epoch dakika** (int64). Bar `ts` = açılış; karar anı = kapanış (ts + TF).
Maliyet modeli research/btc_scalp_20261021/strateji/lib_st.py ile birebir (MT5 tarzı, yol-içi bid/ask).
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

HARNESS = Path(__file__).resolve().parent
RESEARCH = HARNESS.parent.parent
PANEL = RESEARCH.parent
PY = str(PANEL / ".venv" / "bin" / "python")
CACHE = HARNESS / "cache"
EVENTS = HARNESS / "events"
RESULTS = HARNESS / "results"
LOGS = HARNESS / "logs"
for _d in (CACHE, EVENTS, RESULTS, LOGS):
    _d.mkdir(exist_ok=True)

R5 = RESEARCH / "btc_5y_20261021"
RS = RESEARCH / "btc_scalp_20261021"
RI = RESEARCH / "btc_indep_2017_2021"

DATA_DIRS = {"main": R5 / "data", "indep": RI / "data"}
SCALP_1M = {"main": RS / "data" / "btc_scalp_1m.parquet", "indep": RI / "data" / "btc_scalp_1m.parquet"}


def m(ts: str) -> int:
    """UTC zaman dizgesi → epoch dakika."""
    return int(pd.Timestamp(ts, tz="UTC").value // 60_000_000_000)


# ─────────────────────────── maliyet (lib_st ile birebir) ───────────────────────────
SPREAD = {"base": 0.000185, "stress": 0.0002775}   # gidiş-dönüş, fiyat oranı
SPREAD_ABS = 15.0                                   # $ gidiş-dönüş (sabit 15 $ varyantı)
SWAP_LONG = -0.14 / 365                             # rollover başına, giriş nominali oranı
SWAP_SHORT = 0.02 / 365
SLIP_BP, SLIP_HOT_BP = 1.0, 5.0                     # SL/stop dolumuna ek kayma
HOT_THR_BP = 29.298164936615546                     # dondurulmuş: ana DISC |1m log getiri| p99 (lib_st / port ile aynı)
MAX_DELAY = 10                                      # giriş gecikmesi tavanı (dk)
COST_MODES = ("base", "stress", "abs", "opt")

# ─────────────────────────── dönemler ───────────────────────────
MAIN_START, MAIN_END = m("2021-06-01"), m("2026-10-21")
INDEP_START, INDEP_END = m("2017-08-17"), m("2021-06-01")
EX0, EX1 = m("2023-03-24 11:28"), m("2023-03-24 14:00")   # Binance spot durdurması (yalnız ana veri)
METRICS_SWITCH = m("2024-03-04")                          # E71: metrics damga anlamı değişimi (nedensel eff_ts ile çözülü)

# önceki turların bölmeleri (yalnız bilgi / doğrulama için)
SPLITS_PRIOR = {"DISC": (m("2021-06-01"), m("2024-01-01")),
                "OOS": (m("2024-01-11"), m("2025-07-01")),
                "BLIND": (m("2025-07-01"), m("2026-10-21"))}

TF_MIN = {"5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}

# ─────────────────────────── holdout kilidi ───────────────────────────
HOLDOUT_TOKEN = "I_UNDERSTAND_THIS_SPENDS_THE_2017_2021_HOLDOUT"
HOLDOUT_LEDGER = HARNESS / "HOLDOUT_LEDGER.jsonl"


class HoldoutError(RuntimeError):
    """Bağımsız 2017-08→2021-05 verisine izinsiz sonuç erişimi."""


def assert_main(data: str) -> None:
    """Optimizasyon/WFO yalnız ana veride koşar."""
    if data != "main":
        raise HoldoutError(
            f"data={data!r}: optimizasyon/WFO/tarama yalnız 'main' veride yapılabilir. Bağımsız dönem yalnız "
            "holdout.evaluate_frozen_on_holdout(...) ile, donmuş spec ve açık token ile değerlendirilir.")


def holdout_unlocked() -> bool:
    return os.environ.get("BTC_HARNESS_HOLDOUT_TOKEN") == HOLDOUT_TOKEN
