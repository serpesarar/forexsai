"""dax_fomc_shadow.py birim testleri (MT5 gerekmez).
Çalıştır:  cd 'yeni deneme' && python3 -m pytest test_dax_fomc_shadow.py"""
import ast
import logging
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

import caprev_shadow as cs
import dax_fomc_shadow as df

LOG = logging.getLogger("test")
FOMC = date(2026, 12, 9)           # Çarşamba
ENTRY = date(2026, 12, 8)          # Salı


def t_at(d: date, minute: int) -> int:
    return int(cs.local_to_utc(d, minute, "EU"))


def bar(d: date, minute: int, o: float) -> dict:
    return {"t": t_at(d, minute), "open": o, "high": o + 5, "low": o - 5, "close": o}


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "EVENTS_JSONL", tmp_path / "ev.jsonl")
    monkeypatch.setattr(df, "STATE_FILE", tmp_path / "st.json")
    monkeypatch.setattr(df, "CAPREV_STATE", tmp_path / "none.json")
    return tmp_path


def records(tmp):
    import json
    p = tmp / "ev.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def test_no_order_calls():
    src = Path(df.__file__).read_text(encoding="utf-8")
    names = {n.attr for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Attribute)}
    assert "order_send" not in names and "TRADE_ACTION_DEAL" not in names


def test_prev_weekday_skips_weekend():
    assert df.prev_weekday(date(2026, 11, 2)) == date(2026, 10, 30)   # Pazartesi → Cuma
    assert df.prev_weekday(FOMC) == ENTRY


def test_calendar_and_override():
    ds = df.fomc_dates()
    assert ds == sorted(ds) and all(d.weekday() < 5 for d in ds)
    assert df.fomc_dates(SimpleNamespace(DAX_FOMC_DATES=["2027-01-27"])) == [date(2027, 1, 27)]
    assert df.next_event(date(2026, 11, 12), ds) == FOMC


def test_bar_open_at_berlin_time():
    bars = [bar(ENTRY, 17 * 60, 100.0), bar(ENTRY, 17 * 60 + 30, 101.0)]
    assert df.bar_open_at(bars, ENTRY, df.ENTRY_MIN)["open"] == 101.0
    assert df.bar_open_at(bars, ENTRY, 18 * 60) is None


def test_model_bp():
    assert df.model_bp(100.0, 101.0, 1, spread=0.0) == pytest.approx(100.0 - df.SWAP_BP_NIGHT)


def test_full_cycle_entry_then_exit(files):
    st = df._load_state()
    ds = [FOMC]
    bars = [bar(ENTRY, df.ENTRY_MIN, 24000.0)]
    now = t_at(ENTRY, df.ENTRY_MIN) + 60
    assert df.step(st, bars, now, ds, (24001.0, 24000.0), 18.0, LOG)
    assert st["pos"]["E"] == 24000.0 and st["pos"]["fill"] == 24001.0
    # FOMC günü 19:00: henüz çıkış yok
    bars.append(bar(FOMC, 19 * 60, 24050.0))
    assert not df.step(st, bars, t_at(FOMC, 19 * 60) + 60, ds, (24051.0, 24050.0), 18.0, LOG)
    # 19:30 barı açıldı → çıkış
    bars.append(bar(FOMC, df.EXIT_MIN, 24100.0))
    assert df.step(st, bars, t_at(FOMC, df.EXIT_MIN) + 30, ds, (24101.0, 24100.0), 18.0, LOG)
    assert st["pos"] is None and FOMC.isoformat() in st["done"]
    res = [r for r in records(files) if r["kind"] == "result"][0]
    assert res["bp_model"] == pytest.approx(df.model_bp(24000.0, 24100.0, 1), abs=0.01)
    assert res["bp_fill"] is not None and res["nights"] == 1
    # aynı olay tekrar açılmaz
    assert not df.step(st, bars, t_at(FOMC, df.EXIT_MIN) + 600, ds, None, None, LOG)


def test_late_entry_uses_bar_open_but_no_fill(files):
    st = df._load_state()
    bars = [bar(ENTRY, df.ENTRY_MIN, 24000.0)]
    df.step(st, bars, t_at(ENTRY, df.ENTRY_MIN) + 1200, [FOMC], (24001.0, 24000.0), None, LOG)
    assert st["pos"]["E"] == 24000.0 and st["pos"]["fill"] is None


def test_missed_when_bot_down_on_entry_day(files):
    st = df._load_state()
    assert df.step(st, [], t_at(FOMC, 10 * 60), [FOMC], None, None, LOG)
    assert st["pos"] is None and records(files)[-1] == {"kind": "missed", "fomc": FOMC.isoformat(), "why": "bot_kapali"}


def test_before_entry_time_nothing(files):
    st = df._load_state()
    assert not df.step(st, [bar(ENTRY, 17 * 60, 1.0)], t_at(ENTRY, 17 * 60 + 10), [FOMC], None, None, LOG)
    assert st["pos"] is None


def test_summarize():
    s = df.summarize([{"kind": "result", "bp_model": 30.0, "bp_fill": 28.0}, {"kind": "result", "bp_model": -10.0, "bp_fill": None},
                      {"kind": "missed"}])
    assert s["n"] == 2 and s["bp_model"] == 10.0 and s["isabet"] == 0.5 and s["n_fill"] == 1 and s["kacirilan"] == 1


def test_research_parity():
    """Araştırmadaki broker işlemleri: bar açılışı → bar açılışı, modelle aynı yön ve büyüklük (spread/swap farkı küçük)."""
    import csv
    p = Path(__file__).resolve().parent.parent / "research/dax_profesor_20261112/results/d3_broker_islemler.csv"
    if not p.exists():
        pytest.skip("araştırma çıktısı yok (kutuda research/ sparse-checkout dışı)")
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == 52
    mean_gross = sum(float(r["gross"]) for r in rows) / len(rows)
    assert mean_gross == pytest.approx(34.1, abs=0.5)
