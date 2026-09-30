"""MT5 kaydedici beslemesi — saf dönüşümler + DataHub öncelik/sahiplik kuralları.

Vaka: 2026-09-03'ten beri hybrid mod USOIL'de Yahoo CL=F kullanıyordu (broker
SpotCrude'dan 0,1–4,7$ farklı). Besleme broker barlarını `mt5_recorder` kaynağıyla alır.
"""
import asyncio
import time

import pytest

from services import data_hub as hub
from services import mt5_recorder_feed as feed


def test_row_to_candle_utc_ms():
    c = feed.row_to_candle({"candle_time": "2026-09-28T12:10:00+00:00", "open": 98.67,
                            "high": 98.756, "low": 98.603, "close": 98.719, "volume": 120})
    assert c["timestamp"] == 1790597400000 and c["close"] == 98.719


def test_row_to_candle_bozuk_satir():
    assert feed.row_to_candle({"candle_time": None}) is None
    assert feed.row_to_candle({"candle_time": "2026-09-28T12:10:00+00:00"}) is None


def test_latest_price_taze_ve_bayat():
    now = 1790683800 + 60 + 30
    bars = [{"timestamp": 1790683740000, "close": 1.0}, {"timestamp": 1790683800000, "close": 2.0}]
    assert feed.latest_price(bars, now) == (2.0, 1790683860)
    assert feed.latest_price(bars, now + feed.MAX_PRICE_AGE_SEC + 5) is None
    assert feed.latest_price([], now) is None


def test_varsayilan_kapsam_yalniz_usoil(monkeypatch):
    monkeypatch.delenv("MT5_RECORDER_FEED_SYMBOLS", raising=False)
    assert feed.feed_symbols() == ["USOIL.FOREX"]
    monkeypatch.setenv("MT5_RECORDER_FEED_SYMBOLS", "USOIL.FOREX, XAUUSD")
    assert feed.feed_symbols() == ["USOIL.FOREX", "XAUUSD"]


def test_mt5_fiyati_yahoo_zaman_damgasini_ezer():
    sym = "USOIL.FOREX"
    now = time.time()
    hub._prices[sym] = {"price": 91.02, "timestamp": now, "source": "upstream_poll"}
    ok = asyncio.run(hub.ingest_live_price(sym, 94.6, timestamp=now - 90,
                                           source=hub.MT5_RECORDER_SOURCE))
    assert ok and hub._prices[sym]["price"] == 94.6
    assert hub._mt5_price_is_fresh(sym)            # 90 sn < 300 sn kaydedici penceresi


def test_yahoo_mt5_fiyatini_ezmez_sirasi_korunur():
    sym = "USOIL.FOREX"
    now = time.time()
    hub._prices[sym] = {"price": 94.6, "timestamp": now, "source": hub.MT5_RECORDER_SOURCE}
    ok = asyncio.run(hub.ingest_live_price(sym, 91.0, timestamp=now - 60, source="mt5_redis"))
    assert not ok                                  # MT5→MT5: eski damga yine reddedilir


def test_sahiplik_besleme_calismiyorsa_yok(monkeypatch):
    monkeypatch.setitem(feed._state, "running", False)
    assert hub.recorder_feed_owns("USOIL.FOREX") is False


def test_sahiplik_ilk_yuklemeden_sonra(monkeypatch):
    monkeypatch.setitem(feed._state, "running", True)
    monkeypatch.setitem(feed._state, "symbols", {"USOIL.FOREX": {"seeded": True}})
    assert hub.recorder_feed_owns("USOIL.FOREX") is True
    assert hub.recorder_feed_owns("USOIL") is True          # takma ad
    assert hub.recorder_feed_owns("NDX.INDX") is False


def test_replace_candles_yahoo_gecmisini_siler():
    sym = "USOIL.FOREX"
    hub._candles_5m[sym] = {"candles": [{"timestamp": 1790000000000, "open": 90, "high": 90,
                                         "low": 90, "close": 90, "volume": 0}],
                            "timestamp": 0, "source": "upstream_poll"}
    base = 1790683800000
    bars = [{"timestamp": base + i * 300_000, "open": 98.0, "high": 98.2, "low": 97.9,
             "close": 98.1, "volume": 1} for i in range(3)]
    n = hub.replace_candles(sym, "5m", bars, hub.MT5_RECORDER_SOURCE)
    st = hub._candles_5m[sym]
    assert n == 3 and len(st["candles"]) == 3 and st["source"] == hub.MT5_RECORDER_SOURCE
    assert all(c["close"] == 98.1 for c in st["candles"])
    assert hub._mt5_candles_are_fresh(sym, "5m")


def test_bos_okumada_sahiplik_alinmaz(monkeypatch):
    """RLS yüzünden boş okuma → seeded False, Yahoo yedeği kapanmaz (2026-09-30 olayı)."""
    class EmptyDB:
        def table(self, *_):
            return self
        def select(self, *_):
            return self
        def eq(self, *_):
            return self
        def gte(self, *_):
            return self
        def order(self, *_, **__):
            return self
        def range(self, *_):
            return self
        def execute(self):
            class R:
                data = []
            return R()
    monkeypatch.setitem(feed._state, "symbols", {})
    monkeypatch.setitem(feed._state, "running", True)
    asyncio.run(feed._cycle(EmptyDB()))
    assert feed._state["symbols"]["USOIL.FOREX"]["seeded"] is False
    assert hub.recorder_feed_owns("USOIL.FOREX") is False
