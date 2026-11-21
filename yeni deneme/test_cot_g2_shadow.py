"""cot_g2_shadow.py birim testleri (MT5/ağ gerekmez). Çalıştır: cd 'yeni deneme' && python3 -m pytest test_cot_g2_shadow.py"""
from datetime import date, timedelta

import cot_g2_shadow as c


def test_select_cross_and_usd_fallback():
    z = {"EUR": 2.5, "GBP": 0.1, "JPY": -1.2, "AUD": 0.3, "CAD": 0.0, "CHF": 0.2, "NZD": -0.1}
    assert c.select(z) == ("EURJPY", -1, "EUR", "JPY")          # EUR uzun-kalabalık → EURJPY SAT
    z2 = {"EUR": 0.5, "GBP": 0.1, "JPY": 0.2, "AUD": 0.3, "CAD": -1.8, "CHF": 0.9, "NZD": -0.1}
    # CHF uzun-kalabalık, CAD kısa-kalabalık; CHFCAD/CADCHF listede yok → |z| büyük olan CAD, USD karşısında AL → USDCAD SAT
    assert c.select(z2) == ("USDCAD", -1, "CHF", "CAD")
    z3 = {"EUR": 0.5, "GBP": 0.1, "JPY": 0.2, "AUD": 0.3, "CAD": -2.2, "CHF": 0.1, "NZD": -0.1}
    assert c.select(z3) == ("EURCAD", -1, "EUR", "CAD")


def test_select_spread_threshold():
    z = {k: 0.5 for k in c.CODES.values()}
    z["EUR"] = 1.4
    assert c.select(z) is None                                   # 1,4 − 0 (USD) < 2


def test_zscore_needs_history():
    s = {date(2020, 1, 7) + timedelta(weeks=i): 0.1 * (i % 3) for i in range(30)}
    assert c.zscore_last(s, max(s)) is None
    s = {date(2020, 1, 7) + timedelta(weeks=i): 0.1 * (i % 3) for i in range(60)}
    assert c.zscore_last(s, max(s)) is not None


def test_resolve_tp_sl_same_bar_is_sl():
    pos = {"E": 1.0, "side": 1, "tp": 0.005, "sl": 0.03}
    assert c.resolve(pos, [{"o": 1, "h": 1.006, "l": 0.99, "c": 1}])["why"] == "TP"
    assert c.resolve(pos, [{"o": 1, "h": 1.006, "l": 0.96, "c": 1}])["why"] == "SL"
    bars = [{"o": 1, "h": 1.001, "l": 0.999, "c": 1.0 + i * 1e-4} for i in range(10)]
    r = c.resolve(pos, bars)
    assert r["why"] == "ZAMAN" and r["bars"] == 10 and abs(r["X"] - bars[9]["c"]) < 1e-12
    assert c.resolve(pos, bars[:9]) is None


def test_release_due_friday_evening():
    rep = date(2026, 11, 17)                                     # Salı
    from datetime import datetime, timezone
    fri_20 = datetime(2026, 11, 20, 20, tzinfo=timezone.utc).timestamp()
    assert not c.release_due(rep, fri_20)
    assert c.release_due(rep, fri_20 + 3600)
