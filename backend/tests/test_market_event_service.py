"""market_event_service çekirdek mantık testleri.

Gelecek-bug koruması: makro pencere hesabı (overnight gap dahil), haber
başlık-dedup'u (RSS+Telegram çakışması), mum bulma toleransı, teknik anomali
sınıflaması ve marker dedup davranışını kilitler.
"""
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from services.market_event_service import (
    _classify_magnitude,
    _compute_technicals,
    _dedupe_news_items,
    _find_candle_index,
    _headline_key,
    _macro_window_change,
    canonical_symbol,
)


# ── canonical_symbol ──────────────────────────────────────────────────────────

def test_canonical_symbol_aliases():
    assert canonical_symbol("NDX") == "NDX.INDX"
    assert canonical_symbol("dax") == "GDAXI.INDX"
    assert canonical_symbol("XAUUSD") == "XAUUSD"
    assert canonical_symbol("usoil") == "USOIL.FOREX"
    assert canonical_symbol("BILINMEYEN") == "BILINMEYEN"


# ── _headline_key + dedup (haber çakışması) ───────────────────────────────────

def test_headline_key_normalizes_similar_headlines():
    a = _headline_key("Fed Signals Potential Rate Cuts in September Meeting")
    b = _headline_key("FED signals potential rate cuts in September meeting!!!")
    assert a == b and a != ""


def test_headline_key_distinguishes_different_news():
    a = _headline_key("Gold surges on Fed rate cut signals")
    b = _headline_key("Oil drops on OPEC supply increase")
    assert a != b


def test_dedupe_news_items_keeps_highest_urgency_copy():
    items = [
        {"id": "rss-1", "title": "Fed cuts rates by 25bp", "impact": "medium", "score": 5},
        {"id": "tg-99", "title": "FED cuts rates by 25bp!", "impact": "breaking", "score": 8},
        {"id": "rss-2", "title": "Oil inventories rise unexpectedly", "impact": "high", "score": 6},
    ]
    deduped = _dedupe_news_items(items)
    ids = {item["id"] for item in deduped}
    assert len(deduped) == 2
    assert "tg-99" in ids          # breaking kopya kazandı
    assert "rss-1" not in ids      # düşük aciliyetli kopya elendi
    assert "rss-2" in ids


def test_dedupe_news_items_empty_title_passthrough():
    items = [{"id": "1", "title": ""}, {"id": "2", "title": None}]
    assert len(_dedupe_news_items(items)) == 2


# ── _macro_window_change ──────────────────────────────────────────────────────

def _series(hours_values):
    idx = pd.DatetimeIndex(
        [datetime(2026, 7, 8, h, tzinfo=timezone.utc) for h, _ in hours_values]
    )
    return pd.DataFrame({"close": [v for _, v in hours_values]}, index=idx)


def test_macro_window_change_includes_bar_at_window_start():
    """Bar-start etiketli seride mumun kendi saatindeki bar dahil edilmeli
    (overnight gap yakalama — VIX +11.4% vakası)."""
    df = _series([(5, 100.0), (6, 100.0), (8, 111.4)])  # 7'de bar yok (kapalı)
    start = datetime(2026, 7, 8, 8, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    change, spark = _macro_window_change(df, start, end)
    assert change == pytest.approx(11.4, abs=0.01)
    assert len(spark) >= 2


def test_macro_window_change_no_reference_returns_none():
    df = _series([(8, 100.0)])  # pencere öncesi veri yok
    start = datetime(2026, 7, 8, 8, tzinfo=timezone.utc)
    change, spark = _macro_window_change(df, start, start + timedelta(hours=1))
    assert change is None and spark == []


def test_macro_window_change_empty_window_uses_reference():
    """Pencerede bar yoksa (hafta sonu) değişim 0 olmalı, çökmemeli."""
    df = _series([(5, 100.0), (6, 101.0)])
    start = datetime(2026, 7, 8, 12, tzinfo=timezone.utc)
    change, _ = _macro_window_change(df, start, start + timedelta(hours=1))
    assert change == pytest.approx(0.0)


def test_macro_window_change_none_df_fail_open():
    change, spark = _macro_window_change(
        None,
        datetime(2026, 7, 8, tzinfo=timezone.utc),
        datetime(2026, 7, 8, 1, tzinfo=timezone.utc),
    )
    assert change is None and spark == []


# ── _find_candle_index ────────────────────────────────────────────────────────

def _candles(n=30, start_ms=1_700_000_000_000, step_ms=3_600_000, base=100.0):
    out = []
    for i in range(n):
        out.append({
            "timestamp": start_ms + i * step_ms,
            "open": base, "high": base + 1.0, "low": base - 1.0,
            "close": base + 0.5, "volume": 1000.0,
        })
    return out


def test_find_candle_index_exact_bucket():
    candles = _candles()
    # 5. mumun ortasına düşen timestamp o mumu bulmalı
    target = candles[5]["timestamp"] + 30 * 60 * 1000
    assert _find_candle_index(candles, target, 60) == 5


def test_find_candle_index_rejects_far_timestamp():
    candles = _candles()
    far = candles[-1]["timestamp"] + 10 * 3_600_000  # son mumdan 10 saat sonra
    assert _find_candle_index(candles, far, 60) == -1


# ── _compute_technicals + magnitude ───────────────────────────────────────────

def test_classify_magnitude_thresholds():
    assert _classify_magnitude(3.5)[0] == "extreme"
    assert _classify_magnitude(2.2)[0] == "big"
    assert _classify_magnitude(1.5)[0] == "notable"
    assert _classify_magnitude(0.8)[0] == "minor"
    assert _classify_magnitude(None)[0] == "minor"


def test_compute_technicals_flags_anomalous_candle():
    candles = _candles(30)
    # Son mumu 5× büyüklükte anomaliye çevir
    candles[-1] = {
        "timestamp": candles[-1]["timestamp"],
        "open": 100.0, "high": 108.0, "low": 98.0, "close": 99.0,
        "volume": 8000.0,
    }
    tech = _compute_technicals(candles, len(candles) - 1)
    assert tech["is_significant"] is True
    assert tech["range_vs_atr"] is not None and tech["range_vs_atr"] > 2.0
    assert tech["direction"] == "down"
    assert tech["volume_ratio"] is not None and tech["volume_ratio"] > 2.0
    # Sızıntısızlık: ATR seçili mumun kendisini içermemeli → normal mumla aynı
    normal_tech = _compute_technicals(_candles(30), 29)
    assert tech["atr20"] == normal_tech["atr20"]


def test_compute_technicals_zero_open_no_crash():
    candles = _candles(25)
    candles[10]["open"] = 0.0
    tech = _compute_technicals(candles, 10)
    assert tech["change_pct"] == 0.0
