"""c3b_shadow.py birim testleri (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 -m pytest test_c3b_shadow.py"""
import ast
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import c3b_shadow as c3
import caprev_shadow as cs


def t_at(d: date, minute: int) -> int:
    return int(cs.local_to_utc(d, minute, "US"))


def bar(d: date, minute: int, o: float, c: float) -> dict:
    return {"t": t_at(d, minute), "open": o, "high": max(o, c), "low": min(o, c), "close": c}


def days(n: int, start: date = date(2026, 3, 2)) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def make_bars(closes: list[float], opens: list[float] | None = None) -> list[dict]:
    rows = []
    for k, (d, s) in enumerate(zip(days(len(closes)), closes)):
        rows.append(bar(d, 900, s, s))
        rows.append(bar(d, 930, opens[k] if opens else s, s))
    return rows


def test_no_order_call_in_module():
    tree = ast.parse(Path(c3.__file__).read_text(encoding="utf-8"))
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {"order_send", "order_check", "Close", "positions_get"}


def test_series_takes_close_before_1530_and_open_of_1530():
    d = days(1)[0]
    s = c3.daily_series([bar(d, 900, 100, 101), bar(d, 930, 102, 103), bar(d, 960, 103, 104)])
    assert s[0]["S"] == 101 and s[0]["E"] == 102


def test_series_drops_gap_before_entry():
    d = days(1)[0]
    assert c3.daily_series([bar(d, 600, 100, 101), bar(d, 930, 102, 103)]) == []


def test_rsi_matches_pandas_recursion():
    v = [100, 101, 99, 98, 99, 102, 101, 97, 96, 100, 103, 102.5]
    s = pd.Series(v, dtype=float); g = s.diff()
    up = g.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-g.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
    exp = (100 - 100 / (1 + up / (dn + 1e-12))).to_numpy()
    assert np.allclose(c3.rsi2(v)[1:], exp[1:], atol=1e-6)


def test_replay_exit_on_first_rising_s():
    closes = [100, 101, 102, 100, 97, 94, 95, 96]
    tr = c3.replay(c3.daily_series(make_bars(closes)))
    assert len(tr) >= 1 and tr[0]["how"] == "yukselis"
    assert tr[0]["exit_d"] == str(days(len(closes))[6])


def test_replay_time_exit_after_five_days():
    closes = [100, 101, 102] + [100 - i for i in range(9)]
    tr = c3.replay(c3.daily_series(make_bars(closes)))
    assert tr[0]["how"] == "sure" and tr[0]["days"] == 5


def test_model_bp_costs():
    assert c3.model_bp(1000, 1000, 2, spread=0) == -4.0
    assert c3.model_bp(1000, 1010, 1, spread=0) == pytest.approx(98.0, abs=.01)


def test_summarize_arms():
    r = [{"kind": "signal"}, {"kind": "result", "arm": "C3b", "bp_model": 50, "bp_fill": 40},
         {"kind": "result", "arm": "C3", "bp_model": -10, "bp_fill": None}]
    s = c3.summarize(r)
    assert s["sinyal"] == 1 and s["C3b"]["bp_fill"] == 40 and s["C3"]["n_fill"] == 0


class FakeMT5:
    TIMEFRAME_M30 = 30

    def __init__(self, bars):
        self.bars = bars

    def copy_rates_from_pos(self, sym, tf, pos, n):
        return np.array([(b["t"], b["open"], b["high"], b["low"], b["close"]) for b in self.bars],
                        dtype=[("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8")])

    def symbol_info_tick(self, sym):
        return SimpleNamespace(ask=95.0, bid=94.0, time=0)


LOG = SimpleNamespace(info=lambda *a, **k: None, debug=lambda *a, **k: None)


@pytest.fixture
def tmp_state(tmp_path, monkeypatch):
    monkeypatch.setattr(c3, "EVENTS_JSONL", tmp_path / "e.jsonl")
    monkeypatch.setattr(c3, "STATE_FILE", tmp_path / "s.json")
    monkeypatch.setattr(c3, "CAPREV_STATE", tmp_path / "yok.json")
    return tmp_path


def _poll(mt, now):
    c3.poll(mt, LOG, lambda m: "NAS100", lambda: 20.0, lambda s: 0, now=now, force=True)


def test_poll_first_start_does_not_replay_history(tmp_state):
    closes = [100, 101, 102, 100, 97, 94]
    ds = days(len(closes))
    _poll(FakeMT5(make_bars(closes)), t_at(ds[-1], 932))
    lines = c3.EVENTS_JSONL.read_text().splitlines()
    assert len(lines) == 1 and '"kind": "signal"' in lines[0] and str(ds[-1]) in lines[0]


def test_poll_full_cycle_and_once_per_day(tmp_state):
    closes = [100, 101, 102, 100, 97, 94, 95]
    ds = days(len(closes))
    bars = make_bars(closes)
    _poll(FakeMT5(bars[:-2]), t_at(ds[5], 932))
    _poll(FakeMT5(bars[:-2]), t_at(ds[5], 934))
    _poll(FakeMT5(bars), t_at(ds[6], 932))
    lines = c3.EVENTS_JSONL.read_text().splitlines()
    assert sum('"kind": "signal"' in x for x in lines) == 1
    assert sum('"arm": "C3b"' in x for x in lines) == 1 and sum('"arm": "C3"' in x for x in lines) == 1


def test_poll_before_1530_silent(tmp_state):
    closes = [100, 101, 102, 100, 97, 94]
    ds = days(len(closes))
    mt = FakeMT5(make_bars(closes))
    _poll(mt, t_at(ds[-1], 900))
    assert not c3.EVENTS_JSONL.exists()


def test_late_detection_has_no_fill(tmp_state):
    closes = [100, 101, 102, 100, 97, 94]
    ds = days(len(closes))
    _poll(FakeMT5(make_bars(closes)), t_at(ds[-1], 945))
    assert '"fill": null' in c3.EVENTS_JSONL.read_text()
