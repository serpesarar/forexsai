"""Kural DENKLİK testi: koddaki kurallar, analizin ölçtüğü kuralların aynısı mı?

Gerçek 133 NASDAQ işlemi + 33.353 adet 1m bar üzerinde karşı-olgusal replay
çalıştırır ve analizin bildirdiği referans rakamlarla karşılaştırır. Tutarsa
`phase_rules` içindeki eşikler/tanımlar analizle birebir aynı demektir.

Veri `1MDATA/` altında ve .gitignore'da → veri yoksa test ATLANIR (CI'da sorun
çıkarmaz, geliştiricide gerçek doğrulama yapar).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "1MDATA" / "mt5_islem_analizi"
REPLAY = DATA / "04_phase_replay.py"

pytestmark = pytest.mark.skipif(
    not (REPLAY.exists() and (DATA / "nasdaq_1m.csv").exists()
         and (DATA / "trades_nasdaq.csv").exists()),
    reason="1MDATA replay verisi yok (gitignore) — denklik testi atlandı")


@pytest.fixture(scope="module")
def rep():
    sys.path.insert(0, str(ROOT / "yeni deneme"))
    spec = importlib.util.spec_from_file_location("phase_replay", REPLAY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def data(rep):
    return rep.load()


PHASE1 = dict(NDX_SESSION_BLOCK_ENABLED=True,
              NDX_SESSION_BLOCK=(("22:00", "07:00"),),
              NDX_FRIDAY_BLOCK=True, NDX_WEEKEND_HOLD_BLOCK=True,
              NDX_SR_ENTRY_ENABLED=False)
OFF = dict(NDX_SESSION_BLOCK_ENABLED=False, NDX_FRIDAY_BLOCK=False,
           NDX_WEEKEND_HOLD_BLOCK=False, NDX_SR_ENTRY_ENABLED=True)


def _run(rep, data, cfg_kw, filt_kw=None, probation=False):
    bars, times, trades = data
    cfg = rep.Cfg(**cfg_kw)
    filt = rep.Cfg(**filt_kw) if filt_kw else None
    rows = []
    for t in trades:
        if filt is not None:
            ok, _ = rep.passes_phase1(t, filt)
            if not ok:
                continue
        r = rep.simulate(t, bars, times, cfg, probation=probation)
        if r:
            rows.append(r)
    res = [r for r in rows if r.get("win") is not None]
    wr = 100 * sum(1 for r in res if r["win"]) / len(res) if res else 0.0
    return len(res), wr, sum(r["pnl"] for r in rows)


def test_simulator_matches_reference_calibration(rep, data):
    """Analizin simülatör kalibrasyonu: mevcut kurallar (BE'siz) → WR %60.2."""
    n, wr, _ = _run(rep, data, {**OFF, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0})
    assert n == 133
    assert wr == pytest.approx(60.2, abs=0.6)


def test_phase1_filters_select_the_same_71_trades(rep, data):
    """Faz-1 giriş filtreleri analizle AYNI alt kümeyi seçmeli (n=71)."""
    n, _, _ = _run(rep, data,
                   {**PHASE1, "TP_MODE": "atr", "TP_ATR_MULT": 2.5,
                    "TP_ATR_PERIOD": 70, "MGMT_TIME_STOP_MIN": 0},
                   filt_kw=PHASE1)
    assert n == 71


def test_atr_tp_is_the_strongest_single_lever(rep, data):
    """TP=2.5×ATR70 tek başına WR'ı ~%71-74'e taşımalı (analiz: %71.4)."""
    n, wr, net = _run(rep, data, {**OFF, "TP_MODE": "atr", "TP_ATR_MULT": 2.5,
                                  "TP_ATR_PERIOD": 70, "MGMT_TIME_STOP_MIN": 0})
    assert n == 133
    assert wr > 70.0
    base_n, base_wr, base_net = _run(
        rep, data, {**OFF, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0})
    assert wr - base_wr > 10.0
    assert net > base_net


def test_mod_e_reproduces_reference_numbers(rep, data):
    """MOD-E (probasyon + TP80, Faz-1 filtreli): analiz n=65, WR %75.4, +8.537$."""
    n, wr, net = _run(rep, data,
                      {**PHASE1, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0,
                       "PROBATION_BARS": 5, "PROBATION_Z": 1.28},
                      filt_kw=PHASE1, probation=True)
    assert n == 65
    assert wr == pytest.approx(75.4, abs=0.5)
    assert net == pytest.approx(8537, abs=50)


def test_probation_plus_small_tp_is_worse(rep, data):
    """Yasak kombinasyon: probasyon + ATR TP, MOD-E'den belirgin KÖTÜ olmalı."""
    _, _, mod_e = _run(rep, data,
                       {**PHASE1, "TP_MODE": "fixed", "MGMT_TIME_STOP_MIN": 0,
                        "PROBATION_BARS": 5, "PROBATION_Z": 1.28},
                       filt_kw=PHASE1, probation=True)
    _, _, combo = _run(rep, data,
                       {**PHASE1, "TP_MODE": "atr", "TP_ATR_MULT": 2.5,
                        "TP_ATR_PERIOD": 70, "MGMT_TIME_STOP_MIN": 0,
                        "PROBATION_BARS": 5, "PROBATION_Z": 1.28},
                       filt_kw=PHASE1, probation=True)
    assert combo < mod_e


def test_time_stop_120_costs_money_240_is_cheap(rep, data):
    """Varsayılanın neden 240 olduğunun kilidi (plan 120 diyordu)."""
    base = {**OFF, "TP_MODE": "atr", "TP_ATR_MULT": 2.5, "TP_ATR_PERIOD": 70}
    _, _, no_stop = _run(rep, data, {**base, "MGMT_TIME_STOP_MIN": 0})
    _, _, s120 = _run(rep, data, {**base, "MGMT_TIME_STOP_MIN": 120})
    _, _, s240 = _run(rep, data, {**base, "MGMT_TIME_STOP_MIN": 240})
    assert s120 < no_stop - 500          # 120 dk belirgin zararlı
    assert s240 > s120                   # 240 dk daha iyi
    assert abs(no_stop - s240) < 200     # 240 dk neredeyse nötr
