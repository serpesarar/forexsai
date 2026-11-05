"""prediction_logger._range_band_tag — bant etiketi + gölge verdikti; önbellek yoksa etiketsiz (fail-open)."""
from services import prediction_logger as pl
from services import time_machine_service as tm

BAND = {"rel_p5": 0.99, "rel_p25": 0.997, "rel_p50": 1.0, "rel_p75": 1.003, "rel_p95": 1.01, "width_pct": 2.0}


def test_tag_outside_band_creates_shadow_verdict(monkeypatch):
    monkeypatch.setattr(tm, "peek_range_band", lambda s, *a, **k: BAND)
    f = {}
    v = pl._range_band_tag("NDX.INDX", "BUY", 100.0, {"TP1": 102.0, "SL": 99.9}, f)
    assert v and v["gate"] == "range_tp_gate"
    assert f["tp1_outside_p90"] is True and f["sl_inside_p50"] is True and f["tm_band60"]["p95"] == 101.0


def test_tag_inside_band_no_verdict_and_env_off(monkeypatch):
    monkeypatch.setattr(tm, "peek_range_band", lambda s, *a, **k: BAND)
    f = {}
    assert pl._range_band_tag("NDX.INDX", "SELL", 100.0, {"TP1": 99.5}, f) is None and f["tp1_outside_p90"] is False
    monkeypatch.setenv("RANGE_TP_GATE_ENABLED", "0")
    f2 = {}
    assert pl._range_band_tag("NDX.INDX", "BUY", 100.0, {"TP1": 105.0}, f2) is None and f2["tp1_outside_p90"] is True


def test_tag_without_cached_band_is_silent(monkeypatch):
    monkeypatch.setattr(tm, "peek_range_band", lambda s, *a, **k: None)
    f = {}
    assert pl._range_band_tag("NDX.INDX", "BUY", 100.0, {"TP1": 105.0}, f) is None and f == {}
