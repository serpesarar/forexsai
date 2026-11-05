"""orb_vix_shadow.py birim testleri (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 -m pytest test_orb_vix_shadow.py"""
import ast
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import caprev_shadow as cs
import orb_vix_shadow as ov

DAY = date(2026, 10, 5)      # Pazartesi, EDT: 09:30 ET = 13:30Z


def t_at(minute: int, day: date = DAY) -> float:
    return cs.local_to_utc(day, minute, "US")


def bar(minute: int, o: float, h: float, l: float, c: float, day: date = DAY) -> dict:
    return {"t": int(t_at(minute, day)), "open": o, "high": h, "low": l, "close": c}


def or_bars(day: date = DAY) -> list[dict]:
    return [bar(570, 100, 105, 99, 103, day), bar(575, 103, 110, 102, 104, day), bar(580, 104, 106, 90, 100, day)]


def test_no_order_call_in_module():
    """Gölge modülü emir gönderemez: kaynakta order_send / order_check / positions_get çağrısı yok."""
    tree = ast.parse(Path(ov.__file__).read_text(encoding="utf-8"))
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {"order_send", "order_check", "Close", "positions_get"}


def test_trigger_is_first_close_above_or_high():
    bars = or_bars() + [bar(585, 100, 109, 99, 108), bar(590, 108, 112, 107, 111), bar(595, 111, 113, 110, 112)]
    trig = ov.find_trigger(ov.session_bars(bars, DAY))
    assert trig["oh"] == 110 and trig["ol"] == 90 and trig["stop"] == 100
    assert trig["trig_close"] == 111 and trig["trig_t"] == int(t_at(590))
    assert trig["entry_t"] == int(t_at(595)) and trig["entry_open"] == 111


def test_wick_above_high_is_not_a_trigger():
    bars = or_bars() + [bar(585, 100, 120, 99, 109)]
    assert ov.find_trigger(ov.session_bars(bars, DAY)) is None


def test_or_needs_three_bars():
    bars = or_bars()[:2] + [bar(585, 100, 130, 99, 125)]
    assert ov.find_trigger(ov.session_bars(bars, DAY)) is None


def test_no_new_entry_after_1530():
    """Bar bitişi 15:30'u aşan kırılım sayılmaz; 15:25 barı (bitiş 15:30) sayılır."""
    last_ok = 925  # 15:25
    flat = [bar(m, 100, 101, 99, 100) for m in range(585, last_ok, 5)]
    ok = or_bars() + flat + [bar(last_ok, 100, 112, 99, 111), bar(930, 111, 112, 110, 111)]
    assert ov.find_trigger(ov.session_bars(ok, DAY))["trig_t"] == int(t_at(last_ok))
    flat2 = [bar(m, 100, 101, 99, 100) for m in range(585, 930, 5)]
    late = or_bars() + flat2 + [bar(930, 100, 112, 99, 111), bar(935, 111, 112, 110, 111)]
    assert ov.find_trigger(ov.session_bars(late, DAY)) is None


def test_bars_of_other_days_and_premarket_ignored():
    prev = DAY - timedelta(days=3)
    bars = [bar(570, 100, 500, 1, 400, prev), bar(560, 100, 500, 1, 400)] + or_bars()
    sess = ov.session_bars(bars, DAY)
    assert len(sess) == 3 and min(b["m"] for b in sess) == 570


def test_dst_winter_session():
    winter = date(2026, 12, 7)
    assert t_at(570, winter) - cs.local_to_utc(winter, 0, "US") == 570 * 60
    bars = or_bars(winter) + [bar(585, 100, 112, 99, 111, winter), bar(590, 111, 112, 110, 111, winter)]
    assert ov.find_trigger(ov.session_bars(bars, winter))["oh"] == 110


def test_walk_stop_wins_same_bar():
    assert ov.walk([{"low": 95, "high": 200}], 110, 100)[:2] == (-1.0, "sl")


def test_walk_target_and_open():
    assert ov.walk([{"low": 105, "high": 130}], 110, 100)[:2] == (2.0, "tp")
    assert ov.walk([{"low": 105, "high": 125}], 110, 100)[:2] == (None, None)


def _ev(fill=112.0, detect_min=596, spread=1.0):
    return {"id": "x", "day": str(DAY), "arm": "hi", "stop": 100.0, "entry_model": None, "fill": fill,
            "detect_t": t_at(detect_min), "spread": spread, "status": "open"}


def _trigger_bars(after):
    return or_bars() + [bar(585, 100, 109, 99, 108), bar(590, 108, 112, 107, 111)] + after


def test_resolve_model_entry_includes_spread_and_tp():
    m5 = _trigger_bars([bar(595, 111, 113, 110, 112), bar(600, 112, 140, 111, 139)])
    m1 = [bar(597, 112, 140, 111, 139)]
    out = ov.resolve_event(_ev(), m5, m1, t_at(610))
    assert out["entry_model"] == 112.0 and out["R_model"] == 2.0 and out["how_model"] == "tp"
    assert out["R_fill"] == 2.0 and out["status"] == "done"


def test_resolve_time_exit_only_after_session_end():
    m5 = _trigger_bars([bar(595, 111, 113, 110, 112), bar(950, 112, 114, 111, 113)])
    m1 = [bar(597, 112, 114, 111, 113), bar(954, 113, 114, 112, 113)]
    open_ = ov.resolve_event(_ev(), m5, m1, t_at(951))
    assert open_["status"] == "open" and open_.get("R_model") is None
    done = ov.resolve_event(_ev(), m5, m1, t_at(956))
    assert done["status"] == "done" and done["how_model"] == "time" and done["R_model"] == pytest.approx(1 / 12, abs=1e-3)


def test_resolve_narrow_risk_invalid():
    ev = _ev(); ev["stop"] = 111.99
    m5 = _trigger_bars([bar(595, 111, 113, 110, 112)])
    assert ov.resolve_event(ev, m5, [], t_at(600))["status"] == "invalid"


def test_late_event_measures_only_model():
    m5 = _trigger_bars([bar(595, 111, 113, 110, 112), bar(600, 112, 140, 111, 139)])
    out = ov.resolve_event(_ev(fill=None), m5, [], t_at(610))
    assert out["status"] == "done" and out["R_model"] == 2.0 and out.get("R_fill") is None


def test_arm_threshold():
    assert ov.arm_of(18.4) == "hi" and ov.arm_of(18.39) == "lo" and ov.arm_of(None) == "unknown"


def test_summarize_splits_arms():
    rec = [{"kind": "event"}, {"kind": "event"},
           {"kind": "result", "status": "done", "arm": "hi", "R_model": 2.0, "R_fill": 1.5, "spread": 1, "latency_s": 40},
           {"kind": "result", "status": "done", "arm": "lo", "R_model": -1.0, "R_fill": None, "spread": 1, "latency_s": 20},
           {"kind": "result", "status": "invalid", "arm": "hi"}]
    s = ov.summarize(rec)
    assert s["olay"] == 2 and s["cozulen"] == 2
    assert s["kollar"]["hi"]["R_model"] == 2.0 and s["kollar"]["lo"]["n_fill"] == 0


class FakeMT5:
    TIMEFRAME_M5, TIMEFRAME_M1 = 5, 1

    def __init__(self, bars):
        self.calls = []
        rec = np.array([(b["t"], b["open"], b["high"], b["low"], b["close"]) for b in bars],
                       dtype=[("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8")])
        self.rec = rec

    def copy_rates_from_pos(self, sym, tf, pos, n):
        self.calls.append(tf)
        return self.rec

    def symbol_info_tick(self, sym):
        return SimpleNamespace(ask=112.0, bid=111.0, time=0)


def _log():
    return SimpleNamespace(info=lambda *a, **k: None, debug=lambda *a, **k: None)


@pytest.fixture
def tmp_state(tmp_path, monkeypatch):
    monkeypatch.setattr(ov, "EVENTS_JSONL", tmp_path / "e.jsonl")
    monkeypatch.setattr(ov, "STATE_FILE", tmp_path / "s.json")
    monkeypatch.setattr(ov, "CAPREV_STATE", tmp_path / "yok.json")
    return tmp_path


def test_poll_records_once_and_uses_previous_day_vix(tmp_state):
    prior = str(DAY - timedelta(days=3))
    ov.STATE_FILE.write_text('{"vix_hist": {"%s": 20.0}}' % prior)
    mt = FakeMT5(_trigger_bars([bar(595, 111, 113, 110, 112)]))
    # canlı VIX 15 olsa da kol dünkü kapanışa bakar (kart ile aynı, sızıntı yok)
    ov.poll(mt, _log(), lambda m: "NAS100", lambda: 15.0, lambda s: 0, now=t_at(597), force=True)
    ov.poll(mt, _log(), lambda m: "NAS100", lambda: 15.0, lambda s: 0, now=t_at(599), force=True)
    lines = ov.EVENTS_JSONL.read_text().splitlines()
    assert len([x for x in lines if '"kind": "event"' in x]) == 1
    assert '"arm": "hi"' in lines[0] and '"vix_prev": 20.0' in lines[0]


def test_poll_silent_outside_window(tmp_state):
    mt = FakeMT5(_trigger_bars([]))
    ov.poll(mt, _log(), lambda m: "NAS100", lambda: 20.0, lambda s: 0, now=t_at(575), force=True)
    assert not ov.EVENTS_JSONL.exists() and mt.calls == []


def test_poll_resolves_and_writes_result(tmp_state):
    mt = FakeMT5(_trigger_bars([bar(595, 111, 113, 110, 112), bar(600, 112, 140, 111, 139)]))
    ov.poll(mt, _log(), lambda m: "NAS100", lambda: 20.0, lambda s: 0, now=t_at(605), force=True)
    lines = ov.EVENTS_JSONL.read_text().splitlines()
    assert any('"kind": "result"' in x and '"R_model": 2.0' in x for x in lines)
