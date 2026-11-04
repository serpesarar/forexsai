"""candle_cache karışık besleme kilitleri (2026-11-04).

Vaka: Yahoo barları broker satırlarının üstüne yazıldı; kaydedici soğuk açılışta geçmişi
tek offset'le 60 dk kaydırdı. Bkz. analyst_reports/candle_cache_karisik_besleme_2026-11-04.md
"""
import asyncio
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services import candle_cache_store as store
from services import candle_integrity as integrity
from services import data_hub as hub

_path = Path(__file__).resolve().parents[2] / "yeni deneme" / "broker_time.py"
_spec = importlib.util.spec_from_file_location("broker_time", _path)
broker_time = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(broker_time)


def _epoch(*args) -> int:
    return int(datetime(*args, tzinfo=timezone.utc).timestamp())


@pytest.mark.parametrize("wall,expected_hours", [
    ((2026, 3, 6, 16, 30), 2),    # ABD geçişinden önceki Cuma
    ((2026, 3, 9, 16, 30), 3),    # ABD geçti, AB geçmedi: yine NY + 7
    ((2026, 3, 30, 16, 30), 3),
    ((2026, 7, 15, 16, 30), 3),
    ((2026, 10, 30, 23, 54), 3),  # son yaz barı (box_b.csv)
    ((2026, 11, 2, 1, 0), 2),     # ilk kış barı (box_bars.csv)
    ((2027, 1, 15, 16, 30), 2),
    ((2027, 3, 15, 16, 30), 3),   # bir sonraki yılın geçişi (14 Mart 2027)
])
def test_broker_donem_offseti(wall, expected_hours):
    assert broker_time.rule_offset_sec(_epoch(*wall)) == expected_hours * 3600


def test_acilis_saati_kurala_gore_ayni_utc_degil_ny():
    # 09:30 ET: yazın 13:30 UTC, kışın 14:30 UTC; sunucuda hep 16:30
    summer = _epoch(2026, 10, 27, 16, 30)
    winter = _epoch(2026, 11, 3, 16, 30)
    assert datetime.fromtimestamp(summer - broker_time.rule_offset_sec(summer), tz=timezone.utc).hour == 13
    assert datetime.fromtimestamp(winter - broker_time.rule_offset_sec(winter), tz=timezone.utc).hour == 14


def test_olcum_kurala_uymuyorsa_guvenme():
    now = _epoch(2026, 11, 4, 12, 0)
    assert broker_time.rule_matches_measured(2 * 3600, now) is True
    assert broker_time.rule_matches_measured(3 * 3600, now) is False


@pytest.mark.parametrize("source,timeframe,allowed", [
    ("upstream_poll", "5m", False),
    ("upstream_poll", "1h", False),
    ("dynamic_fallback", "1m", False),
    (hub.MT5_RECORDER_SOURCE, "1m", False),   # kaydedici zaten yazdı
    ("mt5_redis", "5m", True),
    ("upstream_poll", "eod", True),           # kaydedici günlük bar yazmaz
])
def test_kaynak_yazma_kilidi(source, timeframe, allowed):
    assert hub._may_persist(timeframe, source) is allowed


def test_yahoo_ingest_cache_e_yazmaz(monkeypatch):
    calls = []
    monkeypatch.setattr(store, "persist_candles", lambda *a, **k: calls.append(a) or 1)
    monkeypatch.setattr(hub, "_persist_timestamps", {})
    bar = {"timestamp": 1793700000000, "open": 29290.5, "high": 29300.5, "low": 29280.5, "close": 29290.5, "volume": 10}
    asyncio.run(hub.ingest_candles("NDX.INDX", "1m", [bar], source="dynamic_fallback"))
    assert calls == []


class _Table:
    def __init__(self, sink, select_error=None):
        self.sink = sink
        self.select_error = select_error

    def upsert(self, rows, on_conflict=None):
        self.sink.extend(rows)
        return {"data": rows, "error": None}

    def select(self, *_):
        return self

    def limit(self, _):
        return self

    def execute(self):
        return {"data": [], "error": self.select_error}


class _DB:
    def __init__(self, select_error=None):
        self.rows = []
        self.select_error = select_error

    def table(self, name):
        return _Table(self.rows if name == "candle_cache" else [], self.select_error)


def test_persist_yabanci_seriyi_reddeder_kaynagi_yazar(monkeypatch):
    db = _DB()
    monkeypatch.setattr(store, "_get_db", lambda: db)
    monkeypatch.setattr(store, "_source_column_known", None)
    ok = {"timestamp": 1793700000000, "open": 1, "high": 1, "low": 1, "close": 98.719, "volume": 1}
    yahoo = {"timestamp": 1793700060000, "open": 1, "high": 1, "low": 1, "close": 29290.773438, "volume": 1}
    assert store.persist_candles("USOIL.FOREX", "1m", [ok, yahoo], source="mt5_upload") == 1
    assert len(db.rows) == 1
    assert db.rows[0]["source"] == "mt5_upload" and db.rows[0]["fetched_at"]


def test_source_kolonu_yoksa_yazim_surer(monkeypatch):
    db = _DB(select_error="column candle_cache.source does not exist")
    monkeypatch.setattr(store, "_get_db", lambda: db)
    monkeypatch.setattr(store, "_source_column_known", None)
    bar = {"timestamp": 1793700000000, "open": 1, "high": 1, "low": 1, "close": 98.719, "volume": 1}
    assert store.persist_candles("USOIL.FOREX", "1m", [bar], source="mt5_upload") == 1
    assert "source" not in db.rows[0] and db.rows[0]["fetched_at"]


def test_persist_eod_yahoo_kabul(monkeypatch):
    db = _DB()
    monkeypatch.setattr(store, "_get_db", lambda: db)
    monkeypatch.setattr(store, "_source_column_known", None)
    bar = {"timestamp": 1793664000000, "open": 1, "high": 1, "low": 1, "close": 29290.773438, "volume": 1}
    assert store.persist_candles("NDX.INDX", "eod", [bar], source="upstream_eod") == 1


@pytest.mark.parametrize("close", [29290.7, 4001.25, 98.719, 0.0])
def test_broker_fiyati_yabanci_sayilmaz(close):
    assert integrity.has_foreign_decimals(close) is False
    assert store._is_foreign_price({"close": close}, "1m") is False


def test_integrity_temiz_seri():
    broker = {"1000": 10.5, "4600": 10.7}
    counts = integrity.assess_series({"4600": 10.7}, broker)
    assert counts["mismatch"] == 0 and integrity.series_issues("NDX.INDX", "1m", counts) == []


def test_integrity_kaymayi_ve_yahooyu_yakalar():
    broker = {str(i * 60): 100.0 + i for i in range(200)}
    shifted = {str((i + 60) * 60): 100.0 + i for i in range(100)}
    counts = integrity.assess_series(shifted, broker)
    assert counts["shifted"] == 100
    assert any("kayık" in issue for issue in integrity.series_issues("NDX.INDX", "1m", counts))
    counts = integrity.assess_series({"60": 29290.773438}, {"60": 29290.7})
    assert any("yabancı" in issue for issue in integrity.series_issues("NDX.INDX", "1m", counts))


def test_integrity_hub_yahoo_kaynagini_yakalar():
    good = {tf: "mt5_recorder" for tf in integrity.HUB_INTRADAY_TIMEFRAMES}
    sources = {s: good for s in integrity.SYMBOLS}
    prices = {s: "mt5_recorder" for s in integrity.SYMBOLS}
    assert integrity.hub_source_issues(sources, prices) == []
    bad = dict(sources, XAUUSD=dict(good, **{"1m": "dynamic_fallback"}))
    issues = integrity.hub_source_issues(bad, dict(prices, NDX=None, **{"GDAXI.INDX": "upstream_poll"}))
    assert any("XAUUSD/1m" in i for i in issues) and any("GDAXI.INDX: fiyat" in i for i in issues)


def test_xau_besleme_zinciri_gercek_1h_korur(monkeypatch):
    sym = "XAUUSD"
    monkeypatch.setattr(hub, "_persist_async", lambda *a, **k: None)
    start = 1793664000
    bars_5m = [{"timestamp": (start + i * 300) * 1000, "open": 4000.0, "high": 4001.0, "low": 3999.0,
                "close": 4000.5, "volume": 10} for i in range(600)]
    bars_1h = [{"timestamp": (start + i * 3600) * 1000, "open": 4000.0, "high": 4010.0, "low": 3990.0,
                "close": 4005.0, "volume": 100} for i in range(50)]
    assert hub.replace_candles(sym, "5m", bars_5m, hub.MT5_RECORDER_SOURCE)
    assert hub.replace_candles(sym, "1h", bars_1h, hub.MT5_RECORDER_SOURCE)
    hub._rebuild_derived(sym)
    assert "mt5" in hub._candles_1h[sym]["source"]
    assert hub._candles_1h[sym]["candles"][0]["high"] == 4010.0
    assert hub._candles_4h[sym]["candles"]
